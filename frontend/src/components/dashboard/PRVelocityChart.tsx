import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts'
import { useQuery } from '@tanstack/react-query'
import { dashboardApi } from '../../api/dashboard'
import { Card, CardHeader, CardTitle } from '../ui/Card'
import { PageLoader } from '../ui/LoadingSpinner'
import { format, parseISO } from 'date-fns'

const CustomTooltip = ({ active, payload, label }: any) => {
  if (active && payload && payload.length) {
    return (
      <div className="bg-gray-800 border border-gray-700 rounded-lg p-3 shadow-xl">
        <p className="text-xs text-gray-400 mb-2">{label}</p>
        {payload.map((entry: any) => (
          <div key={entry.name} className="flex items-center gap-2 text-xs">
            <div className="w-2 h-2 rounded-full" style={{ backgroundColor: entry.color }} />
            <span className="text-gray-300 capitalize">{entry.name}:</span>
            <span className="text-white font-medium">{entry.value}</span>
          </div>
        ))}
      </div>
    )
  }
  return null
}

export default function PRVelocityChart() {
  const { data, isLoading } = useQuery({
    queryKey: ['dashboard', 'pr-velocity'],
    queryFn: () => dashboardApi.getPRVelocity(30),
  })

  if (isLoading) return <Card><PageLoader /></Card>

  const chartData = (data || []).map(item => ({
    ...item,
    week: format(parseISO(item.week), 'MMM d'),
  }))

  return (
    <Card>
      <CardHeader>
        <CardTitle>PR Velocity</CardTitle>
        <span className="text-xs text-gray-500">Last 30 days</span>
      </CardHeader>

      {chartData.length === 0 ? (
        <div className="h-48 flex items-center justify-center text-gray-500 text-sm">
          No data yet. Analyze some PRs to see velocity trends.
        </div>
      ) : (
        <ResponsiveContainer width="100%" height={220}>
          <LineChart data={chartData} margin={{ top: 5, right: 10, left: -20, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" />
            <XAxis
              dataKey="week"
              tick={{ fill: '#6b7280', fontSize: 11 }}
              axisLine={{ stroke: '#374151' }}
              tickLine={false}
            />
            <YAxis
              tick={{ fill: '#6b7280', fontSize: 11 }}
              axisLine={false}
              tickLine={false}
            />
            <Tooltip content={<CustomTooltip />} />
            <Legend
              wrapperStyle={{ fontSize: '11px', color: '#6b7280' }}
            />
            <Line
              type="monotone"
              dataKey="opened"
              stroke="#6366f1"
              strokeWidth={2}
              dot={{ fill: '#6366f1', r: 3 }}
              activeDot={{ r: 5 }}
            />
            <Line
              type="monotone"
              dataKey="merged"
              stroke="#10b981"
              strokeWidth={2}
              dot={{ fill: '#10b981', r: 3 }}
              activeDot={{ r: 5 }}
            />
            <Line
              type="monotone"
              dataKey="closed"
              stroke="#6b7280"
              strokeWidth={2}
              strokeDasharray="5 5"
              dot={{ fill: '#6b7280', r: 3 }}
            />
          </LineChart>
        </ResponsiveContainer>
      )}
    </Card>
  )
}
