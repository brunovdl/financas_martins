import React, { useState, useMemo, useRef, useCallback } from "react";
import { ChevronLeft, ChevronRight, Plus, Search, Trash2, Link as LinkIcon, X, Wallet, CircleCheck, CircleDashed, Sun, Moon, Upload, FileSpreadsheet, CheckCircle2, AlertCircle, ChevronDown } from "lucide-react";

// ---------------------------------------------------------------------------
// Estrutura de dados espelha 1:1 o schema do Supabase (schema.sql):
// categories(id, name, color) | expenses(id, due_date, category_id,
// description, amount, payment_date, status, observation, month_ref)
// Aqui fica em memória; para produção, troque os setState por chamadas
// supabase.from('expenses').select/insert/update — ver lib/supabaseClient.ts
// ---------------------------------------------------------------------------

const CATEGORIES = [
  { id: "outros", name: "Outros", dark: "#94A3B8", light: "#475569" },
  { id: "daae", name: "DAAE", dark: "#5EA8F2", light: "#1D4ED8" },
  { id: "condinvest", name: "CondInvest", dark: "#B399F5", light: "#7C3AED" },
  { id: "imposto", name: "Imposto", dark: "#F5738C", light: "#BE123C" },
  { id: "caixa", name: "Caixa", dark: "#F2B84B", light: "#B45309" },
  { id: "cpfl", name: "CPFL", dark: "#3FD6C4", light: "#0F766E" },
];

const MONTH_NAMES = [
  "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
  "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro",
];

let idCounter = 1000;
const nextId = () => `exp-${idCounter++}`;

const seedExpenses = [
  { id: nextId(), monthRef: "2026-04", dueDay: 5, category: "outros", description: "Empréstimo Rato (niver Miguel)", amount: 4350.00, paymentDay: "2.abr", status: "pago", observation: "" },
  { id: nextId(), monthRef: "2026-04", dueDay: 6, category: "daae", description: "Água 03.2026 Araraquara", amount: 82.44, paymentDay: "2.abr", status: "pago", observation: "Matrícula: 1200534 Link: DAAE" },
  { id: nextId(), monthRef: "2026-04", dueDay: 6, category: "outros", description: "Primeira Semana Airbnb", amount: 600.00, paymentDay: "6.abr", status: "pago", observation: "" },
  { id: nextId(), monthRef: "2026-04", dueDay: 10, category: "outros", description: "Internet 04.2026", amount: 127.98, paymentDay: "2.abr", status: "pago", observation: "" },
  { id: nextId(), monthRef: "2026-04", dueDay: 10, category: "condinvest", description: "Garagem 16 de 24", amount: 83.80, paymentDay: "2.abr", status: "pago", observation: "" },
  { id: nextId(), monthRef: "2026-04", dueDay: 10, category: "outros", description: "Material Miguel 4 de 10", amount: 223.95, paymentDay: "2.abr", status: "pago", observation: "" },
  { id: nextId(), monthRef: "2026-04", dueDay: 13, category: "condinvest", description: "Condomínio 04 de 12", amount: 342.10, paymentDay: "2.abr", status: "pago", observation: "" },
  { id: nextId(), monthRef: "2026-04", dueDay: 15, category: "outros", description: "Empréstimo Rato (Receita e Escola)", amount: 3400.00, paymentDay: "2.abr", status: "pago", observation: "" },
  { id: nextId(), monthRef: "2026-04", dueDay: 17, category: "outros", description: "Financiamento Carro 19 de 48", amount: 748.00, paymentDay: "6.abr", status: "pago", observation: "Pix: 10907124801" },
  { id: nextId(), monthRef: "2026-04", dueDay: 19, category: "imposto", description: "IPVA 04 de 05", amount: 253.73, paymentDay: "2.abr", status: "pago", observation: "" },
  { id: nextId(), monthRef: "2026-04", dueDay: 19, category: "outros", description: "Refinanciamento Pai (Creta) 7 de 13", amount: 1441.70, paymentDay: "6.abr", status: "pago", observation: "" },
  { id: nextId(), monthRef: "2026-04", dueDay: 19, category: "outros", description: "Internet Celular Bia", amount: 50.00, paymentDay: "30.mar", status: "pago", observation: "" },
  { id: nextId(), monthRef: "2026-04", dueDay: 19, category: "outros", description: "Condomínio (Condinveste Araraquara)", amount: 0.00, paymentDay: "", status: "pendente", observation: "Aguardando retorno fórum" },
  { id: nextId(), monthRef: "2026-04", dueDay: 20, category: "caixa", description: "Financiamento Apto Araraquara", amount: 605.05, paymentDay: "", status: "pendente", observation: "" },
  { id: nextId(), monthRef: "2026-04", dueDay: 20, category: "outros", description: "Cartão Mãe Bia Compras Niver Miguel 1 de 1", amount: 1500.00, paymentDay: "", status: "pendente", observation: "" },
  { id: nextId(), monthRef: "2026-04", dueDay: 20, category: "outros", description: "Cartão Mãe Bia Sofá 5 de 12", amount: 258.38, paymentDay: "", status: "pendente", observation: "" },
  { id: nextId(), monthRef: "2026-04", dueDay: 20, category: "outros", description: "Cartão Mãe Bia Material Miguel 3 de 5", amount: 260.27, paymentDay: "", status: "pendente", observation: "" },
  { id: nextId(), monthRef: "2026-04", dueDay: 20, category: "outros", description: "MEI Bia 03.2026", amount: 86.05, paymentDay: "", status: "pendente", observation: "" },
  { id: nextId(), monthRef: "2026-04", dueDay: 29, category: "outros", description: "Internet Celular Bruno", amount: 50.00, paymentDay: "", status: "pendente", observation: "" },
  { id: nextId(), monthRef: "2026-04", dueDay: 30, category: "outros", description: "Escola Miguel", amount: 850.00, paymentDay: "", status: "pendente", observation: "" },
  { id: nextId(), monthRef: "2026-04", dueDay: 30, category: "cpfl", description: "Energia", amount: 293.85, paymentDay: "", status: "pendente", observation: "" },
  { id: nextId(), monthRef: "2026-04", dueDay: 30, category: "imposto", description: "Negociação Receita Federal 06 de 60", amount: 2400.00, paymentDay: "", status: "pendente", observation: "" },
  { id: nextId(), monthRef: "2026-05", dueDay: 6, category: "daae", description: "Água 04.2026 Araraquara", amount: 79.10, paymentDay: "3.mai", status: "pago", observation: "" },
  { id: nextId(), monthRef: "2026-05", dueDay: 10, category: "condinvest", description: "Garagem 17 de 24", amount: 83.80, paymentDay: "3.mai", status: "pago", observation: "" },
  { id: nextId(), monthRef: "2026-05", dueDay: 13, category: "condinvest", description: "Condomínio 05 de 12", amount: 342.10, paymentDay: "", status: "pendente", observation: "" },
  { id: nextId(), monthRef: "2026-05", dueDay: 30, category: "cpfl", description: "Energia", amount: 310.40, paymentDay: "", status: "pendente", observation: "" },
];

