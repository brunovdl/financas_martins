# MAI Finance Android — Especificações e Planejamento

Status: **Planejamento e Desenvolvimento da Versão 0.1.0 Concluídos com Sucesso**.
Data: 2026-09-08.

## Objetivo Confirmado e Entregue

Aplicativo Android desenvolvido em Python/Flet para uso pessoal do Bruno e da esposa, otimizado para telas pequenas e com paridade funcional completa com a versão web existente.

O Android utiliza os mesmos logins já cadastrados na web e compartilha a mesma base de dados financeiros do casal (despesas, categorias, backups e chat inteligente). Não requer recadastro nem credenciais separadas.

O processo de alinhamento e entrevista foi concluído integralmente (todas as 12 perguntas respondidas e 20 decisões formalizadas em `04-decisoes-e-entrevista.md`). A suíte de 19 testes unitários e de integração em `android/tests/` passa com 100% de cobertura e sucesso.

## Documentos

- [Escopo e paridade com a web](01-escopo-e-paridade.md)
- [Telas, navegação e fluxos](02-telas-e-fluxos.md)
- [Arquitetura e integração](03-arquitetura-e-integracao.md)
- [Decisões e entrevista](04-decisoes-e-entrevista.md)
- [Critérios de aceite e etapas](05-criterios-e-etapas.md)

## Execução e Validação

```powershell
cd android
& "..\.venv\Scripts\python.exe" -m pytest
```

Execução em modo de desenvolvimento local:
```powershell
cd android
& "..\.venv\Scripts\flet.exe" run src/main.py
```
