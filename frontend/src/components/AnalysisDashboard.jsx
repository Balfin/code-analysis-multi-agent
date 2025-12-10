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
  Activity
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
            setResults({
              total: status.issues_found || 0,
              security: 0, // Will be updated by fetching summary
              performance: 0,
              architecture: 0,
              healthScore: status.health_score || 0,
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
            setProgress(status.progress || 50)
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

  const fetchIssueSummary = async () => {
    try {
      const summary = await apiClient.getIssuesSummary()
      setResults(prev => prev ? {
        ...prev,
        security: summary.by_type?.security || 0,
        performance: summary.by_type?.performance || 0,
        architecture: summary.by_type?.architecture || 0,
        criticalCount: summary.by_risk_level?.critical || 0,
        highCount: summary.by_risk_level?.high || 0,
        mediumCount: summary.by_risk_level?.medium || 0,
        lowCount: summary.by_risk_level?.low || 0,
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
      if (analysisMode === 'async') {
        // Async mode - start and poll
        const response = await apiClient.startAnalysis(path, { asyncMode: true })
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

        const response = await apiClient.startAnalysis(path, { asyncMode: false })
        
        clearInterval(progressInterval)
        setProgress(100)
        setCurrentStatus('Analysis complete!')
        setIsAnalyzing(false)

        // Parse the summary to extract health score
        const healthMatch = response.summary?.match(/Health Score:\s*(\d+)/i)
        const healthScore = healthMatch ? parseInt(healthMatch[1]) : 50

        setResults({
          total: response.issues_found || 0,
          security: 0,
          performance: 0,
          architecture: 0,
          healthScore: response.health_score || healthScore,
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
              
              {/* Health Score */}
              <div className="flex items-center gap-4">
                <div className="text-center">
                  <div className="relative w-20 h-20">
                    <svg className="w-20 h-20 transform -rotate-90">
                      <circle
                        cx="40"
                        cy="40"
                        r="36"
                        fill="none"
                        stroke="currentColor"
                        strokeWidth="6"
                        className="text-zinc-800"
                      />
                      <circle
                        cx="40"
                        cy="40"
                        r="36"
                        fill="none"
                        stroke="currentColor"
                        strokeWidth="6"
                        strokeDasharray={`${results.healthScore * 2.26} 226`}
                        className={getHealthGrade(results.healthScore).color}
                        strokeLinecap="round"
                      />
                    </svg>
                    <div className="absolute inset-0 flex flex-col items-center justify-center">
                      <span className={`text-xl font-bold ${getHealthGrade(results.healthScore).color}`}>
                        {results.healthScore}
                      </span>
                    </div>
                  </div>
                  <p className="text-xs text-zinc-500 mt-1">
                    {getHealthGrade(results.healthScore).label}
                  </p>
                </div>

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

          {/* Stats Grid - By Severity */}
          {(results.criticalCount !== undefined) && (
            <div>
              <h4 className="text-sm font-medium text-zinc-400 mb-3 flex items-center gap-2">
                <AlertCircle className="w-4 h-4" />
                Issues by Severity
              </h4>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="card p-4 text-center border-red-900/30 hover:border-red-800/50 transition-colors">
                  <span className="text-3xl font-bold text-red-400">{results.criticalCount || 0}</span>
                  <p className="text-sm text-zinc-500 mt-1">Critical</p>
                </div>
                <div className="card p-4 text-center border-orange-900/30 hover:border-orange-800/50 transition-colors">
                  <span className="text-3xl font-bold text-orange-400">{results.highCount || 0}</span>
                  <p className="text-sm text-zinc-500 mt-1">High</p>
                </div>
                <div className="card p-4 text-center border-yellow-900/30 hover:border-yellow-800/50 transition-colors">
                  <span className="text-3xl font-bold text-yellow-400">{results.mediumCount || 0}</span>
                  <p className="text-sm text-zinc-500 mt-1">Medium</p>
                </div>
                <div className="card p-4 text-center border-green-900/30 hover:border-green-800/50 transition-colors">
                  <span className="text-3xl font-bold text-green-400">{results.lowCount || 0}</span>
                  <p className="text-sm text-zinc-500 mt-1">Low</p>
                </div>
              </div>
            </div>
          )}

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
