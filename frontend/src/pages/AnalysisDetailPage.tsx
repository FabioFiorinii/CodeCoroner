import { useParams, useNavigate, Link } from 'react-router-dom'
import {
  ArrowLeft, Clock, CheckCircle2, AlertCircle, Loader2,
  FileCode, Target, FileSearch, BookOpen, Wrench, GitBranch, Globe,
  FileText, Trash2,
} from 'lucide-react'
import { useAnalysis, useDeleteAnalysis } from '../lib/queries'
import { useAuthStore } from '../stores/authStore'
import { Card } from '../components/common/Card'
import { Button } from '../components/common/Button'

const STATUS_ICON: Record<string, typeof Clock> = {
  queued: Clock,
  indexing: Loader2,
  analyzing: Loader2,
  bug_localization: Loader2,
  rca: Loader2,
  fix_suggestion: Loader2,
  completed: CheckCircle2,
  failed: AlertCircle,
}

const STATUS_COLOR: Record<string, string> = {
  queued: 'text-yellow-600 bg-yellow-50 border-yellow-200',
  indexing: 'text-blue-600 bg-blue-50 border-blue-200',
  analyzing: 'text-blue-600 bg-blue-50 border-blue-200',
  bug_localization: 'text-purple-600 bg-purple-50 border-purple-200',
  rca: 'text-purple-600 bg-purple-50 border-purple-200',
  fix_suggestion: 'text-amber-600 bg-amber-50 border-amber-200',
  completed: 'text-green-600 bg-green-50 border-green-200',
  failed: 'text-red-600 bg-red-50 border-red-200',
}

function formatDuration(seconds: number | null): string {
  if (!seconds) return ''
  if (seconds < 60) return `${seconds}s`
  return `${Math.floor(seconds / 60)}m ${seconds % 60}s`
}

