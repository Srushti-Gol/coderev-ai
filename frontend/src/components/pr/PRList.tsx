import { PullRequest } from '../../types'
import PRCard from './PRCard'
import { GitPullRequest } from 'lucide-react'

interface PRListProps {
  prs: PullRequest[]
  repoFullName?: string
  emptyMessage?: string
}

export default function PRList({ prs, repoFullName, emptyMessage }: PRListProps) {
  if (prs.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-16 text-center">
        <GitPullRequest className="w-12 h-12 text-gray-700 mb-4" />
        <h3 className="text-gray-400 font-medium mb-2">No pull requests</h3>
        <p className="text-gray-600 text-sm max-w-md">
          {emptyMessage || 'No pull requests found. Activate a repository and open some PRs to get started.'}
        </p>
      </div>
    )
  }

  return (
    <div className="space-y-3">
      {prs.map((pr) => (
        <PRCard key={pr.id} pr={pr} repoFullName={repoFullName} />
      ))}
    </div>
  )
}
