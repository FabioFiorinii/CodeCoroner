import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { ArrowLeft } from 'lucide-react'
import { useCreateProject } from '../lib/queries'
import { Button } from '../components/common/Button'
import { Input } from '../components/common/Input'
import { Card } from '../components/common/Card'

export function ProjectNewPage() {
  const navigate = useNavigate()
  const createProject = useCreateProject()
  const [name, setName] = useState('')
  const [description, setDescription] = useState('')
  const [errors, setErrors] = useState<Record<string, string>>({})

  const validate = () => {
    const e: Record<string, string> = {}
    if (!name.trim()) e.name = 'Project name is required'
    setErrors(e)
    return Object.keys(e).length === 0
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!validate()) return
    try {
      const project = await createProject.mutateAsync({ name, description })
      navigate(`/projects/${project.id}`, { replace: true })
    } catch {
      // error handled by mutation
    }
  }

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <div>
        <button
          onClick={() => navigate(-1)}
          className="flex items-center gap-1.5 text-sm text-text-secondary hover:text-text-primary transition-colors mb-4"
        >
          <ArrowLeft className="w-4 h-4" />
          Back
        </button>
        <h1 className="text-2xl font-bold text-text-primary">New Project</h1>
        <p className="text-text-secondary text-sm mt-1">
          Create a new code analysis project.
        </p>
      </div>

      <Card padding="lg">
        <form onSubmit={handleSubmit} className="space-y-5">
          <Input
            label="Project Name"
            placeholder="e.g. my-awesome-app"
            value={name}
            onChange={(e) => setName(e.target.value)}
            error={errors.name}
            autoFocus
          />

          <div className="space-y-1.5">
            <label className="label">Description (optional)</label>
            <textarea
              className="input-field min-h-[100px] resize-y"
              placeholder="What is this project about?"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
            />
          </div>

          <div className="flex items-center gap-3 pt-2">
            <Button type="submit" loading={createProject.isPending}>
              Create Project
            </Button>
            <Button
              type="button"
              variant="ghost"
              onClick={() => navigate(-1)}
            >
              Cancel
            </Button>
          </div>
        </form>
      </Card>
    </div>
  )
}