export function AnalysisDetailPage() {
  const { projectId, id } = useParams<{ projectId: string; id: string }>()
  const navigate = useNavigate()
  const { data: analysis, isLoading, error } = useAnalysis(id)
  const deleteAnalysis = useDeleteAnalysis()
  const { user } = useAuthStore()

  if (isLoading) {
    return (
      <div className="max-w-3xl mx-auto space-y-4 animate-pulse">
        <div className="h-8 bg-surface-alt rounded w-1/3" />
        <div className="h-4 bg-surface-alt rounded w-2/3" />
        <Card padding="lg">
          <div className="space-y-3">
            <div className="h-5 bg-surface-alt rounded w-1/2" />
            <div className="h-4 bg-surface-alt rounded w-full" />
          </div>
        </Card>
      </div>
    )
  }

  if (error || !analysis) {
    return (
      <Card padding="lg" className="max-w-3xl mx-auto text-center">
        <p className="text-red-500 font-medium">Analysis not found</p>
        <Button variant="ghost" className="mt-4" onClick={() => navigate(`/projects/${projectId}/analyses`)}>
          Back to Analyses
        </Button>
      </Card>
    )
  }

  const StatusIcon = STATUS_ICON[analysis.status] || Clock
  const isBusy = ['queued', 'indexing', 'analyzing', 'bug_localization', 'rca', 'fix_suggestion'].includes(analysis.status)

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div>
        <Link
          to={`/projects/${projectId}/analyses`}
          className="flex items-center gap-1.5 text-sm text-text-secondary hover:text-text-primary transition-colors mb-4"
        >
          <ArrowLeft className="w-4 h-4" />
          Analyses
        </Link>
        <div className="flex items-start justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold text-text-primary">{analysis.title || 'Untitled Analysis'}</h1>
            <p className="text-text-secondary mt-1">
              {new Date(analysis.created_at).toLocaleString()}
              {analysis.duration_seconds ? ` · ${formatDuration(analysis.duration_seconds)}` : ''}
            </p>
            <p className="text-xs text-text-muted mt-1">
              by {analysis.user_email || analysis.user_username || analysis.user}
            </p>
          </div>
          {user?.is_superuser && (
            <Button
              variant="ghost"
              size="sm"
              className="text-red-500 hover:text-red-600 hover:bg-red-50 shrink-0"
              onClick={() => {
                if (confirm('Delete this analysis? This cannot be undone.')) {
                  deleteAnalysis.mutate(analysis.id, {
                    onSuccess: () => navigate(`/projects/${projectId}/analyses`),
                  })
                }
              }}
            >
              <Trash2 className="w-4 h-4" />
              Delete
            </Button>
          )}
        </div>
      </div>

      {analysis.repositories && analysis.repositories.length > 0 && (
        <Card padding="md">
          <h3 className="font-semibold text-text-primary flex items-center gap-2 mb-3 text-sm">
            <Globe className="w-4 h-4" />
            Analyzed Repositories
          </h3>
          <div className="space-y-2">
            {analysis.repositories.map((r) => (
              <Link
                key={r.id}
                to={`/repositories/${r.id}`}
                className="flex items-center gap-3 p-2.5 rounded-lg border border-border hover:border-primary/50 transition-colors group"
              >
                <GitBranch className="w-4 h-4 text-primary shrink-0" />
                <div className="min-w-0 flex-1">
                  <p className="text-sm font-medium text-text-primary group-hover:text-primary transition-colors truncate">
                    {r.git_url}
                  </p>
                  <p className="text-xs text-text-muted">{r.git_branch}</p>
                </div>
              </Link>
            ))}
          </div>
        </Card>
      )}

      {analysis.error_context && Object.keys(analysis.error_context).length > 0 && (
        <Card padding="md">
          <h3 className="font-semibold text-text-primary flex items-center gap-2 mb-3 text-sm">
            <FileText className="w-4 h-4" />
            Input Details
          </h3>
          <div className="space-y-3">
            {Object.entries(analysis.error_context).map(([key, value]) => (
              <div key={key}>
                <p className="text-xs font-medium text-text-muted uppercase tracking-wider mb-1">
                  {key.replace(/_/g, ' ')}
                </p>
                {typeof value === 'string' && value.length > 100 ? (
                  <pre className="text-xs font-mono bg-surface-alt rounded p-3 overflow-x-auto whitespace-pre-wrap leading-relaxed border max-h-48 overflow-y-auto">
                    {value}
                  </pre>
                ) : (
                  <p className="text-sm text-text-secondary">
                    {typeof value === 'string' ? value : JSON.stringify(value, null, 2)}
                  </p>
                )}
              </div>
            ))}
          </div>
        </Card>
      )}

      <div className={`border rounded-lg p-4 ${STATUS_COLOR[analysis.status] || 'border-gray-200'}`}>
        <div className="flex items-center gap-2">
          <StatusIcon className={`w-5 h-5 ${isBusy ? 'animate-spin' : ''}`} />
          <span className="font-medium capitalize">{analysis.status}</span>
          {analysis.duration_seconds && (
            <span className="text-sm ml-auto">{formatDuration(analysis.duration_seconds)}</span>
          )}
        </div>
        {analysis.error_message && (
          <p className="text-sm mt-2 text-red-600">{analysis.error_message}</p>
        )}
      </div>

      <div className="space-y-2">
        <h3 className="font-semibold text-text-primary flex items-center gap-2">
          <Clock className="w-4 h-4" />
          Pipeline Steps
        </h3>
        <div className="space-y-1">
          {['ensure_repo_indexed', 'analyze_input', 'bug_localization', 'root_cause', 'generate_report', 'fix_suggestion', 'completed'].map((step) => {
            const run = analysis.runs?.find((r) => r.step === step)
            if (!run && step !== 'completed') return null
            return (
              <div key={step} className="flex items-center gap-3 text-sm py-1.5">
                {!run ? (
                  <div className="w-2 h-2 rounded-full bg-gray-300 shrink-0" />
                ) : run.status === 'completed' ? (
                  <CheckCircle2 className="w-4 h-4 text-green-500 shrink-0" />
                ) : run.status === 'failed' ? (
                  <AlertCircle className="w-4 h-4 text-red-500 shrink-0" />
                ) : (
                  <Loader2 className="w-4 h-4 text-blue-500 animate-spin shrink-0" />
                )}
                <span className="capitalize">{step.replace(/_/g, ' ')}</span>
                {run?.error && <span className="text-red-500 text-xs ml-auto">{run.error}</span>}
              </div>
            )
          })}
        </div>
      </div>

      {analysis.bug_localization && (
        <Card padding="lg">
          <h3 className="font-semibold text-text-primary flex items-center gap-2 mb-4">
            <Target className="w-4 h-4" />
            Bug Localization
          </h3>
          <p className="text-sm text-text-secondary mb-4">{analysis.bug_localization.summary}</p>
          <div className="space-y-2">
            {analysis.bug_localization.suspicious_files?.map((f) => (
              <div
                key={f.rank}
                className="flex items-center gap-3 p-3 rounded-lg border"
              >
                <div className="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center text-sm font-bold text-primary shrink-0">
                  {f.rank}
                </div>
                <div className="min-w-0 flex-1">
                  <p className="text-sm font-medium text-text-primary truncate">{f.file_path}</p>
                  {f.evidence && (
                    <p className="text-xs text-text-muted mt-0.5 line-clamp-2">{f.evidence}</p>
                  )}
                </div>
                <div className="text-right shrink-0">
                  <div className="text-sm font-semibold text-primary">
                    {(f.suspicion_score * 100).toFixed(0)}%
                  </div>
                  <div className="text-xs text-text-muted">suspicion</div>
                </div>
              </div>
            ))}
          </div>
        </Card>
      )}

      {analysis.root_cause && (
        <Card padding="lg">
          <h3 className="font-semibold text-text-primary flex items-center gap-2 mb-4">
            <FileSearch className="w-4 h-4" />
            Root Cause Analysis
          </h3>
          <p className="font-medium text-text-primary mb-2">{analysis.root_cause.summary}</p>
          {analysis.root_cause.root_file && (
            <div className="flex items-center gap-2 text-sm text-text-secondary mb-3">
              <FileCode className="w-4 h-4" />
              <span>{analysis.root_cause.root_file}</span>
              {analysis.root_cause.root_line && (
                <span className="text-text-muted">: line {analysis.root_cause.root_line}</span>
              )}
            </div>
          )}
          <div className="text-sm text-text-secondary space-y-3">
            {analysis.root_cause.cause_chain && (
              <div>
                <p className="font-medium text-text-primary mb-1">Cause Chain</p>
                <p className="whitespace-pre-wrap">{analysis.root_cause.cause_chain}</p>
              </div>
            )}
            {analysis.root_cause.reasoning && (
              <div>
                <p className="font-medium text-text-primary mb-1">Reasoning</p>
                <p className="whitespace-pre-wrap">{analysis.root_cause.reasoning}</p>
              </div>
            )}
          </div>
          <div className="mt-3 flex items-center gap-2 text-sm">
            <span className="text-text-muted">Confidence:</span>
            <div className="flex-1 max-w-[200px] h-2 bg-surface-alt rounded-full overflow-hidden">
              <div
                className="h-full bg-primary rounded-full transition-all"
                style={{ width: `${(analysis.root_cause.confidence * 100).toFixed(0)}%` }}
              />
            </div>
            <span className="font-medium text-text-primary">
              {(analysis.root_cause.confidence * 100).toFixed(0)}%
            </span>
          </div>
        </Card>
      )}

      {analysis.fix_suggestion && (
        <Card padding="lg">
          <h3 className="font-semibold text-text-primary flex items-center gap-2 mb-4">
            <Wrench className="w-4 h-4" />
            Fix Suggestion
          </h3>

          {analysis.fix_suggestion.diff && (
            <div className="mb-4">
              <p className="font-medium text-text-primary mb-2 text-sm">Proposed Diff</p>
              <pre className="text-xs font-mono bg-surface-alt rounded-lg p-4 overflow-x-auto whitespace-pre-wrap leading-relaxed border">
                {analysis.fix_suggestion.diff}
              </pre>
            </div>
          )}

          {analysis.fix_suggestion.plan && (
            <div className="mb-4">
              <p className="font-medium text-text-primary mb-2 text-sm">Fix Plan (AI Prompt)</p>
              <pre className="text-xs font-mono bg-surface-alt rounded-lg p-4 overflow-x-auto whitespace-pre-wrap leading-relaxed border">
                {analysis.fix_suggestion.plan}
              </pre>
            </div>
          )}

          {analysis.fix_suggestion.explanation && (
            <div>
              <p className="font-medium text-text-primary mb-2 text-sm">Explanation</p>
              <p className="text-sm text-text-secondary whitespace-pre-wrap leading-relaxed">
                {analysis.fix_suggestion.explanation}
              </p>
            </div>
          )}
        </Card>
      )}

      {analysis.report && (
        <Card padding="lg">
          <h3 className="font-semibold text-text-primary flex items-center gap-2 mb-4">
            <BookOpen className="w-4 h-4" />
            Report
          </h3>
          <div className="prose prose-sm max-w-none text-text-secondary">
            {analysis.report.markdown.split('\n').map((line, i) => {
              if (line.startsWith('### ')) return <h4 key={i} className="text-text-primary font-semibold mt-4 mb-2">{line.slice(4)}</h4>
              if (line.startsWith('## ')) return <h3 key={i} className="text-text-primary font-bold mt-5 mb-2">{line.slice(3)}</h3>
              if (line.startsWith('# ')) return <h2 key={i} className="text-text-primary font-bold text-lg mt-5 mb-3">{line.slice(2)}</h2>
              if (line.startsWith('- ')) return <li key={i} className="ml-4 text-sm">{line.slice(2)}</li>
              if (line.startsWith('1. ')) return <li key={i} className="ml-4 text-sm list-decimal">{line.slice(3)}</li>
              if (line.trim() === '') return <br key={i} />
              return <p key={i} className="text-sm mb-1">{line}</p>
            })}
          </div>
        </Card>
      )}

      {analysis.status === 'completed' && !analysis.report && (
        <Card padding="lg" className="text-center text-text-muted">
          Analysis complete but no report was generated.
        </Card>
      )}
    </div>
  )
}
