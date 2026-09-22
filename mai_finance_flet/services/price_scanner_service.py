"""
price_scanner_service.py — Serviço de extração inteligente de preços de etiquetas de supermercado.

Utiliza visão computacional (Groq Llama 3.2 Vision) para extrair o valor
numérico da etiqueta de gôndola fotografada pela câmera do celular.
"""
from __future__ import annotations

import base64
import logging
import os
import re
from typing import Any

import config

logger = logging.getLogger(__name__)


def extract_price_from_text(text: str) -> float | None:
    """
    Extrai valor monetário brasileiro de uma string de texto.
    Exemplos: 'R$ 14,90', '14.90', 'POR: 8,79', '23,50 UN'.
    """
    if not text:
        return None

    # Padrão 1: Com prefixo R$ ou RS (ex: R$ 12,99)
    m1 = re.search(r'(?:R\$|RS|\$)\s*(\d{1,4}[,.]\d{2})', text, re.IGNORECASE)
    if m1:
        val_str = m1.group(1).replace(",", ".")
        try:
            val = float(val_str)
            if 0.10 <= val <= 9999.0:
                return val
        except ValueError:
            pass

    # Padrão 2: Apenas números decimais com vírgula ou ponto (ex: 12,99 ou 5.49)
    matches = re.findall(r'\b(\d{1,4}[,.]\d{2})\b', text)
    for m in matches:
        try:
            val = float(m.replace(",", "."))
            if 0.10 <= val <= 9999.0:
                return val
        except ValueError:
            continue

    return None


def extract_price_from_image_bytes(image_bytes: bytes, item_name: str = "") -> dict[str, Any]:
    """
    Envia a imagem da etiqueta para a API Groq com modelo de visão (Llama 3.2 11B/90B Vision)
    para identificar e extrair o preço final da etiqueta com alta precisão.
    """
    if not image_bytes:
        return {"success": False, "price": None, "error": "Dados da imagem vazios"}

    api_key = getattr(config, "GROQ_API_KEY", "") or os.getenv("GROQ_API_KEY", "")
    if not api_key:
        logger.warning("[PriceScanner] GROQ_API_KEY não configurada para visão computacional.")
        return {"success": False, "price": None, "error": "Chave de IA Groq não configurada"}

    try:
        from groq import Groq
        groq_client = Groq(api_key=api_key)

        b64_image = base64.b64encode(image_bytes).decode("utf-8")
        data_uri = f"data:image/jpeg;base64,{b64_image}"

        vision_models = [
            "llama-3.2-11b-vision-preview",
            "llama-3.2-90b-vision-preview",
        ]

        target_hint = f" referente ao produto '{item_name}'" if item_name else ""
        prompt = (
            f"Você é um leitor óptico de etiquetas de preço de supermercado brasileiro. "
            f"Analise a imagem da etiqueta de gôndola e identifique o PREÇO DE VENDA PRINCIPAL{target_hint} em reais. "
            "Responda ESTRITAMENTE com o número do preço (exemplo: 12.90). Não inclua 'R$', texto, markdown ou explicações."
        )

        for model in vision_models:
            try:
                response = groq_client.chat.completions.create(
                    model=model,
                    messages=[
                        {
                            "role": "user",
                            "content": [
                                {"type": "text", "text": prompt},
                                {
                                    "type": "image_url",
                                    "image_url": {"url": data_uri},
                                },
                            ],
                        }
                    ],
                    temperature=0.1,
                    max_tokens=50,
                )
                raw_answer = (response.choices[0].message.content or "").strip()
                logger.info(f"[PriceScanner] Resposta do modelo {model}: {raw_answer}")
                price = extract_price_from_text(raw_answer)
                if price is not None:
                    return {
                        "success": True,
                        "price": price,
                        "raw_text": raw_answer,
                        "model": model,
                    }
            except Exception as m_err:
                logger.debug(f"[PriceScanner] Tentativa no modelo {model} falhou: {m_err}")
                continue

        return {"success": False, "price": None, "error": "Preço não detectado na etiqueta fotografada"}

    except Exception as exc:
        logger.error(f"[PriceScanner] Erro na chamada de visão da Groq: {exc}")
        return {"success": False, "price": None, "error": f"Erro na análise de visão: {exc}"}


def extract_price_from_base64(b64_str: str, item_name: str = "") -> dict[str, Any]:
    """Decodifica string base64 e processa extração de preço."""
    try:
        data = base64.b64decode(b64_str)
        return extract_price_from_image_bytes(data, item_name=item_name)
    except Exception as exc:
        return {"success": False, "price": None, "error": f"Erro ao decodificar imagem: {exc}"}


def extract_price_from_file_path(file_path: str, item_name: str = "") -> dict[str, Any]:
    """Lê o arquivo de imagem do disco e processa a extração do preço."""
    try:
        if not os.path.exists(file_path):
            return {"success": False, "price": None, "error": "Arquivo de imagem não encontrado"}
        with open(file_path, "rb") as f:
            data = f.read()
        return extract_price_from_image_bytes(data, item_name=item_name)
    except Exception as exc:
        logger.error(f"[PriceScanner] Erro ao ler arquivo {file_path}: {exc}")
        return {"success": False, "price": None, "error": f"Erro ao ler imagem: {exc}"}
