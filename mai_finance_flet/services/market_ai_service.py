"""
market_ai_service.py — Cotação inteligente de lista de compras com Groq e busca web (T-017).

Implementa:
- Consulta a sites oficiais de supermercados regionais (AC-023)
- Comparação de preços totais do carrinho entre 2 ou 3 redes (AC-024)
- Priorização de marcas líderes com melhor custo-benefício via Groq Llama 3.3 (AC-025)
- Seleção de supermercado único para toda a compra
"""
from __future__ import annotations

import json
import logging
import os
import re
from typing import Any
import httpx

import config
from services.geo_service import get_device_location, get_regional_markets

logger = logging.getLogger(__name__)

# Preços base de referência de produtos comuns do varejo brasileiro (fallback de segurança)
REFERENCE_PRICES: dict[str, dict[str, Any]] = {
    "leite": {"brand": "Itambé / Piracanjuba", "price": 5.49, "unit": "cx"},
    "cafe": {"brand": "Pilão / Melitta", "price": 18.90, "unit": "pct"},
    "café": {"brand": "Pilão / Melitta", "price": 18.90, "unit": "pct"},
    "arroz": {"brand": "Camil / Tio João", "price": 31.90, "unit": "pct"},
    "feijao": {"brand": "Camil / Kicaldo", "price": 8.49, "unit": "pct"},
    "feijão": {"brand": "Camil / Kicaldo", "price": 8.49, "unit": "pct"},
    "acucar": {"brand": "União", "price": 4.89, "unit": "pct"},
    "açúcar": {"brand": "União", "price": 4.89, "unit": "pct"},
    "oleo": {"brand": "Liza / Soya", "price": 7.39, "unit": "un"},
    "óleo": {"brand": "Liza / Soya", "price": 7.39, "unit": "un"},
    "detergente": {"brand": "Ypê", "price": 2.49, "unit": "un"},
    "banana": {"brand": "Prata Selecionada", "price": 7.99, "unit": "kg"},
    "maca": {"brand": "Fuji Nacional", "price": 9.90, "unit": "kg"},
    "maçã": {"brand": "Fuji Nacional", "price": 9.90, "unit": "kg"},
    "ovos": {"brand": "Mantiqueira Gr. 20un", "price": 16.50, "unit": "cx"},
    "pao": {"brand": "Pullman / Wickbold", "price": 8.90, "unit": "pct"},
    "pão": {"brand": "Pullman / Wickbold", "price": 8.90, "unit": "pct"},
    "sabao em po": {"brand": "Omo Lavagem Perfeita", "price": 23.90, "unit": "cx"},
    "sabão em pó": {"brand": "Omo Lavagem Perfeita", "price": 23.90, "unit": "cx"},
    "queijo": {"brand": "President / Tirolez", "price": 14.50, "unit": "pct"},
    "frango": {"brand": "Sadia / Seara", "price": 19.90, "unit": "kg"},
}

# Fatores de índice de preço médio por rede de supermercado
MARKET_PRICE_FACTORS: dict[str, float] = {
    "atacadao": 0.92,       # ~8% mais barato em média
    "carrefour": 1.00,      # Padrão
    "pao_de_acucar": 1.07,  # ~7% acima (sortimento premium)
    "guanabara": 0.93,
    "zona_sul": 1.08,
}


def search_web_market_prices(item_name: str, market_name: str = "", market_domain: str = "", city: str = "") -> list[str]:
    """
    Executa busca web inteligente nos sites ou ofertas do supermercado via HTTP.
    Retorna snippets de texto com produtos e preços encontrados.
    """
    if market_domain:
        query = f"site:{market_domain} {item_name} preço"
    else:
        city_term = f"{city} " if city else ""
        market_term = f"{market_name} " if market_name else "supermercado "
        query = f"{market_term}{city_term}{item_name} preço"

    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    results: list[str] = []
    try:
        url = f"https://html.duckduckgo.com/html/?q={query}"
        with httpx.Client(timeout=4.0) as client:
            resp = client.get(url, headers=headers)
            if resp.status_code == 200:
                matches = re.findall(r'<a class="result__snippet"[^>]*>(.*?)</a>', resp.text, re.DOTALL)
                for m in matches[:3]:
                    clean = re.sub(r"<[^>]+>", "", m).strip()
                    if clean:
                        results.append(clean)
    except Exception as exc:
        logger.debug(f"Busca web para {item_name} em {market_name or market_domain} utilizou fallback: {exc}")
    return results


