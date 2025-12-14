import { useState, useEffect, useCallback, useMemo } from 'react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { 
  Shield, 
  Gauge, 
  Boxes, 
  ChevronRight, 
  AlertTriangle, 
  FileCode,
  Search,
  RefreshCw,
  ExternalLink,
  Copy,
  Check,
  Loader2,
  Trash2,
  SortAsc,
  SortDesc,
  ChevronDown,
  Sparkles,
  Save
} from 'lucide-react'
import apiClient from '../api/client'

// Sort options
const SORT_OPTIONS = [
  { value: 'risk_desc', label: 'Risk (High → Low)' },
  { value: 'risk_asc', label: 'Risk (Low → High)' },
  { value: 'type', label: 'Type' },
  { value: 'location', label: 'Location' },
  { value: 'newest', label: 'Newest First' },
  { value: 'oldest', label: 'Oldest First' },
]

// Risk level priority for sorting
const RISK_PRIORITY = {
  critical: 4,
  high: 3,
  medium: 2,
  low: 1,
}

function IssuesList({ onSelectIssue }) {
  const [issues, setIssues] = useState([])
  const [selectedId, setSelectedId] = useState(null)
  const [selectedIssue, setSelectedIssue] = useState(null)
  const [typeFilter, setTypeFilter] = useState('all')
  const [riskFilter, setRiskFilter] = useState('all')
  const [searchQuery, setSearchQuery] = useState('')
  const [sortBy, setSortBy] = useState('risk_desc')
  const [isLoading, setIsLoading] = useState(true)
  const [isLoadingDetail, setIsLoadingDetail] = useState(false)
  const [error, setError] = useState(null)
  const [copiedId, setCopiedId] = useState(null)
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [pageSize] = useState(100)
  
  // Issue improvement state
  const [availableModels, setAvailableModels] = useState([])
  const [selectedModel, setSelectedModel] = useState('')
  const [isImproving, setIsImproving] = useState(false)
  const [improveError, setImproveError] = useState(null)
  const [improvedIssue, setImprovedIssue] = useState(null)
  const [activeTab, setActiveTab] = useState('original')

  // Fetch issues from API
  const fetchIssues = useCallback(async () => {
    setIsLoading(true)
    setError(null)
    
    try {
      const filters = {
        page,
        pageSize,
      }
      
      if (typeFilter !== 'all') filters.type = typeFilter
      if (riskFilter !== 'all') filters.riskLevel = riskFilter
      if (searchQuery) filters.search = searchQuery

      const response = await apiClient.getIssues(filters)
      setIssues(response.issues || [])
      setTotal(response.filtered_total || 0)
    } catch (err) {
      setError(err.message || 'Failed to load issues')
      setIssues([])
    } finally {
      setIsLoading(false)
    }
  }, [typeFilter, riskFilter, searchQuery, page, pageSize])

  // Initial load and filter changes
  useEffect(() => {
    fetchIssues()
  }, [fetchIssues])

  // Fetch available models on mount
  useEffect(() => {
    const fetchModels = async () => {
      try {
        const response = await apiClient.getModels()
        if (response.models && Array.isArray(response.models)) {
          setAvailableModels(response.models)
          if (response.models.length > 0 && !selectedModel) {
            setSelectedModel(response.models[0])
          }
        }
      } catch (err) {
        console.error('Failed to fetch models:', err)
      }
    }
    fetchModels()
  }, [])

  // Reset improvement state when issue changes
  useEffect(() => {
    setImprovedIssue(null)
    setActiveTab('original')
    setImproveError(null)
  }, [selectedId])

  // Sort issues client-side
  const sortedIssues = useMemo(() => {
    const sorted = [...issues]
    
    switch (sortBy) {
      case 'risk_desc':
        sorted.sort((a, b) => (RISK_PRIORITY[b.risk_level] || 0) - (RISK_PRIORITY[a.risk_level] || 0))
        break
      case 'risk_asc':
        sorted.sort((a, b) => (RISK_PRIORITY[a.risk_level] || 0) - (RISK_PRIORITY[b.risk_level] || 0))
        break
      case 'type':
        sorted.sort((a, b) => (a.type || '').localeCompare(b.type || ''))
        break
      case 'location':
        sorted.sort((a, b) => (a.location || '').localeCompare(b.location || ''))
        break
      case 'newest':
        sorted.sort((a, b) => new Date(b.created_at || 0) - new Date(a.created_at || 0))
        break
      case 'oldest':
        sorted.sort((a, b) => new Date(a.created_at || 0) - new Date(b.created_at || 0))
        break
      default:
        break
    }
    
    return sorted
  }, [issues, sortBy])

  // Fetch issue detail when selected
  const handleSelect = async (issue) => {
    setSelectedId(issue.id)
    setIsLoadingDetail(true)
    
    try {
      const detail = await apiClient.getIssueDetail(issue.id)
      setSelectedIssue(detail)
      onSelectIssue?.(detail)
    } catch (err) {
      // Fall back to basic issue data
      setSelectedIssue(issue)
      onSelectIssue?.(issue)
    } finally {
      setIsLoadingDetail(false)
    }
  }

  const handleRefresh = () => {
    setPage(1)
    fetchIssues()
  }

  const handleDelete = async (issueId) => {
    if (!confirm('Are you sure you want to delete this issue?')) return
    
    try {
      await apiClient.deleteIssue(issueId)
      setIssues(prev => prev.filter(i => i.id !== issueId))
      if (selectedId === issueId) {
        setSelectedId(null)
        setSelectedIssue(null)
      }
      setTotal(prev => prev - 1)
    } catch (err) {
      alert('Failed to delete issue: ' + err.message)
    }
  }

  const handleCopyId = (id) => {
    navigator.clipboard.writeText(id)
    setCopiedId(id)
    setTimeout(() => setCopiedId(null), 2000)
  }

  const handleImprove = async () => {
    if (!selectedIssue || !selectedModel || isImproving) return
    
    setIsImproving(true)
    setImproveError(null)
    
    try {
      const improved = await apiClient.improveIssue(selectedIssue.id, selectedModel)
      setImprovedIssue(improved)
      setActiveTab('improved')
    } catch (err) {
      setImproveError(err.message || 'Failed to improve issue')
      console.error('Improve error:', err)
    } finally {
      setIsImproving(false)
    }
  }

  const handleChooseVersion = async () => {
    if (!improvedIssue || !selectedIssue) return
    
    if (!confirm('Are you sure you want to replace the original issue with the improved version?')) {
      return
    }
    
    try {
      // Update the issue with improved data
      const updated = await apiClient.updateIssue(selectedIssue.id, {
        title: improvedIssue.title,
        description: improvedIssue.description,
        solution: improvedIssue.solution,
      })
      
      // Update local state
      setSelectedIssue(updated)
      setImprovedIssue(null)
      setActiveTab('original')
      
      // Refresh issues list to show updated issue
      fetchIssues()
      
      alert('Issue updated successfully!')
    } catch (err) {
      alert('Failed to update issue: ' + err.message)
      console.error('Update error:', err)
    }
  }

  const clearFilters = () => {
    setTypeFilter('all')
    setRiskFilter('all')
    setSearchQuery('')
    setSortBy('risk_desc')
    setPage(1)
  }

  const getTypeIcon = (type) => {
    switch (type) {
      case 'security':
        return <Shield className="w-4 h-4" />
      case 'performance':
        return <Gauge className="w-4 h-4" />
      case 'architecture':
        return <Boxes className="w-4 h-4" />
      default:
        return <AlertTriangle className="w-4 h-4" />
    }
  }

  const getTypeColor = (type) => {
    switch (type) {
      case 'security':
        return 'text-red-400 bg-red-500/20'
      case 'performance':
        return 'text-amber-400 bg-amber-500/20'
      case 'architecture':
        return 'text-blue-400 bg-blue-500/20'
      default:
        return 'text-zinc-400 bg-zinc-500/20'
    }
  }

  const getRiskBadge = (level) => {
    const badges = {
      critical: 'badge-critical',
      high: 'badge-high',
      medium: 'badge-medium',
      low: 'badge-low',
    }
    return badges[level] || 'badge'
  }

  const hasFilters = typeFilter !== 'all' || riskFilter !== 'all' || searchQuery

  // Helper function to render issue content
  const renderIssueContent = (issue) => {
    if (!issue) return null
    
    return (
      <div className="p-6 space-y-6">
        {/* Render markdown if available */}
        {issue.markdown_content ? (
          <div className="markdown-content">
            <ReactMarkdown
              remarkPlugins={[remarkGfm]}
              components={{
                h1: ({ children }) => <h1 className="text-2xl font-bold text-zinc-100 mb-4">{children}</h1>,
                h2: ({ children }) => <h2 className="text-xl font-semibold text-zinc-100 mt-6 mb-3">{children}</h2>,
                h3: ({ children }) => <h3 className="text-lg font-medium text-zinc-200 mt-4 mb-2">{children}</h3>,
                p: ({ children }) => <p className="text-zinc-300 mb-4 leading-relaxed">{children}</p>,
                ul: ({ children }) => <ul className="list-disc pl-6 mb-4 text-zinc-300">{children}</ul>,
                ol: ({ children }) => <ol className="list-decimal pl-6 mb-4 text-zinc-300">{children}</ol>,
                li: ({ children }) => <li className="mb-1">{children}</li>,
                code: ({ inline, children }) => 
                  inline ? (
                    <code className="bg-zinc-800 px-1.5 py-0.5 rounded text-sm font-mono text-indigo-300">{children}</code>
                  ) : (
                    <code className="text-zinc-300">{children}</code>
                  ),
                pre: ({ children }) => (
                  <pre className="bg-zinc-800 rounded-lg p-4 overflow-x-auto mb-4 text-sm">
                    {children}
                  </pre>
                ),
                table: ({ children }) => (
                  <div className="overflow-x-auto mb-4">
                    <table className="w-full text-sm border-collapse">{children}</table>
                  </div>
                ),
                thead: ({ children }) => (
                  <thead className="bg-zinc-800">{children}</thead>
                ),
                tbody: ({ children }) => (
                  <tbody>{children}</tbody>
                ),
                tr: ({ children }) => (
                  <tr className="border-b border-zinc-700">{children}</tr>
                ),
                th: ({ children }) => (
                  <th className="border border-zinc-700 px-3 py-2 text-left bg-zinc-800 font-medium text-zinc-300">{children}</th>
                ),
                td: ({ children }) => (
                  <td className="border border-zinc-700 px-3 py-2 text-zinc-400">{children}</td>
                ),
                strong: ({ children }) => <strong className="font-semibold text-zinc-100">{children}</strong>,
                a: ({ children, href }) => (
                  <a href={href} className="text-indigo-400 hover:underline" target="_blank" rel="noopener noreferrer">{children}</a>
                ),
                blockquote: ({ children }) => (
                  <blockquote className="border-l-4 border-zinc-700 pl-4 italic text-zinc-400 my-4">{children}</blockquote>
                ),
                hr: () => <hr className="border-zinc-700 my-6" />,
              }}
            >
              {issue.markdown_content}
            </ReactMarkdown>
          </div>
        ) : (
          <>
            {/* Fallback: structured display */}
            {/* Location */}
            <div>
              <h3 className="text-sm font-medium text-zinc-400 mb-2">Location</h3>
              <div className="flex items-center gap-2">
                <code className="flex-1 font-mono bg-zinc-800 px-3 py-2 rounded-lg text-zinc-300 text-sm overflow-x-auto">
                  {issue.location}
                </code>
                <button 
                  className="btn btn-secondary p-2"
                  title="Open in editor (coming soon)"
                >
                  <ExternalLink className="w-4 h-4" />
                </button>
              </div>
            </div>

            {/* Description */}
            <div>
              <h3 className="text-sm font-medium text-zinc-400 mb-2">Description</h3>
              <p className="text-zinc-300 leading-relaxed">
                {issue.description}
              </p>
            </div>

            {/* Code Snippet */}
            {issue.code_snippet && (
              <div>
                <h3 className="text-sm font-medium text-zinc-400 mb-2">Code</h3>
                <pre className="bg-zinc-800 rounded-lg p-4 overflow-x-auto">
                  <code className="text-sm font-mono text-zinc-300 whitespace-pre-wrap">
                    {issue.code_snippet}
                  </code>
                </pre>
              </div>
            )}

            {/* Solution */}
            {issue.solution && (
              <div>
                <h3 className="text-sm font-medium text-zinc-400 mb-2">Recommended Solution</h3>
                <div className="bg-green-950/30 border border-green-900/50 rounded-lg p-4">
                  <p className="text-green-300 text-sm leading-relaxed">
                    {issue.solution}
                  </p>
                </div>
              </div>
            )}
          </>
        )}

        {/* Author */}
        {issue.author && (
          <div>
            <h3 className="text-sm font-medium text-zinc-400 mb-2">Detected By</h3>
            <span className="badge bg-zinc-800 text-zinc-300">
              {issue.author}
            </span>
          </div>
        )}

        {/* Issue ID and metadata */}
        <div className="pt-4 border-t border-zinc-800">
          <div className="flex items-center justify-between text-xs">
            <p className="text-zinc-600">
              Issue ID: <code className="font-mono">{issue.id}</code>
            </p>
            <button
              onClick={() => handleCopyId(issue.id)}
              className="text-zinc-500 hover:text-zinc-300 flex items-center gap-1"
            >
              {copiedId === issue.id ? (
                <>
                  <Check className="w-3 h-3" /> Copied!
                </>
              ) : (
                <>
                  <Copy className="w-3 h-3" /> Copy ID
                </>
              )}
            </button>
          </div>
          {issue.created_at && (
            <p className="text-xs text-zinc-600 mt-1">
              Created: {new Date(issue.created_at).toLocaleString()}
            </p>
          )}
        </div>
      </div>
    )
  }

  return (
    <div className="flex flex-col lg:flex-row gap-6 h-[calc(100vh-200px)] animate-fade-in">
      {/* Issues List Panel */}
      <div className="lg:w-1/2 flex flex-col min-h-[300px] lg:min-h-0">
        {/* Filters */}
        <div className="card p-4 mb-4">
          <div className="flex flex-col gap-3">
            {/* Search Row */}
            <div className="flex flex-col sm:flex-row items-start sm:items-center gap-3">
              <div className="relative flex-1 w-full">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-zinc-500" />
                <input
                  type="text"
                  value={searchQuery}
                  onChange={(e) => {
                    setSearchQuery(e.target.value)
                    setPage(1)
                  }}
                  placeholder="Search issues..."
                  className="input pl-10 text-sm py-2 w-full"
                />
              </div>
              
              {/* Refresh button */}
              <button 
                onClick={handleRefresh}
                className="btn btn-secondary p-2"
                title="Refresh issues"
                disabled={isLoading}
              >
                <RefreshCw className={`w-4 h-4 ${isLoading ? 'animate-spin' : ''}`} />
              </button>
            </div>

            {/* Filter Row */}
            <div className="flex flex-wrap items-center gap-2">
              {/* Type Filter */}
              <select
                value={typeFilter}
                onChange={(e) => {
                  setTypeFilter(e.target.value)
                  setPage(1)
                }}
                className="input text-sm py-1.5 w-auto"
              >
                <option value="all">All Types</option>
                <option value="security">🔒 Security</option>
                <option value="performance">⚡ Performance</option>
                <option value="architecture">🏗️ Architecture</option>
              </select>

              {/* Risk Filter */}
              <select
                value={riskFilter}
                onChange={(e) => {
                  setRiskFilter(e.target.value)
                  setPage(1)
                }}
                className="input text-sm py-1.5 w-auto"
              >
                <option value="all">All Risks</option>
                <option value="critical">🔴 Critical</option>
                <option value="high">🟠 High</option>
                <option value="medium">🟡 Medium</option>
                <option value="low">🟢 Low</option>
              </select>

              {/* Sort */}
              <select
                value={sortBy}
                onChange={(e) => setSortBy(e.target.value)}
                className="input text-sm py-1.5 w-auto"
              >
                {SORT_OPTIONS.map(opt => (
                  <option key={opt.value} value={opt.value}>{opt.label}</option>
                ))}
              </select>
            </div>
          </div>

          <div className="mt-3 flex items-center justify-between text-xs text-zinc-500">
            <span>
              {isLoading ? 'Loading...' : `${total} issues found`}
            </span>
            {hasFilters && (
              <button 
                onClick={clearFilters}
                className="text-indigo-400 hover:text-indigo-300"
              >
                Clear filters
              </button>
            )}
          </div>
        </div>

        {/* Error State */}
        {error && (
          <div className="card p-4 mb-4 border-red-900/50 bg-red-950/20">
            <div className="flex items-center gap-2 text-red-400">
              <AlertTriangle className="w-4 h-4" />
              <span className="text-sm">{error}</span>
              <button onClick={handleRefresh} className="ml-auto text-xs hover:underline">
                Retry
              </button>
            </div>
          </div>
        )}

        {/* Issues List */}
        <div className="card flex-1 overflow-hidden">
          <div className="h-full overflow-y-auto">
            {isLoading ? (
              <div className="p-8 text-center">
                <Loader2 className="w-8 h-8 text-indigo-400 mx-auto mb-3 animate-spin" />
                <p className="text-zinc-500">Loading issues...</p>
              </div>
            ) : sortedIssues.length === 0 ? (
              <div className="p-8 text-center">
                <AlertTriangle className="w-10 h-10 text-zinc-600 mx-auto mb-3" />
                <p className="text-zinc-400 font-medium mb-1">No issues found</p>
                <p className="text-sm text-zinc-600">
                  {hasFilters
                    ? 'Try adjusting your filters'
                    : 'Run an analysis from the Dashboard to see issues'}
                </p>
              </div>
            ) : (
              sortedIssues.map((issue, index) => (
                <button
                  key={issue.id}
                  onClick={() => handleSelect(issue)}
                  className={`
                    w-full p-4 text-left border-b border-zinc-800 last:border-b-0
                    transition-all duration-150
                    ${selectedId === issue.id 
                      ? 'bg-zinc-800/80 border-l-2 border-l-indigo-500' 
                      : 'hover:bg-zinc-800/50 border-l-2 border-l-transparent'
                    }
                  `}
                  style={{ animationDelay: `${index * 20}ms` }}
                >
                  <div className="flex items-start gap-3">
                    <div className={`p-2 rounded-lg ${getTypeColor(issue.type)} flex-shrink-0`}>
                      {getTypeIcon(issue.type)}
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-1 flex-wrap">
                        <h3 className="font-medium text-zinc-200 truncate">
                          {issue.title}
                        </h3>
                        <span className={`badge ${getRiskBadge(issue.risk_level)} flex-shrink-0`}>
                          {issue.risk_level}
                        </span>
                      </div>
                      <div className="flex items-center gap-2 text-sm text-zinc-500">
                        <FileCode className="w-3 h-3 flex-shrink-0" />
                        <span className="font-mono truncate text-xs">{issue.location}</span>
                      </div>
                    </div>
                    <ChevronRight className={`w-4 h-4 text-zinc-600 flex-shrink-0 transition-transform ${selectedId === issue.id ? 'rotate-90' : ''}`} />
                  </div>
                </button>
              ))
            )}
          </div>
        </div>
      </div>

      {/* Issue Detail Panel */}
      <div className="lg:w-1/2 min-h-[400px] lg:min-h-0">
        <div className="card h-full overflow-hidden">
          {isLoadingDetail ? (
            <div className="h-full flex items-center justify-center">
              <div className="text-center">
                <Loader2 className="w-8 h-8 text-indigo-400 mx-auto mb-3 animate-spin" />
                <p className="text-zinc-500">Loading details...</p>
              </div>
            </div>
          ) : selectedIssue ? (
            <div className="h-full flex flex-col">
              {/* Header */}
              <div className="p-6 border-b border-zinc-800 bg-zinc-900/50 flex-shrink-0">
                <div className="flex items-start gap-4 mb-4">
                  <div className={`p-3 rounded-lg ${getTypeColor(selectedIssue.type)}`}>
                    {getTypeIcon(selectedIssue.type)}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-2 flex-wrap">
                      <span className={`badge ${getRiskBadge(selectedIssue.risk_level)}`}>
                        {selectedIssue.risk_level}
                      </span>
                      <span className="badge bg-zinc-800 text-zinc-400 capitalize">
                        {selectedIssue.type}
                      </span>
                    </div>
                    <h2 className="text-xl font-semibold text-zinc-100">
                      {selectedIssue.title}
                    </h2>
                  </div>
                  <button
                    onClick={() => handleDelete(selectedIssue.id)}
                    className="btn btn-secondary p-2 text-red-400 hover:text-red-300 hover:bg-red-950/30"
                    title="Delete issue"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
                
                {/* Improve Controls */}
                <div className="flex items-center gap-3 flex-wrap">
                  <select
                    value={selectedModel}
                    onChange={(e) => setSelectedModel(e.target.value)}
                    className="input text-sm py-1.5 flex-1 min-w-[150px]"
                    disabled={isImproving || availableModels.length === 0}
                  >
                    {availableModels.length === 0 ? (
                      <option value="">No models available</option>
                    ) : (
                      availableModels.map(model => (
                        <option key={model} value={model}>{model}</option>
                      ))
                    )}
                  </select>
                  <button
                    onClick={handleImprove}
                    disabled={!selectedModel || isImproving || availableModels.length === 0}
                    className="btn btn-primary text-sm px-4 py-1.5 flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {isImproving ? (
                      <>
                        <Loader2 className="w-4 h-4 animate-spin" />
                        Improving...
                      </>
                    ) : (
                      <>
                        <Sparkles className="w-4 h-4" />
                        Improve
                      </>
                    )}
                  </button>
                </div>
                
                {/* Improve Error */}
                {improveError && (
                  <div className="mt-3 p-2 bg-red-950/30 border border-red-900/50 rounded text-sm text-red-400">
                    {improveError}
                  </div>
                )}
              </div>

              {/* Tabs */}
              {improvedIssue ? (
                <>
                  <div className="border-b border-zinc-800 flex gap-1 px-6 pt-4 flex-shrink-0">
                    <button
                      onClick={() => setActiveTab('original')}
                      className={`px-4 py-2 text-sm font-medium transition-colors border-b-2 ${
                        activeTab === 'original'
                          ? 'border-indigo-500 text-indigo-400'
                          : 'border-transparent text-zinc-500 hover:text-zinc-300'
                      }`}
                    >
                      Original
                    </button>
                    <button
                      onClick={() => setActiveTab('improved')}
                      className={`px-4 py-2 text-sm font-medium transition-colors border-b-2 ${
                        activeTab === 'improved'
                          ? 'border-indigo-500 text-indigo-400'
                          : 'border-transparent text-zinc-500 hover:text-zinc-300'
                      }`}
                    >
                      Improved
                    </button>
                  </div>
                  
                  {/* Tab Content */}
                  <div className="overflow-y-auto flex-1 min-h-0">
                    {activeTab === 'original' ? (
                      renderIssueContent(selectedIssue)
                    ) : (
                      <div>
                        {renderIssueContent(improvedIssue)}
                        <div className="px-6 pb-6 pt-4 border-t border-zinc-800">
                          <button
                            onClick={handleChooseVersion}
                            className="btn btn-primary w-full flex items-center justify-center gap-2"
                          >
                            <Save className="w-4 h-4" />
                            Choose This Version
                          </button>
                        </div>
                      </div>
                    )}
                  </div>
                </>
              ) : (
                <div className="overflow-y-auto flex-1 min-h-0">
                  {renderIssueContent(selectedIssue)}
                </div>
              )}
            </div>
          ) : (
            <div className="h-full flex items-center justify-center p-8">
              <div className="text-center">
                <div className="flex justify-center mb-4">
                  <div className="flex items-center justify-center w-16 h-16 rounded-full bg-zinc-800">
                    <FileCode className="w-8 h-8 text-zinc-600" />
                  </div>
                </div>
                <h3 className="text-lg font-medium text-zinc-400 mb-2">
                  Select an Issue
                </h3>
                <p className="text-sm text-zinc-600 max-w-xs">
                  Click on an issue from the list to view its details, code snippet, and recommended solution.
                </p>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export default IssuesList
