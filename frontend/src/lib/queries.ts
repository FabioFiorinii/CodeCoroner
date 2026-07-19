import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { api } from './api'

export interface Project {
  id: string
  name: string
  description: string
  created_by: string
  created_at: string
  updated_at: string
  member_count: number
  repo_count: number
}

export interface ProjectInput {
  name: string
  description?: string
}

const PROJECTS_KEY = 'projects'

export function useProjects() {
  return useQuery<{ results: Project[] }>({
    queryKey: [PROJECTS_KEY],
    queryFn: () => api.get('/projects/'),
  })
}

export function useProject(id: string | undefined) {
  return useQuery<Project>({
    queryKey: [PROJECTS_KEY, id],
    queryFn: () => api.get(`/projects/${id}/`),
    enabled: !!id,
  })
}

export function useCreateProject() {
  const qc = useQueryClient()
  return useMutation<Project, Error, ProjectInput>({
    mutationFn: (data: ProjectInput) => api.post<Project>('/projects/', data),
    onSuccess: () => qc.invalidateQueries({ queryKey: [PROJECTS_KEY] }),
  })
}

export function useUpdateProject(id: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (data: Partial<ProjectInput>) => api.patch(`/projects/${id}/`, data),
    onSuccess: () => qc.invalidateQueries({ queryKey: [PROJECTS_KEY] }),
  })
}

export function useDeleteProject() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (id: string) => api.delete(`/projects/${id}/`),
    onSuccess: () => qc.invalidateQueries({ queryKey: [PROJECTS_KEY] }),
  })
}
