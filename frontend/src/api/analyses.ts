import apiClient from './client'
import type { Analysis, ErrorContext } from '../types/models'

export async function listAnalyses(params?: Record<string, string>) {
  const { data } = await apiClient.get<Analysis[]>('/analyses/', { params })
  return data
}

export async function getAnalysis(id: string) {
  const { data } = await apiClient.get<Analysis>(`/analyses/${id}/`)
  return data
}

export async function createAnalysis(
  project: string,
  repository: string,
  title: string,
  errorContext: ErrorContext,
) {
  const { data } = await apiClient.post<Analysis>('/analyses/', {
    project,
    repository,
    title,
    error_context: errorContext,
  })
  return data
}

export async function getAnalysisStatus(id: string) {
  const { data } = await apiClient.get(`/analyses/${id}/status/`)
  return data
}

export async function getLocalization(id: string) {
  const { data } = await apiClient.get(`/analyses/${id}/localization/`)
  return data
}

export async function getRootCause(id: string) {
  const { data } = await apiClient.get(`/analyses/${id}/root-cause/`)
  return data
}

export async function getReport(id: string) {
  const { data } = await apiClient.get(`/analyses/${id}/report/`)
  return data
}
