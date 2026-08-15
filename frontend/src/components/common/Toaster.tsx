import { Link } from 'react-router-dom'
import { CheckCircle2, AlertCircle, Info, X } from 'lucide-react'
import { useToasts, dismissToast } from '../../lib/toast'

const ICONS = {
  success: CheckCircle2,
  error: AlertCircle,
  info: Info,
}

const COLORS = {
  success: 'text-green-500',
  error: 'text-red-500',
  info: 'text-primary',
}

export function Toaster() {
  const toasts = useToasts()

  return (
    <div className="fixed bottom-4 right-4 z-[100] space-y-2 w-80">
      {toasts.map((item) => {
        const Icon = ICONS[item.type]
        return (
          <div
            key={item.id}
            className="bg-surface-dark border border-white/10 rounded-lg shadow-lg p-3 flex items-start gap-3 animate-fade-in"
          >
            <Icon className={`w-5 h-5 shrink-0 mt-0.5 ${COLORS[item.type]}`} />
            <div className="min-w-0 flex-1 text-sm text-text-inverse">
              <p>{item.message}</p>
              {item.href && (
                <Link
                  to={item.href}
                  className="text-primary hover:underline text-xs mt-1 block"
                >
                  {item.linkText ?? 'Open'}
                </Link>
              )}
            </div>
            <button
              onClick={() => dismissToast(item.id)}
              className="text-text-inverse/40 hover:text-text-inverse shrink-0"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        )
      })}
    </div>
  )
}