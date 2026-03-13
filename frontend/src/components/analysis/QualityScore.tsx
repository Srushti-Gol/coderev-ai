import { clsx } from 'clsx'

interface QualityScoreProps {
  score: number
  label?: string
  size?: 'sm' | 'md' | 'lg'
}

const sizeConfig = {
  sm: { container: 'w-16 h-16', text: 'text-sm', label: 'text-xs' },
  md: { container: 'w-24 h-24', text: 'text-xl', label: 'text-xs' },
  lg: { container: 'w-32 h-32', text: 'text-3xl', label: 'text-sm' },
}

export default function QualityScore({ score, label = 'Quality', size = 'md' }: QualityScoreProps) {
  const { container, text, label: labelSize } = sizeConfig[size]
  const isGood = score >= 80
  const isOk = score >= 60 && score < 80
  const isBad = score < 60

  const color = isGood ? '#10b981' : isOk ? '#f59e0b' : '#ef4444'
  const textColor = isGood ? 'text-green-400' : isOk ? 'text-yellow-400' : 'text-red-400'

  // Calculate circumference for SVG circle
  const radius = 45
  const circumference = 2 * Math.PI * radius
  const offset = circumference - (score / 100) * circumference

  return (
    <div className="flex flex-col items-center gap-2">
      <div className={clsx('relative', container)}>
        <svg className="w-full h-full -rotate-90" viewBox="0 0 100 100">
          {/* Background track */}
          <circle
            cx="50"
            cy="50"
            r={radius}
            fill="none"
            stroke="#1f2937"
            strokeWidth="8"
          />
          {/* Score arc */}
          <circle
            cx="50"
            cy="50"
            r={radius}
            fill="none"
            stroke={color}
            strokeWidth="8"
            strokeLinecap="round"
            strokeDasharray={circumference}
            strokeDashoffset={offset}
            style={{ transition: 'stroke-dashoffset 0.5s ease' }}
          />
        </svg>
        {/* Center text */}
        <div className="absolute inset-0 flex items-center justify-center">
          <span className={clsx('font-bold', text, textColor)}>
            {score.toFixed(0)}
          </span>
        </div>
      </div>
      <span className={clsx('text-gray-500', labelSize)}>{label}</span>
    </div>
  )
}
