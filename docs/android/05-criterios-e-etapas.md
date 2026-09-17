# Critérios de aceite e etapas

Status: proposta inicial. A conclusão do planejamento depende da entrevista e da revisão dos fluxos; estes documentos não são uma especificação aprovada para começar a programar.

## Conclusão do planejamento

- Contas/compartilhamento resolvidos: mesmos logins da web e dados compartilhados. Resolver conectividade, navegação, armazenamento da sessão existente e distribuição.
- Cobrir toda a matriz de paridade, sem funções exclusivas do navegador.
- Definir cada tela com entrada, conteúdo, ações, saída, carregamento, vazio, erro e confirmação quando pertinente.
- Produzir layouts textuais detalhados das telas principais após as preferências de navegação e densidade.
- Registrar comportamentos diferentes da web e decisões sobre dados inválidos, conflitos e restauração.
- Identificar dependências reais do backend e limites do Flet antes de fixar a implementação.
- Revisar o conjunto com o usuário antes de iniciar desenvolvimento, conforme seu pedido de planejar primeiro.

## Aceite funcional proposto

Pré-requisito de acesso: entrar no Android com as credenciais web já existentes, obter o mesmo UUID/nome/e-mail e consultar os mesmos dados sem recadastro ou migração. Validar sessão de 24 horas, retorno ao app, expiração e logout. Cadastro mobile de uma conta nova, quando utilizado, deve criar uma conta válida também na web pelo serviço existente.

1. Criar uma despesa no Android e vê-la na web e no segundo aparelho; editar em qualquer cliente e refletir o resultado nos demais, respeitando o compartilhamento decidido.
2. Conferir totais mensais, filtros e soma da seleção com dados conhecidos; itens pagos e pendentes permanecem consistentes.
3. Editar todos os campos, lidar com meses de 28/29/30/31 dias e registrar pagamentos conforme uma regra comum aprovada.
4. Excluir categoria sem excluir suas despesas; renomear sem perder vínculos.
5. Selecionar/excluir em lote sem atingir itens fora do escopo mostrado; apresentar falha parcial caso esse seja o contrato aprovado.
6. Clonar um mês ainda não carregado no aparelho; ajustar vencimentos e impedir duplicação por toque duplo/reenvio.
7. Importar CSV, XLS e XLSX, incluindo várias abas/meses, valores brasileiros e datas de pagamento; revisar o resultado antes de gravar.
8. Gerar/listar/restaurar backup e confirmar efeito nos dois aparelhos; falha de restauração não pode ser apresentada como sucesso.
9. Usar pelo chat todas as consultas e mutações atuais, incluindo Open Finance; confirmação executa exatamente a proposta exibida uma única vez.
10. Tratar expiração de sessão, perda de conexão e retorno ao app sem perder silenciosamente alterações.

## Aceite de telas pequenas proposto

- Conferir todas as telas a 360 × 640 e 320 de largura, além dos dois aparelhos reais.
- Usar fonte ampliada a 200%, teclado aberto e navegação por gestos/Voltar do Android.
- Não exigir rolagem horizontal para CRUD, listagem cotidiana, revisão de importação ou chat.
- Manter botões importantes acessíveis; garantir identificação textual de status e ações para leitores de tela.
- Conferir descrições longas, categorias longas, valores altos, listas vazias e grandes volumes.
- Testar toda função com toque explícito, sem depender de hover ou gesto não indicado.

## Etapas futuras de implementação — não iniciadas

1. Verificar ambiente e dependências Flet/Android, backend real e schema sem mutações.
2. Preparar contratos autenticados, regras comuns e correções necessárias de persistência.
3. Implementar estrutura visual, sessão, navegação, Início e Despesas.
4. Implementar categorias, seleção em lote e pendências anteriores.
5. Implementar importação, clonagem e backups completos.
6. Integrar assistente e operações bancárias com confirmação.
7. Implementar opções adicionais aprovadas, validar sincronização e UX nos aparelhos reais.
8. Gerar pacote assinado e validar instalação/atualização preservando dados.

A divisão organiza o trabalho; não reduz o requisito de paridade na entrega final. Nenhum prazo ou versão mínima Android foi definido.
