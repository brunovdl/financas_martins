#!/usr/bin/env python3
"""
inject_version.py — Injeta dinamicamente a versão calculada no app Flet e gera arquivos de versão.
"""
import argparse
import json
import os
import re
import sys


def inject_version(version: str, build_number: str) -> None:
    version_clean = version.strip().lstrip("vV")
    build_num_clean = str(build_number).strip()

    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    # 1. Atualizar CURRENT_VERSION em services/updater.py
    updater_path = os.path.join(base_dir, "services", "updater.py")
    if os.path.exists(updater_path):
        with open(updater_path, "r", encoding="utf-8") as f:
            code = f.read()

        new_code = re.sub(
            r'CURRENT_VERSION\s*=\s*["\'].*?["\']',
            f'CURRENT_VERSION = "{version_clean}"',
            code,
        )
        with open(updater_path, "w", encoding="utf-8") as f:
            f.write(new_code)
        print(f"[inject_version] Atualizado CURRENT_VERSION = \"{version_clean}\" em {updater_path}")

    # 2. Gravar version.json na raiz do mai_finance_flet e em assets/version.json
    version_data = {
        "version": version_clean,
        "build_number": build_num_clean,
    }

    target_files = [
        os.path.join(base_dir, "version.json"),
        os.path.join(base_dir, "assets", "version.json"),
    ]

    for target_path in target_files:
        os.makedirs(os.path.dirname(target_path), exist_ok=True)
        with open(target_path, "w", encoding="utf-8") as f:
            json.dump(version_data, f, indent=2)
        print(f"[inject_version] Gravado {target_path}")

    print(f"[inject_version] Sucesso: Versao {version_clean} (build {build_num_clean}) aplicada com sucesso.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Injeta versao e build number no app MAI Finance.")
    parser.add_argument("--version", required=True, help="Versao semantica do app (ex: 1.0.10)")
    parser.add_argument("--build-number", required=True, help="Numero sequencial da build (ex: 10)")
    args = parser.parse_args()

    inject_version(args.version, args.build_number)


if __name__ == "__main__":
    main()
