import { useAnalysis } from '../../hooks/useAnalysis'
import AnalysisComment from '../pr/AnalysisComment'
import { PageLoader } from '../ui/LoadingSpinner'
import { Shield, AlertTriangle } from 'lucide-react'

interface SecurityFindingsProps {
  prId: number
}

export default function SecurityFindings({ prId }: SecurityFindingsProps) {
  const { data: findings, isLoading } = useAnalysis(prId, { analysis_type: 'security' })

  if (isLoading) return <PageLoader />

  const critical = findings?.filter(f => f.severity === 'critical') || []
  const high = findings?.filter(f => f.severity === 'high') || []
  const other = findings?.filter(f => f.severity !== 'critical' && f.severity !== 'high') || []

  if (!findings || findings.length === 0) {
    return (
      <div className="text-center py-8">
        <Shield className="w-10 h-10 text-green-400 mx-auto mb-3" />
        <p className="text-green-400 font-medium">No security issues found</p>
        <p className="text-sm text-gray-500 mt-1">This PR looks clean!</p>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      {/* Critical */}
      {critical.length > 0 && (
        <div>
          <div className="flex items-center gap-2 mb-3">
            <AlertTriangle className="w-4 h-4 text-red-400" />
            <h4 className="text-sm font-semibold text-red-400">
              Critical ({critical.length})
            </h4>
          </div>
          <div className="space-y-2">
            {critical.map(f => <AnalysisComment key={f.id} analysis={f} />)}
          </div>
        </div>
      )}

      {/* High */}
      {high.length > 0 && (
        <div>
          <div className="flex items-center gap-2 mb-3">
            <AlertTriangle className="w-4 h-4 text-orange-400" />
            <h4 className="text-sm font-semibold text-orange-400">
              High ({high.length})
            </h4>
          </div>
          <div className="space-y-2">
            {high.map(f => <AnalysisComment key={f.id} analysis={f} />)}
          </div>
        </div>
      )}

      {/* Other */}
      {other.length > 0 && (
        <div className="space-y-2">
          {other.map(f => <AnalysisComment key={f.id} analysis={f} />)}
        </div>
      )}
    </div>
  )
}
