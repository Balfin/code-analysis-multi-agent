import { useState } from 'react'
import { FolderSearch, Play, Loader2, Shield, Gauge, Boxes, AlertCircle, CheckCircle } from 'lucide-react'

function AnalysisDashboard() {
  const [path, setPath] = useState('')
  const [isAnalyzing, setIsAnalyzing] = useState(false)
  const [results, setResults] = useState(null)
  const [error, setError] = useState(null)

  const handleAnalyze = async () => {
    if (!path.trim()) {
      setError('Please enter a path to analyze')
      return
    }

    setIsAnalyzing(true)
    setError(null)
    setResults(null)

    // TODO: Implement actual API call in Phase 7
    // Simulating analysis for now
    setTimeout(() => {
      setIsAnalyzing(false)
      setResults({
        total: 12,
        security: 4,
        performance: 5,
        architecture: 3,
        summary: 'Analysis complete. Found 12 issues across 3 categories.',
      })
    }, 2000)
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

        <div className="flex gap-3">
          <input
            type="text"
            value={path}
            onChange={(e) => setPath(e.target.value)}
            placeholder="./path/to/your/project"
            className="input flex-1"
            disabled={isAnalyzing}
          />
          <button
            onClick={handleAnalyze}
            disabled={isAnalyzing}
            className="btn btn-primary flex items-center gap-2 min-w-[140px] justify-center"
          >
            {isAnalyzing ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                Analyzing...
              </>
            ) : (
              <>
                <Play className="w-4 h-4" />
                Start Analysis
              </>
            )}
          </button>
        </div>

        {error && (
          <div className="mt-4 flex items-center gap-2 text-red-400 text-sm">
            <AlertCircle className="w-4 h-4" />
            {error}
          </div>
        )}
      </div>

      {/* Progress Section */}
      {isAnalyzing && (
        <div className="card p-6 animate-slide-up">
          <div className="flex items-center gap-3 mb-4">
            <Loader2 className="w-5 h-5 text-indigo-400 animate-spin" />
            <span className="text-zinc-300">Analysis in progress...</span>
          </div>
          <div className="w-full bg-zinc-800 rounded-full h-2">
            <div className="bg-indigo-500 h-2 rounded-full animate-pulse" style={{ width: '60%' }}></div>
          </div>
          <p className="mt-2 text-sm text-zinc-500">Scanning files and identifying issues...</p>
        </div>
      )}

      {/* Results Section */}
      {results && (
        <div className="space-y-6 animate-slide-up">
          {/* Summary */}
          <div className="card p-6 border-green-800/50">
            <div className="flex items-center gap-3">
              <div className="flex items-center justify-center w-10 h-10 rounded-lg bg-green-500/20">
                <CheckCircle className="w-5 h-5 text-green-400" />
              </div>
              <div>
                <h3 className="text-lg font-semibold text-zinc-100">Analysis Complete</h3>
                <p className="text-sm text-zinc-400">{results.summary}</p>
              </div>
            </div>
          </div>

          {/* Stats Grid */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {/* Security */}
            <div className="card p-6 hover:border-red-800/50 transition-colors">
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-3">
                  <div className="flex items-center justify-center w-10 h-10 rounded-lg bg-red-500/20">
                    <Shield className="w-5 h-5 text-red-400" />
                  </div>
                  <span className="font-medium text-zinc-300">Security</span>
                </div>
                <span className="text-2xl font-bold text-red-400">{results.security}</span>
              </div>
              <p className="text-sm text-zinc-500">Vulnerabilities and security risks</p>
            </div>

            {/* Performance */}
            <div className="card p-6 hover:border-amber-800/50 transition-colors">
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-3">
                  <div className="flex items-center justify-center w-10 h-10 rounded-lg bg-amber-500/20">
                    <Gauge className="w-5 h-5 text-amber-400" />
                  </div>
                  <span className="font-medium text-zinc-300">Performance</span>
                </div>
                <span className="text-2xl font-bold text-amber-400">{results.performance}</span>
              </div>
              <p className="text-sm text-zinc-500">Performance bottlenecks and inefficiencies</p>
            </div>

            {/* Architecture */}
            <div className="card p-6 hover:border-blue-800/50 transition-colors">
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-3">
                  <div className="flex items-center justify-center w-10 h-10 rounded-lg bg-blue-500/20">
                    <Boxes className="w-5 h-5 text-blue-400" />
                  </div>
                  <span className="font-medium text-zinc-300">Architecture</span>
                </div>
                <span className="text-2xl font-bold text-blue-400">{results.architecture}</span>
              </div>
              <p className="text-sm text-zinc-500">Design patterns and code quality</p>
            </div>
          </div>

          {/* Total Issues */}
          <div className="card p-6 bg-gradient-to-r from-zinc-900 to-zinc-800">
            <div className="text-center">
              <p className="text-zinc-500 mb-2">Total Issues Found</p>
              <p className="text-5xl font-bold text-zinc-100">{results.total}</p>
            </div>
          </div>
        </div>
      )}

      {/* Empty State */}
      {!isAnalyzing && !results && (
        <div className="card p-12 text-center">
          <div className="flex justify-center mb-4">
            <div className="flex items-center justify-center w-16 h-16 rounded-full bg-zinc-800">
              <FolderSearch className="w-8 h-8 text-zinc-600" />
            </div>
          </div>
          <h3 className="text-lg font-medium text-zinc-400 mb-2">No Analysis Yet</h3>
          <p className="text-sm text-zinc-600 max-w-md mx-auto">
            Enter the path to your codebase above and click "Start Analysis" to begin 
            scanning for security, performance, and architecture issues.
          </p>
        </div>
      )}
    </div>
  )
}

export default AnalysisDashboard

