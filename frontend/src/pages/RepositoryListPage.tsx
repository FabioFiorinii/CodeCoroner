import { useState } from 'react'
import { Link, useParams, useNavigate } from 'react-router-dom'
import { Plus, Search, GitBranch, Globe, FileCode, ArrowLeft } from 'lucide-react'
import { useProjectRepositories } from '../lib/queries'
import { Card } from '../components/common/Card'
import { Button } from '../components/common/Button'

const STATUS_BADGE: Record<string, string> = {
  pending: 'bg-yellow-100 text-yellow-800',
  cloning: 'bg-blue-100 text-blue-800',
  indexing: 'bg-blue-100 text-blue-800',
  indexed: 'bg-green-100 text-green-800',
  error: 'bg-red-100 text-red-800',
}

export function RepositoryListPage() {
  const { projectId } = useParams<{ projectId: string }>()
  const navigate = useNavigate()
  const { data, isLoading, error } = useProjectRepositories(projectId)
  const [search, setSearch] = useState('')

  const repos = data?.results?.filter(
    (r) => r.git_url.toLowerCase().includes(search.toLowerCase()),
  )

  return (
    <div className="space-y-6">
      <div>
        <button
          onClick={() => navigate(`/projects/${projectId}`)}
          className="flex items-center gap-1.5 text-sm text-text-secondary hover:text-text-primary transition-colors mb-4"
        >
          <ArrowLeft className="w-4 h-4" />
          Back to Project
        </button>
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-[clamp(2.5rem,5vw,4rem)] font-bold text-text-primary leading-tight">
              Repositories
            </h1>
            <p className="text-text-secondary mt-1">
              {data?.results?.length ?? 0} total
            </p>
          </div>
          <Link to={`/projects/${projectId}/repos/new`}>
            <Button>
              <Plus className="w-4 h-4" />
              Add Repository
            </Button>
          </Link>
        </div>
      </div>

      <div className="relative max-w-md">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-text-muted" />
        <input
          className="input-field pl-10"
          placeholder="Search repositories..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
      </div>

      {isLoading && (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {[1, 2, 3].map((i) => (
            <Card key={i} padding="md" className="animate-pulse space-y-3">
              <div className="h-5 bg-surface-alt rounded w-3/4" />
              <div className="h-4 bg-surface-alt rounded w-full" />
              <div className="flex gap-4">
                <div className="h-4 bg-surface-alt rounded w-16" />
                <div className="h-4 bg-surface-alt rounded w-16" />
              </div>
            </Card>
          ))}
        </div>
      )}

      {error && (
        <Card padding="md" className="text-red-500 border-red-200 bg-red-50">
          Failed to load repositories.
        </Card>
      )}

      {repos?.length === 0 && !isLoading && (
        <Card padding="lg" className="empty-state">
          <GitBranch className="w-12 h-12 text-text-muted" />
          <div>
            <p className="font-medium text-text-primary">No repositories yet</p>
            <p className="text-sm text-text-muted mt-1">
              Add a Git repository to start indexing code.
            </p>
          </div>
          <Link to={`/projects/${projectId}/repos/new`}>
            <Button variant="secondary" className="mt-2">
              <Plus className="w-4 h-4" />
              Add Repository
            </Button>
          </Link>
        </Card>
      )}

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {repos?.map((repo) => (
          <Link
            key={repo.id}
            to={`/projects/${projectId}/repos/${repo.id}`}
            className="block group"
          >
            <Card hover padding="md" className="h-full">
              <div className="flex items-start justify-between mb-3">
                <Globe className="w-5 h-5 text-primary mt-0.5" />
                <span
                  className={`text-xs font-medium px-2 py-0.5 rounded-full capitalize ${STATUS_BADGE[repo.status] || 'bg-gray-100 text-gray-800'}`}
                >
                  {repo.status}
                </span>
              </div>
              <h3 className="font-semibold text-text-primary group-hover:text-primary transition-colors text-sm truncate">
                {repo.git_url}
              </h3>
              <p className="text-sm text-text-secondary mt-1 flex items-center gap-1">
                <GitBranch className="w-3.5 h-3.5" />
                {repo.git_branch}
              </p>
              {repo.status === 'indexed' && (
                <div className="flex items-center gap-3 mt-4 text-xs text-text-muted">
                  <span className="flex items-center gap-1">
                    <FileCode className="w-3.5 h-3.5" />
                    {repo.file_count} files
                  </span>
                </div>
              )}
              {repo.status === 'error' && repo.error_message && (
                <p className="text-xs text-red-500 mt-2 truncate">
                  {repo.error_message}
                </p>
              )}
            </Card>
          </Link>
        ))}
      </div>
    </div>
  )
}
