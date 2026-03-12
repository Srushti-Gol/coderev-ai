import { useQuery } from '@tanstack/react-query'
import { dashboardApi } from '../api/dashboard'
import StatCard from '../components/ui/StatCard'
import PRVelocityChart from '../components/dashboard/PRVelocityChart'
import CycleTimeChart from '../components/dashboard/CycleTimeChart'
import PRSizeDistribution from '../components/dashboard/PRSizeDistribution'
import ReviewWorkload from '../components/dashboard/ReviewWorkload'
import WeeklyDigest from '../components/dashboard/WeeklyDigest'
import TechnicalDebtChart from '../components/analysis/TechnicalDebtChart'
import {
  FolderGit2,
  GitPullRequest,
  AlertTriangle,
  CheckCircle,
  Zap,
  TrendingUp,
} from 'lucide-react'
import { useAuth } from '../hooks/useAuth'

export default function DashboardPage() {
  const { user } = useAuth()
  const { data: stats, isLoading } = useQuery({
    queryKey: ['dashboard', 'stats'],
    queryFn: () => dashboardApi.getStats(30),
  })

  return (
    <div className="space-y-6">
      {/* Page header */}
      <div>
        <h1 className="text-2xl font-bold text-white">
          Welcome back, {user?.name || user?.github_login}
        </h1>
        <p className="text-gray-500 mt-1">Here's your code review overview for the last 30 days.</p>
      </div>

      {/* Stat cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="Repositories"
          value={isLoading ? '—' : stats?.active_repos ?? 0}
          subtitle={`of ${stats?.total_repos || 0}`}
          icon={<FolderGit2 className="w-5 h-5" />}
          accentColor="indigo"
        />
        <StatCard
          title="Open PRs"
          value={isLoading ? '—' : stats?.open_prs ?? 0}
          subtitle="active"
          icon={<GitPullRequest className="w-5 h-5" />}
          accentColor="green"
        />
        <StatCard
          title="Issues Found"
          value={isLoading ? '—' : stats?.total_issues ?? 0}
          subtitle="this period"
          icon={<AlertTriangle className="w-5 h-5" />}
          trend={stats?.critical_issues && stats.critical_issues > 0 ? -stats.critical_issues : undefined}
          trendLabel="critical"
          accentColor="red"
        />
        <StatCard
          title="Avg Quality"
          value={isLoading ? '—' : `${stats?.avg_quality_score ?? 0}`}
          subtitle="/ 100"
          icon={<TrendingUp className="w-5 h-5" />}
          accentColor="purple"
        />
      </div>

      {/* Secondary stats */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="PRs Analyzed"
          value={isLoading ? '—' : stats?.analyzed_prs ?? 0}
          icon={<Zap className="w-5 h-5" />}
          accentColor="yellow"
        />
        <StatCard
          title="Critical Issues"
          value={isLoading ? '—' : stats?.critical_issues ?? 0}
          icon={<AlertTriangle className="w-5 h-5" />}
          accentColor="orange"
        />
        <StatCard
          title="Analyzed Rate"
          value={
            isLoading || !stats
              ? '—'
              : stats.total_prs > 0
              ? `${Math.round((stats.analyzed_prs / stats.total_prs) * 100)}%`
              : '0%'
          }
          icon={<CheckCircle className="w-5 h-5" />}
          accentColor="green"
        />
        <StatCard
          title="Active Repos"
          value={isLoading ? '—' : stats?.active_repos ?? 0}
          icon={<FolderGit2 className="w-5 h-5" />}
          accentColor="indigo"
        />
      </div>

      {/* Charts row 1 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <PRVelocityChart />
        <CycleTimeChart />
      </div>

      {/* Charts row 2 */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2">
          <TechnicalDebtChart />
        </div>
        <WeeklyDigest />
      </div>

      {/* Charts row 3 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <PRSizeDistribution />
        <ReviewWorkload />
      </div>
    </div>
  )
}
