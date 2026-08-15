import { useSyncExternalStore } from 'react'

export interface ToastItem {
  id: number
  message: string
  type: 'success' | 'error' | 'info'
  href?: string
  linkText?: string
}

type Listener = () => void

let toasts: ToastItem[] = []
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

export function toast(
  message: string,
  options: { type?: ToastItem['type']; href?: string; linkText?: string } = {},
) {
  const item: ToastItem = {
    id: nextId++,
    message,
    type: options.type ?? 'info',
    href: options.href,
    linkText: options.linkText,
  }
  toasts = [...toasts, item]
  emit()
  window.setTimeout(() => dismissToast(item.id), 6000)
}

export function dismissToast(id: number) {
  toasts = toasts.filter((t) => t.id !== id)
  emit()
}

export function useToasts() {
  return useSyncExternalStore(subscribe, () => toasts)
}