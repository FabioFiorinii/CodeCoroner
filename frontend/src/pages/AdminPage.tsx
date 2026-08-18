import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { Shield, Users, UserX, Save, Plus, X, Search, Sparkles, Download } from 'lucide-react'
import { Card } from '../components/common/Card'
import { Button } from '../components/common/Button'
import { useAuthStore } from '../stores/authStore'
import { api, ApiError } from '../lib/api'
import { confirmDialog } from '../lib/confirm'

interface AdminUser {
  id: number
  email: string
  username: string
  is_active: boolean
  is_superuser: boolean
  date_joined: string
  groups: string[]
}

interface GroupItem {
  id: number
  name: string
  user_count: number
}

interface ModelOption {
  key: string
  label: string
  model: string
  params: string
  installed: boolean
}

interface ModelSettings {
  tier: string
  model: string
  available: ModelOption[]
}

const TIER_KEYS = ['fast', 'balanced', 'precise']

export function AdminPage() {
  const { user } = useAuthStore()
  const navigate = useNavigate()
  const [users, setUsers] = useState<AdminUser[]>([])
  const [groups, setGroups] = useState<GroupItem[]>([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')
  const [editingUser, setEditingUser] = useState<AdminUser | null>(null)
  const [editGroups, setEditGroups] = useState<string[]>([])
  const [showNewGroup, setShowNewGroup] = useState(false)
  const [newGroupName, setNewGroupName] = useState('')
  const [modelSettings, setModelSettings] = useState<ModelSettings | null>(null)
  const [tierIndex, setTierIndex] = useState(1)
  const [savingModels, setSavingModels] = useState(false)
  const [saveModelError, setSaveModelError] = useState<string | null>(null)
  const [saveModelSuccess, setSaveModelSuccess] = useState<string | null>(null)

  useEffect(() => {
    if (!user?.is_superuser) {
      navigate('/dashboard', { replace: true })
      return
    }
    loadData()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const fetchModelSettings = async () => {
    try {
      const data = await api.get<ModelSettings>('/auth/admin/model-settings/')
      setModelSettings(data)
      setTierIndex(TIER_KEYS.indexOf(data.tier) >= 0 ? TIER_KEYS.indexOf(data.tier) : 1)
    } catch (err) {
      console.error('Failed to load model settings', err)
    }
  }

  const loadData = async () => {
    setLoading(true)
    try {
      const [usersData, groupsData] = await Promise.all([
        api.get<AdminUser[]>('/auth/admin/users/'),
        api.get<GroupItem[]>('/auth/admin/groups/'),
        fetchModelSettings(),
      ])
      setUsers(usersData)
      setGroups(groupsData)
    } catch (err) {
      console.error('Failed to load admin data', err)
    }
    setLoading(false)
  }

  const filteredUsers = users.filter(
    (u) =>
      u.email.toLowerCase().includes(search.toLowerCase()) ||
      u.username.toLowerCase().includes(search.toLowerCase()),
  )

  const handleDeleteUser = async (userId: number, userEmail: string) => {
    const ok = await confirmDialog({
      title: 'Delete user?',
      message: `Delete ${userEmail}? This cannot be undone.`,
      confirmLabel: 'Delete',
      danger: true,
    })
    if (!ok) return
    try {
      await api.delete(`/auth/admin/users/${userId}/`)
      loadData()
    } catch (err) {
      console.error('Failed to delete user', err)
    }
  }

  const handleSaveUser = async () => {
    if (!editingUser) return
    try {
      await api.patch(`/auth/admin/users/${editingUser.id}/`, {
        groups: editGroups,
      })
      setEditingUser(null)
      loadData()
    } catch (err) {
      console.error('Failed to update user', err)
    }
  }

  const handleCreateGroup = async () => {
    if (!newGroupName.trim()) return
    try {
      await api.post('/auth/admin/groups/', { name: newGroupName.trim() })
      setNewGroupName('')
      setShowNewGroup(false)
      loadData()
    } catch (err) {
      console.error('Failed to create group', err)
    }
  }

  const handleDeleteGroup = async (groupId: number, groupName: string) => {
    const ok = await confirmDialog({
      title: 'Delete group?',
      message: `Delete group "${groupName}"?`,
      confirmLabel: 'Delete',
      danger: true,
    })
    if (!ok) return
    try {
      await api.delete(`/auth/admin/groups/${groupId}/`)
      loadData()
    } catch (err) {
      console.error('Failed to delete group', err)
    }
  }

  const handleSaveModelSettings = async () => {
    if (!modelSettings) return
    setSavingModels(true)
    setSaveModelError(null)
    setSaveModelSuccess(null)
    try {
      const res = await api.put<{ tier: string; detail: string }>(
        '/auth/admin/model-settings/',
        { tier: TIER_KEYS[tierIndex] },
      )
      setSaveModelSuccess(res.detail || 'Model profile saved')
      await fetchModelSettings()
    } catch (err) {
      const message =
        err instanceof ApiError
          ? ((err.body as { detail?: string } | null)?.detail as string) || err.message
          : 'Failed to save model settings'
      setSaveModelError(message)
      await fetchModelSettings()
    } finally {
      setSavingModels(false)
    }
  }

  const selectedTier = modelSettings?.available.find((a) => a.key === TIER_KEYS[tierIndex]) ?? null

  if (!user?.is_superuser) {
    return null
  }

  return (
    <div className="space-y-8">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-text-primary flex items-center gap-2">
            <Shield className="w-6 h-6" />
            Admin Settings
          </h1>
          <p className="text-text-secondary mt-1">
            Manage users, groups, and permissions.
          </p>
        </div>
      </div>

      <Card padding="lg">
        <h2 className="text-lg font-semibold text-text-primary flex items-center gap-2">
          <Sparkles className="w-5 h-5" />
          AI Models
        </h2>

        <input
          type="range"
          min={0}
          max={2}
          step={1}
          value={tierIndex}
          disabled={savingModels || !modelSettings}
          onChange={(e) => {
            setTierIndex(Number(e.target.value))
            setSaveModelSuccess(null)
          }}
          className="w-full accent-primary mt-4"
        />
        <div className="flex justify-between text-sm mt-1">
          {modelSettings?.available.map((opt, i) => (
            <span
              key={opt.key}
              className={i === tierIndex ? 'text-primary font-medium' : 'text-text-muted'}
            >
              {opt.label}
            </span>
          ))}
        </div>

        {selectedTier && (
          <div className="mt-4 p-3 rounded-lg bg-surface-alt">
            <p className="text-sm font-medium text-text-primary">{selectedTier.model}</p>
            <p className="text-xs text-text-muted">{selectedTier.params} parameters</p>
            {!selectedTier.installed && (
              <p className="text-xs text-amber-500 mt-1">
                Not installed yet — it will be downloaded when you save.
              </p>
            )}
          </div>
        )}

        <div className="mt-4">
          <Button onClick={handleSaveModelSettings} disabled={savingModels || !modelSettings}>
            {savingModels ? (
              'Downloading model...'
            ) : (
              <>
                <Download className="w-4 h-4" />
                Save & Install
              </>
            )}
          </Button>
        </div>

        {saveModelSuccess && (
          <p className="text-sm text-green-500 mt-3">{saveModelSuccess}</p>
        )}
        {saveModelError && (
          <p className="text-sm text-red-500 mt-3">{saveModelError}</p>
        )}
      </Card>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        <div className="lg:col-span-2 space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-semibold text-text-primary flex items-center gap-2">
              <Users className="w-5 h-5" />
              Users ({users.length})
            </h2>
            <div className="relative max-w-xs">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-text-muted" />
              <input
                className="input-field pl-9 py-1.5 text-sm"
                placeholder="Search users..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
              />
            </div>
          </div>

          {loading ? (
            <div className="space-y-2">
              {[1, 2, 3].map((i) => (
                <div key={i} className="h-16 bg-surface-alt rounded-lg animate-pulse" />
              ))}
            </div>
          ) : (
            <div className="space-y-2">
              {filteredUsers.map((u) => (
                <Card key={u.id} padding="md">
                  <div className="flex items-center justify-between">
                    <div className="min-w-0 flex-1">
                      <div className="flex items-center gap-2">
                        <p className="font-medium text-text-primary">{u.username}</p>
                        {u.is_superuser && (
                          <span className="text-xs bg-primary/10 text-primary px-2 py-0.5 rounded-full font-medium">
                            Admin
                          </span>
                        )}
                        {!u.is_active && (
                          <span className="text-xs bg-red-100 text-red-600 px-2 py-0.5 rounded-full font-medium">
                            Inactive
                          </span>
                        )}
                      </div>
                      <p className="text-sm text-text-muted">{u.email}</p>
                      <div className="flex flex-wrap gap-1 mt-1">
                        {u.groups.map((g) => (
                          <span
                            key={g}
                            className="text-xs bg-surface-alt text-text-secondary px-2 py-0.5 rounded"
                          >
                            {g}
                          </span>
                        ))}
                      </div>
                    </div>
                    <div className="flex items-center gap-2 shrink-0 ml-4">
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => {
                          setEditingUser(u)
                          setEditGroups(u.groups.length > 1 ? [u.groups[0]] : [...u.groups])
                        }}
                      >
                        Edit Groups
                      </Button>
                      {!u.is_superuser && (
                        <button
                          onClick={() => handleDeleteUser(u.id, u.email)}
                          className="p-2 text-text-muted hover:text-red-500 transition-colors"
                          title="Delete user"
                        >
                          <UserX className="w-4 h-4" />
                        </button>
                      )}
                    </div>
                  </div>
                </Card>
              ))}
              {filteredUsers.length === 0 && (
                <p className="text-sm text-text-muted text-center py-8">No users found.</p>
              )}
            </div>
          )}
        </div>

        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-semibold text-text-primary">Groups</h2>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setShowNewGroup(true)}
            >
              <Plus className="w-4 h-4" />
              New Group
            </Button>
          </div>

          {showNewGroup && (
            <div className="flex items-center gap-2">
              <input
                className="input-field flex-1 py-1.5 text-sm"
                placeholder="Group name"
                value={newGroupName}
                onChange={(e) => setNewGroupName(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleCreateGroup()}
              />
              <Button variant="ghost" size="sm" onClick={handleCreateGroup}>
                <Save className="w-4 h-4" />
              </Button>
              <button
                onClick={() => {
                  setShowNewGroup(false)
                  setNewGroupName('')
                }}
                className="p-1 text-text-muted hover:text-text-primary"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
          )}

          <div className="space-y-2">
            {groups.map((g) => (
              <Card key={g.id} padding="sm" className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-text-primary">{g.name}</p>
                  <p className="text-xs text-text-muted">{g.user_count} user(s)</p>
                </div>
                {g.name !== 'default' && (
                  <button
                    onClick={() => handleDeleteGroup(g.id, g.name)}
                    className="p-1 text-text-muted hover:text-red-500 transition-colors"
                    title="Delete group"
                  >
                    <UserX className="w-3.5 h-3.5" />
                  </button>
                )}
              </Card>
            ))}
          </div>
        </div>
      </div>

      {editingUser && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <Card padding="lg" className="w-full max-w-md mx-4">
            <h3 className="font-semibold text-text-primary mb-4">
              Edit Groups — {editingUser.email}
            </h3>
            <div className="space-y-2 max-h-60 overflow-y-auto">
              {groups.map((g) => {
                const isSelected = editGroups.includes(g.name)
                return (
                  <label
                    key={g.id}
                    className={`flex items-center gap-3 p-3 rounded-lg border cursor-pointer transition-all ${
                      isSelected ? 'border-primary bg-primary/5 ring-1 ring-primary' : 'border-border'
                    }`}
                  >
                    <input
                      type="radio"
                      name="user-group"
                      value={g.name}
                      checked={isSelected}
                      onChange={() => setEditGroups([g.name])}
                      className="w-4 h-4 accent-primary"
                    />
                    <div>
                      <p className="text-sm font-medium text-text-primary">{g.name}</p>
                      <p className="text-xs text-text-muted">{g.user_count} users</p>
                    </div>
                  </label>
                )
              })}
            </div>
            <div className="flex justify-end gap-3 mt-6">
              <Button variant="ghost" onClick={() => setEditingUser(null)}>
                Cancel
              </Button>
              <Button onClick={handleSaveUser}>
                <Save className="w-4 h-4" />
                Save
              </Button>
            </div>
          </Card>
        </div>
      )}
    </div>
  )
}
