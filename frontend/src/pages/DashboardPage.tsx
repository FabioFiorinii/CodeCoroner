import { useNavigate, Link } from 'react-router-dom'
import { useProjects, useRepositories } from '../lib/queries'
import { Card } from '../components/common/Card'
import { Button } from '../components/common/Button'
import { useAuthStore } from '../stores/authStore'
import { Plus, FolderOpen, GitBranch, Bug, ArrowRight } from 'lucide-react'

export function DashboardPage() {
  const { user } = useAuthStore()
  const { data: projectsData, isLoading: projectsLoading } = useProjects()
  const { data: reposData } = useRepositories()
  const navigate = useNavigate()

  const projects = projectsData?.results ?? []
  const recentProjects = projects.slice(0, 5)

  return (
    <div className="space-y-8">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-text-primary">
            Welcome back, {user?.username ?? 'Developer'}
          </h1>
          <p className="text-text-secondary mt-1">
            Here's an overview of your debugging workspace.
          </p>
        </div>
        <Button onClick={() => navigate('/projects/new')}>
          <Plus className="w-4 h-4" />
          New Project
        </Button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card padding="lg">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center">
              <FolderOpen className="w-5 h-5 text-primary" />
            </div>
            <div>
              <p className="text-2xl font-bold text-text-primary">{projects.length}</p>
              <p className="text-sm text-text-muted">Projects</p>
            </div>
          </div>
        </Card>

        <Card padding="lg">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-blue-500/10 flex items-center justify-center">
              <GitBranch className="w-5 h-5 text-blue-500" />
            </div>
            <div>
              <p className="text-2xl font-bold text-text-primary">
                {reposData?.results?.length ?? 0}
              </p>
              <p className="text-sm text-text-muted">Repositories</p>
            </div>
          </div>
        </Card>

        <Card padding="lg">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-purple-500/10 flex items-center justify-center">
              <Bug className="w-5 h-5 text-purple-500" />
            </div>
            <div>
              <p className="text-2xl font-bold text-text-primary">
                {projects.reduce((sum, p) => sum + (p.member_count ?? 0), 0)}
              </p>
              <p className="text-sm text-text-muted">Team Members</p>
            </div>
          </div>
        </Card>
      </div>

      <div>
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-text-primary">Recent Projects</h2>
          {projects.length > 0 && (
            <Link to="/projects" className="text-sm text-primary hover:underline flex items-center gap-1">
              View all <ArrowRight className="w-3 h-3" />
            </Link>
          )}
        </div>

        {projectsLoading ? (
          <div className="space-y-3">
            {[1, 2, 3].map((i) => (
              <div key={i} className="h-16 bg-surface-alt rounded-lg animate-pulse" />
            ))}
          </div>
        ) : recentProjects.length === 0 ? (
          <Card padding="lg" className="text-center">
            <p className="text-text-muted mb-4">No projects yet. Create your first project to get started.</p>
            <Button onClick={() => navigate('/projects/new')}>
              <Plus className="w-4 h-4" />
              Create Project
            </Button>
          </Card>
        ) : (
          <div className="space-y-2">
            {recentProjects.map((p) => (
              <Link key={p.id} to={`/projects/${p.id}`} className="block group">
                <Card hover padding="md">
                  <div className="flex items-center justify-between">
                    <div>
                      <h3 className="font-medium text-text-primary group-hover:text-primary transition-colors">
                        {p.name}
                      </h3>
                      {p.description && (
                        <p className="text-sm text-text-muted mt-0.5 line-clamp-1">{p.description}</p>
                      )}
                    </div>
                    <div className="flex items-center gap-3 text-sm text-text-muted shrink-0">
                      <span className="flex items-center gap-1">
                        <GitBranch className="w-3.5 h-3.5" />
                        {p.repo_count}
                      </span>
                      <ArrowRight className="w-4 h-4 group-hover:text-primary transition-colors" />
                    </div>
                  </div>
                </Card>
              </Link>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
