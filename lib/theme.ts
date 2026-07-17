export interface CategoryTheme {
  id: string
  name: string
  dark: string
  light: string
  dbId?: string
}

export const CATEGORIES: CategoryTheme[] = [
  { id: 'outros', name: 'Outros', dark: '#94A3B8', light: '#475569' },
  { id: 'daae', name: 'DAAE', dark: '#5EA8F2', light: '#1D4ED8' },
  { id: 'condinvest', name: 'CondInvest', dark: '#B399F5', light: '#7C3AED' },
  { id: 'imposto', name: 'Imposto', dark: '#F5738C', light: '#BE123C' },
  { id: 'caixa', name: 'Caixa', dark: '#F2B84B', light: '#B45309' },
  { id: 'cpfl', name: 'CPFL', dark: '#3FD6C4', light: '#0F766E' },
]

export const MONTH_NAMES = [
  'Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho',
  'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro',
]

export interface ThemeTokens {
  pageBg: string
  surface: string
  surfaceSolid: string
  surfaceGradientA: string
  surfaceGradientB: string
  border: string
  borderSubtle: string
  textPrimary: string
  textMuted: string
  textFaint: string
  rowHover: string
  accent: string
  accentTo: string
  accentOnBrand: string
  success: string
  successText: string
  successBg: string
  successBorder: string
  warning: string
  warningBg: string
  warningBorder: string
  danger: string
  inputBg: string
  ring1: string
  ring2: string
  ringTrack: string
}

export const THEMES: { dark: ThemeTokens; light: ThemeTokens } = {
  dark: {
    pageBg: 'radial-gradient(ellipse 120% 80% at 50% -10%, #131A30 0%, #0A0D18 55%, #08090F 100%)',
    surface: '#12162860',
    surfaceSolid: '#151B2E',
    surfaceGradientA: '#151B32',
    surfaceGradientB: '#11152580',
    border: '#232A45',
    borderSubtle: '#1B2138',
    textPrimary: '#EDF0F7',
    textMuted: '#8891A8',
    textFaint: '#606A85',
    rowHover: '#161C34',
    accent: '#3FD6C4',
    accentTo: '#5B7FF5',
    accentOnBrand: '#08090F',
    success: '#3FD6C4',
    successText: '#5EE0C4',
    successBg: '#122620',
    successBorder: '#1F3D33',
    warning: '#F2B84B',
    warningBg: '#241D0F',
    warningBorder: '#3D3320',
    danger: '#F5738C',
    inputBg: '#0A0D18',
    ring1: '#3FD6C4',
    ring2: '#5EE0C4',
    ringTrack: '#1E2540',
  },
  light: {
    pageBg: 'radial-gradient(ellipse 120% 80% at 50% -10%, #FFFFFF 0%, #F4F6FB 55%, #EAEDF6 100%)',
    surface: '#FFFFFFB3',
    surfaceSolid: '#FFFFFF',
    surfaceGradientA: '#FFFFFF',
    surfaceGradientB: '#F6F8FC',
    border: '#E1E5F0',
    borderSubtle: '#EAEDF5',
    textPrimary: '#131826',
    textMuted: '#5B6478',
    textFaint: '#8890A3',
    rowHover: '#F4F6FC',
    accent: '#0E9488',
    accentTo: '#3B5FE0',
    accentOnBrand: '#FFFFFF',
    success: '#0D9488',
    successText: '#0D9488',
    successBg: '#ECFBF8',
    successBorder: '#CBEFE8',
    warning: '#B45309',
    warningBg: '#FFF7EB',
    warningBorder: '#F5E3C4',
    danger: '#BE123C',
    inputBg: '#FFFFFF',
    ring1: '#0D9488',
    ring2: '#3FD6C4',
    ringTrack: '#E4E8F0',
  },
}

export function formatBRL(value: number): string {
  return value.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })
}

export function monthLabel(monthRef: string): string {
  const [y, m] = monthRef.split('-').map(Number)
  return `${MONTH_NAMES[m - 1]} ${y}`
}

export function shiftMonth(monthRef: string, delta: number): string {
  const [y, m] = monthRef.split('-').map(Number)
  const d = new Date(y, m - 1 + delta, 1)
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}`
}

export function getCurrentMonthRef(): string {
  const d = new Date()
  const year = d.getFullYear()
  const month = String(d.getMonth() + 1).padStart(2, '0')
  return `${year}-${month}`
}
