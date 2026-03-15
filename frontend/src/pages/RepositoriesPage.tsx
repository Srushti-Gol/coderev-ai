import { useState } from 'react'
import { useRepositories, useSyncRepositories } from '../hooks/useRepositories'
import RepoList from '../components/repositories/RepoList'
import Button from '../components/ui/Button'
import { PageLoader } from '../components/ui/LoadingSpinner'
import { RefreshCw, Search, FolderGit2 } from 'lucide-react'

export default function RepositoriesPage() {
  const [search, setSearch] = useState('')
  const { data: repos, isLoading } = useRepositories({ search: search || undefined })
  const { mutate: sync, isPending: isSyncing } = useSyncRepositories()

  const activeRepos = repos?.filter(r => r.is_active) || []
  const inactiveRepos = repos?.filter(r => !r.is_active) || []

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Repositories</h1>
          <p className="text-gray-500 mt-1">
            Manage which repositories are analyzed by coderev-ai.
          </p>
        </div>
        <Button
          variant="primary"
          loading={isSyncing}
          leftIcon={<RefreshCw className="w-4 h-4" />}
          onClick={() => sync()}
        >
          Sync from GitHub
        </Button>
      </div>

      {/* Search */}
      <div className="relative max-w-sm">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500" />
        <input
          type="text"
          placeholder="Search repositories..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="w-full bg-gray-800 border border-gray-700 rounded-lg pl-10 pr-4 py-2 text-sm text-gray-200 placeholder-gray-500 focus:outline-none focus:border-indigo-500"
        />
      </div>

      {isLoading ? (
        <PageLoader text="Loading repositories..." />
      ) : (
        <>
          {/* Active repos */}
          {activeRepos.length > 0 && (
            <div>
              <div className="flex items-center gap-2 mb-4">
                <div className="w-2 h-2 bg-green-400 rounded-full" />
                <h2 className="text-sm font-semibold text-gray-300">
                  Active ({activeRepos.length})
                </h2>
              </div>
              <RepoList repos={activeRepos} />
            </div>
          )}

          {/* Inactive repos */}
          {inactiveRepos.length > 0 && (
            <div>
              <h2 className="text-sm font-semibold text-gray-500 mb-4">
                Available ({inactiveRepos.length})
              </h2>
              <RepoList
                repos={inactiveRepos}
                emptyMessage="No inactive repositories found."
              />
            </div>
          )}

          {/* Empty state */}
          {(!repos || repos.length === 0) && (
            <div className="flex flex-col items-center justify-center py-20">
              <FolderGit2 className="w-16 h-16 text-gray-700 mb-4" />
              <h3 className="text-gray-400 font-semibold text-lg mb-2">No repositories found</h3>
              <p className="text-gray-600 text-sm mb-6 text-center max-w-sm">
                Click "Sync from GitHub" to import your repositories and start reviewing PRs with AI.
              </p>
              <Button
                variant="primary"
                loading={isSyncing}
                leftIcon={<RefreshCw className="w-4 h-4" />}
                onClick={() => sync()}
              >
                Sync from GitHub
              </Button>
            </div>
          )}
        </>
      )}
    </div>
  )
}
