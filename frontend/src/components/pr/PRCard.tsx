import { Link } from 'react-router-dom'
import { GitPullRequest, Clock, FileCode, Plus, Minus } from 'lucide-react'
import { PullRequest } from '../../types'
import { StatusBadge, AIStatusBadge } from '../ui/Badge'
import { formatDistanceToNow, parseISO } from 'date-fns'
import { clsx } from 'clsx'

interface PRCardProps {
  pr: PullRequest
  repoFullName?: string
}

const pipelineSteps = [
  { label: 'Opened', key: 'opened' },
  { label: 'Checks', key: 'checks' },
  { label: 'AI Review', key: 'review' },
  { label: 'Ready', key: 'ready' },
]

function getPipelineStep(pr: PullRequest): number {
  if (pr.ai_status === 'completed') return 3
  if (pr.ai_status === 'analyzing') return 2
  if (pr.status === 'open') return 1
  return 0
}

export default function PRCard({ pr, repoFullName }: PRCardProps) {
  const ageText = pr.pr_created_at
    ? formatDistanceToNow(parseISO(pr.pr_created_at), { addSuffix: true })
    : formatDistanceToNow(parseISO(pr.created_at), { addSuffix: true })

  const currentStep = getPipelineStep(pr)
  const detailPath = repoFullName
    ? `/repositories/${pr.repo_id}/prs/${pr.id}`
    : `/pull-requests/${pr.id}`

  return (
    <div className="bg-gray-900 border border-gray-800 rounded-xl p-5 hover:border-gray-700 transition-all group">
      {/* Header */}
      <div className="flex items-start justify-between gap-3 mb-3">
        <div className="flex items-start gap-3 min-w-0">
          <GitPullRequest className="w-4 h-4 text-indigo-400 mt-0.5 flex-shrink-0" />
          <div className="min-w-0">
            <Link
              to={detailPath}
              className="text-sm font-medium text-gray-200 hover:text-indigo-400 transition-colors line-clamp-2 group-hover:text-indigo-400"
            >
              {pr.title}
            </Link>
            <div className="flex items-center gap-2 mt-1 flex-wrap">
              <span className="text-xs text-gray-500">#{pr.pr_number}</span>
              <span className="text-xs text-gray-600">•</span>
              <span className="text-xs text-gray-500">by {pr.author}</span>
              {repoFullName && (
                <>
                  <span className="text-xs text-gray-600">•</span>
                  <span className="text-xs text-gray-500">{repoFullName}</span>
                </>
              )}
            </div>
          </div>
        </div>

        <div className="flex items-center gap-2 flex-shrink-0">
          <StatusBadge status={pr.status} />
          <AIStatusBadge status={pr.ai_status} />
        </div>
      </div>

      {/* Stats row */}
      <div className="flex items-center gap-4 mb-4 text-xs text-gray-500">
        <div className="flex items-center gap-1">
          <Clock className="w-3 h-3" />
          {ageText}
        </div>
        <div className="flex items-center gap-1">
          <FileCode className="w-3 h-3" />
          {pr.changed_files} files
        </div>
        <div className="flex items-center gap-1 text-green-400">
          <Plus className="w-3 h-3" />
          {pr.additions}
        </div>
        <div className="flex items-center gap-1 text-red-400">
          <Minus className="w-3 h-3" />
          {pr.deletions}
        </div>

        {/* Quality scores */}
        {pr.ai_status === 'completed' && pr.quality_score !== null && (
          <div className="flex items-center gap-3 ml-auto">
            <span className={clsx(
              'font-medium',
              (pr.quality_score || 0) >= 80 ? 'text-green-400' :
              (pr.quality_score || 0) >= 60 ? 'text-yellow-400' : 'text-red-400'
            )}>
              Q: {pr.quality_score?.toFixed(0)}
            </span>
            {pr.security_score !== null && (
              <span className={clsx(
                'font-medium',
                (pr.security_score || 0) >= 80 ? 'text-green-400' :
                (pr.security_score || 0) >= 60 ? 'text-yellow-400' : 'text-red-400'
              )}>
                S: {pr.security_score?.toFixed(0)}
              </span>
            )}
          </div>
        )}
      </div>

      {/* Pipeline progress */}
      <div className="flex items-center gap-0">
        {pipelineSteps.map((step, index) => (
          <div key={step.key} className="flex items-center flex-1">
            <div className="flex flex-col items-center flex-1">
              <div
                className={clsx(
                  'w-full h-1 rounded-full transition-colors',
                  index <= currentStep ? 'bg-indigo-500' : 'bg-gray-700'
                )}
              />
              <span className={clsx(
                'text-xs mt-1',
                index <= currentStep ? 'text-indigo-400' : 'text-gray-600'
              )}>
                {step.label}
              </span>
            </div>
            {index < pipelineSteps.length - 1 && (
              <div className="w-2" />
            )}
          </div>
        ))}
      </div>
    </div>
  )
}
