import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import Layout from './components/layout/Layout'
import { LoginPage } from './pages/LoginPage'
import { RegisterPage } from './pages/RegisterPage'
import { ProjectListPage } from './pages/ProjectListPage'
import { ProjectNewPage } from './pages/ProjectNewPage'
import { ProjectDetailPage } from './pages/ProjectDetailPage'
import { ProtectedRoute } from './components/common/ProtectedRoute'

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
          <Route path="analyses" element={<div>Analyses</div>} />
          <Route path="analyses/:id" element={<div>Analysis Detail</div>} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}

export default App
