export interface User {
  id: string
  email: string
  username: string
  is_active: boolean
  created_at: string
}

export interface Project {
  id: string
  name: string
  description: string
  created_by: string
  created_at: string
  updated_at: string
  memberships: ProjectMembership[]
  member_count: number
  repo_count: number
}

export interface ProjectMembership {
  id: string
  user: string
  user_email: string
  username: string
  role: 'owner' | 'admin' | 'member' | 'viewer'
  created_at: string
}

export interface Repository {
  id: string
  project: string
  project_name: string
  git_url: string
  git_branch: string
  status: 'pending' | 'cloning' | 'indexing' | 'indexed' | 'error'
  file_count: number
  total_bytes: number
  last_indexed_at: string | null
  created_at: string
}

export interface Analysis {
  id: string
  user: string
  project: string
  repository: string
  title: string
  error_context: ErrorContext
  status: AnalysisStatus
  created_at: string
  completed_at: string | null
  duration_seconds: number | null
  error_message: string
  runs: AnalysisRun[]
  bug_localization: BugLocalization | null
  root_cause: RootCause | null
  patch: Patch | null
  report: ReportData | null
}

export type AnalysisStatus =
  | 'queued' | 'indexing' | 'analyzing'
  | 'bug_localization' | 'rca'
  | 'patching' | 'validating'
  | 'completed' | 'failed'

export interface ErrorContext {
  stacktrace?: string
  logs?: string
  error_message?: string
  description?: string
  environment?: string
  steps_to_reproduce?: string
}

export interface AnalysisRun {
  id: string
  step: string
  status: 'running' | 'completed' | 'failed' | 'skipped'
  started_at: string
  completed_at: string | null
  error: string
}

export interface BugLocalization {
  summary: string
  suspicious_files: SuspiciousFile[]
  created_at: string
}

export interface SuspiciousFile {
  file_path: string
  suspicion_score: number
  matched_lines: number[]
  evidence: string
  rank: number
}

export interface RootCause {
  summary: string
  root_file: string
  root_line: number | null
  cause_chain: string
  confidence: number
  reasoning: string
  created_at: string
}

export interface Patch {
  id: string
  diff: string
  summary: string
  status: 'pending' | 'applied' | 'validated' | 'rejected'
  created_at: string
  validation?: PatchValidation
}

export interface PatchValidation {
  tests_passed: number
  tests_failed: number
  tests_skipped: number
  lint_errors: number
  lint_warnings: number
  type_errors: number
  overall_score: number
  output_log: string
}

export interface ReportData {
  markdown: string
  format: 'markdown' | 'pdf' | 'html'
  created_at: string
}
