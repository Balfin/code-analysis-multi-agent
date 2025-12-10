import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import IssuesList from './IssuesList'

// Mock the API client
vi.mock('../api/client', () => ({
  default: {
    getIssues: vi.fn(),
    getIssueDetail: vi.fn(),
    deleteIssue: vi.fn(),
  },
}))

import apiClient from '../api/client'

// Sample test data
const mockIssues = [
  {
    id: 'issue-1',
    title: 'SQL Injection',
    type: 'security',
    risk_level: 'critical',
    location: 'auth.py:15',
    description: 'SQL injection vulnerability',
    created_at: '2024-01-15T10:00:00Z',
  },
  {
    id: 'issue-2',
    title: 'N+1 Query',
    type: 'performance',
    risk_level: 'medium',
    location: 'api.py:42',
    description: 'N+1 query pattern',
    created_at: '2024-01-14T10:00:00Z',
  },
  {
    id: 'issue-3',
    title: 'Hardcoded Secret',
    type: 'security',
    risk_level: 'high',
    location: 'config.py:8',
    description: 'API key hardcoded',
    created_at: '2024-01-16T10:00:00Z',
  },
  {
    id: 'issue-4',
    title: 'Missing Error Handling',
    type: 'architecture',
    risk_level: 'low',
    location: 'utils.py:23',
    description: 'No error handling',
    created_at: '2024-01-13T10:00:00Z',
  },
]

