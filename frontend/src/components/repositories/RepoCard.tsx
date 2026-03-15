import { Link } from 'react-router-dom'
import { Repository } from '../../types'
import { Star, GitFork, Globe, Lock, Zap, ZapOff, ChevronRight } from 'lucide-react'
import { clsx } from 'clsx'
import Button from '../ui/Button'
import { useActivateRepository, useDeactivateRepository } from '../../hooks/useRepositories'

interface RepoCardProps {
  repo: Repository
}

const LANGUAGE_COLORS: Record<string, string> = {
  Python: 'bg-blue-500',
  JavaScript: 'bg-yellow-400',
  TypeScript: 'bg-blue-400',
  Go: 'bg-cyan-400',
  Rust: 'bg-orange-500',
  Java: 'bg-red-500',
  'C#': 'bg-purple-500',
  Ruby: 'bg-red-400',
  PHP: 'bg-indigo-400',
  Swift: 'bg-orange-400',
  Kotlin: 'bg-purple-400',
}

export default function RepoCard({ repo }: RepoCardProps) {
  const { mutate: activate, isPending: isActivating } = useActivateRepository()
  const { mutate: deactivate, isPending: isDeactivating } = useDeactivateRepository()

  return (
    <div className={clsx(
      'bg-gray-900 border rounded-xl p-5 hover:border-gray-700 transition-all group',
      repo.is_active ? 'border-indigo-500/30' : 'border-gray-800'
    )}>
      {/* Header */}
      <div className="flex items-start justify-between gap-3 mb-3">
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-2 mb-1">
            {repo.is_private ? (
              <Lock className="w-3.5 h-3.5 text-gray-500 flex-shrink-0" />
            ) : (
              <Globe className="w-3.5 h-3.5 text-gray-500 flex-shrink-0" />
            )}
            <Link
              to={`/repositories/${repo.id}`}
              className="text-sm font-semibold text-gray-200 hover:text-indigo-400 transition-colors truncate"
            >
              {repo.full_name}
            </Link>
          </div>

          {repo.description && (
            <p className="text-xs text-gray-500 line-clamp-2 mt-1">{repo.description}</p>
          )}
        </div>

        {repo.is_active && (
          <div className="flex items-center gap-1.5 flex-shrink-0">
            <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse" />
            <span className="text-xs text-green-400 font-medium">Active</span>
          </div>
        )}
      </div>

      {/* Stats */}
      <div className="flex items-center gap-4 text-xs text-gray-500 mb-4">
        {repo.language && (
          <div className="flex items-center gap-1.5">
            <span
              className={clsx(
                'w-2.5 h-2.5 rounded-full',
                LANGUAGE_COLORS[repo.language] || 'bg-gray-500'
              )}
            />
            {repo.language}
          </div>
        )}
        <div className="flex items-center gap-1">
          <Star className="w-3 h-3" />
          {repo.stars_count.toLocaleString()}
        </div>
        <div className="flex items-center gap-1">
          <GitFork className="w-3 h-3" />
          {repo.forks_count}
        </div>
      </div>

      {/* Actions */}
      <div className="flex items-center gap-2">
        {repo.is_active ? (
          <>
            <Link
              to={`/repositories/${repo.id}/prs`}
              className="flex-1 flex items-center justify-center gap-2 btn-secondary text-xs py-1.5"
            >
              View PRs
              <ChevronRight className="w-3 h-3" />
            </Link>
            <Button
              size="sm"
              variant="ghost"
              loading={isDeactivating}
              leftIcon={<ZapOff className="w-3.5 h-3.5" />}
              onClick={() => deactivate(repo.id)}
              className="text-gray-500 hover:text-red-400"
            >
              Disable
            </Button>
          </>
        ) : (
          <Button
            size="sm"
            variant="primary"
            className="w-full"
            loading={isActivating}
            leftIcon={<Zap className="w-3.5 h-3.5" />}
            onClick={() => activate(repo.id)}
          >
            Enable AI Review
          </Button>
        )}
      </div>
    </div>
  )
}
