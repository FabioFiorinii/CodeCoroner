import { useCallback, useEffect, useState } from 'react'
import { Link2, Plus, Send, Trash2, Power, X } from 'lucide-react'
import { useAuthStore } from '../../stores/authStore'
import { api } from '../../lib/api'
import { toast } from '../../lib/toast'
import { confirmDialog } from '../../lib/confirm'
import { Card } from '../common/Card'
import { Button } from '../common/Button'

interface WebhookItem {
  id: string
  project: string
  url: string
  events: string[]
  is_active: boolean
  created_at: string
}

const EVENT_OPTIONS = [
  { value: 'analysis.created', label: 'Analysis created' },
  { value: 'analysis.completed', label: 'Analysis completed' },
  { value: 'analysis.failed', label: 'Analysis failed' },
  { value: 'repository.indexed', label: 'Repository indexed' },
]

export function WebhooksCard({ projectId }: { projectId: string }) {
  const { user } = useAuthStore()
  const [webhooks, setWebhooks] = useState<WebhookItem[]>([])
  const [showForm, setShowForm] = useState(false)
  const [url, setUrl] = useState('')
  const [secret, setSecret] = useState('')
  const [events, setEvents] = useState<string[]>([])
  const [active, setActive] = useState(true)
  const [busy, setBusy] = useState(false)

  const load = useCallback(async () => {
    try {
      const data = await api.get<{ results: WebhookItem[] }>(`/webhooks/?project=${projectId}`)
      setWebhooks(data.results)
    } catch (err) {
      console.error('Failed to load webhooks', err)
    }
  }, [projectId])

  useEffect(() => {
    if (user?.is_superuser) load()
  }, [load, user])

  if (!user?.is_superuser) return null

  const toggleEvent = (value: string) =>
    setEvents((prev) => (prev.includes(value) ? prev.filter((e) => e !== value) : [...prev, value]))

  const handleAdd = async () => {
    if (!url.trim()) return
    setBusy(true)
    try {
      await api.post('/webhooks/', {
        project: projectId,
        url: url.trim(),
        secret: secret.trim(),
        events,
        is_active: active,
      })
      setUrl('')
      setSecret('')
      setEvents([])
      setActive(true)
      setShowForm(false)
      toast('Webhook created', { type: 'success' })
      await load()
    } catch {
      toast('Failed to create webhook', { type: 'error' })
    } finally {
      setBusy(false)
    }
  }

  const handleToggle = async (webhook: WebhookItem) => {
    try {
      await api.patch(`/webhooks/${webhook.id}/`, { is_active: !webhook.is_active })
      await load()
    } catch {
      toast('Failed to update webhook', { type: 'error' })
    }
  }

  const handleDelete = async (webhook: WebhookItem) => {
    const ok = await confirmDialog({
      title: 'Delete webhook?',
      message: webhook.url,
      confirmLabel: 'Delete',
      danger: true,
    })
    if (!ok) return
    try {
      await api.delete(`/webhooks/${webhook.id}/`)
      toast('Webhook deleted', { type: 'success' })
      await load()
    } catch {
      toast('Failed to delete webhook', { type: 'error' })
    }
  }

  const handleTest = async (webhook: WebhookItem) => {
    try {
      const res = await api.post<{ detail: string }>(`/webhooks/${webhook.id}/test/`)
      toast(res.detail, { type: 'success' })
    } catch {
      toast('Webhook test failed', { type: 'error' })
    }
  }

  return (
    <Card padding="lg">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-semibold text-text-primary flex items-center gap-2">
          <Link2 className="w-5 h-5 text-primary" />
          Webhooks
        </h2>
        {!showForm && (
          <Button variant="ghost" size="sm" onClick={() => setShowForm(true)}>
            <Plus className="w-4 h-4" />
            Add
          </Button>
        )}
      </div>

      {showForm && (
        <div className="space-y-3 border border-border rounded-lg p-4 mb-4">
          <input
            className="input-field w-full"
            placeholder="URL (https://...)"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
          />
          <input
            className="input-field w-full"
            placeholder="Secret (optional, used for HMAC signature)"
            value={secret}
            onChange={(e) => setSecret(e.target.value)}
          />
          <div className="flex flex-wrap gap-2">
            {EVENT_OPTIONS.map((option) => (
              <label
                key={option.value}
                className={`text-xs px-2 py-1 rounded-full border cursor-pointer transition-colors ${
                  events.includes(option.value)
                    ? 'border-primary bg-primary/10 text-primary'
                    : 'border-border text-text-muted hover:text-text-secondary'
                }`}
              >
                <input
                  type="checkbox"
                  className="hidden"
                  checked={events.includes(option.value)}
                  onChange={() => toggleEvent(option.value)}
                />
                {option.label}
              </label>
            ))}
          </div>
          <label className="flex items-center gap-2 text-sm text-text-secondary">
            <input
              type="checkbox"
              className="w-4 h-4 accent-primary"
              checked={active}
              onChange={(e) => setActive(e.target.checked)}
            />
            Active
          </label>
          <div className="flex gap-2">
            <Button onClick={handleAdd} loading={busy} size="sm">
              Save
            </Button>
            <Button variant="ghost" size="sm" onClick={() => setShowForm(false)}>
              <X className="w-4 h-4" />
              Cancel
            </Button>
          </div>
        </div>
      )}

      <div className="space-y-2">
        {webhooks.length === 0 && !showForm && (
          <p className="text-sm text-text-muted">No webhooks configured for this project.</p>
        )}
        {webhooks.map((webhook) => (
          <div
            key={webhook.id}
            className={`border rounded-lg p-3 flex items-start justify-between gap-3 ${
              webhook.is_active ? 'border-border' : 'border-border opacity-60'
            }`}
          >
            <div className="min-w-0">
              <p className="text-sm font-medium text-text-primary truncate">{webhook.url}</p>
              <div className="flex flex-wrap gap-1 mt-1">
                {webhook.events.map((event) => (
                  <span
                    key={event}
                    className="text-xs bg-surface-alt text-text-secondary px-2 py-0.5 rounded"
                  >
                    {event}
                  </span>
                ))}
                {webhook.events.length === 0 && (
                  <span className="text-xs text-text-muted">No events</span>
                )}
              </div>
            </div>
            <div className="flex items-center gap-1 shrink-0">
              <button
                onClick={() => handleTest(webhook)}
                title="Send test"
                className="p-1.5 text-text-muted hover:text-primary transition-colors"
              >
                <Send className="w-4 h-4" />
              </button>
              <button
                onClick={() => handleToggle(webhook)}
                title={webhook.is_active ? 'Disable' : 'Enable'}
                className="p-1.5 text-text-muted hover:text-primary transition-colors"
              >
                <Power className="w-4 h-4" />
              </button>
              <button
                onClick={() => handleDelete(webhook)}
                title="Delete"
                className="p-1.5 text-text-muted hover:text-red-500 transition-colors"
              >
                <Trash2 className="w-4 h-4" />
              </button>
            </div>
          </div>
        ))}
      </div>
    </Card>
  )
}