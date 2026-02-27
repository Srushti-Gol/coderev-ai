import { NavLink, useLocation } from 'react-router-dom'
import {
  LayoutDashboard,
  GitPullRequest,
  FolderGit2,
  BarChart3,
  Shield,
  TrendingUp,
  Settings,
  Zap,
  ChevronRight,
} from 'lucide-react'
import { clsx } from 'clsx'

const navItems = [
  { icon: LayoutDashboard, label: 'Dashboard', path: '/dashboard' },
  { icon: GitPullRequest, label: 'Pull Requests', path: '/pull-requests' },
  { icon: FolderGit2, label: 'Repositories', path: '/repositories' },
  { icon: BarChart3, label: 'Analytics', path: '/dashboard#analytics' },
  { icon: Shield, label: 'Security', path: '/dashboard#security' },
  { icon: TrendingUp, label: 'Technical Debt', path: '/dashboard#debt' },
  { icon: Settings, label: 'Settings', path: '/settings' },
]

export default function Sidebar() {
  const location = useLocation()

  return (
    <aside className="w-64 h-screen bg-gray-900 border-r border-gray-800 flex flex-col fixed left-0 top-0 z-40">
      {/* Logo */}
      <div className="flex items-center gap-3 px-6 py-5 border-b border-gray-800">
        <div className="w-8 h-8 bg-indigo-600 rounded-lg flex items-center justify-center">
          <Zap className="w-5 h-5 text-white" />
        </div>
        <div>
          <span className="font-bold text-white text-lg">coderev</span>
          <span className="font-bold text-indigo-400 text-lg">-ai</span>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
        {navItems.map((item) => {
          const Icon = item.icon
          const isActive = location.pathname === item.path ||
            (item.path !== '/dashboard' && location.pathname.startsWith(item.path))

          return (
            <NavLink
              key={item.path}
              to={item.path}
              className={clsx(
                'flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all duration-150 group',
                isActive
                  ? 'bg-indigo-600/20 text-indigo-400 border border-indigo-500/30'
                  : 'text-gray-400 hover:text-gray-200 hover:bg-gray-800'
              )}
            >
              <Icon className="w-4 h-4 flex-shrink-0" />
              <span>{item.label}</span>
              {isActive && (
                <ChevronRight className="w-3 h-3 ml-auto text-indigo-400" />
              )}
            </NavLink>
          )
        })}
      </nav>

      {/* Bottom section */}
      <div className="p-4 border-t border-gray-800">
        <div className="bg-gray-800 rounded-lg p-3 text-xs text-gray-400">
          <div className="flex items-center gap-2 mb-1">
            <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse" />
            <span className="text-green-400 font-medium">AI Active</span>
          </div>
          <p>claude-sonnet-4-6 ready</p>
        </div>
      </div>
    </aside>
  )
}
