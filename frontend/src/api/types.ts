export type RiskLevel = 'likely_scam' | 'suspicious' | 'probably_ok' | 'cannot_tell'

export interface ReasonItem {
  flag: string
  quote: string
  why: string
}

export interface AnalyzeResult {
  risk_level: RiskLevel
  headline: string
  reasons: ReasonItem[]
  what_to_do_now: string[]
  what_not_to_do: string[]
  note: string
}

export interface Scenario {
  id: string
  title: string
  plain_description: string
  scammer_goal: string
  opening_message: string
  tactics: string[]
  payment_method: string
  red_flags_expected: string[]
  difficulty_variants: Record<string, unknown>
  max_turns: number
}

export interface DrillTurn {
  id: number
  role: string
  content: string
  created_at?: string
}

export interface DrillSession {
  id: string
  scenario_id: string
  difficulty: string
  mode: string
  status: string
  turn_count: number
  turns: DrillTurn[]
}

export interface DrillTurnResponse {
  user_turn: DrillTurn
  caller_turn: DrillTurn | null
  finished: boolean
  warning?: string | null
}

export interface DebriefMoment {
  turn_index: number
  quote: string
  flag: string
  why: string
}

export interface Debrief {
  summary_plain: string
  moments: DebriefMoment[]
  what_you_did_well: string[]
  one_thing_to_try: string
  hung_up_early: boolean
}

export interface FamilyContact {
  id: number
  name: string
  email: string
  status: string
  created_at?: string
}

export interface ContactEntry {
  name: string
  how: string
  url: string | null
  phone: string | null
}

export interface HelpNow {
  id: string
  label: string
  help_now_steps: string[]
  who_to_contact: ContactEntry[]
}

export interface ReportSummary {
  area?: string | null
  items: { scam_type: string; count: number }[]
  total: number
  enough: boolean
  message_plain?: string | null
  label: string
  period_days: number
}

export interface User {
  id: number
  email: string
}

export interface ApiErrorBody {
  error?: {
    code: string
    message_plain: string
  }
  detail?: ApiErrorBody['error'] | { error: ApiErrorBody['error'] }
}
