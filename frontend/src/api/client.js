/**
 * API Client for Code Analysis Multi-Agent System
 * 
 * Provides methods to interact with the FastAPI backend:
 * - Health check
 * - Code analysis
 * - Issue management
 * - Chat functionality
 */

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

/**
 * Custom error class for API errors
 */
export class APIError extends Error {
  constructor(message, status, data = null) {
    super(message)
    this.name = 'APIError'
    this.status = status
    this.data = data
  }
}

/**
 * Make an API request with error handling
 */
async function apiRequest(endpoint, options = {}) {
  const url = `${API_BASE_URL}${endpoint}`
  
  const config = {
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
    ...options,
  }

  try {
    const response = await fetch(url, config)
    
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}))
      throw new APIError(
        errorData.detail || `HTTP ${response.status}`,
        response.status,
        errorData
      )
    }

    return await response.json()
  } catch (error) {
    if (error instanceof APIError) {
      throw error
    }
    // Network or other error
    throw new APIError(
      error.message || 'Network error',
      0,
      { originalError: error }
    )
  }
}

// =============================================================================
// Health Check
// =============================================================================

/**
 * Check backend health status
 * @returns {Promise<{status: string, version: string, issues_count: number}>}
 */
export async function checkHealth() {
  return apiRequest('/health')
}

/**
 * Get list of available Ollama models
 * @returns {Promise<{models: string[], error?: string}>}
 */
export async function getModels() {
  return apiRequest('/models')
}

// =============================================================================
// Analysis
// =============================================================================

/**
 * Start code analysis
 * @param {string} path - Path to codebase to analyze
 * @param {Object} options - Analysis options
 * @param {string[]} options.fileTypes - File patterns to analyze (default: ["*.py"])
 * @param {boolean} options.asyncMode - Run in background (default: false)
 * @param {string} options.model - Ollama model to use for analysis
 * @returns {Promise<Object>} Analysis results or task ID
 */
export async function startAnalysis(path, options = {}) {
  const body = {
    path,
    file_types: options.fileTypes || ['*.py'],
    async_mode: options.asyncMode || false,
  }
  
  // Only include model if specified
  if (options.model) {
    body.model = options.model
  }
  
  return apiRequest('/analyze', {
    method: 'POST',
    body: JSON.stringify(body),
  })
}

/**
 * Get status of async analysis task
 * @param {string} taskId - Task ID from startAnalysis
 * @returns {Promise<Object>} Task status and results
 */
export async function getAnalysisStatus(taskId) {
  return apiRequest(`/analyze/${taskId}/status`)
}

// =============================================================================
// Issues
// =============================================================================

/**
 * Get list of issues with optional filtering
 * @param {Object} filters - Filter options
 * @param {string} filters.type - Filter by type (security, performance, architecture)
 * @param {string} filters.riskLevel - Filter by risk (critical, high, medium, low)
 * @param {string} filters.search - Search in title and description
 * @param {string} filters.file - Filter by file path
 * @param {number} filters.page - Page number (1-indexed)
 * @param {number} filters.pageSize - Items per page (max 100)
 * @returns {Promise<{issues: Array, total: number, filtered_total: number, page: number, page_size: number}>}
 */
export async function getIssues(filters = {}) {
  const params = new URLSearchParams()
  
  if (filters.type) params.append('type', filters.type)
  if (filters.riskLevel) params.append('risk_level', filters.riskLevel)
  if (filters.search) params.append('search', filters.search)
  if (filters.file) params.append('file', filters.file)
  if (filters.page) params.append('page', filters.page.toString())
  if (filters.pageSize) params.append('page_size', filters.pageSize.toString())

  const queryString = params.toString()
  return apiRequest(`/issues${queryString ? `?${queryString}` : ''}`)
}

/**
 * Get issues summary statistics
 * @returns {Promise<{total: number, by_type: Object, by_risk_level: Object}>}
 */
export async function getIssuesSummary() {
  return apiRequest('/issues/summary')
}

/**
 * Get detailed information about a specific issue
 * @param {string} issueId - Issue ID
 * @returns {Promise<Object>} Full issue details with markdown content
 */
export async function getIssueDetail(issueId) {
  return apiRequest(`/issues/${issueId}`)
}

/**
 * Delete an issue
 * @param {string} issueId - Issue ID to delete
 * @returns {Promise<{status: string, id: string}>}
 */
export async function deleteIssue(issueId) {
  return apiRequest(`/issues/${issueId}`, {
    method: 'DELETE',
  })
}

/**
 * Clear all issues from the issues folder
 * @returns {Promise<{status: string, deleted_count: number, message: string}>}
 */
export async function clearAllIssues() {
  return apiRequest('/issues', {
    method: 'DELETE',
  })
}

// =============================================================================
// Chat
// =============================================================================

/**
 * Send a chat message and get AI response
 * @param {string} message - User's question or message
 * @param {Object} context - Optional context
 * @param {string} context.issueId - ID of issue being discussed
 * @param {string|string[]} model - Optional model name(s) to use. Can be a single model string or array of models for comparison.
 * @returns {Promise<{response?: string, issues_referenced?: string[], suggestions?: string[], responses?: Object}>}
 */
export async function sendChatMessage(message, context = null, model = null) {
  const body = {
    message,
    context: context ? { issue_id: context.issueId } : null,
  }
  
  // Handle both single model and multiple models
  if (Array.isArray(model)) {
    // Multiple models for comparison
    body.models = model
  } else if (model) {
    // Single model (backward compatibility)
    body.model = model
  }
  
  return apiRequest('/chat', {
    method: 'POST',
    body: JSON.stringify(body),
  })
}

// =============================================================================
// Export default client object
// =============================================================================

const apiClient = {
  checkHealth,
  getModels,
  startAnalysis,
  getAnalysisStatus,
  getIssues,
  getIssuesSummary,
  getIssueDetail,
  deleteIssue,
  clearAllIssues,
  sendChatMessage,
  APIError,
}

export default apiClient
