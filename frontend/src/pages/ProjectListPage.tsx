import { useState } from 'react'
import { Link } from 'react-router-dom'
import { Plus, FolderGit2, Search, Users, GitBranch } from 'lucide-react'
import { useProjects } from '../lib/queries'
import { Card } from '../components/common/Card'
import { Button } from '../components/common/Button'

export function ProjectListPage() {
  const { data, isLoading, error } = useProjects()
  const [search, setSearch] = useState('')

  const projects = data?.results?.filter(
    (p) => p.name.toLowerCase().includes(search.toLowerCase()),
  )

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-[clamp(2.5rem,5vw,4rem)] font-bold text-text-primary leading-tight">
            Projects
          </h1>
          <p className="text-text-secondary mt-1">
            {data?.results?.length ?? 0} total
          </p>
        </div>
        <Link to="/projects/new">
          <Button>
            <Plus className="w-4 h-4" />
            New Project
          </Button>
        </Link>
      </div>

      <div className="relative max-w-md">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-text-muted" />
        <input
          className="input-field pl-10"
          placeholder="Search projects..."
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
          Failed to load projects.
        </Card>
      )}

      {projects?.length === 0 && !isLoading && (
        <Card padding="lg" className="empty-state">
          <FolderGit2 className="w-12 h-12 text-text-muted" />
          <div>
            <p className="font-medium text-text-primary">No projects yet</p>
            <p className="text-sm text-text-muted mt-1">
              Create your first project to get started.
            </p>
          </div>
          <Link to="/projects/new">
            <Button variant="secondary" className="mt-2">
              <Plus className="w-4 h-4" />
              New Project
            </Button>
          </Link>
        </Card>
      )}

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {projects?.map((project) => (
          <Link key={project.id} to={`/projects/${project.id}`} className="block group">
            <Card hover padding="md" className="h-full">
              <div className="flex items-start justify-between mb-3">
                <FolderGit2 className="w-5 h-5 text-primary mt-0.5" />
              </div>
              <h3 className="font-semibold text-text-primary group-hover:text-primary transition-colors">
                {project.name}
              </h3>
              <p className="text-sm text-text-secondary mt-1 line-clamp-2">
                {project.description || 'No description'}
              </p>
              <div className="flex items-center gap-4 mt-4 text-xs text-text-muted">
                <span className="flex items-center gap-1">
                  <Users className="w-3.5 h-3.5" />
                  {project.member_count}
                </span>
                <span className="flex items-center gap-1">
                  <GitBranch className="w-3.5 h-3.5" />
                  {project.repo_count}
                </span>
              </div>
            </Card>
          </Link>
        ))}
      </div>
    </div>
  )
}
