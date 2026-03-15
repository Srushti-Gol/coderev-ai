import { useState } from 'react'
import { useAuth } from '../hooks/useAuth'
import { Card } from '../components/ui/Card'
import Button from '../components/ui/Button'
import {
  User,
  Github,
  Key,
  Bell,
  Shield,
  ExternalLink,
  Copy,
  CheckCircle,
} from 'lucide-react'

export default function SettingsPage() {
  const { user } = useAuth()
  const [copied, setCopied] = useState(false)
  const [notifyOnComplete, setNotifyOnComplete] = useState(true)
  const [notifyOnCritical, setNotifyOnCritical] = useState(true)
  const [notifyOnSecurity, setNotifyOnSecurity] = useState(true)

  const webhookUrl = `${window.location.origin.replace('3000', '8000')}/webhooks/github`

  const copyWebhook = () => {
    navigator.clipboard.writeText(webhookUrl)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  return (
    <div className="space-y-6 max-w-2xl">
      <div>
        <h1 className="text-2xl font-bold text-white">Settings</h1>
        <p className="text-gray-500 mt-1">Manage your account and notification preferences.</p>
      </div>

      {/* Profile */}
      <Card>
        <div className="flex items-center gap-2 mb-5">
          <User className="w-4 h-4 text-gray-400" />
          <h2 className="text-sm font-semibold text-gray-200">Profile</h2>
        </div>

        <div className="flex items-center gap-4">
          {user?.avatar_url ? (
            <img
              src={user.avatar_url}
              alt={user.github_login}
              className="w-16 h-16 rounded-full border-2 border-gray-700"
            />
          ) : (
            <div className="w-16 h-16 rounded-full bg-indigo-600 flex items-center justify-center text-2xl font-bold text-white">
              {user?.github_login?.[0]?.toUpperCase()}
            </div>
          )}
          <div>
            <p className="font-semibold text-white">{user?.name || user?.github_login}</p>
            <p className="text-sm text-gray-500">@{user?.github_login}</p>
            {user?.email && (
              <p className="text-sm text-gray-500">{user.email}</p>
            )}
          </div>
        </div>

        <div className="mt-5 pt-5 border-t border-gray-800">
          <a
            href={`https://github.com/${user?.github_login}`}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-2 text-sm text-indigo-400 hover:text-indigo-300 transition-colors"
          >
            <Github className="w-4 h-4" />
            View GitHub profile
            <ExternalLink className="w-3 h-3" />
          </a>
        </div>
      </Card>

      {/* GitHub Integration */}
      <Card>
        <div className="flex items-center gap-2 mb-5">
          <Github className="w-4 h-4 text-gray-400" />
          <h2 className="text-sm font-semibold text-gray-200">GitHub Integration</h2>
        </div>

        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-200 font-medium">GitHub OAuth</p>
              <p className="text-xs text-gray-500 mt-0.5">Connected as @{user?.github_login}</p>
            </div>
            <div className="flex items-center gap-2 text-xs text-green-400">
              <CheckCircle className="w-3.5 h-3.5" />
              Connected
            </div>
          </div>

          <div className="p-4 bg-gray-800 rounded-lg border border-gray-700">
            <p className="text-xs font-medium text-gray-400 mb-2">Webhook URL</p>
            <div className="flex items-center gap-2">
              <code className="flex-1 text-xs text-gray-300 font-mono break-all">
                {webhookUrl}
              </code>
              <button
                onClick={copyWebhook}
                className="p-1.5 text-gray-400 hover:text-gray-200 transition-colors flex-shrink-0"
              >
                {copied ? (
                  <CheckCircle className="w-4 h-4 text-green-400" />
                ) : (
                  <Copy className="w-4 h-4" />
                )}
              </button>
            </div>
            <p className="text-xs text-gray-600 mt-2">
              Add this URL to your GitHub repository webhooks to automatically analyze PRs.
            </p>
          </div>
        </div>
      </Card>

      {/* Notifications */}
      <Card>
        <div className="flex items-center gap-2 mb-5">
          <Bell className="w-4 h-4 text-gray-400" />
          <h2 className="text-sm font-semibold text-gray-200">Notifications</h2>
        </div>

        <div className="space-y-4">
          {[
            {
              label: 'Analysis complete',
              desc: 'When AI finishes analyzing a PR',
              value: notifyOnComplete,
              onChange: setNotifyOnComplete,
            },
            {
              label: 'Critical issues',
              desc: 'When critical security or quality issues are found',
              value: notifyOnCritical,
              onChange: setNotifyOnCritical,
            },
            {
              label: 'Security findings',
              desc: 'For all security vulnerability findings',
              value: notifyOnSecurity,
              onChange: setNotifyOnSecurity,
            },
          ].map(item => (
            <div key={item.label} className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-200">{item.label}</p>
                <p className="text-xs text-gray-500 mt-0.5">{item.desc}</p>
              </div>
              <button
                onClick={() => item.onChange(!item.value)}
                className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                  item.value ? 'bg-indigo-600' : 'bg-gray-700'
                }`}
              >
                <span
                  className={`inline-block h-4 w-4 transform rounded-full bg-white shadow transition-transform ${
                    item.value ? 'translate-x-6' : 'translate-x-1'
                  }`}
                />
              </button>
            </div>
          ))}
        </div>
      </Card>

      {/* Security */}
      <Card>
        <div className="flex items-center gap-2 mb-5">
          <Shield className="w-4 h-4 text-gray-400" />
          <h2 className="text-sm font-semibold text-gray-200">Security</h2>
        </div>

        <div className="space-y-3">
          <div className="flex items-center justify-between p-3 bg-gray-800 rounded-lg">
            <div>
              <p className="text-sm text-gray-200">GitHub Access Token</p>
              <p className="text-xs text-gray-500 mt-0.5">Used to fetch repository data and PR diffs</p>
            </div>
            <div className="flex items-center gap-2 text-xs">
              <Key className="w-3.5 h-3.5 text-gray-500" />
              <span className="text-gray-500">Encrypted</span>
            </div>
          </div>

          <p className="text-xs text-gray-600">
            coderev-ai requests read-only access to your repositories. Your code is processed
            securely and never stored permanently.
          </p>
        </div>
      </Card>

      {/* Danger zone */}
      <Card className="border-red-500/20">
        <h2 className="text-sm font-semibold text-red-400 mb-4">Danger Zone</h2>
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm text-gray-200">Delete account</p>
            <p className="text-xs text-gray-500 mt-0.5">
              Permanently delete your account and all associated data
            </p>
          </div>
          <Button variant="danger" size="sm">
            Delete account
          </Button>
        </div>
      </Card>
    </div>
  )
}
