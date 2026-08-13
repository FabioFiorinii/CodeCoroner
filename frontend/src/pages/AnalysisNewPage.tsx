import { useState } from 'react'
import { useParams, useNavigate, Link } from 'react-router-dom'
import { ArrowLeft } from 'lucide-react'
import { AnalysisForm } from '../components/AnalysisForm'
import { Card } from '../components/common/Card'
import { useProjectAssignedRepos, useCreateAnalysis } from '../lib/queries'

export function AnalysisNewPage() {
  const { projectId } = useParams<{ projectId: string }>()
  const navigate = useNavigate()
  const { data: reposData } = useProjectAssignedRepos(projectId)
  const createAnalysis = useCreateAnalysis()
  const [submitError, setSubmitError] = useState<string | null>(null)
  const repos = reposData ?? []

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

      <Card padding="lg" className="space-y-4">
        <AnalysisForm
          projectId={projectId!}
          availableRepos={repos}
          submitLabel="Start Analysis"
          loading={createAnalysis.isPending}
          onSubmit={async (input) => {
            setSubmitError(null)
            try {
              const result = await createAnalysis.mutateAsync(input)
              navigate(`/projects/${projectId}/analyses/${result.id}`)
            } catch (err) {
              setSubmitError(err instanceof Error ? err.message : 'Failed to start analysis.')
            }
          }}
        />
      </Card>

      {submitError && <p className="text-sm text-red-500">{submitError}</p>}
    </div>
  )
}