/**
 * API Client for Code Analysis Multi-Agent System
 * 
 * This module provides functions to interact with the backend API.
 * Endpoints will be implemented in Phase 7.
 */

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000'

/**
 * Generic fetch wrapper with error handling
 */
async function fetchAPI(endpoint, options = {}) {
  const url = `${API_BASE}${endpoint}`
  
  const defaultOptions = {
    headers: {
      'Content-Type': 'application/json',
    },
  }

  const response = await fetch(url, { ...defaultOptions, ...options })

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Unknown error' }))
    throw new Error(error.detail || `HTTP ${response.status}`)
  }

  return response.json()
}

/**
 * Health check endpoint
 */
export async function checkHealth() {
  return fetchAPI('/health')
}

/**
 * Start code analysis
 * @param {string} path - Path to the codebase to analyze
 * @param {string[]} fileTypes - File patterns to include (default: ['*.py'])
 */
export async function startAnalysis(path, fileTypes = ['*.py']) {
  return fetchAPI('/analyze', {
    method: 'POST',
    body: JSON.stringify({ path, file_types: fileTypes }),
  })
}

/**
 * Get all issues with optional filters
 * @param {Object} filters - Filter options
 * @param {string} filters.type - Issue type (security, performance, architecture)
 * @param {string} filters.risk_level - Risk level (critical, high, medium, low)
 */
export async function getIssues(filters = {}) {
  const params = new URLSearchParams()
  if (filters.type) params.append('type', filters.type)
  if (filters.risk_level) params.append('risk_level', filters.risk_level)
  
  const query = params.toString()
  return fetchAPI(`/issues${query ? `?${query}` : ''}`)
}

/**
 * Get a specific issue by ID
 * @param {string} issueId - The issue ID
 */
export async function getIssueById(issueId) {
  return fetchAPI(`/issues/${issueId}`)
}

/**
 * Send a chat message
 * @param {string} message - The user's message
 * @param {string|null} context - Optional issue ID for context
 */
export async function sendChatMessage(message, context = null) {
  return fetchAPI('/chat', {
    method: 'POST',
    body: JSON.stringify({ message, context }),
  })
}

export default {
  checkHealth,
  startAnalysis,
  getIssues,
  getIssueById,
  sendChatMessage,
}

