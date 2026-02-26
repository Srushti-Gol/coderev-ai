export interface User {
  id: number
  github_id: number
  github_login: string
  email: string | null
  name: string | null
  avatar_url: string | null
  created_at: string
  updated_at: string | null
}

export interface Repository {
  id: number
  user_id: number
  github_repo_id: number
  full_name: string
  name: string
  description: string | null
  language: string | null
  is_private: boolean
  is_active: boolean
  webhook_id: number | null
  default_branch: string
  stars_count: number
  forks_count: number
  open_prs_count: number
  created_at: string
  updated_at: string | null
}

export type PRStatus = 'open' | 'closed' | 'merged' | 'draft'
export type AIStatus = 'pending' | 'analyzing' | 'completed' | 'failed'

export interface PullRequest {
  id: number
  repo_id: number
  pr_number: number
  title: string
  body: string | null
  author: string
  author_avatar: string | null
  base_branch: string
  head_branch: string
  status: PRStatus
  ai_status: AIStatus
  additions: number
  deletions: number
  changed_files: number
  quality_score: number | null
  security_score: number | null
  performance_score: number | null
  pr_url: string | null
  created_at: string
  updated_at: string | null
  pr_created_at: string | null
  pr_merged_at: string | null
  analyzed_at: string | null
}

export type AnalysisType =
  | 'security'
  | 'quality'
  | 'performance'
  | 'duplicate'
  | 'debt'
  | 'bug'
  | 'readability'
  | 'best_practice'
  | 'test'

export type Severity = 'critical' | 'high' | 'medium' | 'low' | 'info'

export interface Analysis {
  id: number
  pr_id: number
  analysis_type: AnalysisType
  severity: Severity
  file_path: string | null
  line_start: number | null
  line_end: number | null
  message: string
  suggestion: string | null
  code_snippet: string | null
  suggested_code: string | null
  rule_id: string | null
  is_verified: boolean
  is_dismissed: boolean
  created_at: string
}

export interface AnalysisSummary {
  total: number
  critical: number
  high: number
  medium: number
  low: number
  info: number
  by_type: Record<string, number>
  quality_score: number
  security_score: number
  performance_score: number
}

export interface DashboardStats {
  total_repos: number
  active_repos: number
  total_prs: number
  open_prs: number
  analyzed_prs: number
  total_issues: number
  critical_issues: number
  avg_quality_score: number
  period_days: number
}

export interface PRVelocityData {
  week: string
  opened: number
  merged: number
  closed: number
}

export interface CycleTimeData {
  repo: string
  avg_hours: number
  min_hours: number
  max_hours: number
  count: number
}

export interface DebtScoreData {
  date: string
  repo: string
  overall: number
  security: number
  quality: number
  performance: number
  maintainability: number
}

export interface QualityTrendData {
  date: string
  avg_quality: number
  count: number
}

export interface PRSizeDistribution {
  name: string
  value: number
}

export interface WeeklyDigest {
  this_week_prs: number
  prev_week_prs: number
  prs_change_pct: number
  this_week_issues: number
  period: {
    start: string
    end: string
  }
}

export interface ApiError {
  detail: string | { msg: string; type: string }[]
}

export interface PaginatedResponse<T> {
  items: T[]
  total: number
  skip: number
  limit: number
}