describe('IssuesList', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    apiClient.getIssues.mockResolvedValue({
      issues: mockIssues,
      filtered_total: mockIssues.length,
    })
    apiClient.getIssueDetail.mockImplementation((id) => {
      const issue = mockIssues.find(i => i.id === id)
      return Promise.resolve({ ...issue, markdown_content: null })
    })
  })

  describe('Initial Load', () => {
    it('shows loading state initially', () => {
      render(<IssuesList />)
      expect(screen.getByText(/Loading issues/i)).toBeInTheDocument()
    })

    it('fetches issues on mount', async () => {
      render(<IssuesList />)
      
      await waitFor(() => {
        expect(apiClient.getIssues).toHaveBeenCalledTimes(1)
      })
    })

    it('displays issues after loading', async () => {
      render(<IssuesList />)
      
      await waitFor(() => {
        expect(screen.getByText('SQL Injection')).toBeInTheDocument()
        expect(screen.getByText('N+1 Query')).toBeInTheDocument()
      })
    })

    it('shows empty state when no issues', async () => {
      apiClient.getIssues.mockResolvedValue({
        issues: [],
        filtered_total: 0,
      })

      render(<IssuesList />)
      
      await waitFor(() => {
        expect(screen.getByText(/No issues found/i)).toBeInTheDocument()
      })
    })
  })

  describe('Type Filtering', () => {
    it('filters by security type', async () => {
      render(<IssuesList />)
      
      await waitFor(() => {
        expect(screen.getByText('SQL Injection')).toBeInTheDocument()
      })

      // Change filter - first combobox is type filter
      const selects = screen.getAllByRole('combobox')
      fireEvent.change(selects[0], { target: { value: 'security' } })

      await waitFor(() => {
        expect(apiClient.getIssues).toHaveBeenCalledWith(
          expect.objectContaining({ type: 'security' })
        )
      })
    })

    it('filters by performance type', async () => {
      render(<IssuesList />)
      
      await waitFor(() => {
        expect(screen.getByText('SQL Injection')).toBeInTheDocument()
      })

      const typeSelect = screen.getAllByRole('combobox')[0]
      fireEvent.change(typeSelect, { target: { value: 'performance' } })

      await waitFor(() => {
        expect(apiClient.getIssues).toHaveBeenCalledWith(
          expect.objectContaining({ type: 'performance' })
        )
      })
    })

    it('filters by architecture type', async () => {
      render(<IssuesList />)
      
      await waitFor(() => {
        expect(screen.getByText('SQL Injection')).toBeInTheDocument()
      })

      const typeSelect = screen.getAllByRole('combobox')[0]
      fireEvent.change(typeSelect, { target: { value: 'architecture' } })

      await waitFor(() => {
        expect(apiClient.getIssues).toHaveBeenCalledWith(
          expect.objectContaining({ type: 'architecture' })
        )
      })
    })
  })

  describe('Risk Level Filtering', () => {
    it('filters by critical risk', async () => {
      render(<IssuesList />)
      
      await waitFor(() => {
        expect(screen.getByText('SQL Injection')).toBeInTheDocument()
      })

      const riskSelect = screen.getAllByRole('combobox')[1]
      fireEvent.change(riskSelect, { target: { value: 'critical' } })

      await waitFor(() => {
        expect(apiClient.getIssues).toHaveBeenCalledWith(
          expect.objectContaining({ riskLevel: 'critical' })
        )
      })
    })

    it('filters by high risk', async () => {
      render(<IssuesList />)
      
      await waitFor(() => {
        expect(screen.getByText('SQL Injection')).toBeInTheDocument()
      })

      const riskSelect = screen.getAllByRole('combobox')[1]
      fireEvent.change(riskSelect, { target: { value: 'high' } })

      await waitFor(() => {
        expect(apiClient.getIssues).toHaveBeenCalledWith(
          expect.objectContaining({ riskLevel: 'high' })
        )
      })
    })
  })

  describe('Search Filtering', () => {
    it('searches by query', async () => {
      render(<IssuesList />)
      
      await waitFor(() => {
        expect(screen.getByText('SQL Injection')).toBeInTheDocument()
      })

      const searchInput = screen.getByPlaceholderText(/Search issues/i)
      fireEvent.change(searchInput, { target: { value: 'SQL' } })

      await waitFor(() => {
        expect(apiClient.getIssues).toHaveBeenCalledWith(
          expect.objectContaining({ search: 'SQL' })
        )
      })
    })
  })

  describe('Combined Filtering', () => {
    it('combines type and risk filters', async () => {
      render(<IssuesList />)
      
      await waitFor(() => {
        expect(screen.getByText('SQL Injection')).toBeInTheDocument()
      })

      const selects = screen.getAllByRole('combobox')
      fireEvent.change(selects[0], { target: { value: 'security' } })
      fireEvent.change(selects[1], { target: { value: 'critical' } })

      await waitFor(() => {
        expect(apiClient.getIssues).toHaveBeenCalledWith(
          expect.objectContaining({ 
            type: 'security',
            riskLevel: 'critical'
          })
        )
      })
    })
  })

  describe('Clear Filters', () => {
    it('clears all filters', async () => {
      render(<IssuesList />)
      
      await waitFor(() => {
        expect(screen.getByText('SQL Injection')).toBeInTheDocument()
      })

      // Apply filters
      const selects = screen.getAllByRole('combobox')
      fireEvent.change(selects[0], { target: { value: 'security' } })

      // Clear filters button should appear
      await waitFor(() => {
        expect(screen.getByText(/Clear filters/i)).toBeInTheDocument()
      })

      fireEvent.click(screen.getByText(/Clear filters/i))

      await waitFor(() => {
        expect(apiClient.getIssues).toHaveBeenCalledWith(
          expect.objectContaining({ 
            page: 1,
            pageSize: 100
          })
        )
      })
    })
  })

  describe('Issue Selection', () => {
    it('selects an issue and shows detail', async () => {
      render(<IssuesList />)
      
      await waitFor(() => {
        expect(screen.getByText('SQL Injection')).toBeInTheDocument()
      })

      fireEvent.click(screen.getByText('SQL Injection'))

      await waitFor(() => {
        expect(apiClient.getIssueDetail).toHaveBeenCalledWith('issue-1')
      })
    })

    it('calls onSelectIssue callback when issue selected', async () => {
      const onSelectIssue = vi.fn()
      render(<IssuesList onSelectIssue={onSelectIssue} />)
      
      await waitFor(() => {
        expect(screen.getByText('SQL Injection')).toBeInTheDocument()
      })

      fireEvent.click(screen.getByText('SQL Injection'))

      await waitFor(() => {
        expect(onSelectIssue).toHaveBeenCalled()
      })
    })
  })

  describe('Error Handling', () => {
    it('shows error message on API failure', async () => {
      apiClient.getIssues.mockRejectedValue(new Error('Network error'))

      render(<IssuesList />)

      await waitFor(() => {
        expect(screen.getByText(/Network error/i)).toBeInTheDocument()
      })
    })

    it('shows retry button on error', async () => {
      apiClient.getIssues.mockRejectedValue(new Error('Network error'))

      render(<IssuesList />)

      await waitFor(() => {
        expect(screen.getByText(/Retry/i)).toBeInTheDocument()
      })
    })
  })

  describe('Issue Count Display', () => {
    it('shows correct issue count', async () => {
      render(<IssuesList />)

      await waitFor(() => {
        expect(screen.getByText(`${mockIssues.length} issues found`)).toBeInTheDocument()
      })
    })
  })
})

