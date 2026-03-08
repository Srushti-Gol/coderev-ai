import { useQuery } from '@tanstack/react-query'
import { dashboardApi } from '../../api/dashboard'
import { Card, CardHeader, CardTitle } from '../ui/Card'
import { PageLoader } from '../ui/LoadingSpinner'
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts'

const CustomTooltip = ({ active, payload, label }: any) => {
  if (active && payload && payload.length) {
    return (
      <div className="bg-gray-800 border border-gray-700 rounded-lg p-3 shadow-xl">
        <p className="text-sm font-medium text-white mb-1">{label}</p>
        <p className="text-xs text-indigo-400">
          Avg quality: {payload[0].value}
        </p>
        <p className="text-xs text-gray-400">
          {payload[0].payload.count} PRs analyzed
        </p>
      </div>
    )
  }
  return null
}

export default function ReviewWorkload() {
  const { data, isLoading } = useQuery({
    queryKey: ['dashboard', 'quality-trend'],
    queryFn: () => dashboardApi.getQualityOverTime(30),
  })

  if (isLoading) return <Card><PageLoader /></Card>

  const chartData = (data || []).slice(-14) // Last 14 data points

  return (
    <Card>
      <CardHeader>
        <CardTitle>Quality Score Trend</CardTitle>
        <span className="text-xs text-gray-500">Avg per day</span>
      </CardHeader>

      {chartData.length === 0 ? (
        <div className="h-48 flex items-center justify-center text-gray-500 text-sm">
          No quality scores yet. Analyze some PRs first.
        </div>
      ) : (
        <ResponsiveContainer width="100%" height={220}>
          <BarChart data={chartData} margin={{ top: 5, right: 10, left: -20, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" />
            <XAxis
              dataKey="date"
              tick={{ fill: '#6b7280', fontSize: 10 }}
              axisLine={{ stroke: '#374151' }}
              tickLine={false}
            />
            <YAxis
              domain={[0, 100]}
              tick={{ fill: '#6b7280', fontSize: 11 }}
              axisLine={false}
              tickLine={false}
            />
            <Tooltip content={<CustomTooltip />} />
            <Bar
              dataKey="avg_quality"
              fill="#6366f1"
              radius={[4, 4, 0, 0]}
              maxBarSize={40}
            />
          </BarChart>
        </ResponsiveContainer>
      )}
    </Card>
  )
}
