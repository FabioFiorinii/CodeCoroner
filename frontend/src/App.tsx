import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import Layout from './components/layout/Layout'
import { LoginPage } from './pages/LoginPage'
import { RegisterPage } from './pages/RegisterPage'
import { ProjectListPage } from './pages/ProjectListPage'
import { ProjectNewPage } from './pages/ProjectNewPage'
import { ProjectDetailPage } from './pages/ProjectDetailPage'
import { RepositoryListPage } from './pages/RepositoryListPage'
import { RepositoryNewPage } from './pages/RepositoryNewPage'
import { RepositoryDetailPage } from './pages/RepositoryDetailPage'
import { ProtectedRoute } from './components/common/ProtectedRoute'
import { AnalysisListPage } from './pages/AnalysisListPage'
import { AnalysisNewPage } from './pages/AnalysisNewPage'
import { AnalysisDetailPage } from './pages/AnalysisDetailPage'

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />
        <Route
          path="/"
          element={
            <ProtectedRoute>
              <Layout />
            </ProtectedRoute>
          }
        >
          <Route index element={<Navigate to="/dashboard" replace />} />
          <Route path="dashboard" element={<div>Dashboard</div>} />
          <Route path="projects" element={<ProjectListPage />} />
          <Route path="projects/new" element={<ProjectNewPage />} />
          <Route path="projects/:id" element={<ProjectDetailPage />} />
          <Route path="projects/:projectId/repos" element={<RepositoryListPage />} />
          <Route path="projects/:projectId/repos/new" element={<RepositoryNewPage />} />
          <Route path="projects/:projectId/repos/:repoId" element={<RepositoryDetailPage />} />
          <Route path="projects/:projectId/analyses" element={<AnalysisListPage />} />
          <Route path="projects/:projectId/analyses/new" element={<AnalysisNewPage />} />
          <Route path="projects/:projectId/analyses/:id" element={<AnalysisDetailPage />} />
          <Route path="analyses" element={<AnalysisListPage />} />
          <Route path="analyses/:id" element={<AnalysisDetailPage />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}

export default App
