import { useState } from 'react'
import { PullRequest } from '../../types'
import { useAnalysis, useAnalysisSummary } from '../../hooks/useAnalysis'
import { useTriggerAnalysis } from '../../hooks/usePullRequests'
import { StatusBadge, AIStatusBadge } from '../ui/Badge'
import Button from '../ui/Button'
import AnalysisComment from './AnalysisComment'
import { PageLoader } from '../ui/LoadingSpinner'
import {
  Shield,
  Bug,
  Zap,
  BookOpen,
  CheckSquare,
  Layers,
  RefreshCw,
  ExternalLink,
  GitBranch,
  Plus,
  Minus,
} from 'lucide-react'
import { clsx } from 'clsx'
import { formatDistanceToNow, parseISO } from 'date-fns'

interface PRDetailProps {
  pr: PullRequest
}

type TabId = 'security' | 'bugs' | 'performance' | 'readability' | 'best_practice' | 'tests'

const TABS: { id: TabId; label: string; icon: React.ElementType; type: string }[] = [
  { id: 'security', label: 'Security', icon: Shield, type: 'security' },
  { id: 'bugs', label: 'Bugs', icon: Bug, type: 'bug' },
  { id: 'performance', label: 'Performance', icon: Zap, type: 'performance' },
  { id: 'readability', label: 'Readability', icon: BookOpen, type: 'readability' },
  { id: 'best_practice', label: 'Best Practices', icon: CheckSquare, type: 'best_practice' },
  { id: 'tests', label: 'Tests', icon: Layers, type: 'test' },
]

function ScoreMeter({ score, label }: { score: number; label: string }) {
  const color = score >= 80 ? 'text-green-400' : score >= 60 ? 'text-yellow-400' : 'text-red-400'
  const bgColor = score >= 80 ? 'bg-green-500' : score >= 60 ? 'bg-yellow-500' : 'bg-red-500'

  return (
    <div className="text-center">
      <div className="relative w-16 h-16 mx-auto mb-2">
        <svg className="w-16 h-16 -rotate-90" viewBox="0 0 36 36">
          <circle cx="18" cy="18" r="15.9" fill="none" stroke="#1f2937" strokeWidth="2.5" />
          <circle
            cx="18" cy="18" r="15.9" fill="none"
            stroke={score >= 80 ? '#10b981' : score >= 60 ? '#f59e0b' : '#ef4444'}
            strokeWidth="2.5"
            strokeDasharray={`${score} 100`}
            strokeLinecap="round"
          />
        </svg>
        <span className={clsx('absolute inset-0 flex items-center justify-center text-sm font-bold', color)}>
          {score.toFixed(0)}
        </span>
      </div>
      <p className="text-xs text-gray-500">{label}</p>
    </div>
  )
}