// Unit tests for sorting logic (pure function tests)
describe('Sorting Logic', () => {
  const RISK_PRIORITY = {
    critical: 4,
    high: 3,
    medium: 2,
    low: 1,
  }

  const sortByRiskDesc = (issues) => {
    return [...issues].sort((a, b) => 
      (RISK_PRIORITY[b.risk_level] || 0) - (RISK_PRIORITY[a.risk_level] || 0)
    )
  }

  const sortByRiskAsc = (issues) => {
    return [...issues].sort((a, b) => 
      (RISK_PRIORITY[a.risk_level] || 0) - (RISK_PRIORITY[b.risk_level] || 0)
    )
  }

  const sortByType = (issues) => {
    return [...issues].sort((a, b) => (a.type || '').localeCompare(b.type || ''))
  }

  const sortByLocation = (issues) => {
    return [...issues].sort((a, b) => (a.location || '').localeCompare(b.location || ''))
  }

  const sortByNewest = (issues) => {
    return [...issues].sort((a, b) => new Date(b.created_at || 0) - new Date(a.created_at || 0))
  }

  const sortByOldest = (issues) => {
    return [...issues].sort((a, b) => new Date(a.created_at || 0) - new Date(b.created_at || 0))
  }

  it('sorts by risk level descending', () => {
    const sorted = sortByRiskDesc(mockIssues)
    
    expect(sorted[0].risk_level).toBe('critical')
    expect(sorted[1].risk_level).toBe('high')
    expect(sorted[2].risk_level).toBe('medium')
    expect(sorted[3].risk_level).toBe('low')
  })

  it('sorts by risk level ascending', () => {
    const sorted = sortByRiskAsc(mockIssues)
    
    expect(sorted[0].risk_level).toBe('low')
    expect(sorted[1].risk_level).toBe('medium')
    expect(sorted[2].risk_level).toBe('high')
    expect(sorted[3].risk_level).toBe('critical')
  })

  it('sorts by type alphabetically', () => {
    const sorted = sortByType(mockIssues)
    
    expect(sorted[0].type).toBe('architecture')
    expect(sorted[1].type).toBe('performance')
    expect(sorted[2].type).toBe('security')
    expect(sorted[3].type).toBe('security')
  })

  it('sorts by location alphabetically', () => {
    const sorted = sortByLocation(mockIssues)
    
    expect(sorted[0].location).toBe('api.py:42')
    expect(sorted[1].location).toBe('auth.py:15')
    expect(sorted[2].location).toBe('config.py:8')
    expect(sorted[3].location).toBe('utils.py:23')
  })

  it('sorts by newest first', () => {
    const sorted = sortByNewest(mockIssues)
    
    expect(sorted[0].id).toBe('issue-3') // Jan 16
    expect(sorted[1].id).toBe('issue-1') // Jan 15
    expect(sorted[2].id).toBe('issue-2') // Jan 14
    expect(sorted[3].id).toBe('issue-4') // Jan 13
  })

  it('sorts by oldest first', () => {
    const sorted = sortByOldest(mockIssues)
    
    expect(sorted[0].id).toBe('issue-4') // Jan 13
    expect(sorted[1].id).toBe('issue-2') // Jan 14
    expect(sorted[2].id).toBe('issue-1') // Jan 15
    expect(sorted[3].id).toBe('issue-3') // Jan 16
  })

  it('handles empty array', () => {
    expect(sortByRiskDesc([])).toEqual([])
    expect(sortByType([])).toEqual([])
  })

  it('handles single item array', () => {
    const single = [mockIssues[0]]
    expect(sortByRiskDesc(single)).toEqual(single)
  })
})

