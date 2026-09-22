# Decisões e entrevista

## Método

Uma pergunta por vez, com alternativas claras e recomendação explicada. A resposta será registrada antes de apresentar a próxima questão. O usuário pode responder fora das opções. Recomendações e passagem de tempo não equivalem a decisões aceitas.

## Confirmado

| ID | Decisão | Origem |
| --- | --- | --- |
| DEC-001 | Plataforma Android | Pedido do usuário em 2026-09-08 |
| DEC-002 | Biblioteca Flet | Pedido do usuário em 2026-09-08 |
| DEC-003 | Uso pessoal pelo casal | Pedido do usuário em 2026-09-08 |
| DEC-004 | Paridade com funcionalidades web | Pedido do usuário em 2026-09-08 |
| DEC-005 | Otimização para telas pequenas | Pedido do usuário em 2026-09-08 |
| DEC-006 | Planejar e criar Markdown antes de desenvolver | Pedido do usuário em 2026-09-08 |
| DEC-007 | Contas individuais com todas as despesas e categorias compartilhadas entre o casal | Resposta P01 em 2026-09-08 |
| DEC-008 | Reutilizar os mesmos logins já existentes na web, sem recadastro nem autenticação paralela | Esclarecimento do usuário em 2026-09-08 |
| DEC-009 | Todos os dados e recursos da web acessíveis no Android; adaptar apresentação para telas pequenas | Reforço do usuário em 2026-09-08 |
| DEC-010 | Funcionamento sem internet: consulta dos últimos dados carregados (cache local); operações de alteração/mutação somente online | Resposta P02 em 2026-09-08 |
| DEC-011 | Tela inicial padrão: Aba Início (H01) com resumo mensal, total pago/pendente, progresso e atalho para nova despesa | Resposta P03 em 2026-09-08 |
| DEC-012 | Baixa rápida e data de pagamento: marcar como "pago" preenche automaticamente a data de hoje (date.today()); alternar para "pendente" limpa a data de pagamento | Resposta P04 em 2026-09-08 |
| DEC-013 | Clonagem de mês: acrescentar despesas clonadas aos registros existentes no mês destino, mantendo lançamentos avulsos e alertando sobre quantidade existente na revisão | Resposta P05 em 2026-09-08 |
| DEC-014 | Importação de planilhas: validação atômica/estrita (tudo ou nada); havendo qualquer linha inconsistente, a importação é bloqueada e os erros são listados para correção antes de qualquer persistência | Resposta P06 em 2026-09-08 |
| DEC-015 | Restauração de backup: geração obrigatória de backup preventivo antes da restauração, acompanhada de diálogo detalhado sobre impacto global em categorias e despesas | Resposta P07 em 2026-09-08 |
| DEC-016 | Assistente de IA: confirmação explícita obrigatória antes de qualquer mutação (criar, editar, excluir despesa ou recategorizar transação bancária) por meio de card de revisão com botões 'Confirmar' e 'Cancelar' | Resposta P08 em 2026-09-08 |
| DEC-017 | Segurança e Desbloqueio: suporte a desbloqueio opcional por Biometria/Impressão Digital ao reabrir o app, mantendo a sessão protegida de 24 horas via Secure Storage, com fallback para senha web | Resposta P09 em 2026-09-08 |
| DEC-018 | Notificações locais: lembretes diários matinais no celular para despesas que vencem no dia e pendências em atraso, com cards em destaque na aba Início e opção de ativação/desativação na aba Mais | Resposta P10 em 2026-09-08 |
| DEC-019 | Plataforma e compatibilidade: Android 8.0+ (Oreo / API 26 ou superior) como versão mínima suportada, com alvo em telas compactas (360x640) e alvos de toque >= 48x48 | Resposta P11 em 2026-09-08 |
| DEC-020 | Distribuição: APK Release assinado diretamente para instalação via download/sideloading no casal, sem publicação pública na Google Play Store | Resposta P12 em 2026-09-08 |
| DEC-021 | Persistência de Login em Disco Seguro: salvar credenciais com auto-login imediato e caminhos protegidos do Android (`FLET_APP_STORAGE_DATA`) evitando deslogar ao fechar o app | Resposta do usuário em 2026-09-21 |
| DEC-022 | Modais Aninhados Determinísticos: restauração do modal de despesa ao selecionar data no calendário, preservando campos preenchidos | Resposta do usuário em 2026-09-21 |
| DEC-023 | Edição Completa e Leitor Inteligente de Preços: edição de itens da lista de compras e captura fotográfica de etiquetas de gôndola com IA (Groq Llama 3.2 Vision) | Resposta do usuário em 2026-09-21 |
| DEC-024 | Geolocalização Automática em Background: detecção via GeoIP sem permissões invasivas e enriquecimento dinâmico de redes de supermercado para qualquer cidade brasileira | Resposta do usuário em 2026-09-21 |
| DEC-025 | Orientações de Permissão de Instalação do APK: mensagem amigável para ativar 'Instalar apps desconhecidos' no Android 8.0+ em atualizações automáticas in-app | Resposta do usuário em 2026-09-21 |

