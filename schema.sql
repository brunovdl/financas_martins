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
-- backups
-- -------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.backups (
  id               uuid          PRIMARY KEY DEFAULT gen_random_uuid(),
  type             text          NOT NULL DEFAULT 'automatico', -- 'automatico' | 'manual'
  categories_count integer       NOT NULL DEFAULT 0,
  expenses_count   integer       NOT NULL DEFAULT 0,
  total_amount     numeric(12,2) NOT NULL DEFAULT 0,
  data             jsonb         NOT NULL, -- snapshot completo de categorias e despesas
  created_at       timestamptz   NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_backups_created_at ON public.backups(created_at DESC);
ALTER TABLE public.backups DISABLE ROW LEVEL SECURITY;

-- Stored Function para gerar backup no servidor com retenção dos 3 últimos
CREATE OR REPLACE FUNCTION public.create_backup(backup_type text DEFAULT 'automatico')
RETURNS uuid LANGUAGE plpgsql AS $$
DECLARE
  v_backup_id uuid;
  v_cats jsonb;
  v_exps jsonb;
  v_cats_cnt int;
  v_exps_cnt int;
  v_total numeric(12,2);
BEGIN
  SELECT jsonb_agg(to_jsonb(c)), count(*) INTO v_cats, v_cats_cnt FROM public.categories c;
  SELECT jsonb_agg(to_jsonb(e)), count(*), COALESCE(sum(amount), 0) INTO v_exps, v_exps_cnt, v_total FROM public.expenses e;

  INSERT INTO public.backups (type, categories_count, expenses_count, total_amount, data)
  VALUES (
    backup_type,
    COALESCE(v_cats_cnt, 0),
    COALESCE(v_exps_cnt, 0),
    COALESCE(v_total, 0),
    jsonb_build_object(
      'categories', COALESCE(v_cats, '[]'::jsonb),
      'expenses', COALESCE(v_exps, '[]'::jsonb)
    )
  )
  RETURNING id INTO v_backup_id;

  -- Retenção: apagar backups excedentes mantendo apenas os 3 mais recentes
  DELETE FROM public.backups
  WHERE id NOT IN (
    SELECT id FROM public.backups
    ORDER BY created_at DESC
    LIMIT 3
  );

  RETURN v_backup_id;
END;
$$;

-- Agendamento pg_cron (Executa todo dia 1 e 15 de cada mês à meia-noite)
DO $$
BEGIN
  IF EXISTS (SELECT 1 FROM pg_extension WHERE extname = 'pg_cron') THEN
    PERFORM cron.schedule(
      'auto-backup-biweekly',
      '0 0 1,15 * *',
      $$ SELECT public.create_backup('automatico'); $$
    );
  END IF;
END $$;

-- -------------------------------------------------------------
-- RLS - Para habilitar em producao, executar:
-- -------------------------------------------------------------
-- ALTER TABLE public.categories ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE public.expenses   ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE public.backups    ENABLE ROW LEVEL SECURITY;
--
-- CREATE POLICY "authenticated full access on categories"
--   ON public.categories FOR ALL
--   TO authenticated USING (true) WITH CHECK (true);
--
-- CREATE POLICY "authenticated full access on expenses"
--   ON public.expenses FOR ALL
--   TO authenticated USING (true) WITH CHECK (true);
--
-- CREATE POLICY "authenticated full access on backups"
--   ON public.backups FOR ALL
--   TO authenticated USING (true) WITH CHECK (true);