def call_groq_to_structure_quote(
    market_name: str,
    market_id: str,
    items: list[dict[str, Any]],
    search_context: str,
    city: str = "",
) -> dict[str, Any]:
    """
    Utiliza o modelo Llama 3.3 da Groq para estruturar os dados de cotação oficial,
    priorizando o melhor custo-benefício em marcas líderes (AC-025).
    """
    api_key = getattr(config, "GROQ_API_KEY", "") or os.getenv("GROQ_API_KEY", "")
    if not api_key:
        return _build_fallback_market_quote(market_name, market_id, items)

    prompt_items = [
        {"name": it.get("name"), "quantity": it.get("quantity", 1), "unit": it.get("unit", "un")}
        for it in items
    ]

    city_info = f" na cidade/região de {city}" if city else ""
    system_prompt = (
        "Você é um especialista em compras de supermercado e cotação de varejo brasileiro. "
        f"Sua missão é cotar a lista de compras para a rede de supermercado especificada{city_info}.\n"
        "Regras obrigatórias:\n"
        "1. Para CADA item, forneça 2 ou 3 opções de marcas disponíveis com preços diferentes (da mais barata à mais cara).\n"
        "2. Priorize MARCAS LÍDERES/CONHECIDAS com o MELHOR CUSTO-BENEFÍCIO (ex: Camil, Tio João, Nestlé, Pilão, Ypê, Omo, Sadia, Piracanjuba).\n"
        "3. Responda ESTRITAMENTE em formato JSON puro, sem blocos markdown ou texto adicional.\n"
        "Estrutura JSON exigida:\n"
        "{\n"
        '  "market_name": "Nome do Mercado",\n'
        '  "items": [\n'
        '    {"name": "Item Original", "selected_brand": "Marca Melhor Custo-Benefício", "selected_price": 0.00, "brand_options": ['
        '{"brand": "Marca A", "price": 0.00, "product_title": "Descrição Produto A 1kg"}, '
        '{"brand": "Marca B", "price": 0.00, "product_title": "Descrição Produto B 1kg"}, '
        '{"brand": "Marca C", "price": 0.00, "product_title": "Descrição Produto C 1kg"}'
        '], "quantity": 1}\n'
        "  ]\n"
        "}")

    user_prompt = (
        f"Rede de Supermercado: {market_name}{city_info}\n"
        f"Itens da lista para cotar: {json.dumps(prompt_items, ensure_ascii=False)}\n"
        f"Contexto de busca web oficial:\n{search_context or 'Nenhum snippet adicional disponível'}"
    )

    try:
        from groq import Groq
        groq_client = Groq(api_key=api_key)
        models_to_try = [
            "llama-3.3-70b-versatile",
            "openai/gpt-oss-20b",
            "openai/gpt-oss-120b",
            "groq/compound",
            "qwen/qwen3.8-27b",
        ]
        raw_text = ""
        for model in models_to_try:
            try:
                completion = groq_client.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    temperature=0.2,
                    max_tokens=1500,
                )
                raw_text = completion.choices[0].message.content or ""
                if raw_text:
                    break
            except Exception as m_err:
                logger.info(f"Tentativa com modelo {model} no Groq: {m_err}")
                continue

        if not raw_text:
            return _build_fallback_market_quote(market_name, market_id, items)

        # Limpa possíveis delimitadores markdown ```json ... ```
        clean_json = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw_text.strip(), flags=re.MULTILINE)
        data = json.loads(clean_json)

        # Monta a estrutura final calculada
        return _format_market_quote_data(market_name, market_id, items, data.get("items", []))
    except Exception as exc:
        logger.warning(f"Erro ao chamar Groq AI para cotação ({exc}); usando motor de referência.")
        return _build_fallback_market_quote(market_name, market_id, items)


