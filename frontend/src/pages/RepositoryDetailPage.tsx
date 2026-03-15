import { useParams, Link } from 'react-router-dom'
import { useRepository } from '../hooks/useRepositories'
import { usePullRequests } from '../hooks/usePullRequests'
import PRList from '../components/pr/PRList'
import { PageLoader } from '../components/ui/LoadingSpinner'
import {
  Star,
  GitFork,
  Globe,
  Lock,
  ArrowLeft,
  GitPullRequest,
  Zap,
  ZapOff,
} from 'lucide-react'
import { useActivateRepository, useDeactivateRepository } from '../hooks/useRepositories'
import Button from '../components/ui/Button'

export default function RepositoryDetailPage() {
  const { id } = useParams<{ id: string }>()
  const { data: repo, isLoading: repoLoading } = useRepository(Number(id))
  const { data: prs, isLoading: prsLoading } = usePullRequests({ repo_id: Number(id) })
  const { mutate: activate, isPending: isActivating } = useActivateRepository()
  const { mutate: deactivate, isPending: isDeactivating } = useDeactivateRepository()

  if (repoLoading) return <PageLoader />

  if (!repo) {
    return (
      <div className="text-center py-16">
        <p className="text-gray-400">Repository not found.</p>
        <Link to="/repositories" className="text-indigo-400 hover:underline mt-2 block">
          Back to repositories
        </Link>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Breadcrumb */}
      <Link
        to="/repositories"
        className="flex items-center gap-2 text-sm text-gray-500 hover:text-gray-300 transition-colors"
      >
        <ArrowLeft className="w-4 h-4" />
        Back to Repositories
      </Link>

      {/* Repo header */}
      <div className="bg-gray-900 border border-gray-800 rounded-xl p-6">
        <div className="flex items-start justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 mb-2">
              {repo.is_private ? (
                <Lock className="w-4 h-4 text-gray-500" />
              ) : (
                <Globe className="w-4 h-4 text-gray-500" />
              )}
              <h1 className="text-xl font-bold text-white">{repo.full_name}</h1>
              {repo.is_active && (
                <span className="flex items-center gap-1 text-xs bg-green-500/15 text-green-400 border border-green-500/30 px-2 py-0.5 rounded-full">
                  <div className="w-1.5 h-1.5 bg-green-400 rounded-full animate-pulse" />
                  Active
                </span>
              )}
            </div>

            {repo.description && (
              <p className="text-gray-400 text-sm mb-4">{repo.description}</p>
            )}

            <div className="flex items-center gap-6 text-sm text-gray-500">
              {repo.language && (
                <span className="flex items-center gap-1.5">
                  <span className="w-3 h-3 rounded-full bg-indigo-500" />
                  {repo.language}
                </span>
              )}
              <span className="flex items-center gap-1.5">
                <Star className="w-4 h-4" />
                {repo.stars_count.toLocaleString()}
              </span>
              <span className="flex items-center gap-1.5">
                <GitFork className="w-4 h-4" />
                {repo.forks_count}
              </span>
              <span className="flex items-center gap-1.5">
                <GitPullRequest className="w-4 h-4" />
                {prs?.length || 0} PRs tracked
              </span>
            </div>
          </div>

          <div className="flex items-center gap-2">
            {repo.is_active ? (
              <Button
                variant="ghost"
                size="sm"
                loading={isDeactivating}
                leftIcon={<ZapOff className="w-4 h-4" />}
                onClick={() => deactivate(repo.id)}
                className="text-gray-500 hover:text-red-400"
              >
                Disable AI Review
              </Button>
            ) : (
              <Button
                variant="primary"
                size="sm"
                loading={isActivating}
                leftIcon={<Zap className="w-4 h-4" />}
                onClick={() => activate(repo.id)}
              >
                Enable AI Review
              </Button>
            )}
          </div>
        </div>
      </div>

      {/* PRs section */}
      <div>
        <h2 className="text-lg font-semibold text-white mb-4">Pull Requests</h2>
        {prsLoading ? (
          <PageLoader />
        ) : (
          <PRList
            prs={prs || []}
            repoFullName={repo.full_name}
            emptyMessage={
              repo.is_active
                ? 'No pull requests tracked yet. Open a PR in GitHub to trigger analysis.'
                : 'Enable AI review to start tracking pull requests for this repository.'
            }
          />
        )}
      </div>
    </div>
  )
}