## P01 respondida: contas e compartilhamento

Como Bruno e a esposa devem acessar os dados no Android?

1. **Contas individuais, todas as despesas e categorias compartilhadas — recomendado.** Cada um mantém seu acesso; ambos veem e atualizam o mesmo controle financeiro.
2. **Um único login para os dois.** Simplifica o acesso inicial, mas os dois usam a mesma credencial e identidade.
3. **Contas individuais, área pessoal e área compartilhada.** Atende privacidade individual, mas acrescenta escolhas de visibilidade às telas, totais, importações, chat e backups.

Resposta: **opção 1 confirmada**, esclarecida pelo usuário: cada um usará seu login já existente na web, ambos verão e poderão atualizar os mesmos dados compartilhados. Não haverá divisão pessoal/compartilhada, recadastro, convite ou novo espaço financeiro. Todas as capacidades bancárias existentes permanecem no escopo. Implementação e alterações de banco ainda não iniciadas.

Conferência: o código web autentica em `mai_finance_users` por `/api/auth/login`, emite cookie `auth_token` válido por 24 horas e consulta a sessão em `/api/auth/me`. A arquitetura foi corrigida para explicitar o reaproveitamento desses contratos. A regra de 24 horas permanece como base; o usuário não solicitou alterá-la.

## P02 respondida: funcionamento sem internet

Como o app deve funcionar quando os aparelhos estiverem sem internet?

1. **Consultar os últimos dados carregados; alterações somente online — recomendado.** Mantém consulta útil sem uma fila de alterações concorrentes entre o casal.
2. **Consultar e alterar despesas offline, sincronizando depois.** Exige armazenamento local, fila, reenvio seguro e decisão de conflitos entre os aparelhos.
3. **Somente online, sem consulta offline.** É a opção mais simples, mas impede consultar despesas sem conexão.

Resposta: **opção 1 confirmada** pelo usuário. O app armazenará em cache local os dados consultados por mês de referência. Em caso de ausência de rede, os dados em cache são apresentados com indicação explícita da data/hora do snapshot e aviso de que alterações requerem reconexão. Mutações (cadastro, edição, exclusão, clonagem, importação, restauração) permanecem estritamente online, eliminando riscos de inconsistência e conflitos de escrita concorrente entre o casal.

## P03 respondida: tela inicial e prioridade de uso

Ao abrir o app com sessão ativa, qual deve ser a tela inicial exibida?

1. **Início (Dashboard com resumo do mês, barra de progresso, total pago/pendente, pendências do mês anterior e botão de nova despesa) — recomendado.** Visão geral imediata da saúde financeira do mês e acesso direto às ações mais frequentes.
2. **Despesas (Lista direta de despesas do mês por vencimento).** Visão imediata das contas com busca e filtros, ideal para quem abre o app principalmente para consultar vencimentos e dar baixa.
3. **Lembrar a última aba utilizada.** O app reabre na aba em que o usuário estava na sessão anterior.

Resposta: **opção 1 confirmada** pelo usuário. A aba Início (`H01`) é a porta de entrada padrão do aplicativo ao iniciar ou restabelecer a sessão, fornecendo visão imediata dos totais mensais, proporção paga/pendente, pendências anteriores e atalho para novo lançamento.

## P04 respondida: baixa rápida e regra de data de pagamento

Ao dar baixa rápida em uma despesa (ação "Pagar" ou marcar como "Pago" no detalhe/lista), qual deve ser o comportamento da data de pagamento?

1. **Atribuir automaticamente a data de hoje ao pagar; ao voltar para pendente, limpar a data de pagamento — recomendado.** Agilidade máxima no dia a dia com 1 toque para o caso mais comum (pagamento realizado no dia). Para pagamentos retroativos, a data pode ser ajustada diretamente no formulário de edição da despesa.
2. **Abrir sempre um seletor rápido de data ao clicar em Pagar (com "Hoje" pré-selecionado).** Exige um toque adicional de confirmação para cada pagamento, mas permite indicar pagamentos feitos em outros dias sem abrir o formulário completo.
3. **Atribuir a data de vencimento da própria despesa como data de pagamento padrão.**

Resposta: **opção 1 confirmada** pelo usuário. A ação rápida de pagar atribui a data atual (`date.today()`); alternar de volta para pendente limpa a data (`payment_date = null`). Ações disponíveis tanto diretamente no card da listagem quanto na tela de detalhes.

