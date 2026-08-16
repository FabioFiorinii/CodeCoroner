import { useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { Plus, Bug, ArrowLeft, Clock, Trash2, ChevronDown, ChevronUp, ChevronLeft, ChevronRight } from 'lucide-react'
import { useAnalyses, useDeleteAnalysis } from '../lib/queries'
import type { AnalysisItem } from '../lib/queries'
import { api } from '../lib/api'
import { STATUS_ICON, STATUS_COLOR, isBusy } from '../lib/analysisStatus'
import { Card } from '../components/common/Card'
import { Button } from '../components/common/Button'
import { useAuthStore } from '../stores/authStore'

export function AnalysisListPage() {
  const { projectId } = useParams<{ projectId: string }>()
  const { user } = useAuthStore()
  const [page, setPage] = useState(1)
  const { data, isLoading } = useAnalyses(projectId, page)
  const deleteAnalysis = useDeleteAnalysis()
  const [search, setSearch] = useState('')
  const [expandedThreads, setExpandedThreads] = useState<Set<string>>(new Set())
  const [threads, setThreads] = useState<Record<string, AnalysisItem[]>>({})

  const analyses = data?.results?.filter(
    (a) => a.title.toLowerCase().includes(search.toLowerCase()),
  )

  const toggleThread = async (rootId: string) => {
    if (expandedThreads.has(rootId)) {
      setExpandedThreads((prev) => {
        const next = new Set(prev)
        next.delete(rootId)
        return next
      })
      return
    }
    setExpandedThreads((prev) => new Set(prev).add(rootId))
    try {
      const list = await api.get<AnalysisItem[]>(`/analyses/${rootId}/thread/`)
      setThreads((prev) => ({ ...prev, [rootId]: list }))
    } catch {
      setExpandedThreads((prev) => {
        const next = new Set(prev)
        next.delete(rootId)
        return next
      })
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <Link
          to={`/projects/${projectId}`}
          className="flex items-center gap-1.5 text-sm text-text-secondary hover:text-text-primary transition-colors mb-4"
        >
          <ArrowLeft className="w-4 h-4" />
          Project
        </Link>
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-[clamp(2.5rem,5vw,4rem)] font-bold text-text-primary leading-tight">
              Analyses
            </h1>
            <p className="text-text-secondary mt-1">
              {data?.count ?? 0} total
            </p>
          </div>
          <Link to={`/projects/${projectId}/analyses/new`}>
            <Button>
              <Plus className="w-4 h-4" />
              New Analysis
            </Button>
          </Link>
        </div>
      </div>

      <div className="relative max-w-md">
        <input
          className="input-field pl-3"
          placeholder="Search analyses..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
      </div>

      {isLoading && (
        <div className="space-y-3">
          {[1, 2, 3].map((i) => (
            <Card key={i} padding="md" className="animate-pulse">
              <div className="h-5 bg-surface-alt rounded w-3/4 mb-2" />
              <div className="h-4 bg-surface-alt rounded w-1/2" />
            </Card>
          ))}
        </div>
      )}

      {analyses?.length === 0 && !isLoading && (
        <Card padding="lg" className="text-center">
          <Bug className="w-12 h-12 text-text-muted mx-auto mb-3" />
          <p className="font-medium text-text-primary">No analyses yet</p>
          <p className="text-sm text-text-muted mt-1 mb-4">
            Create an analysis to start debugging.
          </p>
          <Link to={`/projects/${projectId}/analyses/new`}>
            <Button variant="secondary">
              <Plus className="w-4 h-4" />
              New Analysis
            </Button>
          </Link>
        </Card>
      )}

      <div className="space-y-3">
        {analyses?.map((a) => {
          const StatusIcon = STATUS_ICON[a.latest_status || a.status] || Clock
          const isExpanded = expandedThreads.has(a.id)
          return (
            <div key={a.id}>
              <div className="flex items-stretch gap-2">
                <Link
                  to={`/projects/${projectId}/analyses/${a.id}`}
                  className="block group flex-1 min-w-0"
                >
                  <Card hover padding="md" className="h-full">
                    <div className="flex items-center justify-between">
                      <div className="min-w-0 flex-1">
                        <h3 className="font-semibold text-text-primary group-hover:text-primary transition-colors truncate">
                          {a.title || 'Untitled Analysis'}
                        </h3>
                        <p className="text-sm text-text-secondary mt-0.5">
                          {new Date(a.created_at).toLocaleString()}
                          {a.duration_seconds ? ` · ${a.duration_seconds}s` : ''}
                        </p>
                      </div>
                      <div className="flex items-center gap-2 shrink-0">
                        {a.children_count > 0 && (
                          <span className="text-xs bg-surface-alt text-text-secondary px-2 py-1 rounded-full">
                            {a.children_count} retr{a.children_count === 1 ? 'y' : 'ies'}
                          </span>
                        )}
                        <div className={`flex items-center gap-1.5 text-sm px-3 py-1 rounded-full border ${STATUS_COLOR[a.latest_status || a.status] || 'border-gray-200'}`}>
                          <StatusIcon className={`w-4 h-4 ${isBusy(a.latest_status || a.status) ? 'animate-spin' : ''}`} />
                          <span className="capitalize">{a.latest_status || a.status}</span>
                        </div>
                      </div>
                    </div>
                    {(a.latest_error_message || a.error_message) && (
                      <p className="text-sm text-red-500 mt-2">{a.latest_error_message || a.error_message}</p>
                    )}
                  </Card>
                </Link>
                {user?.is_superuser && (
                  <button
                    onClick={() => {
                      if (confirm(`Delete "${a.title || 'Untitled Analysis'}"?`)) {
                        deleteAnalysis.mutate(a.id)
                      }
                    }}
                    className="self-center p-2 text-text-muted hover:text-red-500 transition-colors shrink-0"
                    title="Delete analysis"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                )}
                {a.children_count > 0 && (
                  <button
                    onClick={() => toggleThread(a.id)}
                    className="self-center p-2 text-text-muted hover:text-primary transition-colors shrink-0"
                    title={isExpanded ? 'Hide retries' : 'Show retries'}
                  >
                    {isExpanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                  </button>
                )}
              </div>
              {isExpanded && (
                <div className="ml-8 mt-2 space-y-2">
                  {(threads[a.id] ?? []).map((child) => {
                    const ChildIcon = STATUS_ICON[child.status] || Clock
                    return (
                      <Link
                        key={child.id}
                        to={`/projects/${projectId}/analyses/${child.id}`}
                        className="block group"
                      >
                        <Card hover padding="sm" className="border-dashed">
                          <div className="flex items-center justify-between gap-3">
                            <div className="min-w-0 flex-1">
                              <h4 className="text-sm font-medium text-text-primary group-hover:text-primary transition-colors truncate">
                                Retry — {child.title || 'Untitled Analysis'}
                              </h4>
                              <p className="text-xs text-text-secondary mt-0.5">
                                {new Date(child.created_at).toLocaleString()}
                                {child.duration_seconds ? ` · ${child.duration_seconds}s` : ''}
                              </p>
                            </div>
                            <div className={`flex items-center gap-1.5 text-xs px-2.5 py-1 rounded-full border shrink-0 ${STATUS_COLOR[child.status] || 'border-gray-200'}`}>
                              <ChildIcon className={`w-3.5 h-3.5 ${isBusy(child.status) ? 'animate-spin' : ''}`} />
                              <span className="capitalize">{child.status}</span>
                            </div>
                          </div>
                          {child.error_message && (
                            <p className="text-xs text-red-500 mt-2">{child.error_message}</p>
                          )}
                        </Card>
                      </Link>
                    )
                  })}
                  {!threads[a.id] && (
                    <Card padding="sm" className="animate-pulse">
                      <div className="h-4 bg-surface-alt rounded w-2/3" />
                    </Card>
                  )}
                </div>
              )}
            </div>
          )
        })}
      </div>

      {data && data.count > 0 && (
        <div className="flex items-center justify-center gap-4 mt-6">
          <button
            onClick={() => setPage((p) => Math.max(1, p - 1))}
            disabled={!data.previous}
            className="flex items-center gap-1 px-3 py-1.5 rounded border border-border text-sm text-text-secondary hover:bg-surface-alt disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
          >
            <ChevronLeft className="w-4 h-4" />
            Prev
          </button>
          <span className="text-sm text-text-muted">
            Page {page} of {Math.max(1, Math.ceil(data.count / 10))}
          </span>
          <button
            onClick={() => setPage((p) => p + 1)}
            disabled={!data.next}
            className="flex items-center gap-1 px-3 py-1.5 rounded border border-border text-sm text-text-secondary hover:bg-surface-alt disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
          >
            Next
            <ChevronRight className="w-4 h-4" />
          </button>
        </div>
      )}
    </div>
  )
}
