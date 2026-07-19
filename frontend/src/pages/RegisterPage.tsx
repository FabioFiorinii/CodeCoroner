import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuthStore } from '../stores/authStore'
import { Button } from '../components/common/Button'
import { Input } from '../components/common/Input'
import { Card } from '../components/common/Card'

export function RegisterPage() {
  const navigate = useNavigate()
  const { register, isLoading, error, clearError } = useAuthStore()
  const [email, setEmail] = useState('')
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [validationErrors, setValidationErrors] = useState<Record<string, string>>({})

  const validate = () => {
    const errors: Record<string, string> = {}
    if (!email.trim()) errors.email = 'Email is required'
    if (!username.trim()) errors.username = 'Username is required'
    if (!password) errors.password = 'Password is required'
    else if (password.length < 8) errors.password = 'Password must be at least 8 characters'
    if (password !== confirmPassword) errors.confirmPassword = 'Passwords do not match'
    setValidationErrors(errors)
    return Object.keys(errors).length === 0
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    clearError()
    if (!validate()) return
    try {
      await register(email, username, password)
      navigate('/login', { replace: true })
    } catch {
      // error is set in store
    }
  }

  return (
    <div className="min-h-screen star-bg flex items-center justify-center px-4">
      <Card padding="lg" className="w-full max-w-md animate-fade-in">
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-12 h-12 rounded-xl bg-primary/10 mb-4">
            <span className="text-2xl font-bold text-primary">C</span>
          </div>
          <h1 className="text-2xl font-bold text-text-primary">Create account</h1>
          <p className="text-text-secondary text-sm mt-1">Get started with CodeCoroner</p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <Input
            label="Email"
            type="email"
            placeholder="you@example.com"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            error={validationErrors.email}
            autoComplete="email"
          />

          <Input
            label="Username"
            type="text"
            placeholder="yourusername"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            error={validationErrors.username}
            autoComplete="username"
          />

          <Input
            label="Password"
            type="password"
            placeholder="Min. 8 characters"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            error={validationErrors.password}
            autoComplete="new-password"
          />

          <Input
            label="Confirm Password"
            type="password"
            placeholder="Repeat your password"
            value={confirmPassword}
            onChange={(e) => setConfirmPassword(e.target.value)}
            error={validationErrors.confirmPassword}
            autoComplete="new-password"
          />

          {error && (
            <div className="bg-red-50 border border-red-200 text-red-600 text-sm rounded px-3 py-2">
              {error}
            </div>
          )}

          <Button type="submit" loading={isLoading} className="w-full">
            Create Account
          </Button>
        </form>

        <p className="mt-6 text-center text-sm text-text-muted">
          Already have an account?{' '}
          <Link to="/login" className="text-primary font-medium hover:underline">
            Sign in
          </Link>
        </p>
      </Card>
    </div>
  )
}
