import { create } from 'zustand'
import { persist } from 'zustand/middleware'

interface AnalysisWatchState {
  watched: string[]
  watch: (id: string) => void
  unwatch: (id: string) => void
}

export const useAnalysisWatch = create<AnalysisWatchState>()(
  persist(
    (set) => ({
      watched: [],
      watch: (id) =>
        set((s) => (s.watched.includes(id) ? s : { watched: [...s.watched, id] })),
      unwatch: (id) =>
        set((s) => ({ watched: s.watched.filter((w) => w !== id) })),
    }),
    {
      name: 'analysis-watch',
      partialize: (state) => ({ watched: state.watched }),
    },
  ),
)