import { useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { Plus, Bug, ArrowLeft, Clock, Trash2 } from 'lucide-react'
import { useAnalyses, useDeleteAnalysis } from '../lib/queries'
import { STATUS_ICON, STATUS_COLOR, isBusy } from '../lib/analysisStatus'
import { Card } from '../components/common/Card'
import { Button } from '../components/common/Button'
import { useAuthStore } from '../stores/authStore'

export function AnalysisListPage() {
  const { projectId } = useParams<{ projectId: string }>()
  const { user } = useAuthStore()
  const { data, isLoading } = useAnalyses(projectId)
  const deleteAnalysis = useDeleteAnalysis()
  const [search, setSearch] = useState('')

  const analyses = data?.results?.filter(
    (a) => a.title.toLowerCase().includes(search.toLowerCase()),
  )

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
              {data?.results?.length ?? 0} total
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
          const StatusIcon = STATUS_ICON[a.status] || Clock
          return (
            <div key={a.id} className="flex items-stretch gap-2">
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
                      <div className={`flex items-center gap-1.5 text-sm px-3 py-1 rounded-full border ${STATUS_COLOR[a.status] || 'border-gray-200'}`}>
                        <StatusIcon className={`w-4 h-4 ${isBusy(a.status) ? 'animate-spin' : ''}`} />
                        <span className="capitalize">{a.status}</span>
                      </div>
                    </div>
                    {a.error_message && (
                      <p className="text-sm text-red-500 mt-2">{a.error_message}</p>
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
            </div>
          )
        })}
      </div>
    </div>
  )
}