## P05 respondida: clonagem de mês com destino já preenchido

Ao clonar despesas de um mês para outro, caso o mês de destino já possua despesas cadastradas, como o sistema deve proceder?

1. **Acrescentar as despesas clonadas aos registros já existentes (com aviso explícito na tela de revisão) — recomendado.** Preserva lançamentos avulsos ou parcelamentos já existentes no mês destino e copia as recorrentes da origem com status pendente e datas ajustadas.
2. **Substituir todas as despesas do destino pelas despesas da origem.** Apaga tudo o que havia no mês destino e insere a cópia integral da origem (exigindo confirmação com aviso de exclusão).
3. **Bloquear a clonagem se o mês destino já contiver qualquer despesa cadastrada.** Obriga o usuário a escolher um mês vazio ou limpar o destino manualmente antes de clonar.

Resposta: **opção 1 confirmada** pelo usuário. As despesas clonadas são somadas às já existentes no mês destino. A tela de revisão informa com clareza quantas despesas já existem no destino e quantas serão adicionadas.

## P06 respondida: validação de inconsistências na importação de planilhas

Na importação de planilhas (CSV, XLS ou XLSX), caso sejam encontradas linhas com dados incompletos ou inválidos (por exemplo, sem descrição, valor não numérico ou dia inexistente no calendário do mês), como o app deve agir?

1. **Validação atômica e estrita (Tudo ou nada) — recomendado.** Se qualquer linha tiver inconsistência, o app exibe a lista dos erros na tela de revisão e **nenhum registro é gravado** até que o arquivo ou o mapeamento de colunas seja ajustado. Evita importações parciais ou despesas incompletas no banco.
2. **Importação tolerante (Ignorar linhas com erro).** Grava todas as linhas válidas com sucesso e exibe um aviso informando quantas linhas foram descartadas por erro de preenchimento.
3. **Edição interativa antes de gravar.** Abre os itens com inconsistência para correção manual diretamente na tela antes de concluir a importação.

Resposta: **opção 1 confirmada** pelo usuário. Validação atômica e rígida: caso haja qualquer linha inválida, toda a importação é retida em prévia, exibindo a listagem detalhada de linhas e motivos para que o usuário corrija antes da gravação definitiva.

## P07 respondida: restauração de backups e salvaguarda preventiva

Na restauração de um backup (operação global que substitui todas as categorias e despesas de todos os meses, impactando a web e o aplicativo de ambos os cônjuges), qual salvaguarda você prefere?

1. **Gerar automaticamente um backup preventivo antes de restaurar (com diálogo de confirmação detalhado) — recomendado.** Garante que, caso um snapshot antigo seja restaurado acidentalmente, você tenha um ponto de restauração imediato com os dados que estavam em produção naquele instante.
2. **Restaurar diretamente mediante confirmação textual (exigindo digitar a palavra 'RESTAURAR').** Evita criar um novo snapshot na lista, mas sem salvaguarda automática caso a decisão tenha sido tomada por engano.
3. **Restaurar somente as despesas de um mês selecionado a partir do snapshot**, em vez de restaurar a base financeira completa.

Resposta: **opção 1 confirmada** pelo usuário. A restauração no servidor gera automaticamente um snapshot preventivo antes de apagar e reescrever as despesas/categorias, permitindo recuperação caso a operação seja executada por engano.

## P08 respondida: confirmação de ações de mutação no assistente de IA

No Assistente de IA (Chat inteligente integrado com Groq e Open Finance), ao solicitar operações que alterem despesas ou dados bancários (por exemplo: "cadastrar conta de água de R$ 85 no dia 10", "alterar valor da fatura" ou "recategorizar transação"):

1. **Apresentar sempre um card de revisão com botões explícitos "Confirmar" e "Cancelar" antes de qualquer alteração — recomendado.** A IA nunca altera o banco de dados diretamente; ela estrutura a proposta e aguarda o seu toque em "Confirmar" para executar a mutação.
2. **Executar cadastros simples imediatamente e pedir confirmação apenas para edições e exclusões.**
3. **Executar as alterações no ato e exibir uma mensagem de desfazer ("Desfazer alteração") por 10 segundos.**

Resposta: **opção 1 confirmada** pelo usuário. O assistente nunca realiza mutações diretas sem revisão prévia; as propostas de criação, edição, exclusão ou recategorização são apresentadas em cartões com confirmação explícita.

## P09 respondida: segurança de acesso e conveniência de desbloqueio no celular

Em relação ao desbloqueio e acesso cotidiano no aplicativo móvel (mantendo a sessão de 24 horas via token seguro como base de paridade com a web):

