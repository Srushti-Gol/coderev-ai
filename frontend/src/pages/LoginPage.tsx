import { Github, Zap, Shield, BarChart3, GitPullRequest } from 'lucide-react'
import { authApi } from '../api/auth'
import { useAuthStore } from '../store/authStore'
import { Navigate } from 'react-router-dom'

const features = [
  {
    icon: Shield,
    title: 'Security Scanning',
    desc: 'Detect SQL injection, XSS, hardcoded secrets, and OWASP Top 10 vulnerabilities automatically.',
  },
  {
    icon: GitPullRequest,
    title: 'AI Code Review',
    desc: 'Claude claude-sonnet-4-6 reviews every PR for bugs, anti-patterns, and best practices.',
  },
  {
    icon: BarChart3,
    title: 'Technical Debt Tracking',
    desc: 'Monitor code quality trends, cyclomatic complexity, and debt scores over time.',
  },
  {
    icon: Zap,
    title: 'Real-time Webhooks',
    desc: 'Automatic analysis triggered on every PR open or update via GitHub webhooks.',
  },
]

export default function LoginPage() {
  const { token } = useAuthStore()

  if (token) return <Navigate to="/dashboard" replace />

  const handleLogin = () => {
    window.location.href = authApi.getGithubLoginUrl()
  }

  return (
    <div className="min-h-screen bg-gray-950 flex">
      {/* Left panel */}
      <div className="flex-1 flex flex-col justify-center px-8 md:px-16 py-12 bg-gradient-to-br from-gray-950 via-gray-900 to-indigo-950">
        {/* Logo */}
        <div className="flex items-center gap-3 mb-12">
          <div className="w-10 h-10 bg-indigo-600 rounded-xl flex items-center justify-center shadow-lg shadow-indigo-500/30">
            <Zap className="w-6 h-6 text-white" />
          </div>
          <div>
            <span className="font-bold text-white text-2xl">coderev</span>
            <span className="font-bold text-indigo-400 text-2xl">-ai</span>
          </div>
        </div>

        <div className="max-w-lg">
          <h1 className="text-4xl font-bold text-white mb-4 leading-tight">
            AI-Powered Code Review
            <span className="block text-indigo-400">for GitHub PRs</span>
          </h1>
          <p className="text-gray-400 text-lg mb-10">
            Automatically analyze pull requests with Claude AI. Catch security vulnerabilities,
            bugs, and performance issues before they reach production.
          </p>

          {/* GitHub login button */}
          <button
            onClick={handleLogin}
            className="flex items-center gap-3 bg-white hover:bg-gray-100 text-gray-900 font-semibold px-6 py-3.5 rounded-xl transition-all duration-150 shadow-lg hover:shadow-xl mb-6 group"
          >
            <Github className="w-5 h-5" />
            Continue with GitHub
          </button>

          <p className="text-xs text-gray-600">
            By signing in, you agree to give coderev-ai read access to your repositories.
            Your code is never stored permanently.
          </p>
        </div>

        {/* Features */}
        <div className="mt-16 grid grid-cols-1 sm:grid-cols-2 gap-5 max-w-lg">
          {features.map((feature) => {
            const Icon = feature.icon
            return (
              <div key={feature.title} className="flex gap-3">
                <div className="w-9 h-9 bg-indigo-500/15 border border-indigo-500/20 rounded-lg flex items-center justify-center flex-shrink-0 mt-0.5">
                  <Icon className="w-4 h-4 text-indigo-400" />
                </div>
                <div>
                  <h3 className="text-sm font-semibold text-gray-200 mb-0.5">{feature.title}</h3>
                  <p className="text-xs text-gray-500">{feature.desc}</p>
                </div>
              </div>
            )
          })}
        </div>
      </div>

      {/* Right panel - decorative */}
      <div className="hidden lg:flex flex-1 bg-gradient-to-br from-indigo-950 to-gray-950 items-center justify-center p-12 relative overflow-hidden">
        {/* Decorative grid */}
        <div className="absolute inset-0 opacity-10"
          style={{
            backgroundImage: 'linear-gradient(rgba(99,102,241,0.3) 1px, transparent 1px), linear-gradient(90deg, rgba(99,102,241,0.3) 1px, transparent 1px)',
            backgroundSize: '50px 50px',
          }}
        />

        {/* Mock dashboard cards */}
        <div className="relative z-10 space-y-4 w-full max-w-sm">
          {/* Mock PR card */}
          <div className="bg-gray-900/80 backdrop-blur border border-gray-700 rounded-xl p-5">
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-2">
                <div className="w-2 h-2 bg-green-400 rounded-full" />
                <span className="text-xs text-gray-300 font-medium">PR #142 — Security fix</span>
              </div>
              <span className="text-xs bg-red-500/20 text-red-400 border border-red-500/30 px-2 py-0.5 rounded">CRITICAL</span>
            </div>
            <p className="text-xs text-gray-500 mb-2">SQL injection detected in user authentication</p>
            <div className="bg-gray-950 rounded p-2 font-mono text-xs text-red-300">
              cursor.execute(f"SELECT * FROM users WHERE id = {'{'}user_id{'}'}")
            </div>
          </div>

          {/* Mock scores */}
          <div className="bg-gray-900/80 backdrop-blur border border-gray-700 rounded-xl p-5">
            <p className="text-xs text-gray-500 mb-3 font-medium">Analysis Complete</p>
            <div className="grid grid-cols-3 gap-3">
              {[
                { label: 'Quality', score: 87, color: 'text-green-400' },
                { label: 'Security', score: 65, color: 'text-yellow-400' },
                { label: 'Performance', score: 92, color: 'text-green-400' },
              ].map(item => (
                <div key={item.label} className="text-center">
                  <div className={`text-2xl font-bold ${item.color}`}>{item.score}</div>
                  <div className="text-xs text-gray-500 mt-0.5">{item.label}</div>
                </div>
              ))}
            </div>
          </div>

          {/* Mock stats */}
          <div className="bg-gray-900/80 backdrop-blur border border-gray-700 rounded-xl p-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <div className="text-2xl font-bold text-indigo-400">24</div>
                <div className="text-xs text-gray-500">PRs analyzed</div>
              </div>
              <div>
                <div className="text-2xl font-bold text-orange-400">3</div>
                <div className="text-xs text-gray-500">Critical issues</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
