import { Outlet } from 'react-router-dom'

export default function Layout() {
  return (
    <div className="min-h-screen flex">
      <aside className="w-64 bg-white dark:bg-gray-900 border-r border-gray-200 dark:border-gray-800 p-4">
        <div className="text-xl font-bold mb-8">CodeCoroner</div>
        <nav className="space-y-2">
          <a href="/dashboard" className="block px-3 py-2 rounded hover:bg-gray-100 dark:hover:bg-gray-800">Dashboard</a>
          <a href="/projects" className="block px-3 py-2 rounded hover:bg-gray-100 dark:hover:bg-gray-800">Projects</a>
          <a href="/analyses" className="block px-3 py-2 rounded hover:bg-gray-100 dark:hover:bg-gray-800">Analyses</a>
        </nav>
      </aside>
      <main className="flex-1 p-8">
        <Outlet />
      </main>
    </div>
  )
}
