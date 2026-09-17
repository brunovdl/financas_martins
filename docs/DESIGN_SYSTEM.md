# MAI Finance — Design System & Padrões de Interface

Guia oficial e normativo de interface, componentes visuais, paleta de cores e padrões de experiência de usuário (UX/UI) do **MAI Finance** para as plataformas Web e Mobile (Flet/Flutter/React).

> [!IMPORTANT]
> **Norma Mandatória de Engenharia**: Sempre que qualquer componente, tela, formulário ou diálogo for criado ou alterado no frontend do MAI Finance, consulte e respeite integralmente os padrões definidos neste documento.

---

## 1. Identidade Visual & Branding

### 1.1. Logotipo Oficial da Marca
- **Formato**: Squircle (superelipse com cantos contínuos e suaves).
- **Fundo**: Superfície escura profunda (`#121828` no escuro / `#0F172A`).
- **Contorno**: Borda néon contínua na cor Accent Teal (`#3FD6C4`).
- **Símbolo Central**: Gráfico de linha ascendente em zigue-zague financeiro com cabeça de seta estilizada e expressiva apontando a 45° (nordeste), simbolizando crescimento e prosperidade financeira.
- **Assets Oficiais**:
  - `assets/logo.svg`: Vetor escalável limpo.
  - `assets/logo.png`: Bitmap 512×512 em alta resolução.
  - `assets/favicon.png`: Ícone 64×64 para abas de navegador.
  - `assets/favicon.ico`: Ícone multi-resolução (16×16 e 32×32).
  - `assets/icons/icon-192.png` e `icon-512.png`: PWA e launchers Android.
- **Regra**: Nunca utilize os ícones ou favicons padrão de frameworks (ex: fita/triângulo do Flet). Em toda inicialização ou cabeçalho, utilize exclusivamente a logo oficial da marca.

---

## 2. Paleta de Cores e Tokens Oficiais

O MAI Finance suporta alternância dinâmica e instantânea entre os modos **Dark** (Padrão) e **Light**. Todos os controles devem obter suas cores a partir de `get_tokens(theme_mode)`.

| Token | Dark Mode | Light Mode | Finalidade |
|---|---|---|---|
| `pageBg` | `#08090F` | `#EAEDF6` | Fundo principal da página |
| `surface` | `#121628` | `#FFFFFF` | Superfície de cartões e modais |
| `surfaceSolid` | `#151B2E` | `#FFFFFF` | Fundo sólido para inputs e sub-cartões |
| `border` | `#232A45` | `#CBD5E1` | Borda estrutural padrão |
| `borderSubtle` | `#1B2138` | `#E2E8F0` | Borda sutil de divisores e inputs |
| `tableHeaderBg` | `#151B2E` | `#F1F5F9` | Fundo de cabeçalhos de tabela |
| `tableHeaderBorder` | `#232A45` | `#CBD5E1` | Borda de cabeçalhos de tabela |
| `textPrimary` | `#EDF0F7` | `#0F172A` | Texto principal com contraste máximo |
| `textHeader` | `#EDF0F7` | `#1E293B` | Tipografia de títulos e colunas |
| `textMuted` | `#8891A8` | `#334155` | Texto secundário legível (WCAG AA) |
| `textFaint` | `#606A85` | `#64748B` | Legendas, hints e metadados |
| `accent` | `#3FD6C4` | `#0E9488` | Cor primária da marca (Teal luminoso/escuro) |
| `accentOnBrand` | `#08090F` | `#FFFFFF` | Texto sobre fundos na cor `accent` |
| `success` | `#3FD6C4` | `#0E9488` | Status 'Pago' / sucesso |
| `successBg` | `#122620` | `#ECFDF5` | Fundo de badges de sucesso |
| `successBorder` | `#1F3D33` | `#A7F3D0` | Borda de badges de sucesso |
| `warning` | `#F2B84B` | `#B45309` | Status 'Pendente' / alerta |
| `warningBg` | `#241D0F` | `#FFFBEB` | Fundo de badges de alerta |
| `warningBorder` | `#3D3320` | `#FDE68A` | Borda de badges de alerta |
| `danger` | `#F5738C` | `#BE123C` | Erros, cancelamentos e exclusão |

### 2.1. Regra Crítica de Contraste para Badges de Categoria
Nunca aplique texto branco fixo (`#FFFFFF`) sobre cores claras aleatórias (amarelo, verde claro, rosa suave). Utilize sempre a função utilitária:
```python
bg_color, text_color, border_color = get_badge_colors(category_color_hex, is_light)
```
- **Tema Claro**: Fundo suave pastel (16% de opacidade da cor), texto escuro saturado com contraste superior a 4.5:1 (WCAG AA) e borda sutil.
- **Tema Escuro**: Fundo translúcido moderno com texto vibrante e luminoso.

---

## 3. Anatomia Padrão de Diálogos e Modais (Gold Standard)

