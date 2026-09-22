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
    Exemplos: 'R$ 14,90', '14.90', 'POR: 8,79', '99,99', '23,50 UN'.
    """
    if not text:
        return None

    # Remove qualquer bloco <think>...</think> antes da extração
    cleaned_text = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL).strip()
    target = cleaned_text if cleaned_text else text

    # Padrão 1: Com prefixo R$ ou RS (ex: R$ 99,99)
    m1 = re.search(r'(?:R\$|RS|\$)\s*(\d{1,4}[,.]\d{2})', target, re.IGNORECASE)
    if m1:
        val_str = m1.group(1).replace(",", ".")
        try:
            val = float(val_str)
            if 0.10 <= val <= 9999.0:
                return val
        except ValueError:
            pass

    # Padrão 1b: Valor antes de R$ (ex: 99,99 R$)
    m1b = re.search(r'(\d{1,4}[,.]\d{2})\s*(?:R\$|RS|\$)', target, re.IGNORECASE)
    if m1b:
        val_str = m1b.group(1).replace(",", ".")
        try:
            val = float(val_str)
            if 0.10 <= val <= 9999.0:
                return val
        except ValueError:
            pass

    # Padrão 2: Apenas números decimais com vírgula ou ponto (ex: 99,99 ou 12.90)
    matches = re.findall(r'\b(\d{1,4}[,.]\d{2})\b', target)
    for m in matches:
        try:
            val = float(m.replace(",", "."))
            if 0.10 <= val <= 9999.0:
                return val
        except ValueError:
            continue

    return None


def optimize_image_bytes(image_bytes: bytes, max_dim: int = 1024, quality: int = 80) -> tuple[bytes, str]:
    """
    Otimiza e redimensiona imagem de câmera para envio ultra-rápido à API de visão.
    Reduz fotos brutas de smartphones (5-12MB) para ~25-70KB preservando os dígitos da etiqueta.
    Retorna (bytes_otimizados, mime_type).
    """
    if not image_bytes:
        return image_bytes, "image/jpeg"
    try:
        from io import BytesIO
        from PIL import Image

        with Image.open(BytesIO(image_bytes)) as img:
            if img.mode in ("RGBA", "P", "LA"):
                img = img.convert("RGB")

            w, h = img.size
            if max(w, h) > max_dim:
                scale = max_dim / float(max(w, h))
                new_w = max(1, int(w * scale))
                new_h = max(1, int(h * scale))
                img = img.resize((new_w, new_h), Image.Resampling.LANCZOS)

            out_buf = BytesIO()
            img.save(out_buf, format="JPEG", quality=quality, optimize=True)
            return out_buf.getvalue(), "image/jpeg"
    except Exception as err:
        logger.warning(f"[PriceScanner] Falha ao otimizar imagem com Pillow, usando bytes originais: {err}")
        mime_type = "image/jpeg"
        if image_bytes.startswith(b"\x89PNG"):
            mime_type = "image/png"
        elif image_bytes.startswith(b"RIFF") and b"WEBP" in image_bytes[:16]:
            mime_type = "image/webp"
        return image_bytes, mime_type


def extract_price_from_image_bytes(image_bytes: bytes, item_name: str = "") -> dict[str, Any]:
    """
    Envia a imagem da etiqueta para a API Groq com modelo multimodal de visão
    (qwen/qwen3.8-27b / qwen/qwen3.6-27b) para identificar e extrair o preço principal da gôndola.
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

        # Otimiza e comprime bytes da imagem para upload ultra-rápido no celular
        opt_bytes, mime_type = optimize_image_bytes(image_bytes)

        b64_image = base64.b64encode(opt_bytes).decode("utf-8")
        data_uri = f"data:{mime_type};base64,{b64_image}"

        # Modelos ativos no Groq com suporte nativo a visão multimodal
        vision_models = [
            "qwen/qwen3.8-27b",
            "qwen/qwen3.6-27b",
        ]

        target_hint = f" referente ao produto '{item_name}'" if item_name else ""
        prompt = (
            "Você é um leitor óptico especialista em etiquetas de preço de gôndola de supermercados brasileiros.\n"
            f"Analise a imagem da etiqueta e identifique o PREÇO DE VENDA PRINCIPAL{target_hint} em reais.\n"
            "Regras obrigatórias:\n"
            "1. O preço principal é o valor numérico em MAIOR DESTAQUE / MAIOR FONTE na etiqueta (geralmente ao lado ou acima de R$).\n"
            "2. IGNORE completamente valores secundários como impostos ('VL. APROX. TRIB', 'IBPT'), código de barras ou 'PRECO LITRO' / 'PRECO KG'.\n"
            "3. Se houver divergência no nome do produto, foque no valor principal impresso na etiqueta.\n"
            "4. Responda ESTRITAMENTE com o número decimal no formato X.XX ou X,XX (exemplo: 99.99 ou 1.99).\n"
            "5. Não inclua 'R$', explicações, tags <think> ou outros textos."
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
                    temperature=0.0,
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
                logger.warning(f"[PriceScanner] Tentativa no modelo {model} falhou: {m_err}")
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
