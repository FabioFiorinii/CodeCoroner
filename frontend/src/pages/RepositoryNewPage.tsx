import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { ArrowLeft } from 'lucide-react'
import { useCreateRepository } from '../lib/queries'
import { Button } from '../components/common/Button'
import { Input } from '../components/common/Input'
import { Card } from '../components/common/Card'

export function RepositoryNewPage() {
  const navigate = useNavigate()
  const createRepo = useCreateRepository()
  const [gitUrl, setGitUrl] = useState('')
  const [gitBranch, setGitBranch] = useState('main')
  const [errors, setErrors] = useState<Record<string, string>>({})

  const validate = () => {
    const e: Record<string, string> = {}
    if (!gitUrl.trim()) e.git_url = 'Git URL is required'
    else if (!/^(https?:\/\/|git@)/.test(gitUrl.trim())) {
      e.git_url = 'Invalid Git URL format'
    }
    if (!gitBranch.trim()) e.git_branch = 'Branch name is required'
    setErrors(e)
    return Object.keys(e).length === 0
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!validate()) return
    try {
      await createRepo.mutateAsync({
        git_url: gitUrl.trim(),
        git_branch: gitBranch.trim(),
      })
      navigate('/repositories', { replace: true })
    } catch {
      // error handled by mutation
    }
  }

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <div>
        <button
          onClick={() => navigate('/repositories')}
          className="flex items-center gap-1.5 text-sm text-text-secondary hover:text-text-primary transition-colors mb-4"
        >
          <ArrowLeft className="w-4 h-4" />
          Back to Repositories
        </button>
        <h1 className="text-2xl font-bold text-text-primary">Add Repository</h1>
        <p className="text-text-secondary text-sm mt-1">
          Add a Git repository to start indexing code for analysis.
        </p>
      </div>

      <Card padding="lg">
        <form onSubmit={handleSubmit} className="space-y-5">
          <Input
            label="Git URL"
            placeholder="e.g. https://github.com/user/repo.git"
            value={gitUrl}
            onChange={(e) => setGitUrl(e.target.value)}
            error={errors.git_url}
            autoFocus
          />

          <Input
            label="Branch (optional)"
            placeholder="main"
            value={gitBranch}
            onChange={(e) => setGitBranch(e.target.value)}
            error={errors.git_branch}
          />

          <div className="flex items-center gap-3 pt-2">
            <Button type="submit" loading={createRepo.isPending}>
              Add Repository
            </Button>
            <Button
              type="button"
              variant="ghost"
              onClick={() => navigate('/repositories')}
            >
              Cancel
            </Button>
          </div>
        </form>
      </Card>
    </div>
  )
}
