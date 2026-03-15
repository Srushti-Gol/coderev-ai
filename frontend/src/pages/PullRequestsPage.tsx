import { useState } from 'react'
import { usePullRequests } from '../hooks/usePullRequests'
import PRList from '../components/pr/PRList'
import { PageLoader } from '../components/ui/LoadingSpinner'
import { GitPullRequest } from 'lucide-react'
import { clsx } from 'clsx'

type FilterStatus = 'all' | 'open' | 'merged' | 'closed'
type FilterAI = 'all' | 'pending' | 'analyzing' | 'completed' | 'failed'

export default function PullRequestsPage() {
  const [statusFilter, setStatusFilter] = useState<FilterStatus>('all')
  const [aiFilter, setAIFilter] = useState<FilterAI>('all')

  const { data: prs, isLoading } = usePullRequests({
    status: statusFilter !== 'all' ? statusFilter : undefined,
    ai_status: aiFilter !== 'all' ? aiFilter : undefined,
  })

  const statusFilters: { value: FilterStatus; label: string }[] = [
    { value: 'all', label: 'All' },
    { value: 'open', label: 'Open' },
    { value: 'merged', label: 'Merged' },
    { value: 'closed', label: 'Closed' },
  ]

  const aiFilters: { value: FilterAI; label: string }[] = [
    { value: 'all', label: 'All' },
    { value: 'pending', label: 'Pending' },
    { value: 'analyzing', label: 'Analyzing' },
    { value: 'completed', label: 'Analyzed' },
    { value: 'failed', label: 'Failed' },
  ]

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-white">Pull Requests</h1>
        <p className="text-gray-500 mt-1">
          All tracked pull requests across your repositories.
        </p>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap gap-4">
        {/* Status filter */}
        <div className="flex items-center gap-2">
          <span className="text-xs text-gray-500 font-medium">Status:</span>
          <div className="flex bg-gray-800 rounded-lg p-1 gap-1">
            {statusFilters.map(filter => (
              <button
                key={filter.value}
                onClick={() => setStatusFilter(filter.value)}
                className={clsx(
                  'px-3 py-1 rounded-md text-xs font-medium transition-colors',
                  statusFilter === filter.value
                    ? 'bg-gray-700 text-white'
                    : 'text-gray-400 hover:text-gray-200'
                )}
              >
                {filter.label}
              </button>
            ))}
          </div>
        </div>

        {/* AI status filter */}
        <div className="flex items-center gap-2">
          <span className="text-xs text-gray-500 font-medium">AI:</span>
          <div className="flex bg-gray-800 rounded-lg p-1 gap-1">
            {aiFilters.map(filter => (
              <button
                key={filter.value}
                onClick={() => setAIFilter(filter.value)}
                className={clsx(
                  'px-3 py-1 rounded-md text-xs font-medium transition-colors',
                  aiFilter === filter.value
                    ? 'bg-gray-700 text-white'
                    : 'text-gray-400 hover:text-gray-200'
                )}
              >
                {filter.label}
              </button>
            ))}
          </div>
        </div>

        {prs && (
          <div className="flex items-center gap-1.5 ml-auto text-sm text-gray-500">
            <GitPullRequest className="w-4 h-4" />
            <span>{prs.length} PRs</span>
          </div>
        )}
      </div>

      {/* PR List */}
      {isLoading ? (
        <PageLoader text="Loading pull requests..." />
      ) : (
        <PRList prs={prs || []} />
      )}
    </div>
  )
}