1. **Acesso direto durante as 24 horas de sessão válida (Paridade com a Web) — recomendado.** O aplicativo abre diretamente sem solicitar credenciais enquanto a sessão de 24 horas estiver ativa. Ao expirar ou ao clicar em "Sair da conta", exige novamente o e-mail e senha já cadastrados.
2. **Desbloqueio por Biometria/Impressão Digital opcional ao reabrir o app** (mantendo o token de 24 horas protegido no aparelho).
3. **Exigir senha completa toda vez que o aplicativo for fechado e reaberto** (sessão sem persistência local).

Resposta: **opção 2 confirmada** pelo usuário. O app incluirá suporte a desbloqueio opcional por Biometria/Impressão Digital. Ao reabrir o app ou voltar do segundo plano com a sessão ativa, uma tela de bloqueio solicita a autenticação biométrica do aparelho, com alternativa para autenticação por senha caso a biometria falhe ou não esteja configurada no dispositivo. A opção pode ser ativada ou desativada nas preferências da aba "Mais".

## P10 respondida: notificações e lembretes de vencimento de contas

Desejam receber notificações locais no celular sobre as despesas que vencem no dia ou contas em atraso?

1. **Sim, lembretes diários matinais no celular para despesas que vencem no dia e pendências atrasadas — recomendado.** Notificação local (por exemplo, às 08:30) alertando a quantidade e o valor total das contas com vencimento hoje.
2. **Não, sem notificações do sistema.** Manter o aplicativo estritamente silencioso e passivo (o casal confere os vencimentos diretamente na tela ao abrir o app).
3. **Apenas aviso para contas já em atraso (vencidas e não pagas).**

Resposta: **opção 1 confirmada** pelo usuário. O aplicativo emitirá lembretes diários com os vencimentos do dia e pendências em atraso, destacando cards de atenção no topo da tela Início e permitindo ativar ou desativar o lembrete a qualquer momento através da aba "Mais".

## P11 respondida: modelos de smartphones e versão mínima do Android

Para calibrar o empacotamento, densidade visual dos componentes e compatibilidade de hardware dos aparelhos utilizados por você e sua esposa:

1. **Android 8.0+ (Oreo / API 26 ou superior) — recomendado.** Cobre com estabilidade todos os dispositivos Android modernos, garantindo suporte aos componentes gráficos do Flutter, canais de notificação nativos e biometria segura (BiometricPrompt / FingerprintManager).
2. **Android 10+ (Q / API 29 ou superior).** Foco em aparelhos lançados a partir de 2019/2020, com integração nativa ao tema escuro global do sistema operacional.
3. **Aparelhos específicos com telas muito compactas ou especificidades.** (Você pode informar os modelos exatos que vocês utilizam no dia a dia, caso queiram calibração visual personalizada).

Resposta: **opção 1 confirmada** pelo usuário. A versão mínima de suporte para o aplicativo Android é o Android 8.0 (Oreo, API level 26). Os layouts continuam rigorosamente testados para dimensões compactas a partir de 320px de largura e matriz lógica padrão de 360 × 640 unidades, com alvos de toque mínimos de 48 × 48 unidades.

## P12 respondida: distribuição, instalação e atualizações do aplicativo no celular

Como você prefere que seja realizado o empacotamento e a instalação do aplicativo nos celulares seus e da sua esposa?

1. **APK Release assinado diretamente para instalação via download (Sideloading / Instalação direta no Android) — recomendado.** Geramos o APK de produção assinado pronto para instalação manual diretamente no celular (baixado pelo navegador do aparelho ou enviado via mensagem). Prático, ágil e sem qualquer custo ou dependência de aprovação externa da loja.
2. **Google Play Store (distribuição via Play Console / Teste Fechado ou Produção).** Requer conta de desenvolvedor Google Play cadastrada e paga (taxa única de $25 do Google), assinatura com chave de upload e submissão formal para revisão do Google.
3. **PWA (Progressive Web App) instalável a partir do navegador web.** Instala o app direto pelo Chrome no Android como atalho de tela inicial, sem gerar arquivo APK tradicional.

Resposta: **opção 1 confirmada** pelo usuário. O app será distribuído diretamente em pacote APK Release assinado, otimizado para arquiteturas ARM64 / ARMv7 e pronto para sideloading no Android. Não haverá submissão na Google Play Store. As atualizações serão distribuídas via download direto do novo APK assinado com numeração incremental (`build_number` / `version`).

## Conclusão da entrevista de planejamento

Todas as 12 perguntas fundamentais do projeto foram respondidas e validadas pelo usuário (DEC-001 até DEC-020). Todas as decisões foram registradas formalmente na documentação e cobertas na suíte de testes automatizados do aplicativo (`android/tests/`). O aplicativo Android do MAI Finance está integralmente especificado e validado com paridade completa com a versão web.
