import {
  PieChart,
  Pie,
  Cell,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from 'recharts'
import { useQuery } from '@tanstack/react-query'
import { dashboardApi } from '../../api/dashboard'
import { Card, CardHeader, CardTitle } from '../ui/Card'
import { PageLoader } from '../ui/LoadingSpinner'

const COLORS = {
  XS: '#10b981',
  S: '#6366f1',
  M: '#f59e0b',
  L: '#f97316',
  XL: '#ef4444',
}

const SIZE_LABELS: Record<string, string> = {
  XS: 'XS (<10 lines)',
  S: 'S (<50 lines)',
  M: 'M (<200 lines)',
  L: 'L (<500 lines)',
  XL: 'XL (500+ lines)',
}

const CustomTooltip = ({ active, payload }: any) => {
  if (active && payload && payload.length) {
    const item = payload[0].payload
    return (
      <div className="bg-gray-800 border border-gray-700 rounded-lg p-3 shadow-xl">
        <p className="text-sm font-medium text-white">{SIZE_LABELS[item.name]}</p>
        <p className="text-xs text-gray-400 mt-1">
          {item.value} PRs ({((item.value / item.total) * 100).toFixed(1)}%)
        </p>
      </div>
    )
  }
  return null
}

export default function PRSizeDistribution() {
  const { data, isLoading } = useQuery({
    queryKey: ['dashboard', 'pr-size'],
    queryFn: () => dashboardApi.getPRSizeDistribution(30),
  })

  if (isLoading) return <Card><PageLoader /></Card>

  const total = data?.reduce((sum, item) => sum + item.value, 0) || 0
  const chartData = (data || []).map(item => ({ ...item, total })).filter(item => item.value > 0)

  return (
    <Card>
      <CardHeader>
        <CardTitle>PR Size Distribution</CardTitle>
        <span className="text-xs text-gray-500">Last 30 days</span>
      </CardHeader>

      {chartData.length === 0 ? (
        <div className="h-48 flex items-center justify-center text-gray-500 text-sm">
          No PR data yet.
        </div>
      ) : (
        <div className="flex items-center gap-4">
          <ResponsiveContainer width="60%" height={180}>
            <PieChart>
              <Pie
                data={chartData}
                cx="50%"
                cy="50%"
                innerRadius={45}
                outerRadius={70}
                paddingAngle={2}
                dataKey="value"
              >
                {chartData.map((entry, index) => (
                  <Cell
                    key={index}
                    fill={COLORS[entry.name as keyof typeof COLORS] || '#6b7280'}
                  />
                ))}
              </Pie>
              <Tooltip content={<CustomTooltip />} />
            </PieChart>
          </ResponsiveContainer>

          {/* Legend */}
          <div className="flex flex-col gap-2 flex-1">
            {chartData.map(item => (
              <div key={item.name} className="flex items-center justify-between gap-2">
                <div className="flex items-center gap-2">
                  <div
                    className="w-2.5 h-2.5 rounded-sm flex-shrink-0"
                    style={{ backgroundColor: COLORS[item.name as keyof typeof COLORS] || '#6b7280' }}
                  />
                  <span className="text-xs text-gray-400">{item.name}</span>
                </div>
                <span className="text-xs font-medium text-gray-300">{item.value}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </Card>
  )
}
