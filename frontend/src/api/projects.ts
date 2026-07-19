import apiClient from './client'
import type { Project } from '../types/models'

export async function listProjects() {
  const { data } = await apiClient.get<Project[]>('/projects/')
  return data
}

export async function getProject(id: string) {
  const { data } = await apiClient.get<Project>(`/projects/${id}/`)
  return data
}

export async function createProject(name: string, description: string) {
  const { data } = await apiClient.post<Project>('/projects/', { name, description })
  return data
}

export async function updateProject(id: string, payload: Partial<Project>) {
  const { data } = await apiClient.patch<Project>(`/projects/${id}/`, payload)
  return data
}

export async function deleteProject(id: string) {
  await apiClient.delete(`/projects/${id}/`)
}