export default function PRDetail({ pr }: PRDetailProps) {
  const [activeTab, setActiveTab] = useState<TabId>('security')
  const { mutate: triggerAnalysis, isPending: isTriggering } = useTriggerAnalysis()
  const { data: summary } = useAnalysisSummary(pr.id)

  const activeTabDef = TABS.find(t => t.id === activeTab)!
  const { data: analyses, isLoading } = useAnalysis(pr.id, { analysis_type: activeTabDef.type })

  const ageText = pr.pr_created_at
    ? formatDistanceToNow(parseISO(pr.pr_created_at), { addSuffix: true })
    : formatDistanceToNow(parseISO(pr.created_at), { addSuffix: true })

  const getTabCount = (type: string): number => {
    if (!summary) return 0
    return summary.by_type[type] || 0
  }

  return (
    <div className="space-y-6">
      {/* PR Header */}
      <div className="bg-gray-900 border border-gray-800 rounded-xl p-6">
        <div className="flex items-start justify-between gap-4">
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-3 flex-wrap mb-2">
              <StatusBadge status={pr.status} />
              <AIStatusBadge status={pr.ai_status} />
              <span className="text-sm text-gray-500">#{pr.pr_number}</span>
            </div>
            <h1 className="text-xl font-bold text-white mb-3">{pr.title}</h1>

            <div className="flex items-center gap-4 text-sm text-gray-400 flex-wrap">
              <div className="flex items-center gap-1.5">
                <img
                  src={pr.author_avatar || `https://github.com/${pr.author}.png`}
                  alt={pr.author}
                  className="w-5 h-5 rounded-full"
                />
                {pr.author}
              </div>
              <div className="flex items-center gap-1">
                <GitBranch className="w-3.5 h-3.5" />
                {pr.head_branch} → {pr.base_branch}
              </div>
              <span>{ageText}</span>
              <span className="flex items-center gap-2">
                <span className="text-green-400 flex items-center gap-0.5">
                  <Plus className="w-3 h-3" />{pr.additions}
                </span>
                <span className="text-red-400 flex items-center gap-0.5">
                  <Minus className="w-3 h-3" />{pr.deletions}
                </span>
                <span>{pr.changed_files} files</span>
              </span>
            </div>
          </div>

          <div className="flex items-center gap-2 flex-shrink-0">
            {pr.pr_url && (
              <Button
                variant="ghost"
                size="sm"
                leftIcon={<ExternalLink className="w-3.5 h-3.5" />}
                onClick={() => window.open(pr.pr_url!, '_blank')}
              >
                GitHub
              </Button>
            )}
            <Button
              variant="primary"
              size="sm"
              loading={isTriggering || pr.ai_status === 'analyzing'}
              leftIcon={<RefreshCw className="w-3.5 h-3.5" />}
              onClick={() => triggerAnalysis(pr.id)}
            >
              {pr.ai_status === 'analyzing' ? 'Analyzing...' : 'Re-analyze'}
            </Button>
          </div>
        </div>

        {/* Scores */}
        {pr.ai_status === 'completed' && (
          <div className="mt-6 pt-5 border-t border-gray-800 flex items-center justify-around">
            <ScoreMeter score={pr.quality_score || 0} label="Quality" />
            <ScoreMeter score={pr.security_score || 0} label="Security" />
            <ScoreMeter score={pr.performance_score || 0} label="Performance" />
            {summary && (
              <div className="text-center">
                <div className="text-2xl font-bold text-white mb-1">{summary.total}</div>
                <p className="text-xs text-gray-500">Total Issues</p>
                <div className="flex items-center gap-2 mt-1 text-xs">
                  {summary.critical > 0 && (
                    <span className="text-red-400">{summary.critical} critical</span>
                  )}
                  {summary.high > 0 && (
                    <span className="text-orange-400">{summary.high} high</span>
                  )}
                </div>
              </div>
            )}
          </div>
        )}

        {pr.ai_status === 'pending' && (
          <div className="mt-4 p-3 bg-gray-800 rounded-lg text-sm text-gray-400 text-center">
            Click "Re-analyze" to run AI code review on this PR.
          </div>
        )}

        {pr.ai_status === 'analyzing' && (
          <div className="mt-4 p-3 bg-indigo-500/10 border border-indigo-500/20 rounded-lg text-sm text-indigo-400 text-center animate-pulse">
            AI analysis in progress... This may take 1-2 minutes.
          </div>
        )}
      </div>

      {/* Analysis tabs */}
      {pr.ai_status === 'completed' && (
        <div className="bg-gray-900 border border-gray-800 rounded-xl overflow-hidden">
          {/* Tab bar */}
          <div className="flex border-b border-gray-800 overflow-x-auto">
            {TABS.map((tab) => {
              const Icon = tab.icon
              const count = getTabCount(tab.type)
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={clsx(
                    'flex items-center gap-2 px-4 py-3 text-sm font-medium whitespace-nowrap transition-colors border-b-2',
                    activeTab === tab.id
                      ? 'border-indigo-500 text-indigo-400 bg-indigo-500/5'
                      : 'border-transparent text-gray-400 hover:text-gray-200 hover:bg-gray-800/50'
                  )}
                >
                  <Icon className="w-4 h-4" />
                  {tab.label}
                  {count > 0 && (
                    <span className={clsx(
                      'text-xs px-1.5 py-0.5 rounded-full font-medium',
                      tab.id === 'security' && count > 0
                        ? 'bg-red-500/20 text-red-400'
                        : 'bg-gray-700 text-gray-300'
                    )}>
                      {count}
                    </span>
                  )}
                </button>
              )
            })}
          </div>

          {/* Tab content */}
          <div className="p-4 space-y-3">
            {isLoading ? (
              <PageLoader />
            ) : !analyses || analyses.length === 0 ? (
              <div className="text-center py-8 text-gray-500">
                <p className="text-sm">No {activeTabDef.label.toLowerCase()} issues found.</p>
                <p className="text-xs mt-1 text-gray-600">That's great!</p>
              </div>
            ) : (
              analyses.map(analysis => (
                <AnalysisComment key={analysis.id} analysis={analysis} />
              ))
            )}
          </div>
        </div>
      )}
    </div>
  )
}
