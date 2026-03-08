import { useQuery } from '@tanstack/react-query'
import { dashboardApi } from '../../api/dashboard'
import { Card, CardHeader, CardTitle } from '../ui/Card'
import { TrendingUp, TrendingDown, GitPullRequest, AlertTriangle } from 'lucide-react'
import { clsx } from 'clsx'

export default function WeeklyDigest() {
  const { data, isLoading } = useQuery({
    queryKey: ['dashboard', 'weekly-digest'],
    queryFn: dashboardApi.getWeeklyDigest,
  })

  if (isLoading || !data) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Weekly Digest</CardTitle>
        </CardHeader>
        <div className="animate-pulse space-y-3">
          {[1, 2, 3].map(i => (
            <div key={i} className="h-14 bg-gray-800 rounded-lg" />
          ))}
        </div>
      </Card>
    )
  }

  const prsUp = data.prs_change_pct > 0
  const prsDown = data.prs_change_pct < 0

  return (
    <Card>
      <CardHeader>
        <CardTitle>Weekly Digest</CardTitle>
        <span className="text-xs text-gray-500">
          {data.period.start} → {data.period.end}
        </span>
      </CardHeader>

      <div className="space-y-3">
        {/* PRs this week */}
        <div className="flex items-center justify-between p-3 bg-gray-800/50 rounded-lg border border-gray-700/50">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 bg-indigo-500/15 rounded-lg flex items-center justify-center">
              <GitPullRequest className="w-4 h-4 text-indigo-400" />
            </div>
            <div>
              <p className="text-sm font-medium text-gray-200">Pull Requests</p>
              <p className="text-xs text-gray-500">vs last week</p>
            </div>
          </div>
          <div className="text-right">
            <p className="text-xl font-bold text-white">{data.this_week_prs}</p>
            <div className={clsx(
              'flex items-center justify-end gap-1 text-xs font-medium',
              prsUp && 'text-green-400',
              prsDown && 'text-red-400',
              !prsUp && !prsDown && 'text-gray-500'
            )}>
              {prsUp && <TrendingUp className="w-3 h-3" />}
              {prsDown && <TrendingDown className="w-3 h-3" />}
              {data.prs_change_pct > 0 ? '+' : ''}{data.prs_change_pct}%
            </div>
          </div>
        </div>

        {/* Issues found */}
        <div className="flex items-center justify-between p-3 bg-gray-800/50 rounded-lg border border-gray-700/50">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 bg-orange-500/15 rounded-lg flex items-center justify-center">
              <AlertTriangle className="w-4 h-4 text-orange-400" />
            </div>
            <div>
              <p className="text-sm font-medium text-gray-200">Issues Found</p>
              <p className="text-xs text-gray-500">By AI analysis</p>
            </div>
          </div>
          <div className="text-right">
            <p className="text-xl font-bold text-white">{data.this_week_issues}</p>
            <p className="text-xs text-gray-500">this week</p>
          </div>
        </div>

        {/* Summary */}
        <div className="p-3 bg-indigo-500/10 border border-indigo-500/20 rounded-lg">
          <p className="text-xs text-indigo-300">
            {data.this_week_prs > data.prev_week_prs
              ? `${data.prs_change_pct}% more PRs this week. Keep up the velocity!`
              : data.this_week_prs < data.prev_week_prs
              ? `Slower week with ${Math.abs(data.prs_change_pct)}% fewer PRs.`
              : 'Consistent PR velocity this week.'}
          </p>
        </div>
      </div>
    </Card>
  )
}
