import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import Layout from './components/layout/Layout'

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<Navigate to="/dashboard" replace />} />
          <Route path="dashboard" element={<div>Dashboard</div>} />
          <Route path="projects" element={<div>Projects</div>} />
          <Route path="projects/new" element={<div>New Project</div>} />
          <Route path="projects/:id" element={<div>Project Detail</div>} />
          <Route path="analyses" element={<div>Analyses</div>} />
          <Route path="analyses/:id" element={<div>Analysis Detail</div>} />
          <Route path="login" element={<div>Login</div>} />
          <Route path="register" element={<div>Register</div>} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}

export default App
