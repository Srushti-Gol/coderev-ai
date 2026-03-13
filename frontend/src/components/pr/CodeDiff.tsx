import { useState } from 'react'
import { clsx } from 'clsx'
import { ChevronDown, ChevronRight, FileCode } from 'lucide-react'

interface DiffLine {
  type: 'added' | 'removed' | 'context'
  content: string
  lineNumber?: number
}

interface DiffFile {
  filename: string
  additions: number
  deletions: number
  lines: DiffLine[]
}

function parseDiff(diff: string): DiffFile[] {
  const files: DiffFile[] = []
  let currentFile: DiffFile | null = null
  let lineNumber = 0

  for (const line of diff.split('\n')) {
    if (line.startsWith('diff --git') || line.startsWith('+++ b/')) {
      if (line.startsWith('+++ b/')) {
        const filename = line.slice(6)
        currentFile = {
          filename,
          additions: 0,
          deletions: 0,
          lines: [],
        }
        files.push(currentFile)
      }
    } else if (line.startsWith('@@')) {
      const match = line.match(/\+(\d+)/)
      if (match) lineNumber = parseInt(match[1]) - 1
    } else if (currentFile) {
      if (line.startsWith('+') && !line.startsWith('+++')) {
        lineNumber++
        currentFile.additions++
        currentFile.lines.push({ type: 'added', content: line.slice(1), lineNumber })
      } else if (line.startsWith('-') && !line.startsWith('---')) {
        currentFile.deletions++
        currentFile.lines.push({ type: 'removed', content: line.slice(1) })
      } else if (!line.startsWith('---') && !line.startsWith('+++')) {
        lineNumber++
        currentFile.lines.push({ type: 'context', content: line, lineNumber })
      }
    }
  }

  return files
}

interface CodeDiffProps {
  diff: string
}

function FileDiff({ file }: { file: DiffFile }) {
  const [collapsed, setCollapsed] = useState(false)

  return (
    <div className="border border-gray-800 rounded-xl overflow-hidden mb-4">
      {/* File header */}
      <button
        onClick={() => setCollapsed(!collapsed)}
        className="w-full flex items-center justify-between px-4 py-3 bg-gray-800/50 hover:bg-gray-800 transition-colors"
      >
        <div className="flex items-center gap-3">
          {collapsed ? (
            <ChevronRight className="w-4 h-4 text-gray-500" />
          ) : (
            <ChevronDown className="w-4 h-4 text-gray-500" />
          )}
          <FileCode className="w-4 h-4 text-gray-400" />
          <span className="text-sm font-mono text-gray-300">{file.filename}</span>
        </div>
        <div className="flex items-center gap-3 text-xs font-medium">
          <span className="text-green-400">+{file.additions}</span>
          <span className="text-red-400">-{file.deletions}</span>
        </div>
      </button>

      {!collapsed && (
        <div className="overflow-auto max-h-96">
          <table className="w-full text-xs font-mono">
            <tbody>
              {file.lines.map((line, i) => (
                <tr
                  key={i}
                  className={clsx(
                    line.type === 'added' && 'bg-green-500/10',
                    line.type === 'removed' && 'bg-red-500/10',
                    line.type === 'context' && 'hover:bg-gray-800/50',
                  )}
                >
                  <td className="select-none text-right pr-3 pl-3 text-gray-600 w-10 border-r border-gray-800">
                    {line.lineNumber || ''}
                  </td>
                  <td className="pl-3 pr-4 py-0.5">
                    <span className={clsx(
                      line.type === 'added' && 'text-green-400',
                      line.type === 'removed' && 'text-red-400',
                      line.type === 'context' && 'text-gray-400',
                    )}>
                      {line.type === 'added' ? '+ ' : line.type === 'removed' ? '- ' : '  '}
                    </span>
                    <span className={clsx(
                      line.type === 'added' && 'text-green-300',
                      line.type === 'removed' && 'text-red-300',
                      line.type === 'context' && 'text-gray-300',
                    )}>
                      {line.content}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}

export default function CodeDiff({ diff }: CodeDiffProps) {
  if (!diff) {
    return (
      <div className="text-center py-8 text-gray-500 text-sm">
        No diff available.
      </div>
    )
  }

  const files = parseDiff(diff)

  if (files.length === 0) {
    return (
      <div className="text-center py-8 text-gray-500 text-sm">
        Unable to parse diff.
      </div>
    )
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <p className="text-sm text-gray-400">
          {files.length} file{files.length !== 1 ? 's' : ''} changed
        </p>
        <div className="flex items-center gap-3 text-xs">
          <span className="text-green-400">
            +{files.reduce((sum, f) => sum + f.additions, 0)} additions
          </span>
          <span className="text-red-400">
            -{files.reduce((sum, f) => sum + f.deletions, 0)} deletions
          </span>
        </div>
      </div>
      {files.map((file, i) => (
        <FileDiff key={i} file={file} />
      ))}
    </div>
  )
}
