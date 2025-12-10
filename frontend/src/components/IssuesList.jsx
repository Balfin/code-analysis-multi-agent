import { useState, useEffect } from 'react'
import { Shield, Gauge, Boxes, Filter, ChevronRight, AlertTriangle, FileCode } from 'lucide-react'

// Sample issues for development (will be replaced with API data)
const sampleIssues = [
  {
    id: 'abc123def456',
    title: 'SQL Injection Vulnerability',
    type: 'security',
    risk_level: 'critical',
    location: 'auth.py:15',
    description: 'User input is directly interpolated into SQL query without sanitization.',
  },
  {
    id: 'def456ghi789',
    title: 'Hardcoded API Key',
    type: 'security',
    risk_level: 'high',
    location: 'config.py:8',
    description: 'API key is hardcoded in source code instead of using environment variables.',
  },
  {
    id: 'ghi789jkl012',
    title: 'N+1 Query Pattern',
    type: 'performance',
    risk_level: 'medium',
    location: 'api.py:42',
    description: 'Loop performs individual database queries, causing N+1 query problem.',
  },
  {
    id: 'jkl012mno345',
    title: 'Missing Error Handling',
    type: 'architecture',
    risk_level: 'low',
    location: 'utils.py:23',
    description: 'Function does not handle potential exceptions from file operations.',
  },
]

function IssuesList({ onSelectIssue }) {
  const [issues, setIssues] = useState(sampleIssues)
  const [selectedId, setSelectedId] = useState(null)
  const [typeFilter, setTypeFilter] = useState('all')
  const [riskFilter, setRiskFilter] = useState('all')

  const filteredIssues = issues.filter((issue) => {
    if (typeFilter !== 'all' && issue.type !== typeFilter) return false
    if (riskFilter !== 'all' && issue.risk_level !== riskFilter) return false
    return true
  })

  const selectedIssue = issues.find((i) => i.id === selectedId)

  const handleSelect = (issue) => {
    setSelectedId(issue.id)
    onSelectIssue?.(issue)
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

  return (
    <div className="flex gap-6 h-[calc(100vh-200px)] animate-fade-in">
      {/* Issues List Panel */}
      <div className="w-1/2 flex flex-col">
        {/* Filters */}
        <div className="card p-4 mb-4">
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2 text-zinc-400">
              <Filter className="w-4 h-4" />
              <span className="text-sm">Filters:</span>
            </div>
            
            {/* Type Filter */}
            <select
              value={typeFilter}
              onChange={(e) => setTypeFilter(e.target.value)}
              className="input text-sm py-1.5 w-auto"
            >
              <option value="all">All Types</option>
              <option value="security">Security</option>
              <option value="performance">Performance</option>
              <option value="architecture">Architecture</option>
            </select>

            {/* Risk Filter */}
            <select
              value={riskFilter}
              onChange={(e) => setRiskFilter(e.target.value)}
              className="input text-sm py-1.5 w-auto"
            >
              <option value="all">All Risks</option>
              <option value="critical">Critical</option>
              <option value="high">High</option>
              <option value="medium">Medium</option>
              <option value="low">Low</option>
            </select>

            <span className="text-xs text-zinc-500 ml-auto">
              {filteredIssues.length} issues
            </span>
          </div>
        </div>

        {/* Issues List */}
        <div className="card flex-1 overflow-hidden">
          <div className="h-full overflow-y-auto">
            {filteredIssues.length === 0 ? (
              <div className="p-8 text-center">
                <AlertTriangle className="w-8 h-8 text-zinc-600 mx-auto mb-2" />
                <p className="text-zinc-500">No issues match your filters</p>
              </div>
            ) : (
              filteredIssues.map((issue) => (
                <button
                  key={issue.id}
                  onClick={() => handleSelect(issue)}
                  className={`
                    w-full p-4 text-left border-b border-zinc-800 last:border-b-0
                    transition-colors duration-150
                    ${selectedId === issue.id 
                      ? 'bg-zinc-800' 
                      : 'hover:bg-zinc-800/50'
                    }
                  `}
                >
                  <div className="flex items-start gap-3">
                    <div className={`p-2 rounded-lg ${getTypeColor(issue.type)}`}>
                      {getTypeIcon(issue.type)}
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-1">
                        <h3 className="font-medium text-zinc-200 truncate">
                          {issue.title}
                        </h3>
                        <span className={`badge ${getRiskBadge(issue.risk_level)}`}>
                          {issue.risk_level}
                        </span>
                      </div>
                      <div className="flex items-center gap-2 text-sm text-zinc-500">
                        <FileCode className="w-3 h-3" />
                        <span className="font-mono">{issue.location}</span>
                      </div>
                    </div>
                    <ChevronRight className={`w-4 h-4 text-zinc-600 transition-transform ${selectedId === issue.id ? 'rotate-90' : ''}`} />
                  </div>
                </button>
              ))
            )}
          </div>
        </div>
      </div>

      {/* Issue Detail Panel */}
      <div className="w-1/2">
        <div className="card h-full overflow-hidden">
          {selectedIssue ? (
            <div className="h-full overflow-y-auto p-6">
              {/* Header */}
              <div className="flex items-start gap-4 mb-6">
                <div className={`p-3 rounded-lg ${getTypeColor(selectedIssue.type)}`}>
                  {getTypeIcon(selectedIssue.type)}
                </div>
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-2">
                    <span className={`badge ${getRiskBadge(selectedIssue.risk_level)}`}>
                      {selectedIssue.risk_level}
                    </span>
                    <span className="badge badge-secondary capitalize">
                      {selectedIssue.type}
                    </span>
                  </div>
                  <h2 className="text-xl font-semibold text-zinc-100">
                    {selectedIssue.title}
                  </h2>
                </div>
              </div>

              {/* Location */}
              <div className="mb-6">
                <h3 className="text-sm font-medium text-zinc-400 mb-2">Location</h3>
                <div className="flex items-center gap-2 text-zinc-300">
                  <FileCode className="w-4 h-4 text-zinc-500" />
                  <code className="font-mono bg-zinc-800 px-2 py-1 rounded">
                    {selectedIssue.location}
                  </code>
                </div>
              </div>

              {/* Description */}
              <div className="mb-6">
                <h3 className="text-sm font-medium text-zinc-400 mb-2">Description</h3>
                <p className="text-zinc-300 leading-relaxed">
                  {selectedIssue.description}
                </p>
              </div>

              {/* Issue ID */}
              <div className="mt-auto pt-6 border-t border-zinc-800">
                <p className="text-xs text-zinc-600">
                  Issue ID: <code className="font-mono">{selectedIssue.id}</code>
                </p>
              </div>
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
                  Click on an issue from the list to view its details and recommendations.
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

