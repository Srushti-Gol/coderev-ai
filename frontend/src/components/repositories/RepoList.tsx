import { Repository } from '../../types'
import RepoCard from './RepoCard'
import { FolderGit2 } from 'lucide-react'

interface RepoListProps {
  repos: Repository[]
  emptyMessage?: string
}

export default function RepoList({ repos, emptyMessage }: RepoListProps) {
  if (repos.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-16 text-center">
        <FolderGit2 className="w-12 h-12 text-gray-700 mb-4" />
        <h3 className="text-gray-400 font-medium mb-2">No repositories</h3>
        <p className="text-gray-600 text-sm max-w-md">
          {emptyMessage || 'Sync your repositories from GitHub to get started.'}
        </p>
      </div>
    )
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
      {repos.map((repo) => (
        <RepoCard key={repo.id} repo={repo} />
      ))}
    </div>
  )
}
