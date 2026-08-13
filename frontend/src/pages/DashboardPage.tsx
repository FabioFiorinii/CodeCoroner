import { Link } from 'react-router-dom'
import { useProjects, useRepositories, useDashboard } from '../lib/queries'
import { STATUS_ICON, STATUS_COLOR, isBusy } from '../lib/analysisStatus'
import { Card } from '../components/common/Card'
import { Button } from '../components/common/Button'
import { useAuthStore } from '../stores/authStore'
import { Plus, FolderOpen, GitBranch, Users, Bug, Clock } from 'lucide-react'

export function DashboardPage() {
  const { user } = useAuthStore()
  const { data: projectsData } = useProjects()
  const { data: reposData } = useRepositories()
  const { data: dashboard } = useDashboard()

  const projects = projectsData?.results ?? []
  const recentAnalyses = dashboard?.recent_analyses ?? []

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-text-primary">
          Welcome back, {user?.username ?? 'Developer'}
        </h1>
        <p className="text-text-secondary mt-1">
          Here's an overview of your debugging workspace.
        </p>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
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
              <Users className="w-5 h-5 text-purple-500" />
            </div>
            <div>
              <p className="text-2xl font-bold text-text-primary">
                {dashboard?.team_member_count ?? 0}
              </p>
              <p className="text-sm text-text-muted">Team Members</p>
            </div>
          </div>
        </Card>

        <Card padding="lg">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-emerald-500/10 flex items-center justify-center">
              <Bug className="w-5 h-5 text-emerald-500" />
            </div>
            <div>
              <p className="text-2xl font-bold text-text-primary">
                {dashboard?.analyses_count ?? 0}
              </p>
              <p className="text-sm text-text-muted">Analyses</p>
            </div>
          </div>
        </Card>
      </div>

      <div>
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-text-primary">Recent Analysis</h2>
        </div>

        {recentAnalyses.length === 0 ? (
          <Card padding="lg" className="text-center">
            <Bug className="w-12 h-12 text-text-muted mx-auto mb-3" />
            <p className="font-medium text-text-primary">No analyses yet</p>
            <p className="text-sm text-text-muted mt-1 mb-4">
              Analyses from your team will show up here.
            </p>
            <Link to="/projects">
              <Button variant="secondary">
                <Plus className="w-4 h-4" />
                Start Analysis
              </Button>
            </Link>
          </Card>
        ) : (
          <div className="space-y-3">
            {recentAnalyses.map((a) => {
              const StatusIcon = STATUS_ICON[a.status] || Clock
              return (
                <Link
                  key={a.id}
                  to={`/projects/${a.project_id}/analyses/${a.id}`}
                  className="block group"
                >
                  <Card hover padding="md">
                    <div className="flex items-center justify-between">
                      <div className="min-w-0 flex-1">
                        <h3 className="font-semibold text-text-primary group-hover:text-primary transition-colors truncate">
                          {a.title || 'Untitled Analysis'}
                        </h3>
                        <p className="text-sm text-text-secondary mt-0.5">
                          {new Date(a.created_at).toLocaleString()}
                          {a.duration_seconds ? ` · ${a.duration_seconds}s` : ''}
                        </p>
                        <p className="text-xs text-text-muted mt-0.5 flex items-center gap-1">
                          <FolderOpen className="w-3 h-3" />
                          {a.project_name}
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
              )
            })}
          </div>
        )}
      </div>
    </div>
  )
}