// ---------------------------------------------------------------------------
// Tokens de tema — única fonte de verdade pras cores dos dois modos
// ---------------------------------------------------------------------------
const THEMES = {
  dark: {
    pageBg: "radial-gradient(ellipse 120% 80% at 50% -10%, #131A30 0%, #0A0D18 55%, #08090F 100%)",
    surface: "#12162860",
    surfaceSolid: "#151B2E",
    surfaceGradientA: "#151B32",
    surfaceGradientB: "#11152580",
    border: "#232A45",
    borderSubtle: "#1B2138",
    textPrimary: "#EDF0F7",
    textMuted: "#8891A8",
    textFaint: "#606A85",
    rowHover: "#161C34",
    accent: "#3FD6C4",
    accentTo: "#5B7FF5",
    accentOnBrand: "#08090F",
    success: "#3FD6C4",
    successText: "#5EE0C4",
    successBg: "#122620",
    successBorder: "#1F3D33",
    warning: "#F2B84B",
    warningBg: "#241D0F",
    warningBorder: "#3D3320",
    danger: "#F5738C",
    inputBg: "#0A0D18",
    ring1: "#3FD6C4",
    ring2: "#5EE0C4",
    ringTrack: "#1E2540",
  },
  light: {
    pageBg: "radial-gradient(ellipse 120% 80% at 50% -10%, #FFFFFF 0%, #F4F6FB 55%, #EAEDF6 100%)",
    surface: "#FFFFFFB3",
    surfaceSolid: "#FFFFFF",
    surfaceGradientA: "#FFFFFF",
    surfaceGradientB: "#F6F8FC",
    border: "#E1E5F0",
    borderSubtle: "#EAEDF5",
    textPrimary: "#131826",
    textMuted: "#5B6478",
    textFaint: "#8890A3",
    rowHover: "#F4F6FC",
    accent: "#0E9488",
    accentTo: "#3B5FE0",
    accentOnBrand: "#FFFFFF",
    success: "#0D9488",
    successText: "#0D9488",
    successBg: "#ECFBF8",
    successBorder: "#CBEFE8",
    warning: "#B45309",
    warningBg: "#FFF7EB",
    warningBorder: "#F5E3C4",
    danger: "#BE123C",
    inputBg: "#FFFFFF",
    ring1: "#0D9488",
    ring2: "#3FD6C4",
    ringTrack: "#E4E8F0",
  },
};

function formatBRL(value) {
  return value.toLocaleString("pt-BR", { style: "currency", currency: "BRL" });
}

function monthLabel(monthRef) {
  const [y, m] = monthRef.split("-").map(Number);
  return `${MONTH_NAMES[m - 1]} ${y}`;
}

function shiftMonth(monthRef, delta) {
  const [y, m] = monthRef.split("-").map(Number);
  const d = new Date(y, m - 1 + delta, 1);
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}`;
}

function ProgressRing({ pct, size = 64, T }) {
  const stroke = 6;
  const r = (size - stroke) / 2;
  const c = 2 * Math.PI * r;
  const offset = c - (pct / 100) * c;
  return (
    <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`} className="-rotate-90">
      <circle cx={size / 2} cy={size / 2} r={r} stroke={T.ringTrack} strokeWidth={stroke} fill="none" />
      <circle
        cx={size / 2}
        cy={size / 2}
        r={r}
        stroke="url(#ringGradient)"
        strokeWidth={stroke}
        fill="none"
        strokeDasharray={c}
        strokeDashoffset={offset}
        strokeLinecap="round"
        style={{ transition: "stroke-dashoffset 0.6s cubic-bezier(0.4, 0, 0.2, 1)" }}
      />
      <defs>
        <linearGradient id="ringGradient" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stopColor={T.ring1} />
          <stop offset="100%" stopColor={T.ring2} />
        </linearGradient>
      </defs>
    </svg>
  );
}

