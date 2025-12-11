import { useState, useEffect } from 'react'
import { 
  FolderSearch, 
  Play, 
  Loader2, 
  Shield, 
  Gauge, 
  Boxes, 
  AlertCircle, 
  CheckCircle,
  TrendingUp,
  FileCode,
  Clock,
  RefreshCw,
  XCircle,
  Activity,
  Trash2,
  ChevronDown
} from 'lucide-react'
import apiClient from '../api/client'

function AnalysisDashboard() {
  const [path, setPath] = useState('')
  const [isAnalyzing, setIsAnalyzing] = useState(false)
  const [progress, setProgress] = useState(0)
  const [currentStatus, setCurrentStatus] = useState('')
  const [results, setResults] = useState(null)
  const [error, setError] = useState(null)
  const [taskId, setTaskId] = useState(null)
  const [analysisMode, setAnalysisMode] = useState('sync') // 'sync' or 'async'
  const [lastAnalyzedPath, setLastAnalyzedPath] = useState('')
  const [isClearing, setIsClearing] = useState(false)
  const [clearMessage, setClearMessage] = useState(null)
  const [availableModels, setAvailableModels] = useState([])
  const [selectedModel, setSelectedModel] = useState('')
  const [isLoadingModels, setIsLoadingModels] = useState(false)

  // Poll for async task status
  useEffect(() => {
    let pollInterval = null
    
    if (taskId && isAnalyzing) {
      pollInterval = setInterval(async () => {
        try {
          const status = await apiClient.getAnalysisStatus(taskId)
          
          if (status.status === 'completed') {
            setIsAnalyzing(false)
            setTaskId(null)
            setProgress(100)
            
            // Determine health score with proper fallback
            const healthScore = status.health_score !== undefined 
              ? status.health_score 
              : (status.issues_found === 0 ? 100 : 50)
            
            setResults({
              total: status.issues_found || 0,
              security: 0, // Will be updated by fetching summary
              performance: 0,
              architecture: 0,
              healthScore,
              filesAnalyzed: status.files_analyzed || 0,
              summary: status.summary || 'Analysis complete.',
            })
            
            // Fetch detailed summary
            fetchIssueSummary()
          } else if (status.status === 'error') {
            setIsAnalyzing(false)
            setTaskId(null)
            setError(status.error || 'Analysis failed')
          } else if (status.status === 'running') {
            setProgress(prev => status.progress ?? prev)
            setCurrentStatus('Analysis in progress...')
          }
        } catch (err) {
          console.error('Poll error:', err)
        }
      }, 2000) // Poll every 2 seconds
    }

    return () => {
      if (pollInterval) clearInterval(pollInterval)
    }
  }, [taskId, isAnalyzing])

  // Fetch available models on mount
  useEffect(() => {
    const fetchModels = async () => {
      setIsLoadingModels(true)
      try {
        const response = await apiClient.getModels()
        if (response.models && response.models.length > 0) {
          setAvailableModels(response.models)
        }
      } catch (err) {
        console.error('Failed to fetch models:', err)
      } finally {
        setIsLoadingModels(false)
      }
    }
    fetchModels()
  }, [])

  // Restore analysis results on mount if issues exist
  useEffect(() => {
    const restoreResults = async () => {
      try {
        const summary = await apiClient.getIssuesSummary()
        
        if (summary.total > 0) {
          // Try to get analyzed path from issues
          let analyzedPath = ''
          try {
            const issuesResponse = await apiClient.getIssues({ page: 1, pageSize: 1 })
            if (issuesResponse.issues && issuesResponse.issues.length > 0) {
              const location = issuesResponse.issues[0].location || ''
              // Extract directory path if location contains a path
              // (e.g., "../example_projects/example_python/file.py:15" -> "../example_projects/example_python")
              const pathMatch = location.match(/^(.+)\/[^/]+:\d+$/)
              if (pathMatch) {
                analyzedPath = pathMatch[1]
              }
            }
          } catch (err) {
            // Ignore errors when fetching path
            console.error('Failed to extract path from issues:', err)
          }
          
          // Calculate health score
          const critical = summary.by_risk_level?.critical || 0
          const high = summary.by_risk_level?.high || 0
          const medium = summary.by_risk_level?.medium || 0
          const low = summary.by_risk_level?.low || 0
          
          let calculatedHealth = 100
          calculatedHealth -= Math.min(critical * 15, 60)
          calculatedHealth -= Math.min(high * 8, 40)
          calculatedHealth -= Math.min(medium * 3, 30)
          calculatedHealth -= Math.min(low * 1, 10)
          calculatedHealth = Math.max(0, Math.min(100, calculatedHealth))
          
          // Get files analyzed count (approximate from total issues or use a default)
          // Note: We don't have exact files_analyzed count from summary, so we'll use a reasonable default
          const filesAnalyzed = Math.max(1, Math.ceil(summary.total / 10)) // Rough estimate
          
          setResults({
            total: summary.total,
            security: summary.by_type?.security || 0,
            performance: summary.by_type?.performance || 0,
            architecture: summary.by_type?.architecture || 0,
            healthScore: calculatedHealth,
            filesAnalyzed: filesAnalyzed,
            summary: `Found ${summary.total} issues in previously analyzed codebase.`,
          })
          
          if (analyzedPath) {
            setLastAnalyzedPath(analyzedPath)
          }
        }
      } catch (err) {
        // Silently fail - don't break UI if summary fetch fails
        console.error('Failed to restore analysis results:', err)
      }
    }
    
    restoreResults()
  }, []) // Only run on mount

  const fetchIssueSummary = async () => {
    try {
      const summary = await apiClient.getIssuesSummary()
      
      // Get issue counts by severity
      const critical = summary.by_risk_level?.critical || 0
      const high = summary.by_risk_level?.high || 0
      const medium = summary.by_risk_level?.medium || 0
      const low = summary.by_risk_level?.low || 0
      
      // Calculate health score from actual issue counts (same formula as backend)
      let calculatedHealth = 100
      calculatedHealth -= Math.min(critical * 15, 60)
      calculatedHealth -= Math.min(high * 8, 40)
      calculatedHealth -= Math.min(medium * 3, 30)
      calculatedHealth -= Math.min(low * 1, 10)
      calculatedHealth = Math.max(0, Math.min(100, calculatedHealth))
      
      setResults(prev => prev ? {
        ...prev,
        security: summary.by_type?.security || 0,
        performance: summary.by_type?.performance || 0,
        architecture: summary.by_type?.architecture || 0,
        criticalCount: critical,
        highCount: high,
        mediumCount: medium,
        lowCount: low,
        // Update health score if we have actual issue data
        healthScore: summary.total > 0 || prev.healthScore === 0 ? calculatedHealth : prev.healthScore,
      } : null)
    } catch (err) {
      console.error('Failed to fetch summary:', err)
    }
  }

  const handleAnalyze = async () => {
    if (!path.trim()) {
      setError('Please enter a path to analyze')
      return
    }

    setIsAnalyzing(true)
    setError(null)
    setResults(null)
    setProgress(0)
    setCurrentStatus('Starting analysis...')
    setLastAnalyzedPath(path)

    try {
      // Build analysis options with selected model
      const analysisOptions = {
        asyncMode: analysisMode === 'async',
        model: selectedModel || undefined,  // Only pass if selected
      }

      if (analysisMode === 'async') {
        // Async mode - start and poll
        const response = await apiClient.startAnalysis(path, analysisOptions)
        setTaskId(response.task_id)
        setCurrentStatus('Analysis started, monitoring progress...')
        setProgress(10)
      } else {
        // Sync mode - wait for completion
        setProgress(20)
        setCurrentStatus('Discovering files...')
        
        // Simulate progress during sync request
        const progressInterval = setInterval(() => {
          setProgress(prev => Math.min(prev + 10, 90))
        }, 1000)

        const response = await apiClient.startAnalysis(path, analysisOptions)
        
        clearInterval(progressInterval)
        setProgress(100)
        setCurrentStatus('Analysis complete!')
        setIsAnalyzing(false)

        // Use health score from response, or parse from summary as fallback
        const healthMatch = response.summary?.match(/Health Score:\s*(\d+)/i)
        const parsedHealthScore = healthMatch ? parseInt(healthMatch[1]) : null
        
        // Determine health score: use response value, parsed value, or default to 100 if no issues
        const healthScore = response.health_score !== undefined 
          ? response.health_score 
          : (parsedHealthScore !== null 
              ? parsedHealthScore 
              : (response.issues_found === 0 ? 100 : 50))

        setResults({
          total: response.issues_found || 0,
          security: 0,
          performance: 0,
          architecture: 0,
          healthScore,
          filesAnalyzed: response.files_analyzed || 0,
          summary: response.summary || 'Analysis complete.',
          rawSummary: response.summary,
        })

        // Fetch detailed summary
        await fetchIssueSummary()
      }
    } catch (err) {
      setIsAnalyzing(false)
      setTaskId(null)
      
      if (err.status === 400) {
        setError(`Invalid path: ${err.data?.detail || 'Path does not exist'}`)
      } else if (err.status === 0) {
        setError('Cannot connect to backend. Make sure the server is running on http://localhost:8000')
      } else {
        setError(err.message || 'Analysis failed. Please try again.')
      }
    }
  }

  const handleCancel = () => {
    setIsAnalyzing(false)
    setTaskId(null)
    setProgress(0)
    setCurrentStatus('')
  }

  const getHealthGrade = (score) => {
    if (score >= 90) return { grade: 'A', color: 'text-green-400', bgColor: 'bg-green-500', label: 'Excellent' }
    if (score >= 80) return { grade: 'B', color: 'text-green-500', bgColor: 'bg-green-500', label: 'Good' }
    if (score >= 70) return { grade: 'C', color: 'text-yellow-400', bgColor: 'bg-yellow-500', label: 'Acceptable' }
    if (score >= 60) return { grade: 'D', color: 'text-orange-400', bgColor: 'bg-orange-500', label: 'Needs Work' }
    return { grade: 'F', color: 'text-red-400', bgColor: 'bg-red-500', label: 'Critical' }
  }

  const handleClearIssues = async () => {
    if (!confirm('Are you sure you want to clear all issues? This action cannot be undone.')) {
      return
    }

    setIsClearing(true)
    setClearMessage(null)

    try {
      const response = await apiClient.clearAllIssues()
      setClearMessage({
        type: 'success',
        text: response.message || `Cleared ${response.deleted_count} issues`
      })
      // Reset results since issues are cleared
      setResults(null)
    } catch (err) {
      setClearMessage({
        type: 'error',
        text: err.message || 'Failed to clear issues'
      })
    } finally {
      setIsClearing(false)
      // Clear message after 5 seconds
      setTimeout(() => setClearMessage(null), 5000)
    }
  }

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Input Section */}
      <div className="card p-6">
        <div className="flex items-center gap-3 mb-4">
          <div className="flex items-center justify-center w-10 h-10 rounded-lg bg-indigo-500/20">
            <FolderSearch className="w-5 h-5 text-indigo-400" />
          </div>
          <div>
            <h2 className="text-lg font-semibold text-zinc-100">Analyze Codebase</h2>
            <p className="text-sm text-zinc-500">Enter the path to your project directory</p>
          </div>
        </div>

        <div className="flex flex-col gap-3">
          <div className="flex flex-col sm:flex-row gap-3">
            <input
              type="text"
              value={path}
              onChange={(e) => setPath(e.target.value)}
              placeholder="../example_projects/example_python"
              className="input flex-1 font-mono text-sm"
              disabled={isAnalyzing}
              onKeyDown={(e) => e.key === 'Enter' && !isAnalyzing && handleAnalyze()}
            />
            
            {/* Model Selector */}
            {availableModels.length > 0 && (
              <div className="relative min-w-[180px]">
                <select
                  value={selectedModel}
                  onChange={(e) => setSelectedModel(e.target.value)}
                  className="w-full appearance-none bg-zinc-800 border border-zinc-700 text-zinc-300 text-sm rounded-lg px-3 py-2.5 pr-8 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent cursor-pointer"
                  disabled={isAnalyzing}
                >
                  <option value="">Default Model</option>
                  {availableModels.map((model) => (
                    <option key={model} value={model}>
                      {model}
                    </option>
                  ))}
                </select>
                <ChevronDown className="absolute right-2 top-1/2 -translate-y-1/2 w-4 h-4 text-zinc-500 pointer-events-none" />
              </div>
            )}
          </div>
          
          <div className="flex gap-2">
            {isAnalyzing ? (
              <button
                onClick={handleCancel}
                className="btn btn-secondary flex items-center gap-2 min-w-[120px] justify-center"
              >
                <XCircle className="w-4 h-4" />
                Cancel
              </button>
            ) : (
              <button
                onClick={handleAnalyze}
                disabled={isAnalyzing}
                className="btn btn-primary flex items-center gap-2 min-w-[140px] justify-center"
              >
                <Play className="w-4 h-4" />
                Start Analysis
              </button>
            )}
            <button
              onClick={handleClearIssues}
              disabled={isAnalyzing || isClearing}
              className="btn btn-secondary flex items-center gap-2 hover:bg-red-950/50 hover:border-red-800/50 hover:text-red-400 transition-colors"
              title="Clear all issues"
            >
              {isClearing ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <Trash2 className="w-4 h-4" />
              )}
              Clear Issues
            </button>
          </div>
        </div>

        {/* Quick paths */}
        <div className="mt-3 flex flex-wrap gap-2">
          <span className="text-xs text-zinc-500">Quick paths:</span>
          {['../example_projects/example_python', './'].map((quickPath) => (
            <button
              key={quickPath}
              onClick={() => setPath(quickPath)}
              className="text-xs text-indigo-400 hover:text-indigo-300 font-mono bg-zinc-800 px-2 py-1 rounded"
              disabled={isAnalyzing}
            >
              {quickPath}
            </button>
          ))}
        </div>

        {error && (
          <div className="mt-4 flex items-start gap-2 text-red-400 text-sm bg-red-950/30 border border-red-900/50 rounded-lg px-4 py-3">
            <AlertCircle className="w-4 h-4 flex-shrink-0 mt-0.5" />
            <div>
              <p className="font-medium">Analysis Error</p>
              <p className="text-red-400/80">{error}</p>
            </div>
          </div>
        )}

        {clearMessage && (
          <div className={`mt-4 flex items-start gap-2 text-sm rounded-lg px-4 py-3 ${
            clearMessage.type === 'success' 
              ? 'text-green-400 bg-green-950/30 border border-green-900/50' 
              : 'text-red-400 bg-red-950/30 border border-red-900/50'
          }`}>
            {clearMessage.type === 'success' ? (
              <CheckCircle className="w-4 h-4 flex-shrink-0 mt-0.5" />
            ) : (
              <AlertCircle className="w-4 h-4 flex-shrink-0 mt-0.5" />
            )}
            <div>
              <p className="font-medium">{clearMessage.type === 'success' ? 'Issues Cleared' : 'Clear Failed'}</p>
              <p className={clearMessage.type === 'success' ? 'text-green-400/80' : 'text-red-400/80'}>
                {clearMessage.text}
              </p>
            </div>
          </div>
        )}
      </div>

      {/* Progress Section */}
      {isAnalyzing && (
        <div className="card p-6 animate-slide-up border-indigo-800/30">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-3">
              <Loader2 className="w-5 h-5 text-indigo-400 animate-spin" />
              <span className="text-zinc-300 font-medium">Analysis in progress...</span>
            </div>
            <span className="text-sm text-zinc-500">{progress}%</span>
          </div>
          
          {/* Progress bar */}
          <div className="w-full bg-zinc-800 rounded-full h-2 mb-4 overflow-hidden">
            <div 
              className="bg-gradient-to-r from-indigo-600 to-purple-500 h-2 rounded-full transition-all duration-500"
              style={{ width: `${progress}%` }}
            />
          </div>
          
          {/* Current status */}
          <div className="flex items-center gap-2 text-sm text-zinc-500">
            <Activity className="w-4 h-4 animate-pulse" />
            <span>{currentStatus}</span>
          </div>

          {taskId && (
            <div className="mt-2 text-xs text-zinc-600">
              Task ID: <code className="font-mono">{taskId}</code>
            </div>
          )}
        </div>
      )}

      {/* Results Section */}
      {results && !isAnalyzing && (
        <div className="space-y-6 animate-slide-up">
          {/* Summary Card */}
          <div className="card p-6 border-green-800/30 bg-gradient-to-r from-green-950/20 to-zinc-900">
            <div className="flex flex-col lg:flex-row lg:items-start justify-between gap-4">
              <div className="flex items-center gap-3">
                <div className="flex items-center justify-center w-10 h-10 rounded-lg bg-green-500/20">
                  <CheckCircle className="w-5 h-5 text-green-400" />
                </div>
                <div>
                  <h3 className="text-lg font-semibold text-zinc-100">Analysis Complete</h3>
                  <p className="text-sm text-zinc-400">
                    Analyzed {results.filesAnalyzed} files, found {results.total} issues
                  </p>
                </div>
              </div>
              
              <div className="flex items-center gap-3">
                {/* Model Selector */}
                {availableModels.length > 0 && (
                  <div className="relative">
                    <select
                      value={selectedModel}
                      onChange={(e) => setSelectedModel(e.target.value)}
                      className="appearance-none bg-zinc-800 border border-zinc-700 text-zinc-300 text-sm rounded-lg px-3 py-2 pr-8 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent cursor-pointer"
                      disabled={isAnalyzing}
                    >
                      <option value="">Default Model</option>
                      {availableModels.map((model) => (
                        <option key={model} value={model}>
                          {model}
                        </option>
                      ))}
                    </select>
                    <ChevronDown className="absolute right-2 top-1/2 -translate-y-1/2 w-4 h-4 text-zinc-500 pointer-events-none" />
                  </div>
                )}
                
                <button
                  onClick={handleAnalyze}
                  className="btn btn-secondary flex items-center gap-2"
                  title="Re-run analysis"
                >
                  <RefreshCw className="w-4 h-4" />
                  Re-analyze
                </button>
              </div>
            </div>

            {/* Quick Stats */}
            <div className="mt-6 flex flex-wrap items-center gap-4 text-sm">
              <div className="flex items-center gap-2">
                <FileCode className="w-4 h-4 text-zinc-500" />
                <span className="text-zinc-400">{results.filesAnalyzed} files analyzed</span>
              </div>
              <div className="flex items-center gap-2">
                <AlertCircle className="w-4 h-4 text-zinc-500" />
                <span className="text-zinc-400">{results.total} total issues</span>
              </div>
              <div className="flex items-center gap-2">
                <FolderSearch className="w-4 h-4 text-zinc-500" />
                <span className="text-zinc-400 font-mono text-xs">{lastAnalyzedPath}</span>
              </div>
            </div>
          </div>

          {/* Stats Grid - By Type */}
          <div>
            <h4 className="text-sm font-medium text-zinc-400 mb-3 flex items-center gap-2">
              <TrendingUp className="w-4 h-4" />
              Issues by Category
            </h4>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {/* Security */}
              <div className="card p-5 hover:border-red-800/50 transition-colors group cursor-pointer">
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center gap-3">
                    <div className="flex items-center justify-center w-10 h-10 rounded-lg bg-red-500/20 group-hover:bg-red-500/30 transition-colors">
                      <Shield className="w-5 h-5 text-red-400" />
                    </div>
                    <span className="font-medium text-zinc-300">Security</span>
                  </div>
                  <span className="text-2xl font-bold text-red-400">{results.security}</span>
                </div>
                <p className="text-sm text-zinc-500">Vulnerabilities and security risks</p>
                {results.total > 0 && (
                  <div className="mt-3 w-full bg-zinc-800 rounded-full h-1.5">
                    <div 
                      className="bg-red-500 h-1.5 rounded-full transition-all duration-500" 
                      style={{ width: `${(results.security / results.total) * 100}%` }}
                    />
                  </div>
                )}
              </div>

              {/* Performance */}
              <div className="card p-5 hover:border-amber-800/50 transition-colors group cursor-pointer">
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center gap-3">
                    <div className="flex items-center justify-center w-10 h-10 rounded-lg bg-amber-500/20 group-hover:bg-amber-500/30 transition-colors">
                      <Gauge className="w-5 h-5 text-amber-400" />
                    </div>
                    <span className="font-medium text-zinc-300">Performance</span>
                  </div>
                  <span className="text-2xl font-bold text-amber-400">{results.performance}</span>
                </div>
                <p className="text-sm text-zinc-500">Performance bottlenecks</p>
                {results.total > 0 && (
                  <div className="mt-3 w-full bg-zinc-800 rounded-full h-1.5">
                    <div 
                      className="bg-amber-500 h-1.5 rounded-full transition-all duration-500" 
                      style={{ width: `${(results.performance / results.total) * 100}%` }}
                    />
                  </div>
                )}
              </div>

              {/* Architecture */}
              <div className="card p-5 hover:border-blue-800/50 transition-colors group cursor-pointer">
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center gap-3">
                    <div className="flex items-center justify-center w-10 h-10 rounded-lg bg-blue-500/20 group-hover:bg-blue-500/30 transition-colors">
                      <Boxes className="w-5 h-5 text-blue-400" />
                    </div>
                    <span className="font-medium text-zinc-300">Architecture</span>
                  </div>
                  <span className="text-2xl font-bold text-blue-400">{results.architecture}</span>
                </div>
                <p className="text-sm text-zinc-500">Design patterns and quality</p>
                {results.total > 0 && (
                  <div className="mt-3 w-full bg-zinc-800 rounded-full h-1.5">
                    <div 
                      className="bg-blue-500 h-1.5 rounded-full transition-all duration-500" 
                      style={{ width: `${(results.architecture / results.total) * 100}%` }}
                    />
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* View Issues CTA */}
          <div className="card p-6 bg-gradient-to-r from-indigo-950/30 to-zinc-900 border-indigo-800/30">
            <div className="flex items-center justify-between">
              <div>
                <h4 className="font-medium text-zinc-200">Ready to review issues?</h4>
                <p className="text-sm text-zinc-500">Browse all {results.total} issues in the Issues tab</p>
              </div>
              <div className="flex items-center gap-2 text-indigo-400">
                <span className="text-sm">Go to Issues</span>
                <Shield className="w-4 h-4" />
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Empty State */}
      {!isAnalyzing && !results && (
        <div className="card p-12 text-center">
          <div className="flex justify-center mb-4">
            <div className="flex items-center justify-center w-20 h-20 rounded-full bg-gradient-to-br from-zinc-800 to-zinc-900 shadow-inner">
              <FolderSearch className="w-10 h-10 text-zinc-600" />
            </div>
          </div>
          <h3 className="text-xl font-medium text-zinc-300 mb-2">No Analysis Yet</h3>
          <p className="text-sm text-zinc-500 max-w-md mx-auto mb-6">
            Enter the path to your codebase above and click "Start Analysis" to begin 
            scanning for security, performance, and architecture issues.
          </p>
          <div className="flex flex-wrap justify-center gap-4 text-xs text-zinc-600">
            <span className="flex items-center gap-1.5 bg-zinc-800/50 px-3 py-1.5 rounded-full">
              <Shield className="w-3 h-3 text-red-500" /> SQL Injection
            </span>
            <span className="flex items-center gap-1.5 bg-zinc-800/50 px-3 py-1.5 rounded-full">
              <Shield className="w-3 h-3 text-red-500" /> Hardcoded Secrets
            </span>
            <span className="flex items-center gap-1.5 bg-zinc-800/50 px-3 py-1.5 rounded-full">
              <Gauge className="w-3 h-3 text-amber-500" /> N+1 Queries
            </span>
            <span className="flex items-center gap-1.5 bg-zinc-800/50 px-3 py-1.5 rounded-full">
              <Boxes className="w-3 h-3 text-blue-500" /> Code Smells
            </span>
          </div>
        </div>
      )}
    </div>
  )
}

export default AnalysisDashboard
