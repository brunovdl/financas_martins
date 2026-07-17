-- =============================================================
-- MAI Finance — schema.sql
-- Banco: Supabase (Postgres)
-- Gerado em: 2026-07-16
-- =============================================================

-- -------------------------------------------------------------
-- ENUM
-- -------------------------------------------------------------
DO $$ BEGIN
  CREATE TYPE public.expense_status AS ENUM ('pago', 'pendente');
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

-- -------------------------------------------------------------
-- categories
-- -------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.categories (
  id         uuid        PRIMARY KEY DEFAULT gen_random_uuid(),
  name       text        NOT NULL UNIQUE,
  color      text        NOT NULL,          -- hex base; variante claro/escuro resolvida no frontend
  created_at timestamptz NOT NULL DEFAULT now()
);

-- RLS desabilitado para testes (habilitar antes de producao)
ALTER TABLE public.categories DISABLE ROW LEVEL SECURITY;

-- -------------------------------------------------------------
-- expenses
-- -------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.expenses (
  id           uuid                  PRIMARY KEY DEFAULT gen_random_uuid(),
  due_date     date                  NOT NULL,
  category_id  uuid                  REFERENCES public.categories(id) ON DELETE SET NULL,
  description  text                  NOT NULL,
  amount       numeric(12,2)         NOT NULL DEFAULT 0,
  payment_date date,                          -- data em que foi pago (nullable)
  status       public.expense_status NOT NULL DEFAULT 'pendente',
  observation  text,                          -- link, chave Pix, etc. (nullable)
  month_ref    date                  NOT NULL, -- primeiro dia do mes: 2026-04-01
  created_at   timestamptz           NOT NULL DEFAULT now(),
  updated_at   timestamptz           NOT NULL DEFAULT now()
);

-- Indices
CREATE INDEX IF NOT EXISTS idx_expenses_month_ref   ON public.expenses(month_ref);
CREATE INDEX IF NOT EXISTS idx_expenses_category_id ON public.expenses(category_id);
CREATE INDEX IF NOT EXISTS idx_expenses_status      ON public.expenses(status);

-- Trigger updated_at
CREATE OR REPLACE FUNCTION public.set_updated_at()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
BEGIN
  NEW.updated_at = now();
  RETURN NEW;
END;
$$;

CREATE TRIGGER trg_expenses_updated_at
  BEFORE UPDATE ON public.expenses
  FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();

-- RLS desabilitado para testes
ALTER TABLE public.expenses DISABLE ROW LEVEL SECURITY;

-- -------------------------------------------------------------
-- VIEW: monthly_summary
-- Agrega por month_ref - alimenta os cards de resumo do dashboard
-- -------------------------------------------------------------
CREATE OR REPLACE VIEW public.monthly_summary AS
SELECT
  month_ref,
  SUM(amount)                                               AS total_despesas,
  SUM(CASE WHEN status = 'pendente' THEN amount ELSE 0 END) AS total_pendente,
  COUNT(*) FILTER (WHERE status = 'pendente')               AS qtd_pendente
FROM public.expenses
GROUP BY month_ref
ORDER BY month_ref DESC;

-- -------------------------------------------------------------
-- RLS - Para habilitar em producao, executar:
-- -------------------------------------------------------------
-- ALTER TABLE public.categories ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE public.expenses   ENABLE ROW LEVEL SECURITY;
--
-- CREATE POLICY "authenticated full access on categories"
--   ON public.categories FOR ALL
--   TO authenticated USING (true) WITH CHECK (true);
--
-- CREATE POLICY "authenticated full access on expenses"
--   ON public.expenses FOR ALL
--   TO authenticated USING (true) WITH CHECK (true);
