import { useParams, Link } from 'react-router-dom'
import { usePullRequest } from '../hooks/usePullRequests'
import { useAnalysisSummary } from '../hooks/useAnalysis'
import PRDetail from '../components/pr/PRDetail'
import SuggestionCategories from '../components/analysis/SuggestionCategories'
import { PageLoader } from '../components/ui/LoadingSpinner'
import { ArrowLeft } from 'lucide-react'

export default function PRDetailPage() {
  const { prId } = useParams<{ prId: string }>()
  const { data: pr, isLoading } = usePullRequest(Number(prId))
  const { data: summary } = useAnalysisSummary(Number(prId))

  if (isLoading) return <PageLoader />

  if (!pr) {
    return (
      <div className="text-center py-16">
        <p className="text-gray-400">Pull request not found.</p>
        <Link to="/pull-requests" className="text-indigo-400 hover:underline mt-2 block">
          Back to pull requests
        </Link>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Breadcrumb */}
      <Link
        to="/pull-requests"
        className="flex items-center gap-2 text-sm text-gray-500 hover:text-gray-300 transition-colors"
      >
        <ArrowLeft className="w-4 h-4" />
        Back to Pull Requests
      </Link>

      <div className="grid grid-cols-1 xl:grid-cols-4 gap-6">
        {/* Main content */}
        <div className="xl:col-span-3">
          <PRDetail pr={pr} />
        </div>

        {/* Sidebar */}
        <div className="space-y-4">
          {summary && summary.total > 0 && (
            <SuggestionCategories summary={summary} />
          )}

          {/* PR metadata */}
          <div className="bg-gray-900 border border-gray-800 rounded-xl p-4">
            <h3 className="text-sm font-semibold text-gray-200 mb-3">Details</h3>
            <div className="space-y-2.5 text-xs">
              <div className="flex justify-between">
                <span className="text-gray-500">Base branch</span>
                <span className="text-gray-300 font-mono">{pr.base_branch}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-500">Head branch</span>
                <span className="text-gray-300 font-mono">{pr.head_branch}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-500">Files changed</span>
                <span className="text-gray-300">{pr.changed_files}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-500">Additions</span>
                <span className="text-green-400">+{pr.additions}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-500">Deletions</span>
                <span className="text-red-400">-{pr.deletions}</span>
              </div>
              {pr.analyzed_at && (
                <div className="flex justify-between">
                  <span className="text-gray-500">Analyzed</span>
                  <span className="text-gray-300">
                    {new Date(pr.analyzed_at).toLocaleDateString()}
                  </span>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
