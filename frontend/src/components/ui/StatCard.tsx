import { clsx } from 'clsx'
import { TrendingUp, TrendingDown, Minus } from 'lucide-react'

interface StatCardProps {
  title: string
  value: string | number
  subtitle?: string
  icon?: React.ReactNode
  trend?: number  // positive = up, negative = down
  trendLabel?: string
  className?: string
  accentColor?: 'indigo' | 'green' | 'red' | 'yellow' | 'purple' | 'orange'
}

const accentColors = {
  indigo: 'bg-indigo-500/10 text-indigo-400',
  green: 'bg-green-500/10 text-green-400',
  red: 'bg-red-500/10 text-red-400',
  yellow: 'bg-yellow-500/10 text-yellow-400',
  purple: 'bg-purple-500/10 text-purple-400',
  orange: 'bg-orange-500/10 text-orange-400',
}

export default function StatCard({
  title,
  value,
  subtitle,
  icon,
  trend,
  trendLabel,
  className,
  accentColor = 'indigo',
}: StatCardProps) {
  const isPositive = trend !== undefined && trend > 0
  const isNegative = trend !== undefined && trend < 0
  const isNeutral = trend === 0

  return (
    <div
      className={clsx(
        'bg-gray-900 border border-gray-800 rounded-xl p-5 hover:border-gray-700 transition-colors',
        className
      )}
    >
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <p className="text-xs font-medium text-gray-500 uppercase tracking-wider mb-2">
            {title}
          </p>
          <div className="flex items-baseline gap-2">
            <span className="text-2xl font-bold text-white">{value}</span>
            {subtitle && (
              <span className="text-sm text-gray-500">{subtitle}</span>
            )}
          </div>

          {/* Trend indicator */}
          {trend !== undefined && (
            <div className="flex items-center gap-1.5 mt-2">
              {isPositive && <TrendingUp className="w-3 h-3 text-green-400" />}
              {isNegative && <TrendingDown className="w-3 h-3 text-red-400" />}
              {isNeutral && <Minus className="w-3 h-3 text-gray-500" />}
              <span
                className={clsx(
                  'text-xs font-medium',
                  isPositive && 'text-green-400',
                  isNegative && 'text-red-400',
                  isNeutral && 'text-gray-500'
                )}
              >
                {trend > 0 ? '+' : ''}{trend}% {trendLabel}
              </span>
            </div>
          )}
        </div>

        {/* Icon */}
        {icon && (
          <div
            className={clsx(
              'w-10 h-10 rounded-lg flex items-center justify-center flex-shrink-0',
              accentColors[accentColor]
            )}
          >
            {icon}
          </div>
        )}
      </div>
    </div>
  )
}
