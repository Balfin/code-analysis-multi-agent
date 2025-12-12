import { useState, useEffect } from 'react'
import { 
  FileText, 
  Loader2, 
  Download, 
  AlertCircle, 
  Info,
  ChevronDown,
  Sparkles
} from 'lucide-react'
import apiClient from '../api/client'

const DEFAULT_PROMPT = `Generate a comprehensive summary of all code issues found in the analysis. Include: 1) Executive summary with total issues and health score, 2) Critical and high-risk issues prioritized, 3) Breakdown by type (security, performance, architecture), 4) Detailed descriptions and solutions for top issues, 5) Recommendations for improvement. Format the output clearly with sections and bullet points.`

function ReportGenerator() {
  const [prompt, setPrompt] = useState(DEFAULT_PROMPT)
  const [selectedModel, setSelectedModel] = useState(null)
  const [availableModels, setAvailableModels] = useState([])
  const [isLoadingModels, setIsLoadingModels] = useState(false)
  const [isGenerating, setIsGenerating] = useState(false)
  const [error, setError] = useState(null)
  const [generatedFiles, setGeneratedFiles] = useState([])

  // Fetch available models on mount
  useEffect(() => {
    const fetchModels = async () => {
      setIsLoadingModels(true)
      try {
        const response = await apiClient.getModels()
        if (response.models && Array.isArray(response.models)) {
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

  const handleGenerate = async () => {
    if (!prompt.trim() || isGenerating) return

    setIsGenerating(true)
    setError(null)
    setGeneratedFiles([])

    try {
      const response = await apiClient.generateReport(prompt, selectedModel)
      if (response.files && response.files.length > 0) {
        setGeneratedFiles(response.files)
      } else {
        setError('No files were generated. Make sure to include format keywords (pdf, doc, or md) in your prompt.')
      }
    } catch (err) {
      setError(err.message || 'Failed to generate report')
    } finally {
      setIsGenerating(false)
    }
  }

  const handleDownload = (file) => {
    const url = file.url.startsWith('http') 
      ? file.url 
      : `${import.meta.env.VITE_API_URL || 'http://localhost:8000'}${file.url}`
    
    window.open(url, '_blank')
  }

  return (
    <div className="flex flex-col h-[calc(100vh-200px)] animate-fade-in">
      <div className="card flex-1 overflow-hidden flex flex-col">
        {/* Header */}
        <div className="border-b border-zinc-800 p-4">
          <div className="flex items-center gap-3">
            <div className="flex items-center justify-center w-10 h-10 rounded-lg bg-gradient-to-br from-indigo-500/20 to-purple-500/20">
              <FileText className="w-5 h-5 text-indigo-400" />
            </div>
            <div>
              <h2 className="text-lg font-semibold text-zinc-100">Generate Report</h2>
              <p className="text-sm text-zinc-500">Create comprehensive reports of code analysis issues</p>
            </div>
          </div>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {/* Prompt Section */}
          <div className="space-y-3">
            <label className="text-sm font-medium text-zinc-300 flex items-center gap-2">
              <Sparkles className="w-4 h-4 text-indigo-400" />
              Report Prompt
            </label>
            <textarea
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              placeholder="Enter your report generation prompt..."
              rows={8}
              className="input resize-none w-full font-mono text-sm"
              disabled={isGenerating}
            />
            
            {/* Format Hint */}
            <div className="card p-3 border-indigo-800/50 bg-indigo-950/20">
              <div className="flex items-start gap-2 text-sm">
                <Info className="w-4 h-4 text-indigo-400 flex-shrink-0 mt-0.5" />
                <div className="text-zinc-400">
                  <span className="font-medium text-indigo-300">Format Hint:</span>{' '}
                  Include 'pdf', 'doc', or 'md' in your prompt to generate files in those formats (e.g., 'generate pdf report' or 'in pdf format')
                </div>
              </div>
            </div>
          </div>

          {/* Model Selector */}
          <div className="space-y-3">
            <label className="text-sm font-medium text-zinc-300">Model</label>
            <div className="relative isolate">
              <select
                value={selectedModel || 'default'}
                onChange={(e) => setSelectedModel(e.target.value === 'default' ? null : e.target.value)}
                disabled={isLoadingModels || isGenerating}
                className="input text-sm pr-8 appearance-none cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed w-full bg-zinc-900"
              >
                <option value="default">Default</option>
                {availableModels.map((model) => (
                  <option key={model} value={model}>
                    {model}
                  </option>
                ))}
              </select>
              <div className="absolute inset-y-0 right-0 flex items-center pr-2 pointer-events-none">
                <ChevronDown className="w-4 h-4 text-zinc-400" />
              </div>
            </div>
          </div>

          {/* Error Display */}
          {error && (
            <div className="card p-4 border-red-800/50 bg-red-950/20">
              <div className="flex items-center gap-2 text-sm text-red-400">
                <AlertCircle className="w-4 h-4 flex-shrink-0" />
                <span>{error}</span>
              </div>
            </div>
          )}

          {/* Generated Files */}
          {generatedFiles.length > 0 && (
            <div className="space-y-3">
              <label className="text-sm font-medium text-zinc-300 flex items-center gap-2">
                <Download className="w-4 h-4 text-indigo-400" />
                Generated Files
              </label>
              <div className="space-y-2">
                {generatedFiles.map((file, idx) => (
                  <div
                    key={idx}
                    className="card p-4 border-zinc-800 hover:border-indigo-800/50 transition-colors"
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        <div className="flex items-center justify-center w-10 h-10 rounded-lg bg-zinc-800">
                          <FileText className="w-5 h-5 text-indigo-400" />
                        </div>
                        <div>
                          <div className="text-sm font-medium text-zinc-200">{file.filename}</div>
                          <div className="text-xs text-zinc-500">
                            Format: {file.format.toUpperCase()}
                            {file.size && ` • ${(file.size / 1024).toFixed(1)} KB`}
                          </div>
                        </div>
                      </div>
                      <button
                        onClick={() => handleDownload(file)}
                        className="btn btn-primary flex items-center gap-2"
                      >
                        <Download className="w-4 h-4" />
                        Download
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Footer with Generate Button */}
        <div className="border-t border-zinc-800 p-4">
          <button
            onClick={handleGenerate}
            disabled={!prompt.trim() || isGenerating}
            className={`
              w-full btn btn-primary flex items-center justify-center gap-2
              disabled:opacity-50 disabled:cursor-not-allowed
            `}
          >
            {isGenerating ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                Generating Report...
              </>
            ) : (
              <>
                <FileText className="w-4 h-4" />
                Generate Report
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  )
}

export default ReportGenerator
