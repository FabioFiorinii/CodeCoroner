import { useEffect } from 'react'
import { AlertTriangle } from 'lucide-react'
import { useConfirmDialog, resolveConfirm } from '../../lib/confirm'
import { Button } from './Button'

export function ConfirmDialog() {
  const dialog = useConfirmDialog()

  useEffect(() => {
    if (!dialog) return
    const onKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') resolveConfirm(dialog.id, false)
    }
    window.addEventListener('keydown', onKeyDown)
    return () => window.removeEventListener('keydown', onKeyDown)
  }, [dialog])

  if (!dialog) return null

  return (
    <div
      className="fixed inset-0 z-[90] flex items-center justify-center p-4"
      role="dialog"
      aria-modal="true"
    >
      <div
        className="absolute inset-0 bg-[#050B1A]/60 backdrop-blur-sm animate-fade-in"
        onClick={() => resolveConfirm(dialog.id, false)}
      />
      <div className="relative card p-6 w-full max-w-md animate-slide-up shadow-cardHover">
        <div className="flex items-start gap-4">
          <div
            className={`shrink-0 w-10 h-10 rounded-full flex items-center justify-center ${
              dialog.danger ? 'bg-red-500/10 text-red-500' : 'bg-primary/10 text-primary'
            }`}
          >
            <AlertTriangle className="w-5 h-5" />
          </div>
          <div className="min-w-0">
            <h3 className="text-lg font-semibold text-text-primary">{dialog.title}</h3>
            {dialog.message && <p className="text-sm text-text-secondary mt-1">{dialog.message}</p>}
          </div>
        </div>
        <div className="flex justify-end gap-2 mt-6">
          <Button variant="secondary" onClick={() => resolveConfirm(dialog.id, false)}>
            {dialog.cancelLabel ?? 'Cancel'}
          </Button>
          <Button
            variant={dialog.danger ? 'danger' : 'primary'}
            onClick={() => resolveConfirm(dialog.id, true)}
          >
            {dialog.confirmLabel ?? 'Confirm'}
          </Button>
        </div>
      </div>
    </div>
  )
}