// Filter logic tests
describe('Filter Logic', () => {
  const filterByType = (issues, type) => {
    if (type === 'all') return issues
    return issues.filter(issue => issue.type === type)
  }

  const filterByRisk = (issues, riskLevel) => {
    if (riskLevel === 'all') return issues
    return issues.filter(issue => issue.risk_level === riskLevel)
  }

  const filterBySearch = (issues, query) => {
    if (!query) return issues
    const lowerQuery = query.toLowerCase()
    return issues.filter(issue => 
      issue.title.toLowerCase().includes(lowerQuery) ||
      issue.description.toLowerCase().includes(lowerQuery) ||
      issue.location.toLowerCase().includes(lowerQuery)
    )
  }

  describe('Type Filter', () => {
    it('returns all issues when type is "all"', () => {
      const result = filterByType(mockIssues, 'all')
      expect(result).toHaveLength(4)
    })

    it('filters security issues', () => {
      const result = filterByType(mockIssues, 'security')
      expect(result).toHaveLength(2)
      expect(result.every(i => i.type === 'security')).toBe(true)
    })

    it('filters performance issues', () => {
      const result = filterByType(mockIssues, 'performance')
      expect(result).toHaveLength(1)
      expect(result[0].type).toBe('performance')
    })

    it('filters architecture issues', () => {
      const result = filterByType(mockIssues, 'architecture')
      expect(result).toHaveLength(1)
      expect(result[0].type).toBe('architecture')
    })
  })

  describe('Risk Filter', () => {
    it('returns all issues when risk is "all"', () => {
      const result = filterByRisk(mockIssues, 'all')
      expect(result).toHaveLength(4)
    })

    it('filters critical issues', () => {
      const result = filterByRisk(mockIssues, 'critical')
      expect(result).toHaveLength(1)
      expect(result[0].risk_level).toBe('critical')
    })

    it('filters high issues', () => {
      const result = filterByRisk(mockIssues, 'high')
      expect(result).toHaveLength(1)
      expect(result[0].risk_level).toBe('high')
    })

    it('filters medium issues', () => {
      const result = filterByRisk(mockIssues, 'medium')
      expect(result).toHaveLength(1)
      expect(result[0].risk_level).toBe('medium')
    })

    it('filters low issues', () => {
      const result = filterByRisk(mockIssues, 'low')
      expect(result).toHaveLength(1)
      expect(result[0].risk_level).toBe('low')
    })
  })

  describe('Search Filter', () => {
    it('returns all issues when query is empty', () => {
      const result = filterBySearch(mockIssues, '')
      expect(result).toHaveLength(4)
    })

    it('searches by title', () => {
      const result = filterBySearch(mockIssues, 'SQL')
      expect(result).toHaveLength(1)
      expect(result[0].title).toBe('SQL Injection')
    })

    it('searches by description', () => {
      const result = filterBySearch(mockIssues, 'N+1')
      expect(result).toHaveLength(1)
      expect(result[0].title).toBe('N+1 Query')
    })

    it('searches by location', () => {
      const result = filterBySearch(mockIssues, 'auth.py')
      expect(result).toHaveLength(1)
      expect(result[0].location).toBe('auth.py:15')
    })

    it('is case insensitive', () => {
      const result = filterBySearch(mockIssues, 'sql')
      expect(result).toHaveLength(1)
    })

    it('returns empty when no match', () => {
      const result = filterBySearch(mockIssues, 'xyz123')
      expect(result).toHaveLength(0)
    })
  })

  describe('Combined Filters', () => {
    it('applies multiple filters', () => {
      let result = filterByType(mockIssues, 'security')
      result = filterByRisk(result, 'critical')
      
      expect(result).toHaveLength(1)
      expect(result[0].title).toBe('SQL Injection')
    })

    it('applies all three filters', () => {
      let result = filterByType(mockIssues, 'security')
      result = filterByRisk(result, 'high')
      result = filterBySearch(result, 'hardcoded')
      
      expect(result).toHaveLength(1)
      expect(result[0].title).toBe('Hardcoded Secret')
    })
  })
})

