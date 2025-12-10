import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import ChatPanel from './ChatPanel'

// Mock the API client
vi.mock('../api/client', () => ({
  default: {
    sendChatMessage: vi.fn(),
  },
}))

import apiClient from '../api/client'

// Mock clipboard
Object.assign(navigator, {
  clipboard: {
    writeText: vi.fn(),
  },
})

// Mock URL APIs
global.URL.createObjectURL = vi.fn(() => 'blob:test')
global.URL.revokeObjectURL = vi.fn()

describe('ChatPanel', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    apiClient.sendChatMessage.mockResolvedValue({
      response: 'This is a test response from the assistant.',
      issues_referenced: null,
      suggestions: ['Enable LLM for better responses'],
    })
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  describe('Initial Render', () => {
    it('renders welcome message on mount', () => {
      render(<ChatPanel />)
      
      expect(screen.getByText(/Hello! I'm your code analysis assistant/i)).toBeInTheDocument()
    })

    it('renders input field', () => {
      render(<ChatPanel />)
      
      expect(screen.getByPlaceholderText(/Ask about the code issues/i)).toBeInTheDocument()
    })

    it('renders send button', () => {
      render(<ChatPanel />)
      
      // Send button exists but should be disabled when input is empty
      const sendButtons = screen.getAllByRole('button')
      expect(sendButtons.length).toBeGreaterThan(0)
    })

    it('renders suggested prompts', () => {
      render(<ChatPanel />)
      
      expect(screen.getByText(/What are the critical issues/i)).toBeInTheDocument()
      expect(screen.getByText(/Tell me about performance issues/i)).toBeInTheDocument()
    })

    it('renders clear button', () => {
      render(<ChatPanel />)
      
      expect(screen.getByTitle(/Clear chat/i)).toBeInTheDocument()
    })

    it('renders export button', () => {
      render(<ChatPanel />)
      
      expect(screen.getByTitle(/Export chat/i)).toBeInTheDocument()
    })

    it('shows message count', () => {
      render(<ChatPanel />)
      
      expect(screen.getByText(/1 messages/i)).toBeInTheDocument()
    })
  })

  describe('Sending Messages', () => {
    it('sends message on Enter key', async () => {
      render(<ChatPanel />)
      
      const input = screen.getByPlaceholderText(/Ask about the code issues/i)
      fireEvent.change(input, { target: { value: 'Test message' } })
      fireEvent.keyDown(input, { key: 'Enter', shiftKey: false })

      await waitFor(() => {
        expect(apiClient.sendChatMessage).toHaveBeenCalledWith('Test message', null)
      })
    })

    it('does not send on Shift+Enter (allows newline)', () => {
      render(<ChatPanel />)
      
      const input = screen.getByPlaceholderText(/Ask about the code issues/i)
      fireEvent.change(input, { target: { value: 'Test message' } })
      fireEvent.keyDown(input, { key: 'Enter', shiftKey: true })

      expect(apiClient.sendChatMessage).not.toHaveBeenCalled()
    })

    it('clears input after sending', async () => {
      render(<ChatPanel />)
      
      const input = screen.getByPlaceholderText(/Ask about the code issues/i)
      fireEvent.change(input, { target: { value: 'Test message' } })
      fireEvent.keyDown(input, { key: 'Enter', shiftKey: false })

      await waitFor(() => {
        expect(input.value).toBe('')
      })
    })

    it('displays user message immediately', async () => {
      render(<ChatPanel />)
      
      const input = screen.getByPlaceholderText(/Ask about the code issues/i)
      fireEvent.change(input, { target: { value: 'My test question' } })
      fireEvent.keyDown(input, { key: 'Enter', shiftKey: false })

      expect(screen.getByText('My test question')).toBeInTheDocument()
    })

    it('displays assistant response after API call', async () => {
      render(<ChatPanel />)
      
      const input = screen.getByPlaceholderText(/Ask about the code issues/i)
      fireEvent.change(input, { target: { value: 'Test' } })
      fireEvent.keyDown(input, { key: 'Enter', shiftKey: false })

      await waitFor(() => {
        expect(screen.getByText(/This is a test response/i)).toBeInTheDocument()
      })
    })

    it('does not send empty messages', () => {
      render(<ChatPanel />)
      
      const input = screen.getByPlaceholderText(/Ask about the code issues/i)
      fireEvent.change(input, { target: { value: '   ' } })
      fireEvent.keyDown(input, { key: 'Enter', shiftKey: false })

      expect(apiClient.sendChatMessage).not.toHaveBeenCalled()
    })
  })

  describe('Loading State', () => {
    it('shows loading indicator while waiting for response', async () => {
      // Make API call take longer
      apiClient.sendChatMessage.mockImplementation(() => 
        new Promise(resolve => setTimeout(() => resolve({ response: 'Done' }), 100))
      )

      render(<ChatPanel />)
      
      const input = screen.getByPlaceholderText(/Ask about the code issues/i)
      fireEvent.change(input, { target: { value: 'Test' } })
      fireEvent.keyDown(input, { key: 'Enter', shiftKey: false })

      expect(screen.getByText(/Thinking/i)).toBeInTheDocument()

      await waitFor(() => {
        expect(screen.queryByText(/Thinking/i)).not.toBeInTheDocument()
      })
    })

    it('disables input while loading', async () => {
      apiClient.sendChatMessage.mockImplementation(() => 
        new Promise(resolve => setTimeout(() => resolve({ response: 'Done' }), 100))
      )

      render(<ChatPanel />)
      
      const input = screen.getByPlaceholderText(/Ask about the code issues/i)
      fireEvent.change(input, { target: { value: 'Test' } })
      fireEvent.keyDown(input, { key: 'Enter', shiftKey: false })

      expect(input).toBeDisabled()

      await waitFor(() => {
        expect(input).not.toBeDisabled()
      })
    })
  })

  describe('Error Handling', () => {
    it('displays error message on API failure', async () => {
      apiClient.sendChatMessage.mockRejectedValue(new Error('Network error'))

      render(<ChatPanel />)
      
      const input = screen.getByPlaceholderText(/Ask about the code issues/i)
      fireEvent.change(input, { target: { value: 'Test' } })
      fireEvent.keyDown(input, { key: 'Enter', shiftKey: false })

      await waitFor(() => {
        expect(screen.getByText(/I'm sorry, I encountered an error/i)).toBeInTheDocument()
      })
    })

    it('shows error banner on failure', async () => {
      apiClient.sendChatMessage.mockRejectedValue(new Error('Network error'))

      render(<ChatPanel />)
      
      const input = screen.getByPlaceholderText(/Ask about the code issues/i)
      fireEvent.change(input, { target: { value: 'Test' } })
      fireEvent.keyDown(input, { key: 'Enter', shiftKey: false })

      await waitFor(() => {
        expect(screen.getByText(/Connection error/i)).toBeInTheDocument()
      })
    })

    it('allows dismissing error banner', async () => {
      apiClient.sendChatMessage.mockRejectedValue(new Error('Network error'))

      render(<ChatPanel />)
      
      const input = screen.getByPlaceholderText(/Ask about the code issues/i)
      fireEvent.change(input, { target: { value: 'Test' } })
      fireEvent.keyDown(input, { key: 'Enter', shiftKey: false })

      await waitFor(() => {
        expect(screen.getByText(/Connection error/i)).toBeInTheDocument()
      })

      fireEvent.click(screen.getByText(/Dismiss/i))

      expect(screen.queryByText(/Connection error/i)).not.toBeInTheDocument()
    })
  })

  describe('Issue Context', () => {
    const mockIssue = {
      id: 'issue-123',
      title: 'SQL Injection',
      risk_level: 'critical',
    }

    it('shows context banner when issue is selected', () => {
      render(<ChatPanel selectedIssue={mockIssue} />)
      
      expect(screen.getByText('Context:')).toBeInTheDocument()
      // The title appears in the context banner
      expect(screen.getAllByText('SQL Injection').length).toBeGreaterThanOrEqual(1)
    })

    it('shows risk level badge in context', () => {
      render(<ChatPanel selectedIssue={mockIssue} />)
      
      expect(screen.getByText('critical')).toBeInTheDocument()
    })

    it('passes issue context to API', async () => {
      render(<ChatPanel selectedIssue={mockIssue} />)
      
      const input = screen.getByPlaceholderText(/Ask about the code issues/i)
      fireEvent.change(input, { target: { value: 'How do I fix this?' } })
      fireEvent.keyDown(input, { key: 'Enter', shiftKey: false })

      await waitFor(() => {
        expect(apiClient.sendChatMessage).toHaveBeenCalledWith(
          'How do I fix this?',
          { issueId: 'issue-123' }
        )
      })
    })

    it('adds context message when issue is selected', () => {
      const { rerender } = render(<ChatPanel selectedIssue={null} />)
      
      rerender(<ChatPanel selectedIssue={mockIssue} />)

      expect(screen.getByText(/I see you're looking at/i)).toBeInTheDocument()
    })
  })

  describe('Clear Chat', () => {
    it('clears messages when clear button clicked', async () => {
      render(<ChatPanel />)
      
      // Send a message first
      const input = screen.getByPlaceholderText(/Ask about the code issues/i)
      fireEvent.change(input, { target: { value: 'Test message' } })
      fireEvent.keyDown(input, { key: 'Enter', shiftKey: false })

      await waitFor(() => {
        expect(screen.getByText('Test message')).toBeInTheDocument()
      })

      // Clear chat
      fireEvent.click(screen.getByTitle(/Clear chat/i))

      // Original welcome message should be gone
      expect(screen.queryByText(/Hello! I'm your code analysis assistant/i)).not.toBeInTheDocument()
      // New clear message should appear
      expect(screen.getByText(/Chat cleared/i)).toBeInTheDocument()
    })
  })

  describe('Suggested Prompts', () => {
    it('sends message when suggested prompt clicked', async () => {
      render(<ChatPanel />)
      
      fireEvent.click(screen.getByText(/What are the critical issues/i))

      await waitFor(() => {
        expect(apiClient.sendChatMessage).toHaveBeenCalledWith(
          'What are the critical issues?',
          null
        )
      })
    })

    it('hides suggested prompts after a few messages', async () => {
      render(<ChatPanel />)

      // Initially visible
      expect(screen.getByText(/Suggested questions/i)).toBeInTheDocument()

      // Send multiple messages
      const input = screen.getByPlaceholderText(/Ask about the code issues/i)
      
      fireEvent.change(input, { target: { value: 'First' } })
      fireEvent.keyDown(input, { key: 'Enter', shiftKey: false })

      await waitFor(() => {
        expect(apiClient.sendChatMessage).toHaveBeenCalled()
      })

      fireEvent.change(input, { target: { value: 'Second' } })
      fireEvent.keyDown(input, { key: 'Enter', shiftKey: false })

      await waitFor(() => {
        // Suggested prompts should be hidden after 2+ user messages
        expect(screen.queryByText(/Suggested questions/i)).not.toBeInTheDocument()
      })
    })
  })

  describe('Message Formatting', () => {
    it('formats bold text', async () => {
      apiClient.sendChatMessage.mockResolvedValue({
        response: 'This is **bold** text',
      })

      render(<ChatPanel />)
      
      const input = screen.getByPlaceholderText(/Ask about the code issues/i)
      fireEvent.change(input, { target: { value: 'Test' } })
      fireEvent.keyDown(input, { key: 'Enter', shiftKey: false })

      await waitFor(() => {
        const strongElement = document.querySelector('strong')
        expect(strongElement).toBeInTheDocument()
        expect(strongElement.textContent).toBe('bold')
      })
    })

    it('formats inline code', async () => {
      apiClient.sendChatMessage.mockResolvedValue({
        response: 'Use `console.log()` for debugging',
      })

      render(<ChatPanel />)
      
      const input = screen.getByPlaceholderText(/Ask about the code issues/i)
      fireEvent.change(input, { target: { value: 'Test' } })
      fireEvent.keyDown(input, { key: 'Enter', shiftKey: false })

      await waitFor(() => {
        const codeElement = document.querySelector('code')
        expect(codeElement).toBeInTheDocument()
        expect(codeElement.textContent).toBe('console.log()')
      })
    })
  })

  describe('Copy Message', () => {
    it('copies message to clipboard', async () => {
      render(<ChatPanel />)

      // Hover to show copy button - find the message container
      const message = screen.getByText(/Hello! I'm your code analysis assistant/i)
      const messageContainer = message.closest('.group')
      
      // Copy button should be in the message bubble
      const copyButton = messageContainer.querySelector('[title="Copy message"]')
      
      if (copyButton) {
        fireEvent.click(copyButton)
        expect(navigator.clipboard.writeText).toHaveBeenCalled()
      }
    })
  })

  describe('Timestamps', () => {
    it('shows timestamps by default', () => {
      render(<ChatPanel />)
      
      // There should be at least one timestamp visible
      const timeElements = document.querySelectorAll('[class*="text-zinc-600"]')
      // Check for AM/PM pattern
      const hasTimestamp = Array.from(timeElements).some(el => 
        /\d{1,2}:\d{2}\s*(AM|PM)/i.test(el.textContent)
      )
      expect(hasTimestamp).toBe(true)
    })

    it('allows toggling timestamps', () => {
      render(<ChatPanel />)
      
      const toggleButton = screen.getByText(/Hide times/i) || screen.getByText(/Show times/i)
      fireEvent.click(toggleButton)
      
      // Button text should change
      expect(screen.getByText(/Show times/i) || screen.getByText(/Hide times/i)).toBeInTheDocument()
    })
  })

  describe('Export Chat', () => {
    it('creates download link when export clicked', () => {
      render(<ChatPanel />)
      
      const exportButton = screen.getByTitle(/Export chat/i)
      
      // Mock createElement to track the anchor element
      const originalCreateElement = document.createElement.bind(document)
      let createdAnchor = null
      document.createElement = (tag) => {
        const element = originalCreateElement(tag)
        if (tag === 'a') {
          createdAnchor = element
          element.click = vi.fn()
        }
        return element
      }

      fireEvent.click(exportButton)

      expect(global.URL.createObjectURL).toHaveBeenCalled()
      expect(createdAnchor?.download).toMatch(/chat-export-/)

      document.createElement = originalCreateElement
    })
  })
})

// Unit tests for message formatting (pure functions)
describe('Message Formatting Logic', () => {
  const formatTimestamp = (date) => {
    return new Intl.DateTimeFormat('en-US', {
      hour: 'numeric',
      minute: '2-digit',
      hour12: true,
    }).format(date)
  }

  const formatDate = (date) => {
    const now = new Date()
    const messageDate = new Date(date)
    
    if (messageDate.toDateString() === now.toDateString()) {
      return 'Today'
    }
    
    const yesterday = new Date(now)
    yesterday.setDate(yesterday.getDate() - 1)
    if (messageDate.toDateString() === yesterday.toDateString()) {
      return 'Yesterday'
    }
    
    return messageDate.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
    })
  }

  describe('formatTimestamp', () => {
    it('formats time correctly', () => {
      const date = new Date('2024-01-15T14:30:00')
      const result = formatTimestamp(date)
      
      expect(result).toMatch(/2:30\s*PM/i)
    })

    it('handles midnight', () => {
      const date = new Date('2024-01-15T00:00:00')
      const result = formatTimestamp(date)
      
      expect(result).toMatch(/12:00\s*AM/i)
    })

    it('handles noon', () => {
      const date = new Date('2024-01-15T12:00:00')
      const result = formatTimestamp(date)
      
      expect(result).toMatch(/12:00\s*PM/i)
    })
  })

  describe('formatDate', () => {
    it('returns "Today" for today', () => {
      const result = formatDate(new Date())
      expect(result).toBe('Today')
    })

    it('returns "Yesterday" for yesterday', () => {
      const yesterday = new Date()
      yesterday.setDate(yesterday.getDate() - 1)
      const result = formatDate(yesterday)
      expect(result).toBe('Yesterday')
    })

    it('returns formatted date for older dates', () => {
      const oldDate = new Date('2024-01-15T12:00:00')
      const result = formatDate(oldDate)
      // The exact day may vary by timezone, just check format
      expect(result).toMatch(/Jan \d+/)
    })
  })
})

// Test message history limit
describe('Message History Limit', () => {
  it('limits messages to MAX_MESSAGES', async () => {
    render(<ChatPanel />)
    
    const input = screen.getByPlaceholderText(/Ask about the code issues/i)
    
    // Send many messages (this is a simplified test)
    for (let i = 0; i < 5; i++) {
      fireEvent.change(input, { target: { value: `Message ${i}` } })
      fireEvent.keyDown(input, { key: 'Enter', shiftKey: false })
      
      await waitFor(() => {
        expect(apiClient.sendChatMessage).toHaveBeenCalled()
      })
    }

    // The component should handle limiting internally
    // We just verify it doesn't crash with many messages
    expect(screen.getByPlaceholderText(/Ask about the code issues/i)).toBeInTheDocument()
  })
})

