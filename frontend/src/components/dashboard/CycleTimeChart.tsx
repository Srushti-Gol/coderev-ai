import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from 'recharts'
import { useQuery } from '@tanstack/react-query'
import { dashboardApi } from '../../api/dashboard'
import { Card, CardHeader, CardTitle } from '../ui/Card'
import { PageLoader } from '../ui/LoadingSpinner'

const COLORS = ['#6366f1', '#8b5cf6', '#a78bfa', '#c4b5fd', '#ddd6fe']

const CustomTooltip = ({ active, payload, label }: any) => {
  if (active && payload && payload.length) {
    const data = payload[0].payload
    return (
      <div className="bg-gray-800 border border-gray-700 rounded-lg p-3 shadow-xl">
        <p className="text-sm font-medium text-white mb-2">{label}</p>
        <div className="space-y-1 text-xs">
          <div className="flex justify-between gap-4">
            <span className="text-gray-400">Avg cycle time:</span>
            <span className="text-indigo-400 font-medium">{data.avg_hours}h</span>
          </div>
          <div className="flex justify-between gap-4">
            <span className="text-gray-400">Min:</span>
            <span className="text-green-400">{data.min_hours}h</span>
          </div>
          <div className="flex justify-between gap-4">
            <span className="text-gray-400">Max:</span>
            <span className="text-red-400">{data.max_hours}h</span>
          </div>
          <div className="flex justify-between gap-4">
            <span className="text-gray-400">PRs merged:</span>
            <span className="text-white">{data.count}</span>
          </div>
        </div>
      </div>
    )
  }
  return null
}

export default function CycleTimeChart() {
  const { data, isLoading } = useQuery({
    queryKey: ['dashboard', 'cycle-time'],
    queryFn: () => dashboardApi.getCycleTime(30),
  })

  if (isLoading) return <Card><PageLoader /></Card>

  return (
    <Card>
      <CardHeader>
        <CardTitle>Avg Cycle Time by Repo</CardTitle>
        <span className="text-xs text-gray-500">Hours to merge</span>
      </CardHeader>

      {!data || data.length === 0 ? (
        <div className="h-48 flex items-center justify-center text-gray-500 text-sm">
          No merged PRs yet in this period.
        </div>
      ) : (
        <ResponsiveContainer width="100%" height={220}>
          <BarChart
            data={data}
            margin={{ top: 5, right: 10, left: -20, bottom: 5 }}
            layout="vertical"
          >
            <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" horizontal={false} />
            <XAxis
              type="number"
              tick={{ fill: '#6b7280', fontSize: 11 }}
              axisLine={{ stroke: '#374151' }}
              tickLine={false}
              unit="h"
            />
            <YAxis
              type="category"
              dataKey="repo"
              tick={{ fill: '#9ca3af', fontSize: 11 }}
              axisLine={false}
              tickLine={false}
              width={80}
            />
            <Tooltip content={<CustomTooltip />} />
            <Bar dataKey="avg_hours" radius={[0, 4, 4, 0]} maxBarSize={28}>
              {data.map((_, index) => (
                <Cell key={index} fill={COLORS[index % COLORS.length]} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      )}
    </Card>
  )
}
