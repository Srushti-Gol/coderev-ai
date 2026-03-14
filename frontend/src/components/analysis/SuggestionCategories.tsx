import { AnalysisSummary } from '../../types'
import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer } from 'recharts'
import { Card, CardHeader, CardTitle } from '../ui/Card'

interface SuggestionCategoriesProps {
  summary: AnalysisSummary
}

const TYPE_COLORS: Record<string, string> = {
  security: '#ef4444',
  bug: '#f97316',
  performance: '#eab308',
  quality: '#6366f1',
  readability: '#8b5cf6',
  best_practice: '#06b6d4',
  test: '#10b981',
  duplicate: '#6b7280',
  debt: '#f59e0b',
}

const TYPE_LABELS: Record<string, string> = {
  security: 'Security',
  bug: 'Bugs',
  performance: 'Performance',
  quality: 'Quality',
  readability: 'Readability',
  best_practice: 'Best Practices',
  test: 'Tests',
  duplicate: 'Duplicates',
  debt: 'Tech Debt',
}

const CustomTooltip = ({ active, payload }: any) => {
  if (active && payload && payload.length) {
    const item = payload[0].payload
    return (
      <div className="bg-gray-800 border border-gray-700 rounded-lg p-3 shadow-xl">
        <p className="text-sm font-medium text-white">{TYPE_LABELS[item.type] || item.type}</p>
        <p className="text-xs text-gray-400">{item.count} issues</p>
      </div>
    )
  }
  return null
}

export default function SuggestionCategories({ summary }: SuggestionCategoriesProps) {
  const chartData = Object.entries(summary.by_type)
    .filter(([, count]) => count > 0)
    .map(([type, count]) => ({ type, count }))

  if (chartData.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Issue Categories</CardTitle>
        </CardHeader>
        <div className="text-center py-6 text-gray-500 text-sm">
          No issues found
        </div>
      </Card>
    )
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Issue Categories</CardTitle>
        <span className="text-xs text-gray-500">{summary.total} total</span>
      </CardHeader>

      <div className="flex items-center gap-4">
        <ResponsiveContainer width="50%" height={160}>
          <PieChart>
            <Pie
              data={chartData}
              cx="50%"
              cy="50%"
              innerRadius={35}
              outerRadius={60}
              paddingAngle={2}
              dataKey="count"
            >
              {chartData.map((entry, index) => (
                <Cell
                  key={index}
                  fill={TYPE_COLORS[entry.type] || '#6b7280'}
                />
              ))}
            </Pie>
            <Tooltip content={<CustomTooltip />} />
          </PieChart>
        </ResponsiveContainer>

        <div className="flex flex-col gap-1.5 flex-1">
          {chartData.map(item => (
            <div key={item.type} className="flex items-center justify-between gap-2">
              <div className="flex items-center gap-2 min-w-0">
                <div
                  className="w-2 h-2 rounded-full flex-shrink-0"
                  style={{ backgroundColor: TYPE_COLORS[item.type] || '#6b7280' }}
                />
                <span className="text-xs text-gray-400 truncate">
                  {TYPE_LABELS[item.type] || item.type}
                </span>
              </div>
              <span className="text-xs font-medium text-gray-300 flex-shrink-0">
                {item.count}
              </span>
            </div>
          ))}
        </div>
      </div>
    </Card>
  )
}
