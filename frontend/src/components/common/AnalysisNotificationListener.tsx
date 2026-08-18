import { useEffect } from 'react'
import { useAnalysisWatch } from '../../lib/analysisWatch'
import { api } from '../../lib/api'
import { toast } from '../../lib/toast'
import type { AnalysisItem } from '../../lib/queries'

const TERMINAL = new Set(['completed', 'failed'])

interface Meta {
  title: string
  project: string
}

export function AnalysisNotificationListener() {
  const watched = useAnalysisWatch((s) => s.watched)
  const unwatch = useAnalysisWatch((s) => s.unwatch)

  useEffect(() => {
    const sockets: WebSocket[] = []
    const meta = new Map<string, Meta>()
    const fired = new Set<string>()

    const fire = (id: string, status: string) => {
      if (fired.has(id)) return
      fired.add(id)
      const m = meta.get(id)
      const title = m?.title || 'analysis'
      toast(
        status === 'completed' ? `Analysis completed: ${title}` : `Analysis failed: ${title}`,
        {
          type: status === 'completed' ? 'success' : 'error',
          href: m?.project ? `/projects/${m.project}/analyses/${id}` : undefined,
          linkText: status === 'completed' ? 'Open analysis' : 'View details',
          duration: 20000,
        },
      )
      unwatch(id)
    }

    const fetchMeta = async (id: string) => {
      try {
        const a = await api.get<AnalysisItem>(`/analyses/${id}/`)
        meta.set(id, { title: a.title, project: a.project })
        return a.status
      } catch {
        return null
      }
    }

    for (const id of watched) {
      fetchMeta(id).then((status) => {
        if (status && TERMINAL.has(status)) fire(id, status)
      })

      const protocol = window.location.protocol === 'https:' ? 'wss' : 'ws'
      const ws = new WebSocket(`${protocol}://${window.location.host}/ws/analyses/${id}/`)
      ws.onmessage = (event) => {
        let msg: { status?: string }
        try {
          msg = JSON.parse(event.data)
        } catch {
          return
        }
        if (msg.status && TERMINAL.has(msg.status)) {
          ws.close()
          fire(id, msg.status)
        }
      }
      sockets.push(ws)
    }

    return () => sockets.forEach((ws) => ws.close())
  }, [watched, unwatch])

  return null
}