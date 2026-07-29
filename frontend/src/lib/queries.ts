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

/* ───── Repositories ───── */

const REPOS_KEY = 'repositories'

export interface RepositoryItem {
  id: string
  project: string
  project_name: string
  git_url: string
  git_branch: string
  status: 'pending' | 'cloning' | 'indexing' | 'indexed' | 'error'
  file_count: number
  total_bytes: number
  error_message: string
  last_indexed_at: string | null
  created_at: string
  updated_at: string
}

export interface RepositoryInput {
  project: string
  git_url: string
  git_branch?: string
}

export interface RepositoryStatus {
  id: string
  status: string
  file_count: number
  total_bytes: number
  last_indexed_at: string | null
  error_message: string | null
}

export interface IndexedFileItem {
  id: string
  file_path: string
  language: string
  file_hash: string
  last_indexed_at: string
}

export interface CodeChunkItem {
  id: string
  file: string
  file_path: string
  chunk_type: string
  start_line: number
  end_line: number
  content: string
  tokens_count: number
  parent_chunk: string | null
  metadata: Record<string, unknown>
  has_embedding: boolean
}

export function useProjectRepositories(projectId: string | undefined) {
  return useQuery<{ results: RepositoryItem[] }>({
    queryKey: [REPOS_KEY, { project: projectId }],
    queryFn: () => api.get(`/repositories/?project=${projectId}`),
    enabled: !!projectId,
  })
}

export function useRepository(id: string | undefined) {
  return useQuery<RepositoryItem>({
    queryKey: [REPOS_KEY, id],
    queryFn: () => api.get(`/repositories/${id}/`),
    enabled: !!id,
    refetchInterval: (query) =>
      query.state.data?.status === 'indexing' || query.state.data?.status === 'cloning' ? 3000 : false,
  })
}

export function useCreateRepository() {
  const qc = useQueryClient()
  return useMutation<RepositoryItem, Error, RepositoryInput>({
    mutationFn: (data) => api.post<RepositoryItem>('/repositories/', data),
    onSuccess: (data) => {
      qc.invalidateQueries({ queryKey: [REPOS_KEY] })
      if (data?.project) {
        qc.invalidateQueries({ queryKey: [PROJECTS_KEY, data.project] })
      }
    },
  })
}

export function useDeleteRepository() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (id: string) => api.delete(`/repositories/${id}/`),
    onSuccess: () => qc.invalidateQueries({ queryKey: [REPOS_KEY] }),
  })
}

export function useIndexRepository() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (id: string) => api.post(`/repositories/${id}/index/`),
    onSuccess: () => qc.invalidateQueries({ queryKey: [REPOS_KEY] }),
  })
}

export function useReindexRepository() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (id: string) => api.post(`/repositories/${id}/reindex/`),
    onSuccess: () => qc.invalidateQueries({ queryKey: [REPOS_KEY] }),
  })
}

export function useRepositoryStatus(id: string | undefined) {
  return useQuery<RepositoryStatus>({
    queryKey: [REPOS_KEY, 'status', id],
    queryFn: () => api.get(`/repositories/${id}/status/`),
    enabled: !!id,
    refetchInterval: (query) =>
      query.state.data?.status === 'indexing' || query.state.data?.status === 'cloning' ? 3000 : false,
  })
}

export function useRepositoryFiles(id: string | undefined) {
  return useQuery<{ results: IndexedFileItem[] }>({
    queryKey: [REPOS_KEY, 'files', id],
    queryFn: () => api.get(`/repositories/${id}/files/`),
    enabled: !!id,
  })
}

export function useRepositoryChunks(id: string | undefined) {
  return useQuery<{ results: CodeChunkItem[] }>({
    queryKey: [REPOS_KEY, 'chunks', id],
    queryFn: () => api.get(`/repositories/${id}/chunks/`),
    enabled: !!id,
  })
}

/* ───── Analyses ───── */

const ANALYSES_KEY = 'analyses'

export interface AnalysisItem {
  id: string
  user: string
  project: string
  repository: string
  title: string
  error_context: Record<string, unknown>
  status: string
  created_at: string
  completed_at: string | null
  duration_seconds: number | null
  error_message: string
  runs: Array<{
    step: string
    status: string
    started_at: string
    completed_at: string | null
    error: string
  }>
  bug_localization: {
    summary: string
    suspicious_files: Array<{
      file_path: string
      suspicion_score: number
      evidence: string
      rank: number
    }>
    created_at: string
  } | null
  root_cause: {
    summary: string
    root_file: string
    root_line: number | null
    cause_chain: string
    confidence: number
    reasoning: string
    created_at: string
  } | null
  fix_suggestion: {
    diff: string
    plan: string
    explanation: string
    created_at: string
  } | null
  report: {
    markdown: string
    format: string
    created_at: string
  } | null
}

export interface AnalysisInput {
  project: string
  repository: string
  title: string
  error_context: Record<string, unknown>
}

export function useAnalyses(projectId: string | undefined) {
  return useQuery<{ results: AnalysisItem[] }>({
    queryKey: [ANALYSES_KEY, { project: projectId }],
    queryFn: () => api.get('/analyses/'),
    enabled: !!projectId,
  })
}

export function useAnalysis(id: string | undefined) {
  return useQuery<AnalysisItem>({
    queryKey: [ANALYSES_KEY, id],
    queryFn: () => api.get(`/analyses/${id}/`),
    enabled: !!id,
    refetchInterval: (query) =>
      ['queued', 'indexing', 'analyzing', 'bug_localization', 'rca', 'patching', 'fix_suggestion'].includes(query.state.data?.status ?? '')
        ? 3000
        : false,
  })
}

export function useCreateAnalysis() {
  const qc = useQueryClient()
  return useMutation<AnalysisItem, Error, AnalysisInput>({
    mutationFn: (data) => api.post<AnalysisItem>('/analyses/', data),
    onSuccess: () => qc.invalidateQueries({ queryKey: [ANALYSES_KEY] }),
  })
}
