import apiClient from './client'
import type { Repository } from '../types/models'

export async function listRepositories(projectId: string) {
  const { data } = await apiClient.get<Repository[]>('/repositories/', {
    params: { project: projectId },
  })
  return data
}

export async function getRepository(id: string) {
  const { data } = await apiClient.get<Repository>(`/repositories/${id}/`)
  return data
}

export async function createRepository(gitUrl: string, gitBranch: string, project: string) {
  const { data } = await apiClient.post<Repository>('/repositories/', {
    git_url: gitUrl,
    git_branch: gitBranch,
    project,
  })
  return data
}

export async function triggerIndex(repoId: string) {
  const { data } = await apiClient.post(`/repositories/${repoId}/index/`)
  return data
}
