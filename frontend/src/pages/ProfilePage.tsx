import { useState } from 'react'
import { User, KeyRound, Check, AlertCircle } from 'lucide-react'
import { Card } from '../components/common/Card'
import { Button } from '../components/common/Button'
import { Input } from '../components/common/Input'
import { useAuthStore } from '../stores/authStore'
import { api, ApiError } from '../lib/api'

export function ProfilePage() {
  const { user } = useAuthStore()
  const [oldPassword, setOldPassword] = useState('')
  const [newPassword, setNewPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [saving, setSaving] = useState(false)
  const [success, setSuccess] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)

  if (!user) return null

  const joinedAt = new Date(user.date_joined)

  const handleChangePassword = async () => {
    setSuccess(null)
    setError(null)
    if (newPassword !== confirmPassword) {
      setError('The new passwords do not match.')
      return
    }
    setSaving(true)
    try {
      const res = await api.post<{ detail: string }>('/auth/password/change/', {
        old_password: oldPassword,
        new_password: newPassword,
      })
      setSuccess(res.detail || 'Password updated successfully')
      setOldPassword('')
      setNewPassword('')
      setConfirmPassword('')
    } catch (err) {
      const message =
        err instanceof ApiError
          ? (err.message || 'Failed to change password')
          : 'Failed to change password'
      const body = (err as ApiError).body as {
        old_password?: string[]
        new_password?: string[]
      } | null
      if (body?.old_password?.[0]) {
        setError(body.old_password[0])
      } else if (body?.new_password?.[0]) {
        setError(body.new_password[0])
      } else {
        setError(message)
      }
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-text-primary flex items-center gap-2">
          <User className="w-6 h-6" />
          Profile
        </h1>
        <p className="text-text-secondary mt-1">Your account details and security settings.</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        <Card padding="lg">
          <h2 className="text-lg font-semibold text-text-primary mb-4">Account</h2>
          <div className="flex items-center gap-4 mb-6">
            <div className="w-16 h-16 rounded-full bg-primary/20 flex items-center justify-center shrink-0">
              <span className="text-primary text-2xl font-semibold">
                {user.username.charAt(0).toUpperCase()}
              </span>
            </div>
            <div>
              <div className="flex items-center gap-2">
                <p className="text-xl font-semibold text-text-primary">{user.username}</p>
                {user.is_superuser && (
                  <span className="text-xs bg-primary/10 text-primary px-2 py-0.5 rounded-full font-medium">
                    Admin
                  </span>
                )}
              </div>
              <p className="text-sm text-text-muted">{user.email}</p>
            </div>
          </div>

          <dl className="space-y-3 text-sm">
            <div className="flex justify-between">
              <dt className="text-text-muted">Email</dt>
              <dd className="text-text-primary">{user.email}</dd>
            </div>
            <div className="flex justify-between">
              <dt className="text-text-muted">Member since</dt>
              <dd className="text-text-primary">{joinedAt.toLocaleDateString()}</dd>
            </div>
            <div className="flex justify-between">
              <dt className="text-text-muted">Status</dt>
              <dd className="text-text-primary">{user.is_active ? 'Active' : 'Inactive'}</dd>
            </div>
            <div>
              <dt className="text-text-muted mb-1">Groups</dt>
              <dd className="flex flex-wrap gap-1">
                {user.groups.length === 0 && <span className="text-text-muted">None</span>}
                {user.groups.map((g) => (
                  <span
                    key={g}
                    className="text-xs bg-surface-alt text-text-secondary px-2 py-0.5 rounded"
                  >
                    {g}
                  </span>
                ))}
              </dd>
            </div>
          </dl>
        </Card>

        <Card padding="lg">
          <h2 className="text-lg font-semibold text-text-primary flex items-center gap-2 mb-4">
            <KeyRound className="w-5 h-5" />
            Change Password
          </h2>
          <div className="space-y-4">
            <Input
              label="Current password"
              type="password"
              value={oldPassword}
              onChange={(e) => setOldPassword(e.target.value)}
              placeholder="••••••••"
            />
            <Input
              label="New password"
              type="password"
              value={newPassword}
              onChange={(e) => setNewPassword(e.target.value)}
              placeholder="At least 8 characters"
            />
            <Input
              label="Confirm new password"
              type="password"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              placeholder="At least 8 characters"
            />

            <Button onClick={handleChangePassword} disabled={saving}>
              {saving ? 'Updating...' : 'Update Password'}
            </Button>

            {success && (
              <p className="text-sm text-green-500 flex items-center gap-1.5 mt-3">
                <Check className="w-4 h-4" />
                {success}
              </p>
            )}
            {error && (
              <p className="text-sm text-red-500 flex items-center gap-1.5 mt-3">
                <AlertCircle className="w-4 h-4" />
                {error}
              </p>
            )}
          </div>
        </Card>
      </div>
    </div>
  )
}