import { useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import {
  ArrowLeft, Globe, GitBranch, FileCode, RefreshCw, Play,
  Trash2, Clock, AlertCircle, CheckCircle2, Loader2,
} from 'lucide-react'
import {
  useRepository, useDeleteRepository,
  useIndexRepository, useReindexRepository,
  useRepositoryFiles, useRepositoryChunks,
} from '../lib/queries'
import { Card } from '../components/common/Card'
import { Button } from '../components/common/Button'

const STATUS_ICON: Record<string, typeof AlertCircle> = {
  pending: Clock,
  cloning: Loader2,
  indexing: Loader2,
  indexed: CheckCircle2,
  error: AlertCircle,
}

const STATUS_COLOR: Record<string, string> = {
  pending: 'text-yellow-600 bg-yellow-50 border-yellow-200',
  cloning: 'text-blue-600 bg-blue-50 border-blue-200',
  indexing: 'text-blue-600 bg-blue-50 border-blue-200',
  indexed: 'text-green-600 bg-green-50 border-green-200',
  error: 'text-red-600 bg-red-50 border-red-200',
}

export function RepositoryDetailPage() {
  const { projectId, repoId } = useParams<{ projectId: string; repoId: string }>()
  const navigate = useNavigate()
  const { data: repo, isLoading, error } = useRepository(repoId)
  const deleteRepo = useDeleteRepository()
  const indexRepo = useIndexRepository()
  const reindexRepo = useReindexRepository()
  const { data: filesData } = useRepositoryFiles(repoId)
  const { data: chunksData } = useRepositoryChunks(repoId)
  const [showChunks, setShowChunks] = useState(false)

  const handleDelete = async () => {
    if (!window.confirm('Delete this repository permanently? Indexed data will be lost.')) return
    try {
      await deleteRepo.mutateAsync(repoId!)
      navigate(-1)
    } catch {
      // error handled by mutation
    }
  }

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

  if (error || !repo) {
    return (
      <Card padding="lg" className="max-w-3xl mx-auto text-center">
        <p className="text-red-500 font-medium">Repository not found</p>
        <Button variant="ghost" className="mt-4" onClick={() => navigate(`/projects/${projectId}/repos`)}>
          Back to Repositories
        </Button>
      </Card>
    )
  }

  const StatusIcon = STATUS_ICON[repo.status] || Clock
  const isBusy = repo.status === 'cloning' || repo.status === 'indexing'

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      <div>
        <button
          onClick={() => navigate(`/projects/${projectId}/repos`)}
          className="flex items-center gap-1.5 text-sm text-text-secondary hover:text-text-primary transition-colors mb-4"
        >
          <ArrowLeft className="w-4 h-4" />
          Repositories
        </button>
        <div className="flex items-start justify-between gap-4">
          <div className="min-w-0">
            <h1 className="text-2xl font-bold text-text-primary truncate">{repo.git_url}</h1>
            <p className="text-text-secondary mt-1 flex items-center gap-1">
              <GitBranch className="w-4 h-4" />
              {repo.git_branch}
            </p>
          </div>
          <div className="flex items-center gap-2 shrink-0">
            <Button
              variant="secondary"
              size="sm"
              onClick={() => indexRepo.mutate(repoId!)}
              loading={indexRepo.isPending}
              disabled={isBusy}
            >
              <Play className="w-4 h-4" />
              Index
            </Button>
            <Button
              variant="secondary"
              size="sm"
              onClick={() => reindexRepo.mutate(repoId!)}
              loading={reindexRepo.isPending}
              disabled={isBusy}
            >
              <RefreshCw className="w-4 h-4" />
              Reindex
            </Button>
            <Button variant="danger" size="sm" onClick={handleDelete} loading={deleteRepo.isPending}>
              <Trash2 className="w-4 h-4" />
            </Button>
          </div>
        </div>
      </div>

      <div className={`border rounded-lg p-4 ${STATUS_COLOR[repo.status] || 'border-gray-200'}`}>
        <div className="flex items-center gap-2">
          <StatusIcon className={`w-5 h-5 ${isBusy ? 'animate-spin' : ''}`} />
          <span className="font-medium capitalize">{repo.status}</span>
        </div>
        {repo.error_message && (
          <p className="text-sm mt-2 text-red-600">{repo.error_message}</p>
        )}
      </div>

      <div className="grid grid-cols-3 gap-4">
        <Card padding="sm" className="text-center">
          <FileCode className="w-5 h-5 text-primary mx-auto mb-1" />
          <p className="text-lg font-semibold">{repo.file_count}</p>
          <p className="text-xs text-text-muted">Files</p>
        </Card>
        <Card padding="sm" className="text-center">
          <Globe className="w-5 h-5 text-primary mx-auto mb-1" />
          <p className="text-lg font-semibold text-sm">
            {repo.total_bytes > 1024 * 1024
              ? `${(repo.total_bytes / (1024 * 1024)).toFixed(1)} MB`
              : repo.total_bytes > 1024
                ? `${(repo.total_bytes / 1024).toFixed(0)} KB`
                : `${repo.total_bytes} B`}
          </p>
          <p className="text-xs text-text-muted">Size</p>
        </Card>
        <Card padding="sm" className="text-center">
          <Clock className="w-5 h-5 text-primary mx-auto mb-1" />
          <p className="text-lg font-semibold text-xs text-text-muted">
            {repo.last_indexed_at
              ? new Date(repo.last_indexed_at).toLocaleDateString()
              : 'Never'}
          </p>
          <p className="text-xs text-text-muted">Last Indexed</p>
        </Card>
      </div>

      <Card padding="lg">
        <div className="flex items-center justify-between mb-4">
          <h3 className="font-semibold text-text-primary">Indexed Files</h3>
          <span className="text-sm text-text-muted">{filesData?.results?.length ?? 0} files</span>
        </div>
        {!filesData?.results?.length ? (
          <p className="text-sm text-text-muted">No files indexed yet. Run indexing to populate.</p>
        ) : (
          <div className="space-y-1 max-h-60 overflow-y-auto">
            {filesData.results.map((f) => (
              <div key={f.id} className="flex items-center gap-2 text-sm py-1">
                <FileCode className="w-4 h-4 text-text-muted shrink-0" />
                <span className="text-text-primary truncate">{f.file_path}</span>
                <span className="text-xs text-text-muted ml-auto shrink-0">{f.language}</span>
              </div>
            ))}
          </div>
        )}
      </Card>

      <Card padding="lg">
        <button
          onClick={() => setShowChunks(!showChunks)}
          className="flex items-center justify-between w-full"
        >
          <h3 className="font-semibold text-text-primary">Code Chunks</h3>
          <span className="text-sm text-text-muted">{chunksData?.results?.length ?? 0} chunks</span>
        </button>
        {showChunks && chunksData?.results?.length ? (
          <div className="space-y-2 mt-4 max-h-80 overflow-y-auto">
            {chunksData.results.map((c) => (
              <div key={c.id} className="text-sm border rounded p-2">
                <div className="flex items-center gap-2 text-text-muted text-xs mb-1">
                  <span className="font-medium text-text-primary">{c.chunk_type}</span>
                  <span>{c.file_path}:{c.start_line}-{c.end_line}</span>
                  {c.has_embedding && (
                    <span className="text-green-600 ml-auto">embedded</span>
                  )}
                </div>
                <pre className="text-xs text-text-secondary overflow-x-auto whitespace-pre-wrap line-clamp-3">
                  {c.content}
                </pre>
              </div>
            ))}
          </div>
        ) : showChunks ? (
          <p className="text-sm text-text-muted mt-4">No chunks found.</p>
        ) : null}
      </Card>
    </div>
  )
}
