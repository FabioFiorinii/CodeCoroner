import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { ArrowLeft, GitBranch, Globe, CheckSquare, Square } from 'lucide-react'
import { useProject, useRepositories, useProjectAssignedRepos, useAssignProjectRepos } from '../lib/queries'
import { Card } from '../components/common/Card'
import { Button } from '../components/common/Button'

export function ProjectReposPage() {
  const { projectId } = useParams<{ projectId: string }>()
  const navigate = useNavigate()
  const { data: project } = useProject(projectId)
  const { data: allRepos } = useRepositories()
  const { data: assignedRepos } = useProjectAssignedRepos(projectId)
  const assignMutation = useAssignProjectRepos(projectId)
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set())
  const [saved, setSaved] = useState(false)

  useEffect(() => {
    if (assignedRepos) {
      setSelectedIds(new Set(assignedRepos.map((r) => r.id)))
    }
  }, [assignedRepos])

  const repos = allRepos?.results ?? []
  const toggle = (id: string) => {
    setSelectedIds((prev) => {
      const next = new Set(prev)
      if (next.has(id)) next.delete(id)
      else next.add(id)
      return next
    })
    setSaved(false)
  }

  const handleSave = async () => {
    await assignMutation.mutateAsync(Array.from(selectedIds))
    setSaved(true)
    setTimeout(() => setSaved(false), 3000)
  }

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      <div>
        <button
          onClick={() => navigate(`/projects/${projectId}`)}
          className="flex items-center gap-1.5 text-sm text-text-secondary hover:text-text-primary transition-colors mb-4"
        >
          <ArrowLeft className="w-4 h-4" />
          Back to Project
        </button>
        <h1 className="text-2xl font-bold text-text-primary">{project?.name ?? 'Project'}</h1>
        <p className="text-text-secondary mt-1">
          Select which repositories are assigned to this project.
          {repos.length === 0 && ' No repositories available globally. Add one first.'}
        </p>
      </div>

      {repos.length === 0 ? (
        <Card padding="lg" className="text-center">
          <GitBranch className="w-12 h-12 text-text-muted mx-auto mb-3" />
          <p className="text-text-muted mb-4">No repositories found globally.</p>
          <Button onClick={() => navigate('/repositories/new')}>
            Add Repository
          </Button>
        </Card>
      ) : (
        <div className="space-y-2">
          {repos.map((repo) => {
            const isSelected = selectedIds.has(repo.id)
            return (
              <Card
                key={repo.id}
                hover
                padding="md"
                className={`cursor-pointer transition-all ${isSelected ? 'ring-2 ring-primary border-primary' : ''}`}
                onClick={() => toggle(repo.id)}
              >
                <div className="flex items-center gap-3">
                  <div className="text-primary shrink-0">
                    {isSelected ? <CheckSquare className="w-5 h-5" /> : <Square className="w-5 h-5 text-text-muted" />}
                  </div>
                  <Globe className="w-5 h-5 text-primary shrink-0" />
                  <div className="min-w-0 flex-1">
                    <p className="text-sm font-medium text-text-primary truncate">{repo.git_url}</p>
                    <p className="text-xs text-text-muted flex items-center gap-1 mt-0.5">
                      <GitBranch className="w-3 h-3" />
                      {repo.git_branch} &middot; {repo.status}
                    </p>
                  </div>
                </div>
              </Card>
            )
          })}
        </div>
      )}

      {repos.length > 0 && (
        <div className="flex items-center gap-3">
          <Button onClick={handleSave} loading={assignMutation.isPending}>
            Save Selection ({selectedIds.size} repos)
          </Button>
          {saved && (
            <span className="text-sm text-green-600 font-medium">Saved!</span>
          )}
        </div>
      )}
    </div>
  )
}
