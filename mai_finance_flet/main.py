"""
main.py — Ponto de entrada oficial para o aplicativo Android (APK) e Desktop.
Importa a função principal `main` de app.py e inicializa a aplicação Flet em modo nativo.
"""
import os
import sys

# Garante que o diretório da aplicação está no sys.path
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

import flet as ft
from app import main

if __name__ == "__main__":
    assets_path = os.path.join(CURRENT_DIR, "assets")
    ft.run(
        main,
        assets_dir=assets_path,
    )
