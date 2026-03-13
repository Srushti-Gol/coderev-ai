import { useState } from 'react'
import { Analysis } from '../../types'
import { SeverityBadge } from '../ui/Badge'
import { ChevronDown, ChevronRight, FileCode, ThumbsUp, X } from 'lucide-react'
import { clsx } from 'clsx'
import Button from '../ui/Button'
import { useDismissAnalysis, useVerifyAnalysis } from '../../hooks/useAnalysis'

interface AnalysisCommentProps {
  analysis: Analysis
}

export default function AnalysisComment({ analysis }: AnalysisCommentProps) {
  const [expanded, setExpanded] = useState(false)
  const { mutate: dismiss, isPending: isDismissing } = useDismissAnalysis()
  const { mutate: verify, isPending: isVerifying } = useVerifyAnalysis()

  if (analysis.is_dismissed) return null

  return (
    <div
      className={clsx(
        'border rounded-xl overflow-hidden transition-all',
        analysis.severity === 'critical' && 'border-red-500/40 bg-red-500/5',
        analysis.severity === 'high' && 'border-orange-500/40 bg-orange-500/5',
        analysis.severity === 'medium' && 'border-yellow-500/40 bg-yellow-500/5',
        analysis.severity === 'low' && 'border-blue-500/40 bg-blue-500/5',
        analysis.severity === 'info' && 'border-gray-700 bg-gray-800/50',
      )}
    >
      {/* Header */}
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full flex items-start gap-3 p-4 text-left hover:bg-white/5 transition-colors"
      >
        <span className="mt-0.5">
          {expanded ? (
            <ChevronDown className="w-4 h-4 text-gray-500" />
          ) : (
            <ChevronRight className="w-4 h-4 text-gray-500" />
          )}
        </span>

        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap mb-1">
            <SeverityBadge severity={analysis.severity} />
            <span className="text-xs text-gray-500 uppercase tracking-wider font-medium">
              {analysis.analysis_type.replace('_', ' ')}
            </span>
            {analysis.is_verified && (
              <span className="text-xs bg-green-500/15 text-green-400 border border-green-500/30 px-1.5 py-0.5 rounded">
                Verified
              </span>
            )}
          </div>
          <p className="text-sm text-gray-200 font-medium">{analysis.message}</p>

          {analysis.file_path && (
            <div className="flex items-center gap-1.5 mt-1">
              <FileCode className="w-3 h-3 text-gray-500" />
              <span className="text-xs text-gray-500 font-mono">
                {analysis.file_path}
                {analysis.line_start && `:${analysis.line_start}`}
                {analysis.line_end && analysis.line_end !== analysis.line_start && `-${analysis.line_end}`}
              </span>
            </div>
          )}
        </div>
      </button>

      {/* Expanded content */}
      {expanded && (
        <div className="px-4 pb-4 space-y-4 border-t border-gray-800/50">
          {/* Code snippet */}
          {analysis.code_snippet && (
            <div>
              <p className="text-xs font-medium text-gray-500 uppercase tracking-wider mb-2 mt-4">
                Problematic code
              </p>
              <pre className="code-block text-xs overflow-auto max-h-40">
                <code className="text-red-300">{analysis.code_snippet}</code>
              </pre>
            </div>
          )}

          {/* Suggestion */}
          {analysis.suggestion && (
            <div>
              <p className="text-xs font-medium text-gray-500 uppercase tracking-wider mb-2">
                Suggestion
              </p>
              <p className="text-sm text-gray-300 bg-gray-800/50 rounded-lg p-3 border border-gray-700">
                {analysis.suggestion}
              </p>
            </div>
          )}

          {/* Suggested code */}
          {analysis.suggested_code && (
            <div>
              <p className="text-xs font-medium text-gray-500 uppercase tracking-wider mb-2">
                Suggested fix
              </p>
              <pre className="code-block text-xs overflow-auto max-h-40">
                <code className="text-green-300">{analysis.suggested_code}</code>
              </pre>
            </div>
          )}

          {/* Actions */}
          <div className="flex items-center gap-2 pt-2">
            {!analysis.is_verified && (
              <Button
                size="sm"
                variant="ghost"
                loading={isVerifying}
                leftIcon={<ThumbsUp className="w-3 h-3" />}
                onClick={() => verify(analysis.id)}
              >
                Mark as valid
              </Button>
            )}
            <Button
              size="sm"
              variant="ghost"
              loading={isDismissing}
              leftIcon={<X className="w-3 h-3" />}
              onClick={() => dismiss(analysis.id)}
              className="text-gray-500 hover:text-gray-300"
            >
              Dismiss
            </Button>
          </div>
        </div>
      )}
    </div>
  )
}
