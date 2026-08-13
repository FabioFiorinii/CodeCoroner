import { useState } from 'react'
import { Send } from 'lucide-react'
import { Button } from './common/Button'

export interface AnalysisFormRepo {
  id: string
  git_url: string
  git_branch: string
}

export interface AnalysisFormInitial {
  title?: string
  errorContext?: Record<string, unknown>
  repoIds?: string[]
}

interface AnalysisFormProps {
  projectId: string
  availableRepos: AnalysisFormRepo[]
  initial?: AnalysisFormInitial
  submitLabel: string
  note?: string
  loading?: boolean
  onSubmit: (input: {
    project: string
    repository: string
    repository_ids: string[]
    title: string
    error_context: Record<string, unknown>
  }) => Promise<void>
}

export function AnalysisForm({
  projectId,
  availableRepos,
  initial,
  submitLabel,
  note,
  loading,
  onSubmit,
}: AnalysisFormProps) {
  const ec = initial?.errorContext ?? {}
  const [selectedRepoIds, setSelectedRepoIds] = useState<Set<string>>(
    () => new Set(initial?.repoIds ?? []),
  )
  const [title, setTitle] = useState(initial?.title ?? '')
  const [errorMessage, setErrorMessage] = useState(
    typeof ec.error_message === 'string' ? ec.error_message : '',
  )
  const [stacktrace, setStacktrace] = useState(
    typeof ec.stacktrace === 'string' ? ec.stacktrace : '',
  )
  const [logs, setLogs] = useState(typeof ec.logs === 'string' ? ec.logs : '')
  const [description, setDescription] = useState(
    typeof ec.description === 'string' ? ec.description : '',
  )
  const [steps, setSteps] = useState(
    typeof ec.steps_to_reproduce === 'string' ? ec.steps_to_reproduce : '',
  )

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

    const primaryRepoId =
      availableRepos.find((r) => selectedRepoIds.has(r.id))?.id ?? availableRepos[0]?.id
    if (!primaryRepoId) return

    await onSubmit({
      project: projectId,
      repository: primaryRepoId,
      repository_ids: Array.from(selectedRepoIds),
      title: title || errorMessage,
      error_context: errorContext,
    })
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div>
        <label className="label-field">Repositories *</label>
        <div className="space-y-2 mt-1">
          {availableRepos.map((r) => {
            const isSelected = selectedRepoIds.has(r.id)
            return (
              <label
                key={r.id}
                className={`flex items-center gap-3 p-3 rounded-lg border cursor-pointer transition-all ${
                  isSelected
                    ? 'border-primary bg-primary/5 ring-1 ring-primary'
                    : 'border-border hover:border-primary/50'
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
          {availableRepos.length === 0 && (
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

      {note && <p className="text-xs text-amber-600">{note}</p>}

      <div className="flex justify-end">
        <Button
          type="submit"
          loading={loading}
          disabled={selectedRepoIds.size === 0 || !errorMessage}
        >
          <Send className="w-4 h-4" />
          {submitLabel}
        </Button>
      </div>
    </form>
  )
}