def quote_shopping_list(
    items: list[dict[str, Any]],
    location: dict[str, Any] | None = None,
    target_market: str | None = None,
    city: str | None = None,
) -> dict[str, Any]:
    """
    Realiza a cotação da lista de compras.
    Se `target_market` estiver especificado, cota diretamente para esse mercado na cidade escolhida.
    Caso contrário, cota comparativamente entre as redes da cidade (AC-023, AC-024).
    """
    if not items:
        return {"markets": [], "best_option": None, "location": {}, "single_market": False}

    loc = location or get_device_location()
    effective_city = city.strip() if city and city.strip() else loc.get("city", "São Paulo")
    loc["city"] = effective_city

    # Caso 1: Mercado específico informado pelo usuário
    is_specific = bool(target_market and target_market.strip() and target_market.strip().lower() not in ["todos os mercados da cidade", "todos"])
    if is_specific:
        m_name = target_market.strip()
        m_id = re.sub(r"[^a-zA-Z0-9_]+", "_", m_name.lower()).strip("_")
        search_snippets: list[str] = []
        for it in items[:4]:
            snips = search_web_market_prices(it.get("name", ""), market_name=m_name, city=effective_city)
            search_snippets.extend(snips)

        context_str = "\n".join(search_snippets)
        market_quote = call_groq_to_structure_quote(m_name, m_id, items, context_str, city=effective_city)
        market_quote["badge"] = f"Selecionado ({effective_city})"

        return {
            "location": loc,
            "markets": [market_quote],
            "best_option": m_name,
            "items_count": len(items),
            "single_market": True,
        }

    # Caso 2: Cotação comparativa entre redes da cidade
    regional_markets = get_regional_markets(effective_city)
    quotes: list[dict[str, Any]] = []

    for m in regional_markets[:3]:
        m_name = m["name"]
        m_id = m["id"]
        m_domain = m.get("domain", "")

        search_snippets: list[str] = []
        for it in items[:4]:
            snips = search_web_market_prices(it.get("name", ""), market_name=m_name, market_domain=m_domain, city=effective_city)
            search_snippets.extend(snips)

        context_str = "\n".join(search_snippets)
        market_quote = call_groq_to_structure_quote(m_name, m_id, items, context_str, city=effective_city)
        market_quote["badge"] = m.get("badge", "")
        quotes.append(market_quote)

    best_market = min(quotes, key=lambda q: q.get("total_amount", float("inf"))) if quotes else None

    return {
        "location": loc,
        "markets": quotes,
        "best_option": best_market.get("market_name") if best_market else None,
        "items_count": len(items),
        "single_market": False,
    }



