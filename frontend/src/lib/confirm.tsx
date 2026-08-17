import { useSyncExternalStore } from 'react'

export interface ConfirmOptions {
  title: string
  message?: string
  confirmLabel?: string
  cancelLabel?: string
  danger?: boolean
}

interface ConfirmState extends ConfirmOptions {
  id: number
  resolve: (ok: boolean) => void
}

type Listener = () => void

let dialog: ConfirmState | null = null
const listeners = new Set<Listener>()
let nextId = 1

function emit() {
  listeners.forEach((listener) => listener())
}

function subscribe(listener: Listener) {
  listeners.add(listener)
  return () => {
    listeners.delete(listener)
  }
}

export function confirmDialog(options: ConfirmOptions): Promise<boolean> {
  return new Promise((resolve) => {
    dialog = {
      id: nextId++,
      ...options,
      resolve,
    }
    emit()
  })
}

export function resolveConfirm(id: number, ok: boolean) {
  if (dialog && dialog.id === id) {
    const resolve = dialog.resolve
    dialog = null
    emit()
    resolve(ok)
  }
}

export function useConfirmDialog() {
  return useSyncExternalStore(subscribe, () => dialog)
}