export default function GastosApp() {
  const [theme, setTheme] = useState("dark");
  const T = THEMES[theme];

  const [expenses, setExpenses] = useState(seedExpenses);
  const [monthRef, setMonthRef] = useState("2026-04");
  const [search, setSearch] = useState("");
  const [onlyPending, setOnlyPending] = useState(false);
  const [editingCell, setEditingCell] = useState(null);
  const [draft, setDraft] = useState("");
  const [showImport, setShowImport] = useState(false);

  const monthExpenses = useMemo(() => {
    return expenses
      .filter((e) => e.monthRef === monthRef)
      .filter((e) => !onlyPending || e.status === "pendente")
      .filter((e) =>
        search.trim() === "" ||
        e.description.toLowerCase().includes(search.toLowerCase()) ||
        CATEGORIES.find((c) => c.id === e.category)?.name.toLowerCase().includes(search.toLowerCase())
      )
      .sort((a, b) => a.dueDay - b.dueDay);
  }, [expenses, monthRef, search, onlyPending]);

  const totals = useMemo(() => {
    const all = expenses.filter((e) => e.monthRef === monthRef);
    const totalDespesas = all.reduce((s, e) => s + e.amount, 0);
    const totalPendente = all.filter((e) => e.status === "pendente").reduce((s, e) => s + e.amount, 0);
    const totalPago = totalDespesas - totalPendente;
    const pctPago = totalDespesas > 0 ? (totalPago / totalDespesas) * 100 : 0;
    const qtdPendente = all.filter((e) => e.status === "pendente").length;
    return { totalDespesas, totalPendente, totalPago, pctPago, qtdPendente, qtdTotal: all.length };
  }, [expenses, monthRef]);

  function updateExpense(id, field, value) {
    setExpenses((prev) => prev.map((e) => (e.id === id ? { ...e, [field]: value } : e)));
  }

  function toggleStatus(id) {
    setExpenses((prev) =>
      prev.map((e) => (e.id === id ? { ...e, status: e.status === "pago" ? "pendente" : "pago" } : e))
    );
  }

  function removeExpense(id) {
    setExpenses((prev) => prev.filter((e) => e.id !== id));
  }

  function addExpense() {
    const newExp = {
      id: nextId(),
      monthRef,
      dueDay: 1,
      category: "outros",
      description: "Nova despesa",
      amount: 0,
      paymentDay: "",
      status: "pendente",
      observation: "",
    };
    setExpenses((prev) => [newExp, ...prev]);
    setEditingCell({ id: newExp.id, field: "description" });
    setDraft("Nova despesa");
  }

  function startEdit(id, field, currentValue) {
    setEditingCell({ id, field });
    setDraft(String(currentValue ?? ""));
  }

  function commitEdit() {
    if (!editingCell) return;
    const { id, field } = editingCell;
    let value = draft;
    if (field === "amount") value = parseFloat(draft.replace(",", ".")) || 0;
    if (field === "dueDay") value = Math.min(31, Math.max(1, parseInt(draft, 10) || 1));
    updateExpense(id, field, value);
    setEditingCell(null);
    setDraft("");
  }

  function cancelEdit() {
    setEditingCell(null);
    setDraft("");
  }

  return (
    <div
      className="min-h-screen p-4 md:p-10 transition-colors duration-300"
      style={{ background: T.pageBg, color: T.textPrimary, fontFamily: "'Inter', -apple-system, BlinkMacSystemFont, sans-serif" }}
    >
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap');
        .font-display { font-family: 'Outfit', sans-serif; }
        .font-mono { font-family: 'JetBrains Mono', ui-monospace, monospace; }
      `}</style>

      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="flex flex-col md:flex-row md:items-end md:justify-between gap-5 mb-8">
          <div className="flex items-center gap-3.5">
            <div
              className="w-11 h-11 rounded-2xl flex items-center justify-center"
              style={{
                background: `linear-gradient(135deg, ${T.accent}, ${T.accentTo})`,
                boxShadow: `0 0 24px -4px ${T.accent}80`,
              }}
            >
              <Wallet size={20} strokeWidth={2.2} style={{ color: T.accentOnBrand }} />
            </div>
            <div>
              <div className="text-[11px] tracking-[0.22em] font-mono font-medium mb-0.5" style={{ color: T.accent }}>
                CONTROLE FINANCEIRO
              </div>
              <h1 className="font-display text-2xl md:text-[28px] font-semibold tracking-tight leading-none">Gastos do mês</h1>
            </div>
          </div>

          <div className="flex items-center gap-2 self-start md:self-auto">
            {/* Toggle de tema */}
            <button
              onClick={() => setTheme((t) => (t === "dark" ? "light" : "dark"))}
              className="p-2.5 rounded-full border transition-all active:scale-95"
              style={{ backgroundColor: `${T.surface}`, borderColor: T.border, color: T.textPrimary }}
              aria-label="Alternar tema"
              title={theme === "dark" ? "Mudar para tema claro" : "Mudar para tema escuro"}
            >
              {theme === "dark" ? <Sun size={16} /> : <Moon size={16} />}
            </button>

            {/* Seletor de mês */}
            <div
              className="flex items-center gap-1 backdrop-blur border rounded-full px-1.5 py-1.5"
              style={{ backgroundColor: T.surface, borderColor: T.border }}
            >
              <button
                onClick={() => setMonthRef((m) => shiftMonth(m, -1))}
                className="p-2 rounded-full active:scale-95 transition-all"
                style={{ color: T.textPrimary }}
                onMouseEnter={(e) => (e.currentTarget.style.backgroundColor = T.rowHover)}
                onMouseLeave={(e) => (e.currentTarget.style.backgroundColor = "transparent")}
                aria-label="Mês anterior"
              >
                <ChevronLeft size={16} />
              </button>
              <div className="w-40 text-center font-display text-sm font-medium">{monthLabel(monthRef)}</div>
              <button
                onClick={() => setMonthRef((m) => shiftMonth(m, 1))}
                className="p-2 rounded-full active:scale-95 transition-all"
                style={{ color: T.textPrimary }}
                onMouseEnter={(e) => (e.currentTarget.style.backgroundColor = T.rowHover)}
                onMouseLeave={(e) => (e.currentTarget.style.backgroundColor = "transparent")}
                aria-label="Próximo mês"
              >
                <ChevronRight size={16} />
              </button>
            </div>
          </div>
        </div>

        {/* Summary cards */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-6">
          <div
            className="col-span-2 md:col-span-1 rounded-2xl border p-4 flex flex-col justify-between"
            style={{ borderColor: T.border, background: `linear-gradient(135deg, ${T.surfaceGradientA}, ${T.surfaceGradientB})` }}
          >
            <span className="text-[11px] font-medium tracking-wide" style={{ color: T.textFaint }}>TOTAL DO MÊS</span>
            <span className="font-mono text-xl font-semibold mt-2">{formatBRL(totals.totalDespesas)}</span>
            <span className="text-[11px] mt-1" style={{ color: T.textFaint }}>{totals.qtdTotal} lançamentos</span>
          </div>

          <div
            className="rounded-2xl border p-4 flex flex-col justify-between"
            style={{ borderColor: T.successBorder, background: T.successBg }}
          >
            <span className="text-[11px] font-medium tracking-wide flex items-center gap-1" style={{ color: T.successText }}>
              <CircleCheck size={12} /> PAGO
            </span>
            <span className="font-mono text-xl font-semibold mt-2">{formatBRL(totals.totalPago)}</span>
            <span className="text-[11px] mt-1" style={{ color: T.textFaint }}>{totals.qtdTotal - totals.qtdPendente} itens quitados</span>
          </div>

          <div
            className="rounded-2xl border p-4 flex flex-col justify-between"
            style={{ borderColor: T.warningBorder, background: T.warningBg }}
          >
            <span className="text-[11px] font-medium tracking-wide flex items-center gap-1" style={{ color: T.warning }}>
              <CircleDashed size={12} /> PENDENTE
            </span>
            <span className="font-mono text-xl font-semibold mt-2">{formatBRL(totals.totalPendente)}</span>
            <span className="text-[11px] mt-1" style={{ color: T.textFaint }}>{totals.qtdPendente} em aberto</span>
          </div>

          <div
            className="rounded-2xl border p-4 flex items-center gap-3"
            style={{ borderColor: T.border, background: `linear-gradient(135deg, ${T.surfaceGradientA}, ${T.surfaceGradientB})` }}
          >
            <ProgressRing pct={totals.pctPago} size={52} T={T} />
            <div>
              <div className="font-mono text-lg font-semibold leading-none">{totals.pctPago.toFixed(0)}%</div>
              <div className="text-[11px] mt-1" style={{ color: T.textFaint }}>do mês quitado</div>
            </div>
          </div>
        </div>

        {/* Toolbar */}
        <div className="flex flex-col sm:flex-row gap-2.5 mb-4">
          <div
            className="flex items-center gap-2 border rounded-xl px-3.5 py-2.5 flex-1 transition-colors"
            style={{ backgroundColor: T.surface, borderColor: T.border }}
          >
            <Search size={15} style={{ color: T.textFaint }} />
            <input
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Buscar por descrição ou categoria..."
              className="bg-transparent outline-none text-sm flex-1"
              style={{ color: T.textPrimary }}
            />
          </div>
          <button
            onClick={() => setOnlyPending((v) => !v)}
            className="px-4 py-2.5 rounded-xl text-sm font-medium border transition-all"
            style={
              onlyPending
                ? { backgroundColor: `${T.warning}1A`, borderColor: `${T.warning}66`, color: T.warning }
                : { backgroundColor: T.surface, borderColor: T.border, color: T.textMuted }
            }
          >
            Só pendentes
          </button>
          <button
            onClick={() => setShowImport(true)}
            className="flex items-center justify-center gap-1.5 px-4 py-2.5 rounded-xl text-sm font-medium border transition-all hover:opacity-90 active:scale-[0.98]"
            style={{ backgroundColor: T.surface, borderColor: T.border, color: T.textMuted }}
          >
            <Upload size={15} strokeWidth={2} /> Importar
          </button>
          <button
            onClick={addExpense}
            className="flex items-center justify-center gap-1.5 px-4 py-2.5 rounded-xl text-sm font-semibold hover:opacity-90 active:scale-[0.98] transition-all"
            style={{ background: `linear-gradient(90deg, ${T.accent}, ${T.accentTo})`, color: T.accentOnBrand }}
          >
            <Plus size={16} strokeWidth={2.5} /> Nova despesa
          </button>
        </div>

        {/* Table */}
        <div className="backdrop-blur border rounded-2xl overflow-hidden" style={{ backgroundColor: T.surface, borderColor: T.border }}>
          <div className="overflow-x-auto">
            <table className="w-full text-sm border-separate border-spacing-0">
              <thead>
                <tr className="text-left text-[11px] uppercase tracking-wider" style={{ color: T.textFaint }}>
                  <th className="px-4 py-3 font-medium w-24" style={{ borderBottom: `1px solid ${T.border}` }}>Vencimento</th>
                  <th className="px-4 py-3 font-medium w-32" style={{ borderBottom: `1px solid ${T.border}` }}>Categoria</th>
                  <th className="px-4 py-3 font-medium" style={{ borderBottom: `1px solid ${T.border}` }}>Descrição</th>
                  <th className="px-4 py-3 font-medium text-right w-28" style={{ borderBottom: `1px solid ${T.border}` }}>Valor</th>
                  <th className="px-4 py-3 font-medium w-24" style={{ borderBottom: `1px solid ${T.border}` }}>Pagamento</th>
                  <th className="px-4 py-3 font-medium w-28" style={{ borderBottom: `1px solid ${T.border}` }}>Status</th>
                  <th className="px-4 py-3 font-medium" style={{ borderBottom: `1px solid ${T.border}` }}>Observação</th>
                  <th className="px-2 py-3 w-8" style={{ borderBottom: `1px solid ${T.border}` }}></th>
                </tr>
              </thead>
              <tbody>
                {monthExpenses.map((e) => {
                  const cat = CATEGORIES.find((c) => c.id === e.category);
                  const catColor = theme === "dark" ? cat?.dark : cat?.light;
                  const isPago = e.status === "pago";
                  const stripeColor = isPago ? T.success : T.warning;
                  return (
                    <tr
                      key={e.id}
                      className="group transition-colors"
                      onMouseEnter={(ev) => (ev.currentTarget.style.backgroundColor = T.rowHover)}
                      onMouseLeave={(ev) => (ev.currentTarget.style.backgroundColor = "transparent")}
                    >
                      {/* Vencimento — com stripe de status */}
                      <td className="px-4 py-2.5 font-mono text-[13px] relative" style={{ color: T.textMuted, borderBottom: `1px solid ${T.borderSubtle}` }}>
                        <span className="absolute left-0 top-1.5 bottom-1.5 w-[2.5px] rounded-full" style={{ backgroundColor: stripeColor, opacity: 0.8 }} />
                        <span className="pl-2">
                          {editingCell?.id === e.id && editingCell.field === "dueDay" ? (
                            <EditInput draft={draft} setDraft={setDraft} onCommit={commitEdit} onCancel={cancelEdit} T={T} />
                          ) : (
                            <button onClick={() => startEdit(e.id, "dueDay", e.dueDay)} className="hover:opacity-70 transition-opacity" style={{ color: "inherit" }}>
                              {String(e.dueDay).padStart(2, "0")}.abr
                            </button>
                          )}
                        </span>
                      </td>

                      {/* Categoria */}
                      <td className="px-4 py-2.5" style={{ borderBottom: `1px solid ${T.borderSubtle}` }}>
                        <select
                          value={e.category}
                          onChange={(ev) => updateExpense(e.id, "category", ev.target.value)}
                          className="text-[11px] font-semibold rounded-full px-2.5 py-1 border-0 outline-none cursor-pointer appearance-none"
                          style={{ backgroundColor: `${catColor}20`, color: catColor }}
                        >
                          {CATEGORIES.map((c) => (
                            <option key={c.id} value={c.id} style={{ backgroundColor: T.surfaceSolid, color: T.textPrimary }}>
                              {c.name}
                            </option>
                          ))}
                        </select>
                      </td>

                      {/* Descrição */}
                      <td className="px-4 py-2.5" style={{ borderBottom: `1px solid ${T.borderSubtle}` }}>
                        {editingCell?.id === e.id && editingCell.field === "description" ? (
                          <EditInput draft={draft} setDraft={setDraft} onCommit={commitEdit} onCancel={cancelEdit} wide T={T} />
                        ) : (
                          <button
                            onClick={() => startEdit(e.id, "description", e.description)}
                            className="text-left transition-colors"
                            style={{ color: T.textPrimary }}
                            onMouseEnter={(ev) => (ev.currentTarget.style.color = T.accent)}
                            onMouseLeave={(ev) => (ev.currentTarget.style.color = T.textPrimary)}
                          >
                            {e.description}
                          </button>
                        )}
                      </td>

                      {/* Valor */}
                      <td className="px-4 py-2.5 text-right font-mono" style={{ borderBottom: `1px solid ${T.borderSubtle}` }}>
                        {editingCell?.id === e.id && editingCell.field === "amount" ? (
                          <EditInput draft={draft} setDraft={setDraft} onCommit={commitEdit} onCancel={cancelEdit} align="right" T={T} />
                        ) : (
                          <button
                            onClick={() => startEdit(e.id, "amount", e.amount)}
                            className="font-medium transition-colors"
                            style={{ color: T.textPrimary }}
                            onMouseEnter={(ev) => (ev.currentTarget.style.color = T.accent)}
                            onMouseLeave={(ev) => (ev.currentTarget.style.color = T.textPrimary)}
                          >
                            {formatBRL(e.amount)}
                          </button>
                        )}
                      </td>

                      {/* Pagamento */}
                      <td className="px-4 py-2.5 font-mono text-xs" style={{ color: T.textFaint, borderBottom: `1px solid ${T.borderSubtle}` }}>
                        {e.paymentDay || "—"}
                      </td>

                      {/* Status */}
                      <td className="px-4 py-2.5" style={{ borderBottom: `1px solid ${T.borderSubtle}` }}>
                        <button
                          onClick={() => toggleStatus(e.id)}
                          className="text-[11px] font-semibold px-2.5 py-1 rounded-full transition-colors flex items-center gap-1 w-fit"
                          style={
                            isPago
                              ? { backgroundColor: `${T.success}1F`, color: T.successText }
                              : { backgroundColor: `${T.warning}1F`, color: T.warning }
                          }
                        >
                          {isPago ? <CircleCheck size={11} /> : <CircleDashed size={11} />}
                          {isPago ? "Pago" : "Pendente"}
                        </button>
                      </td>

                      {/* Observação */}
                      <td className="px-4 py-2.5 text-xs" style={{ color: T.textMuted, borderBottom: `1px solid ${T.borderSubtle}` }}>
                        {editingCell?.id === e.id && editingCell.field === "observation" ? (
                          <EditInput draft={draft} setDraft={setDraft} onCommit={commitEdit} onCancel={cancelEdit} wide T={T} />
                        ) : (
                          <button
                            onClick={() => startEdit(e.id, "observation", e.observation)}
                            className="text-left transition-colors flex items-center gap-1"
                            onMouseEnter={(ev) => (ev.currentTarget.style.color = T.textPrimary)}
                            onMouseLeave={(ev) => (ev.currentTarget.style.color = T.textMuted)}
                          >
                            {e.observation && <LinkIcon size={11} className="shrink-0" />}
                            {e.observation || "—"}
                          </button>
                        )}
                      </td>

                      {/* Delete */}
                      <td className="px-2 py-2.5" style={{ borderBottom: `1px solid ${T.borderSubtle}` }}>
                        <button
                          onClick={() => removeExpense(e.id)}
                          className="p-1 rounded opacity-0 group-hover:opacity-100 transition-all"
                          style={{ color: T.textFaint }}
                          onMouseEnter={(ev) => { ev.currentTarget.style.color = T.danger; ev.currentTarget.style.backgroundColor = `${T.danger}1A`; }}
                          onMouseLeave={(ev) => { ev.currentTarget.style.color = T.textFaint; ev.currentTarget.style.backgroundColor = "transparent"; }}
                          aria-label="Remover"
                        >
                          <Trash2 size={13} />
                        </button>
                      </td>
                    </tr>
                  );
                })}
                {monthExpenses.length === 0 && (
                  <tr>
                    <td colSpan={8} className="px-4 py-12 text-center text-sm" style={{ color: T.textFaint }}>
                      Nenhuma despesa encontrada para {monthLabel(monthRef)}.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>

        <p className="text-xs mt-4 text-center" style={{ color: T.textFaint }}>
          Protótipo com dados em memória, estruturados igual ao schema do Supabase · clique em qualquer célula pra editar
        </p>
      </div>

      {/* Import Modal */}
      {showImport && (
        <ImportModal
          T={T}
          theme={theme}
          monthRef={monthRef}
          onClose={() => setShowImport(false)}
          onImport={(rows) => {
            setExpenses((prev) => [...rows, ...prev]);
            setShowImport(false);
          }}
        />
      )}
    </div>
  );
}

function EditInput({ draft, setDraft, onCommit, onCancel, align, wide, T }) {
  return (
    <div className="flex items-center gap-1">
      <input
        autoFocus
        value={draft}
        onChange={(e) => setDraft(e.target.value)}
        onKeyDown={(e) => {
          if (e.key === "Enter") onCommit();
          if (e.key === "Escape") onCancel();
        }}
        onBlur={onCommit}
        className={`border rounded-lg px-2 py-1 outline-none ${wide ? "w-full min-w-[160px]" : "w-20"} ${align === "right" ? "text-right" : ""}`}
        style={{ backgroundColor: T.inputBg, borderColor: T.accent, color: T.textPrimary }}
      />
      <button onMouseDown={(e) => { e.preventDefault(); onCancel(); }} style={{ color: T.textFaint }}>
        <X size={12} />
      </button>
    </div>
  );
}

// ---------------------------------------------------------------------------
// IMPORT FIELDS — campos do banco que o usuário pode mapear
// ---------------------------------------------------------------------------
const IMPORT_FIELDS = [
  { key: "due_date",     label: "Vencimento",   required: true,  hint: "Data: 05, 5, 05/04/2026, 2026-04-05" },
  { key: "description", label: "Descrição",    required: true,  hint: "Texto livre" },
  { key: "amount",      label: "Valor",         required: true,  hint: "Número: 1234.56 ou 1.234,56" },
  { key: "category",   label: "Categoria",     required: false, hint: "Nome da categoria (Outros, DAAE…)" },
  { key: "status",      label: "Status",        required: false, hint: "pago | pendente" },
  { key: "payment_date",label: "Data Pagamento",required: false, hint: "Igual ao Vencimento" },
  { key: "observation", label: "Observação",    required: false, hint: "Texto livre" },
];

function parseAmount(raw) {
  if (raw === null || raw === undefined || raw === "") return 0;
  const s = String(raw).trim();
  // Remove R$, espaços
  const cleaned = s.replace(/R\$\s*/g, "").trim();
  // Se tem vírgula como decimal: 1.234,56 → 1234.56
  if (/\d,\d{1,2}$/.test(cleaned)) {
    return parseFloat(cleaned.replace(/\./g, "").replace(",", ".")) || 0;
  }
  return parseFloat(cleaned.replace(",", ".")) || 0;
}

function parseDateField(raw, monthRef) {
  if (!raw && raw !== 0) return null;
  const s = String(raw).trim();
  // Apenas dia: "5" ou "05"
  if (/^\d{1,2}$/.test(s)) {
    const [y, m] = monthRef.split("-");
    return parseInt(s, 10);
  }
  // "5.abr" ou "05.abr"
  const dotMatch = s.match(/^(\d{1,2})\..+/);
  if (dotMatch) return parseInt(dotMatch[1], 10);
  // "05/04/2026" ou "05-04-2026"
  const brMatch = s.match(/(\d{1,2})[\/-](\d{1,2})[\/-](\d{4})/);
  if (brMatch) return parseInt(brMatch[1], 10);
  // "2026-04-05"
  const isoMatch = s.match(/(\d{4})-(\d{2})-(\d{2})/);
  if (isoMatch) return parseInt(isoMatch[3], 10);
  // Número serial Excel (dias desde 1900-01-01)
  const num = parseFloat(s);
  if (!isNaN(num) && num > 40000) {
    const d = new Date(Math.round((num - 25569) * 86400 * 1000));
    return d.getDate();
  }
  return null;
}

function parseCategory(raw) {
  if (!raw) return "outros";
  const name = String(raw).trim().toLowerCase();
  const found = CATEGORIES.find((c) => c.name.toLowerCase() === name || c.id === name);
  return found ? found.id : "outros";
}

function parseStatus(raw) {
  if (!raw) return "pendente";
  const s = String(raw).trim().toLowerCase();
  return s === "pago" || s === "paid" ? "pago" : "pendente";
}

// ---------------------------------------------------------------------------
// ImportModal
// ---------------------------------------------------------------------------
function ImportModal({ T, theme, monthRef, onClose, onImport }) {
  const fileRef = useRef(null);
  const [step, setStep] = useState("upload"); // upload | map | preview | done
  const [headers, setHeaders] = useState([]);
  const [rows, setRows] = useState([]);
  const [mapping, setMapping] = useState({});
  const [preview, setPreview] = useState([]);
  const [error, setError] = useState("");
  const [isDragging, setIsDragging] = useState(false);

  // Carrega SheetJS dinamicamente se necessário
  async function loadSheetJS() {
    if (window.XLSX) return window.XLSX;
    return new Promise((resolve, reject) => {
      const s = document.createElement("script");
      s.src = "https://cdn.jsdelivr.net/npm/xlsx@0.18.5/dist/xlsx.full.min.js";
      s.onload = () => resolve(window.XLSX);
      s.onerror = () => reject(new Error("Falha ao carregar SheetJS"));
      document.head.appendChild(s);
    });
  }

  async function handleFile(file) {
    setError("");
    if (!file) return;
    const isCSV = file.name.endsWith(".csv");
    const isXLSX = file.name.endsWith(".xlsx") || file.name.endsWith(".xls");
    if (!isCSV && !isXLSX) {
      setError("Formato não suportado. Use .xlsx, .xls ou .csv");
      return;
    }
    try {
      const XLSX = await loadSheetJS();
      const buf = await file.arrayBuffer();
      const wb = XLSX.read(buf, { type: "array" });
      const ws = wb.Sheets[wb.SheetNames[0]];
      const data = XLSX.utils.sheet_to_json(ws, { header: 1, defval: "" });
      if (data.length < 2) { setError("Arquivo vazio ou sem dados."); return; }
      const hdrs = data[0].map((h) => String(h).trim());
      const dataRows = data.slice(1).filter((r) => r.some((c) => c !== ""));
      setHeaders(hdrs);
      setRows(dataRows);
      // Auto-mapping por nome de coluna
      const autoMap = {};
      const aliases = {
        due_date:     ["vencimento","due_date","due date","data vencimento","data"],
        description:  ["descricao","descrição","description","desc","nome"],
        amount:       ["valor","amount","value","vlr"],
        category:    ["categoria","category","cat"],
        status:       ["status","situacao","situação"],
        payment_date: ["pagamento","data pagamento","payment_date","payment date","pago em"],
        observation:  ["observacao","observação","observation","obs","nota"],
      };
      hdrs.forEach((h, i) => {
        const lower = h.toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g, "");
        for (const [field, list] of Object.entries(aliases)) {
          if (list.some((a) => lower.includes(a))) {
            if (!autoMap[field]) autoMap[field] = i;
          }
        }
      });
      setMapping(autoMap);
      setStep("map");
    } catch (e) {
      setError("Erro ao ler arquivo: " + e.message);
    }
  }

  function onDrop(e) {
    e.preventDefault();
    setIsDragging(false);
    handleFile(e.dataTransfer.files[0]);
  }

  function buildPreview() {
    let idC = Date.now();
    const [y, m] = monthRef.split("-");
    const built = rows.slice(0, 200).map((row) => {
      const dueDay = parseDateField(mapping.due_date !== undefined ? row[mapping.due_date] : null, monthRef) || 1;
      return {
        id: `imp-${idC++}`,
        monthRef,
        dueDay,
        category: parseCategory(mapping.category !== undefined ? row[mapping.category] : ""),
        description: mapping.description !== undefined ? String(row[mapping.description] || "").trim() : "—",
        amount: parseAmount(mapping.amount !== undefined ? row[mapping.amount] : 0),
        paymentDay: mapping.payment_date !== undefined ? String(row[mapping.payment_date] || "").trim() : "",
        status: parseStatus(mapping.status !== undefined ? row[mapping.status] : ""),
        observation: mapping.observation !== undefined ? String(row[mapping.observation] || "").trim() : "",
      };
    });
    setPreview(built);
    setStep("preview");
  }

  const requiredMapped = IMPORT_FIELDS.filter((f) => f.required).every((f) => mapping[f.key] !== undefined);

  const inputStyle = {
    backgroundColor: T.inputBg,
    borderColor: T.border,
    color: T.textPrimary,
  };

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4"
      style={{ backgroundColor: "rgba(0,0,0,0.6)", backdropFilter: "blur(6px)" }}
      onClick={(e) => { if (e.target === e.currentTarget) onClose(); }}
    >
      <div
        className="w-full max-w-2xl rounded-2xl border flex flex-col overflow-hidden"
        style={{ backgroundColor: T.surfaceSolid, borderColor: T.border, maxHeight: "90vh" }}
      >
        {/* Modal header */}
        <div className="flex items-center justify-between px-6 py-4 border-b" style={{ borderColor: T.border }}>
          <div className="flex items-center gap-2.5">
            <FileSpreadsheet size={18} style={{ color: T.accent }} />
            <span className="font-display font-semibold text-base" style={{ color: T.textPrimary }}>Importar Planilha</span>
            <span className="text-xs px-2 py-0.5 rounded-full font-mono" style={{ backgroundColor: `${T.accent}20`, color: T.accent }}>
              {step === "upload" ? "1/3" : step === "map" ? "2/3" : "3/3"}
            </span>
          </div>
          <button onClick={onClose} className="p-1.5 rounded-lg transition-colors" style={{ color: T.textFaint }}
            onMouseEnter={(e) => e.currentTarget.style.color = T.danger}
            onMouseLeave={(e) => e.currentTarget.style.color = T.textFaint}
          >
            <X size={16} />
          </button>
        </div>

        <div className="flex-1 overflow-y-auto">

          {/* STEP 1: Upload */}
          {step === "upload" && (
            <div className="p-6">
              <p className="text-sm mb-5" style={{ color: T.textMuted }}>Faça upload de um arquivo <strong>.xlsx</strong>, <strong>.xls</strong> ou <strong>.csv</strong>. A primeira linha deve conter os nomes das colunas.</p>
              <div
                className="border-2 border-dashed rounded-2xl p-10 flex flex-col items-center gap-3 cursor-pointer transition-colors"
                style={{ borderColor: isDragging ? T.accent : T.border, backgroundColor: isDragging ? `${T.accent}10` : "transparent" }}
                onDragOver={(e) => { e.preventDefault(); setIsDragging(true); }}
                onDragLeave={() => setIsDragging(false)}
                onDrop={onDrop}
                onClick={() => fileRef.current?.click()}
              >
                <Upload size={32} style={{ color: isDragging ? T.accent : T.textFaint }} />
                <p className="text-sm font-medium" style={{ color: isDragging ? T.accent : T.textMuted }}>Arraste o arquivo aqui ou clique para selecionar</p>
                <p className="text-xs" style={{ color: T.textFaint }}>.xlsx · .xls · .csv</p>
              </div>
              <input ref={fileRef} type="file" accept=".xlsx,.xls,.csv" className="hidden" onChange={(e) => handleFile(e.target.files[0])} />
              {error && (
                <div className="mt-4 flex items-center gap-2 text-sm px-3 py-2.5 rounded-lg" style={{ backgroundColor: `${T.danger}18`, color: T.danger }}>
                  <AlertCircle size={14} /> {error}
                </div>
              )}
            </div>
          )}

          {/* STEP 2: Mapping */}
          {step === "map" && (
            <div className="p-6">
              <p className="text-sm mb-1" style={{ color: T.textMuted }}>Arquivo carregado com <strong>{headers.length}</strong> colunas e <strong>{rows.length}</strong> linhas.</p>
              <p className="text-xs mb-5" style={{ color: T.textFaint }}>Associe cada campo abaixo a uma coluna da sua planilha. Campos marcados com * são obrigatórios.</p>

              <div className="flex flex-col gap-3">
                {IMPORT_FIELDS.map((field) => (
                  <div key={field.key} className="flex items-center gap-3">
                    <div className="w-36 flex-shrink-0">
                      <span className="text-sm font-medium" style={{ color: T.textPrimary }}>
                        {field.label}{field.required && <span style={{ color: T.danger }}> *</span>}
                      </span>
                      <p className="text-[11px] mt-0.5" style={{ color: T.textFaint }}>{field.hint}</p>
                    </div>
                    <div className="relative flex-1">
                      <select
                        value={mapping[field.key] !== undefined ? mapping[field.key] : ""}
                        onChange={(e) => {
                          const val = e.target.value;
                          setMapping((prev) => {
                            const next = { ...prev };
                            if (val === "") delete next[field.key];
                            else next[field.key] = parseInt(val, 10);
                            return next;
                          });
                        }}
                        className="w-full text-sm border rounded-xl px-3 py-2 outline-none appearance-none cursor-pointer"
                        style={inputStyle}
                      >
                        <option value="">— não mapear —</option>
                        {headers.map((h, i) => (
                          <option key={i} value={i}>{h} {rows[0]?.[i] !== undefined ? `(ex: ${String(rows[0][i]).slice(0,20)})` : ""}</option>
                        ))}
                      </select>
                      <ChevronDown size={13} className="absolute right-3 top-1/2 -translate-y-1/2 pointer-events-none" style={{ color: T.textFaint }} />
                    </div>
                    {mapping[field.key] !== undefined
                      ? <CheckCircle2 size={16} style={{ color: T.success }} />
                      : <div style={{ width: 16 }} />}
                  </div>
                ))}
              </div>

              {error && (
                <div className="mt-4 flex items-center gap-2 text-sm px-3 py-2.5 rounded-lg" style={{ backgroundColor: `${T.danger}18`, color: T.danger }}>
                  <AlertCircle size={14} /> {error}
                </div>
              )}
            </div>
          )}

          {/* STEP 3: Preview */}
          {step === "preview" && (
            <div className="p-6">
              <p className="text-sm mb-4" style={{ color: T.textMuted }}>
                <strong>{preview.length}</strong> {preview.length === 1 ? "registro" : "registros"} prontos para importar no mês <strong>{monthLabel(monthRef)}</strong>. Confira antes de confirmar:
              </p>
              <div className="overflow-x-auto rounded-xl border" style={{ borderColor: T.border }}>
                <table className="w-full text-xs">
                  <thead>
                    <tr style={{ backgroundColor: `${T.border}60`, color: T.textFaint }}>
                      {["Dia","Categoria","Descrição","Valor","Status"].map((h) => (
                        <th key={h} className="px-3 py-2 text-left font-medium">{h}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {preview.slice(0, 10).map((row, i) => {
                      const cat = CATEGORIES.find((c) => c.id === row.category);
                      const catColor = theme === "dark" ? cat?.dark : cat?.light;
                      const isPago = row.status === "pago";
                      return (
                        <tr key={i} style={{ borderTop: `1px solid ${T.borderSubtle}` }}>
                          <td className="px-3 py-2 font-mono" style={{ color: T.textMuted }}>{String(row.dueDay).padStart(2,"0")}</td>
                          <td className="px-3 py-2">
                            <span className="px-2 py-0.5 rounded-full text-[10px] font-semibold" style={{ backgroundColor: `${catColor}20`, color: catColor }}>{cat?.name}</span>
                          </td>
                          <td className="px-3 py-2" style={{ color: T.textPrimary }}>{row.description}</td>
                          <td className="px-3 py-2 font-mono" style={{ color: T.textPrimary }}>{formatBRL(row.amount)}</td>
                          <td className="px-3 py-2">
                            <span className="px-2 py-0.5 rounded-full text-[10px] font-semibold" style={isPago ? { backgroundColor: `${T.success}1F`, color: T.successText } : { backgroundColor: `${T.warning}1F`, color: T.warning }}>
                              {isPago ? "Pago" : "Pendente"}
                            </span>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
              {preview.length > 10 && (
                <p className="text-xs mt-2 text-center" style={{ color: T.textFaint }}>+ {preview.length - 10} registros não exibidos</p>
              )}
            </div>
          )}
        </div>

        {/* Modal footer */}
        <div className="flex items-center justify-between px-6 py-4 border-t" style={{ borderColor: T.border }}>
          <button
            onClick={() => step === "upload" ? onClose() : step === "map" ? setStep("upload") : setStep("map")}
            className="px-4 py-2 rounded-xl text-sm border transition-all"
            style={{ borderColor: T.border, color: T.textMuted, backgroundColor: "transparent" }}
          >
            {step === "upload" ? "Cancelar" : "← Voltar"}
          </button>
          {step === "map" && (
            <button
              onClick={requiredMapped ? buildPreview : undefined}
              className="px-5 py-2 rounded-xl text-sm font-semibold transition-all"
              style={{
                background: requiredMapped ? `linear-gradient(90deg, ${T.accent}, ${T.accentTo})` : T.border,
                color: requiredMapped ? T.accentOnBrand : T.textFaint,
                cursor: requiredMapped ? "pointer" : "not-allowed",
              }}
            >
              Visualizar prévia →
            </button>
          )}
          {step === "preview" && (
            <button
              onClick={() => onImport(preview)}
              className="flex items-center gap-2 px-5 py-2 rounded-xl text-sm font-semibold transition-all hover:opacity-90 active:scale-[0.98]"
              style={{ background: `linear-gradient(90deg, ${T.accent}, ${T.accentTo})`, color: T.accentOnBrand }}
            >
              <CheckCircle2 size={15} /> Importar {preview.length} registros
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
