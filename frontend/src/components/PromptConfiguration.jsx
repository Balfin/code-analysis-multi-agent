import { useState, useEffect } from 'react'
import { 
  Shield, 
  Gauge, 
  Boxes, 
  ChevronDown,
  ChevronUp,
  Copy,
  Check,
  Loader2,
  AlertCircle,
  FileCode
} from 'lucide-react'
import apiClient from '../api/client'

// Map role types to icons
const ROLE_ICONS = {
  security: Shield,
  performance: Gauge,
  architecture: Boxes,
}

// Map role types to colors
const ROLE_COLORS = {
  security: 'text-red-400',
  performance: 'text-amber-400',
  architecture: 'text-blue-400',
}

const ROLE_BADGE_COLORS = {
  security: 'bg-red-500/20 text-red-400 border-red-500/30',
  performance: 'bg-amber-500/20 text-amber-400 border-amber-500/30',
  architecture: 'bg-blue-500/20 text-blue-400 border-blue-500/30',
}

function PromptConfiguration() {
  const [roles, setRoles] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [expandedRoles, setExpandedRoles] = useState(new Set())
  const [copiedPrompt, setCopiedPrompt] = useState(null)

  useEffect(() => {
    const fetchPrompts = async () => {
      setLoading(true)
      setError(null)
      try {
        const response = await apiClient.getPrompts()
        if (response.roles && Array.isArray(response.roles)) {
          setRoles(response.roles)
          // Expand first role by default
          if (response.roles.length > 0) {
            setExpandedRoles(new Set([response.roles[0].type]))
          }
        } else {
          setError('Invalid response format')
        }
      } catch (err) {
        setError(err.message || 'Failed to load prompts configuration')
      } finally {
        setLoading(false)
      }
    }

    fetchPrompts()
  }, [])

  const toggleRole = (roleType) => {
    const newExpanded = new Set(expandedRoles)
    if (newExpanded.has(roleType)) {
      newExpanded.delete(roleType)
    } else {
      newExpanded.add(roleType)
    }
    setExpandedRoles(newExpanded)
  }

  const handleCopyPrompt = async (text, promptId) => {
    try {
      await navigator.clipboard.writeText(text)
      setCopiedPrompt(promptId)
      setTimeout(() => setCopiedPrompt(null), 2000)
    } catch (err) {
      console.error('Failed to copy:', err)
    }
  }

  const getRoleIcon = (roleType) => {
    const Icon = ROLE_ICONS[roleType] || FileCode
    return Icon
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="flex flex-col items-center gap-3">
          <Loader2 className="w-8 h-8 text-indigo-400 animate-spin" />
          <p className="text-sm text-zinc-400">Loading prompts configuration...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="card p-6 border-red-800/50 bg-red-950/20">
        <div className="flex items-center gap-3 text-red-400">
          <AlertCircle className="w-5 h-5 flex-shrink-0" />
          <div>
            <p className="font-medium">Failed to load prompts</p>
            <p className="text-sm text-red-300/80 mt-1">{error}</p>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-4 animate-fade-in">
      <div className="card p-6">
        <div className="flex items-center gap-3 mb-6">
          <div className="flex items-center justify-center w-10 h-10 rounded-lg bg-gradient-to-br from-indigo-500/20 to-purple-500/20">
            <FileCode className="w-5 h-5 text-indigo-400" />
          </div>
          <div>
            <h2 className="text-xl font-semibold text-zinc-100">Prompt Configuration</h2>
            <p className="text-sm text-zinc-400 mt-0.5">
              View the roles and prompts used for code analysis
            </p>
          </div>
        </div>

        {roles.length === 0 ? (
          <div className="text-center py-8 text-zinc-400">
            <p>No prompts configuration found</p>
          </div>
        ) : (
          <div className="space-y-3">
            {roles.map((role) => {
              const isExpanded = expandedRoles.has(role.type)
              const Icon = getRoleIcon(role.type)
              const roleColor = ROLE_COLORS[role.type] || 'text-zinc-400'
              const badgeColor = ROLE_BADGE_COLORS[role.type] || 'bg-zinc-500/20 text-zinc-400 border-zinc-500/30'

              return (
                <div
                  key={role.type}
                  className="border border-zinc-800 rounded-lg overflow-hidden bg-zinc-900/50"
                >
                  {/* Role Header */}
                  <button
                    onClick={() => toggleRole(role.type)}
                    className="w-full flex items-center justify-between p-4 hover:bg-zinc-800/50 transition-colors"
                  >
                    <div className="flex items-center gap-3 flex-1">
                      <div className={`p-2 rounded-lg bg-zinc-800/50 ${roleColor}`}>
                        <Icon className="w-5 h-5" />
                      </div>
                      <div className="flex-1 text-left">
                        <div className="flex items-center gap-2">
                          <h3 className="font-semibold text-zinc-100">{role.name}</h3>
                          <span className={`px-2 py-0.5 rounded text-xs font-medium border ${badgeColor}`}>
                            {role.type}
                          </span>
                        </div>
                        {role.description && (
                          <p className="text-sm text-zinc-400 mt-1">{role.description}</p>
                        )}
                      </div>
                    </div>
                    {isExpanded ? (
                      <ChevronUp className="w-5 h-5 text-zinc-400 flex-shrink-0" />
                    ) : (
                      <ChevronDown className="w-5 h-5 text-zinc-400 flex-shrink-0" />
                    )}
                  </button>

                  {/* Expanded Content */}
                  {isExpanded && (
                    <div className="border-t border-zinc-800 p-4 space-y-4 bg-zinc-900/30">
                      {/* System Prompt */}
                      <div>
                        <div className="flex items-center justify-between mb-2">
                          <label className="text-sm font-medium text-zinc-300">
                            System Prompt
                          </label>
                          <button
                            onClick={() => handleCopyPrompt(role.system_prompt, `system-${role.type}`)}
                            className="flex items-center gap-1.5 px-2 py-1 rounded text-xs text-zinc-400 hover:text-zinc-200 hover:bg-zinc-800 transition-colors"
                            title="Copy system prompt"
                          >
                            {copiedPrompt === `system-${role.type}` ? (
                              <>
                                <Check className="w-3.5 h-3.5" />
                                <span>Copied!</span>
                              </>
                            ) : (
                              <>
                                <Copy className="w-3.5 h-3.5" />
                                <span>Copy</span>
                              </>
                            )}
                          </button>
                        </div>
                        <div className="relative">
                          <pre className="bg-zinc-950 border border-zinc-800 rounded-lg p-4 overflow-x-auto text-sm text-zinc-300 font-mono">
                            <code>{role.system_prompt}</code>
                          </pre>
                        </div>
                      </div>

                      {/* Human Prompt Template */}
                      <div>
                        <div className="flex items-center justify-between mb-2">
                          <label className="text-sm font-medium text-zinc-300">
                            Human Prompt Template
                          </label>
                          <button
                            onClick={() => handleCopyPrompt(role.human_prompt_template, `human-${role.type}`)}
                            className="flex items-center gap-1.5 px-2 py-1 rounded text-xs text-zinc-400 hover:text-zinc-200 hover:bg-zinc-800 transition-colors"
                            title="Copy human prompt template"
                          >
                            {copiedPrompt === `human-${role.type}` ? (
                              <>
                                <Check className="w-3.5 h-3.5" />
                                <span>Copied!</span>
                              </>
                            ) : (
                              <>
                                <Copy className="w-3.5 h-3.5" />
                                <span>Copy</span>
                              </>
                            )}
                          </button>
                        </div>
                        <div className="relative">
                          <pre className="bg-zinc-950 border border-zinc-800 rounded-lg p-4 overflow-x-auto text-sm text-zinc-300 font-mono">
                            <code>{role.human_prompt_template}</code>
                          </pre>
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              )
            })}
          </div>
        )}
      </div>
    </div>
  )
}

export default PromptConfiguration