def _format_market_quote_data(
    market_name: str,
    market_id: str,
    original_items: list[dict[str, Any]],
    ai_items: list[dict[str, Any]],
) -> dict[str, Any]:
    """Formata os itens cotados com múltiplas opções de marca (DEC-027) e calcula o total do carrinho."""
    ai_by_name = {it.get("name", "").lower(): it for it in ai_items}
    formatted_items: list[dict[str, Any]] = []
    total_amount = 0.0

    for it in original_items:
        orig_name = it.get("name", "")
        qty = float(it.get("quantity", 1.0) or 1.0)
        ai_it = ai_by_name.get(orig_name.lower())

        if ai_it:
            # Novo formato com brand_options (DEC-027)
            brand_options = ai_it.get("brand_options", [])
            selected_brand = ai_it.get("selected_brand") or ai_it.get("brand", "Marca Líder")
            selected_price = float(ai_it.get("selected_price") or ai_it.get("unit_price") or 0)

            # Se não veio brand_options mas veio brand/unit_price no formato antigo, cria opção única
            if not brand_options and ai_it.get("unit_price"):
                brand_options = [{
                    "brand": selected_brand,
                    "price": selected_price,
                    "product_title": ai_it.get("product_title", f"{orig_name} ({selected_brand})"),
                }]

            unit_price = selected_price if selected_price > 0 else (brand_options[0]["price"] if brand_options else 0)
            brand = selected_brand
            title = ai_it.get("product_title", f"{orig_name} ({brand})")
        else:
            ref = _get_reference_item(orig_name)
            factor = MARKET_PRICE_FACTORS.get(market_id, 1.0)
            unit_price = round(ref["price"] * factor, 2)
            brand = ref["brand"]
            title = f"{orig_name} - {brand}"
            brand_options = _generate_brand_variants(orig_name, ref, factor)

        item_total = round(unit_price * qty, 2)
        total_amount += item_total

        formatted_items.append({
            "id": it.get("id"),
            "name": orig_name,
            "quantity": qty,
            "unit": it.get("unit", "un"),
            "corridor_category": it.get("corridor_category", "Outros"),
            "brand": brand,
            "product_title": title,
            "unit_price": unit_price,
            "total_price": item_total,
            "brand_options": brand_options,
        })

    return {
        "market_id": market_id,
        "market_name": market_name,
        "total_amount": round(total_amount, 2),
        "items": formatted_items,
    }


def _build_fallback_market_quote(
    market_name: str,
    market_id: str,
    items: list[dict[str, Any]],
) -> dict[str, Any]:
    """Constrói cotação com dados de referência calibrados por rede de supermercado."""
    factor = MARKET_PRICE_FACTORS.get(market_id, 1.0)
    formatted_items: list[dict[str, Any]] = []
    total_amount = 0.0

    for it in items:
        orig_name = it.get("name", "")
        qty = float(it.get("quantity", 1.0) or 1.0)
        ref = _get_reference_item(orig_name)

        unit_price = round(ref["price"] * factor, 2)
        item_total = round(unit_price * qty, 2)
        total_amount += item_total
        brand_options = _generate_brand_variants(orig_name, ref, factor)

        formatted_items.append({
            "id": it.get("id"),
            "name": orig_name,
            "quantity": qty,
            "unit": it.get("unit", "un"),
            "corridor_category": it.get("corridor_category", "Outros"),
            "brand": ref["brand"],
            "product_title": f"{orig_name} ({ref['brand']})",
            "unit_price": unit_price,
            "total_price": item_total,
            "brand_options": brand_options,
        })

    return {
        "market_id": market_id,
        "market_name": market_name,
        "total_amount": round(total_amount, 2),
        "items": formatted_items,
    }


def _generate_brand_variants(name: str, ref: dict[str, Any], factor: float) -> list[dict[str, Any]]:
    """Gera 2-3 variantes de marca com preços calibrados para fallback (DEC-027)."""
    base_price = round(ref["price"] * factor, 2)
    primary_brand = ref["brand"]

    # Gera variantes com ajuste de +/- 10-15%
    variants = [
        {
            "brand": primary_brand.split(" / ")[0].strip() if " / " in primary_brand else primary_brand,
            "price": base_price,
            "product_title": f"{name} ({primary_brand.split(' / ')[0].strip()})",
        },
    ]

    if " / " in primary_brand:
        alt_brand = primary_brand.split(" / ")[1].strip()
        alt_price = round(base_price * 1.08, 2)
        variants.append({
            "brand": alt_brand,
            "price": alt_price,
            "product_title": f"{name} ({alt_brand})",
        })

    # Opção econômica
    eco_price = round(base_price * 0.85, 2)
    variants.append({
        "brand": "Marca Própria",
        "price": eco_price,
        "product_title": f"{name} (Marca Própria do Mercado)",
    })

    return variants


def _get_reference_item(name: str) -> dict[str, Any]:
    """Recupera dados de referência de preço e marca líder para um item."""
    clean = name.lower().strip()
    for k, v in REFERENCE_PRICES.items():
        if k in clean or clean in k:
            return v
    return {"brand": "Marca Recomendada", "price": 9.90, "unit": "un"}
