import { clsx } from 'clsx'
import { Severity, AIStatus, PRStatus } from '../../types'

interface BadgeProps {
  children: React.ReactNode
  variant?: 'severity' | 'status' | 'ai' | 'default'
  severity?: Severity
  status?: PRStatus
  aiStatus?: AIStatus
  className?: string
}

const severityStyles: Record<Severity, string> = {
  critical: 'bg-red-500/15 text-red-400 border border-red-500/30',
  high: 'bg-orange-500/15 text-orange-400 border border-orange-500/30',
  medium: 'bg-yellow-500/15 text-yellow-400 border border-yellow-500/30',
  low: 'bg-blue-500/15 text-blue-400 border border-blue-500/30',
  info: 'bg-gray-500/15 text-gray-400 border border-gray-500/30',
}

const statusStyles: Record<PRStatus, string> = {
  open: 'bg-green-500/15 text-green-400 border border-green-500/30',
  closed: 'bg-gray-500/15 text-gray-400 border border-gray-500/30',
  merged: 'bg-purple-500/15 text-purple-400 border border-purple-500/30',
  draft: 'bg-gray-600/15 text-gray-500 border border-gray-600/30',
}

const aiStatusStyles: Record<AIStatus, string> = {
  pending: 'bg-gray-500/15 text-gray-400 border border-gray-500/30',
  analyzing: 'bg-blue-500/15 text-blue-400 border border-blue-500/30 animate-pulse',
  completed: 'bg-green-500/15 text-green-400 border border-green-500/30',
  failed: 'bg-red-500/15 text-red-400 border border-red-500/30',
}

export function Badge({ children, severity, status, aiStatus, className }: BadgeProps) {
  let styles = 'bg-gray-700 text-gray-300'

  if (severity) styles = severityStyles[severity]
  else if (status) styles = statusStyles[status]
  else if (aiStatus) styles = aiStatusStyles[aiStatus]

  return (
    <span
      className={clsx(
        'inline-flex items-center px-2 py-0.5 rounded-md text-xs font-medium',
        styles,
        className
      )}
    >
      {children}
    </span>
  )
}

export function SeverityBadge({ severity }: { severity: Severity }) {
  return <Badge severity={severity}>{severity.toUpperCase()}</Badge>
}

export function StatusBadge({ status }: { status: PRStatus }) {
  return <Badge status={status}>{status}</Badge>
}

export function AIStatusBadge({ status }: { status: AIStatus }) {
  const labels: Record<AIStatus, string> = {
    pending: 'Pending',
    analyzing: 'Analyzing...',
    completed: 'Analyzed',
    failed: 'Failed',
  }
  return <Badge aiStatus={status}>{labels[status]}</Badge>
}
