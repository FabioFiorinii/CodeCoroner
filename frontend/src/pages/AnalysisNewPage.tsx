import { useState } from 'react'
import { useParams, useNavigate, Link } from 'react-router-dom'
import { ArrowLeft, Send } from 'lucide-react'
import { Card } from '../components/common/Card'
import { Button } from '../components/common/Button'
import { useProjectAssignedRepos, useCreateAnalysis } from '../lib/queries'

export function AnalysisNewPage() {
  const { projectId } = useParams<{ projectId: string }>()
  const navigate = useNavigate()
  const { data: reposData } = useProjectAssignedRepos(projectId)
  const createAnalysis = useCreateAnalysis()
  const repos = reposData ?? []

  const [selectedRepoIds, setSelectedRepoIds] = useState<Set<string>>(new Set())
  const [title, setTitle] = useState('')
  const [errorMessage, setErrorMessage] = useState('')
  const [stacktrace, setStacktrace] = useState('')
  const [logs, setLogs] = useState('')
  const [description, setDescription] = useState('')
  const [steps, setSteps] = useState('')

  const toggleRepo = (id: string) => {
    setSelectedRepoIds((prev) => {
      const next = new Set(prev)
      if (next.has(id)) next.delete(id)
      else next.add(id)
      return next
    })
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (selectedRepoIds.size === 0 || !errorMessage) return

    const errorContext: Record<string, unknown> = { error_message: errorMessage }
    if (stacktrace) errorContext.stacktrace = stacktrace
    if (logs) errorContext.logs = logs
    if (description) errorContext.description = description
    if (steps) errorContext.steps_to_reproduce = steps

    const primaryRepoId = repos.find((r) => selectedRepoIds.has(r.id))?.id ?? repos[0]?.id
    if (!primaryRepoId) return

    const result = await createAnalysis.mutateAsync({
      project: projectId!,
      repository: primaryRepoId,
      repository_ids: Array.from(selectedRepoIds),
      title: title || errorMessage,
      error_context: errorContext,
    })
    navigate(`/projects/${projectId}/analyses/${result.id}`)
  }

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <Link
        to={`/projects/${projectId}/analyses`}
        className="flex items-center gap-1.5 text-sm text-text-secondary hover:text-text-primary transition-colors"
      >
        <ArrowLeft className="w-4 h-4" />
        Analyses
      </Link>

      <h1 className="text-2xl font-bold text-text-primary">New Analysis</h1>

      <form onSubmit={handleSubmit} className="space-y-4">
        <Card padding="lg" className="space-y-4">
          <div>
            <label className="label-field">Repositories *</label>
            <div className="space-y-2 mt-1">
              {repos.map((r) => {
                const isSelected = selectedRepoIds.has(r.id)
                return (
                  <label
                    key={r.id}
                    className={`flex items-center gap-3 p-3 rounded-lg border cursor-pointer transition-all ${
                      isSelected ? 'border-primary bg-primary/5 ring-1 ring-primary' : 'border-border hover:border-primary/50'
                    }`}
                  >
                    <input
                      type="checkbox"
                      checked={isSelected}
                      onChange={() => toggleRepo(r.id)}
                      className="w-4 h-4 accent-primary"
                    />
                    <div className="min-w-0 flex-1">
                      <p className="text-sm font-medium text-text-primary truncate">{r.git_url}</p>
                      <p className="text-xs text-text-muted">{r.git_branch}</p>
                    </div>
                  </label>
                )
              })}
              {repos.length === 0 && (
                <p className="text-sm text-text-muted">No repositories assigned to this project.</p>
              )}
            </div>
          </div>

          <div>
            <label className="label-field">Title (optional)</label>
            <input
              className="input-field"
              placeholder="Brief title for this analysis"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
            />
          </div>

          <div>
            <label className="label-field">Error Message *</label>
            <input
              className="input-field"
              placeholder="e.g. TypeError: Cannot read property of undefined"
              value={errorMessage}
              onChange={(e) => setErrorMessage(e.target.value)}
              required
            />
          </div>

          <div>
            <label className="label-field">Stacktrace</label>
            <textarea
              className="input-field font-mono text-sm min-h-[120px]"
              placeholder="Paste the stacktrace here..."
              value={stacktrace}
              onChange={(e) => setStacktrace(e.target.value)}
            />
          </div>

          <div>
            <label className="label-field">Logs</label>
            <textarea
              className="input-field font-mono text-sm min-h-[120px]"
              placeholder="Paste relevant logs here..."
              value={logs}
              onChange={(e) => setLogs(e.target.value)}
            />
          </div>

          <div>
            <label className="label-field">Description</label>
            <textarea
              className="input-field text-sm min-h-[80px]"
              placeholder="Describe the bug in detail..."
              value={description}
              onChange={(e) => setDescription(e.target.value)}
            />
          </div>

          <div>
            <label className="label-field">Steps to Reproduce</label>
            <textarea
              className="input-field text-sm min-h-[80px]"
              placeholder="1. Do this... 2. Then this..."
              value={steps}
              onChange={(e) => setSteps(e.target.value)}
            />
          </div>
        </Card>

        <div className="flex justify-end">
          <Button type="submit" loading={createAnalysis.isPending} disabled={selectedRepoIds.size === 0 || !errorMessage}>
            <Send className="w-4 h-4" />
            Start Analysis
          </Button>
        </div>
      </form>
    </div>
  )
}