Todos os modais do MAI Finance (Nova Despesa, Clonagem, Categorias, Backups, Confirmação) devem seguir rigorosamente a mesma anatomia visual e ciclo de vida:

```
┌─────────────────────────────────────────────────────────┐
│ [Logo 22px] Título do Modal                    [ X ]    │ <-- 3.1. Cabeçalho Unificado
├─────────────────────────────────────────────────────────┤
│                                                         │
│   Conteúdo Compacto & Responsivo                        │ <-- 3.2. Corpo
│   - Inputs com dense=True e border_radius=8             │
│   - Campos em linha lógica (ex: Valor + Vencimento)     │
│   - Superfícies adaptadas ao tema ativo                │
│                                                         │
├─────────────────────────────────────────────────────────┤
│                             [ Cancelar ] [ Salvar / OK ]│ <-- 3.3. Rodapé de Ações
└─────────────────────────────────────────────────────────┘
```

### 3.1. Cabeçalho Unificado
- **Composição**: `ft.Row` com alinhamento `SPACE_BETWEEN`.
  - À esquerda: Mini-logo oficial `assets/logo.png` (22×22) + Título semântico (`size=16`, `weight=BOLD`, `color=T["textPrimary"]`).
  - À direita: Botão fechar `ft.IconButton(ft.Icons.CLOSE, icon_size=18, icon_color=T["textMuted"], on_click=fechar)`.
- **Compatibilidade**: Atribuir `modal_header.value = title` para manter total paridade e compatibilidade com asserções de testes unitários.

### 3.2. Corpo do Modal
- **Padding e Espaçamento**: `tight=True`, espaçamento uniforme entre 10 e 12 pixels.
- **Campos de Formulário**: `dense=True`, `border_radius=8`, `bgcolor=T["surfaceSolid"]`, `border_color=T["borderSubtle"]`, foco em `T["accent"]`.
- **Superfícies de Cards Internos**:
  - No Tema Escuro: `bgcolor=T["surfaceSolid"]` (`#151B2E`) com borda `#232A45`.
  - No Tema Claro: `bgcolor="#F8FAFC"` ou `T["surface"]` (`#FFFFFF`) com borda `#E2E8F0`.
  - **PROIBIÇÃO**: É terminantemente proibido manter blocos escuros fixos (`#151B2E`) dentro de modais no Tema Claro.

### 3.3. Rodapé de Ações
- Alinhamento à direita (`ft.MainAxisAlignment.END`).
- **Botão Secundário (Cancelar/Fechar)**:
  - Fundo sutil `T["surfaceSolid"]`, texto `T["textMuted"]`, cantos `radius=8`.
- **Botão Primário (Salvar/Confirmar/Clonar)**:
  - Fundo `T["accent"]`, texto `#08090F` em negrito, ícone semântico (`ft.Icons.CHECK`, `ft.Icons.COPY_ALL`, etc.), cantos `radius=8`.
  - Suporte obrigatório a estado de carregamento com `MaiLoading.button_spinner("Processando...")`.

### 3.4. Ciclo de Vida e Fechamento Determinístico
Para evitar duplicação de dados e conflitos com o WebSocket/Flutter:
1. **Bloqueio Imediato**: No clique do botão de submissão, desabilite imediatamente o botão (`btn.disabled = True`) e ative o spinner de loading.
2. **Fechamento Imediato**: Feche o modal de forma determinística antes de qualquer outra ação:
   ```python
   dlg.open = False
   if hasattr(page, "pop_dialog"):
       page.pop_dialog()
   page.update()
   ```
3. **Atualização de Dados**: Recarregue os dados silenciosamente (`load_data(silent=True)`).
4. **Notificação Desacoplada**: Exiba a notificação Toast via `page.snack_bar = snack; snack.open = True; page.update()`. **Nunca** use `show_dialog(snack)` para notificações.

---

## 4. Componente Oficial de Carregamento (`MaiLoading`)

Localizado em `ui/components/mai_loading.py`:
- **Visual**: Logo oficial centralizado envolvido por anel giratório em Teal `#3FD6C4` com halo pulsante de 12% de opacidade.
- **Variações**:
  1. `MaiLoading(message=...)`: Carregamento inline em telas e listas.
  2. `MaiLoading.full_screen_overlay(message=...)`: Overlay de bloqueio semitransparente para login ou transições pesadas.
  3. `MaiLoading.button_spinner(label=...)`: Indicador ultracompacto para botões com operação em andamento.

---

## 5. Responsividade Mobile-First

- **Largura Máxima de Diálogos**: `min(page_width - 32, 430)`.
- **Alvos de Toque (Touch Targets)**: Mínimo de 44×44 pixels em botões e controles interativos.
- **Campos Agrupados**: Em telas mobile estreitas (<360px), linhas horizontais devem colapsar graciosamente para coluna única quando necessário.
