import { useQuery } from '@tanstack/react-query'
import { dashboardApi } from '../../api/dashboard'
import { Card, CardHeader, CardTitle } from '../ui/Card'
import { PageLoader } from '../ui/LoadingSpinner'
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from 'recharts'

const CustomTooltip = ({ active, payload, label }: any) => {
  if (active && payload && payload.length) {
    return (
      <div className="bg-gray-800 border border-gray-700 rounded-lg p-3 shadow-xl">
        <p className="text-xs text-gray-400 mb-2">{label}</p>
        {payload.map((entry: any) => (
          <div key={entry.name} className="flex items-center gap-2 text-xs">
            <div className="w-2 h-2 rounded-full" style={{ backgroundColor: entry.color }} />
            <span className="text-gray-300 capitalize">{entry.name}:</span>
            <span className="text-white font-medium">{entry.value.toFixed(1)}</span>
          </div>
        ))}
      </div>
    )
  }
  return null
}

export default function TechnicalDebtChart() {
  const { data, isLoading } = useQuery({
    queryKey: ['dashboard', 'debt-score'],
    queryFn: () => dashboardApi.getDebtScore(),
  })

  if (isLoading) return <Card><PageLoader /></Card>

  // Take last 20 data points
  const chartData = (data || []).slice(-20).reverse()

  return (
    <Card>
      <CardHeader>
        <CardTitle>Technical Debt Over Time</CardTitle>
        <span className="text-xs text-gray-500">Score (lower is better)</span>
      </CardHeader>

      {chartData.length === 0 ? (
        <div className="h-56 flex items-center justify-center text-gray-500 text-sm">
          No debt data yet. Run some PR analyses to track technical debt.
        </div>
      ) : (
        <ResponsiveContainer width="100%" height={220}>
          <AreaChart data={chartData} margin={{ top: 5, right: 10, left: -20, bottom: 5 }}>
            <defs>
              <linearGradient id="debtGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#ef4444" stopOpacity={0.3} />
                <stop offset="95%" stopColor="#ef4444" stopOpacity={0} />
              </linearGradient>
              <linearGradient id="secGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#f97316" stopOpacity={0.3} />
                <stop offset="95%" stopColor="#f97316" stopOpacity={0} />
              </linearGradient>
            </defs>
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
            <Legend wrapperStyle={{ fontSize: '11px', color: '#6b7280' }} />
            <Area
              type="monotone"
              dataKey="overall"
              stroke="#ef4444"
              fill="url(#debtGradient)"
              strokeWidth={2}
              name="Overall"
            />
            <Area
              type="monotone"
              dataKey="security"
              stroke="#f97316"
              fill="url(#secGradient)"
              strokeWidth={2}
              name="Security"
            />
          </AreaChart>
        </ResponsiveContainer>
      )}
    </Card>
  )
}
