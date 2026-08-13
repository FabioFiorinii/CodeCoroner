import { Clock, CheckCircle2, AlertCircle, Loader2 } from 'lucide-react'

export const STATUS_ICON: Record<string, typeof Clock> = {
  queued: Clock,
  indexing: Loader2,
  analyzing: Loader2,
  bug_localization: Loader2,
  rca: Loader2,
  completed: CheckCircle2,
  failed: AlertCircle,
}

export const STATUS_COLOR: Record<string, string> = {
  queued: 'text-yellow-600 bg-yellow-50 border-yellow-200',
  indexing: 'text-blue-600 bg-blue-50 border-blue-200',
  analyzing: 'text-blue-600 bg-blue-50 border-blue-200',
  bug_localization: 'text-purple-600 bg-purple-50 border-purple-200',
  rca: 'text-purple-600 bg-purple-50 border-purple-200',
  completed: 'text-green-600 bg-green-50 border-green-200',
  failed: 'text-red-600 bg-red-50 border-red-200',
}

export const isBusy = (s: string) =>
  ['queued', 'indexing', 'analyzing', 'bug_localization', 'rca'].includes(s)