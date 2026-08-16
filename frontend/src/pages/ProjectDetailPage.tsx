import { useParams, useNavigate, Link } from 'react-router-dom'
import { ArrowLeft, Trash2, Edit3, GitBranch, Clock, ChevronRight, Bug } from 'lucide-react'
import { useProject, useDeleteProject } from '../lib/queries'
import { Card } from '../components/common/Card'
import { Button } from '../components/common/Button'
import { WebhooksCard } from '../components/project/WebhooksCard'

export function ProjectDetailPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const { data: project, isLoading, error } = useProject(id)
  const deleteProject = useDeleteProject()

  const handleDelete = async () => {
    if (!window.confirm('Delete this project permanently?')) return
    await deleteProject.mutateAsync(id!)
    navigate('/projects', { replace: true })
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
            <div className="h-4 bg-surface-alt rounded w-3/4" />
          </div>
        </Card>
      </div>
    )
  }

  if (error || !project) {
    return (
      <Card padding="lg" className="max-w-3xl mx-auto text-center">
        <p className="text-red-500 font-medium">Project not found</p>
        <Button variant="ghost" className="mt-4" onClick={() => navigate('/projects')}>
          Back to Projects
        </Button>
      </Card>
    )
  }

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      <div>
        <button
          onClick={() => navigate('/projects')}
          className="flex items-center gap-1.5 text-sm text-text-secondary hover:text-text-primary transition-colors mb-4"
        >
          <ArrowLeft className="w-4 h-4" />
          Projects
        </button>
        <div className="flex items-start justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold text-text-primary">{project.name}</h1>
            {project.description && (
              <p className="text-text-secondary mt-1">{project.description}</p>
            )}
          </div>
          <div className="flex items-center gap-2 shrink-0">
            <Button variant="ghost" size="sm">
              <Edit3 className="w-4 h-4" />
            </Button>
            <Button variant="danger" size="sm" onClick={handleDelete} loading={deleteProject.isPending}>
              <Trash2 className="w-4 h-4" />
            </Button>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-3 gap-4">
        <Card padding="sm" className="text-center">
          <Bug className="w-5 h-5 text-primary mx-auto mb-1" />
          <p className="text-lg font-semibold">{project.analyses_count ?? 0}</p>
          <p className="text-xs text-text-muted">Analyses</p>
        </Card>
        <Card padding="sm" className="text-center">
          <GitBranch className="w-5 h-5 text-primary mx-auto mb-1" />
          <p className="text-lg font-semibold">{project.repo_count}</p>
          <p className="text-xs text-text-muted">Repositories</p>
        </Card>
        <Card padding="sm" className="text-center">
          <Clock className="w-5 h-5 text-primary mx-auto mb-1" />
          <p className="text-lg font-semibold text-xs text-text-muted">
            {new Date(project.created_at).toLocaleDateString()}
          </p>
          <p className="text-xs text-text-muted">Created</p>
        </Card>
      </div>

      <Link to={`/projects/${id}/analyses`} className="block group">
        <Card hover padding="lg">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <Bug className="w-5 h-5 text-primary" />
              <div>
                <h3 className="font-semibold text-text-primary group-hover:text-primary transition-colors">
                  Analyses
                </h3>
                <p className="text-sm text-text-muted">
                  AI-powered bug analysis and root cause detection
                </p>
              </div>
            </div>
            <ChevronRight className="w-5 h-5 text-text-muted group-hover:text-primary transition-colors" />
          </div>
        </Card>
      </Link>

      <Link to={`/projects/${id}/repos`} className="block group">
        <Card hover padding="lg">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <GitBranch className="w-5 h-5 text-primary" />
              <div>
                <h3 className="font-semibold text-text-primary group-hover:text-primary transition-colors">
                  Repositories
                </h3>
                <p className="text-sm text-text-muted">
                  {project.repo_count} {project.repo_count === 1 ? 'repository' : 'repositories'}
                </p>
              </div>
            </div>
            <ChevronRight className="w-5 h-5 text-text-muted group-hover:text-primary transition-colors" />
          </div>
        </Card>
      </Link>

      <WebhooksCard projectId={id!} />

    </div>
  )
}
