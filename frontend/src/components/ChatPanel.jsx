import { useState, useRef, useEffect, useCallback } from 'react'
import { 
  Send, 
  Bot, 
  User, 
  Loader2, 
  Info, 
  Trash2,
  Sparkles,
  MessageSquare,
  Shield,
  Gauge,
  Boxes,
  AlertCircle,
  Clock,
  Download,
  Copy,
  Check,
  ChevronDown
} from 'lucide-react'
import apiClient from '../api/client'

// Suggested prompts for quick access
const SUGGESTED_PROMPTS = [
  { icon: Shield, text: "What are the critical issues?", color: "text-red-400" },
  { icon: Gauge, text: "Tell me about performance issues", color: "text-amber-400" },
  { icon: Boxes, text: "Give me an overview", color: "text-blue-400" },
  { icon: Sparkles, text: "What should I fix first?", color: "text-purple-400" },
]

// Maximum messages to keep in history
const MAX_MESSAGES = 50

// Format timestamp for display
const formatTimestamp = (date) => {
  return new Intl.DateTimeFormat('en-US', {
    hour: 'numeric',
    minute: '2-digit',
    hour12: true,
  }).format(date)
}

// Format date for grouping
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

function ChatPanel({ selectedIssue }) {
  const [messages, setMessages] = useState([
    {
      id: 1,
      role: 'assistant',
      content: "Hello! I'm your code analysis assistant. I can help you understand the issues found in your codebase and provide recommendations for fixing them.\n\nYou can ask me questions like:\n- \"What are the most critical issues?\"\n- \"Tell me about security vulnerabilities\"\n- \"How do I fix the N+1 query problem?\"\n\nWhat would you like to know?",
      timestamp: new Date(),
    },
  ])
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState(null)
  const [copiedMessageId, setCopiedMessageId] = useState(null)
  const [showTimestamps, setShowTimestamps] = useState(true)
  const [selectedModel, setSelectedModel] = useState(null) // null means use default
  const [availableModels, setAvailableModels] = useState([])
  const [isLoadingModels, setIsLoadingModels] = useState(false)
  const messagesEndRef = useRef(null)
  const inputRef = useRef(null)
  const lastIssueIdRef = useRef(null)

  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [])

  useEffect(() => {
    scrollToBottom()
  }, [messages, scrollToBottom])

  // Focus input on mount
  useEffect(() => {
    inputRef.current?.focus()
  }, [])

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
        // Don't show error to user, just continue with default
      } finally {
        setIsLoadingModels(false)
      }
    }
    fetchModels()
  }, [])

  // When a new issue is selected, offer context
  useEffect(() => {
    if (selectedIssue && selectedIssue.id !== lastIssueIdRef.current) {
      lastIssueIdRef.current = selectedIssue.id
      const contextMessage = {
        id: Date.now(),
        role: 'assistant',
        content: `I see you're looking at **${selectedIssue.title}** (${selectedIssue.risk_level}). Would you like me to explain this issue in more detail or suggest how to fix it?`,
        isContext: true,
        timestamp: new Date(),
      }
      addMessage(contextMessage)
    }
  }, [selectedIssue?.id])

  // Add message with history limit
  const addMessage = useCallback((message) => {
    setMessages((prev) => {
      const newMessages = [...prev, message]
      // Keep only last MAX_MESSAGES
      if (newMessages.length > MAX_MESSAGES) {
        return newMessages.slice(-MAX_MESSAGES)
      }
      return newMessages
    })
  }, [])

  const handleSend = async (overrideMessage = null) => {
    const messageToSend = overrideMessage || input
    if (!messageToSend.trim() || isLoading) return

    const userMessage = {
      id: Date.now(),
      role: 'user',
      content: messageToSend,
      timestamp: new Date(),
    }

    addMessage(userMessage)
    setInput('')
    setIsLoading(true)
    setError(null)

    // Reset input height
    if (inputRef.current) {
      inputRef.current.style.height = 'auto'
    }

    try {
      // Call the real chat API
      const context = selectedIssue ? { issueId: selectedIssue.id } : null
      // Pass selectedModel (null means use default)
      const response = await apiClient.sendChatMessage(messageToSend, context, selectedModel)

      const assistantMessage = {
        id: Date.now() + 1,
        role: 'assistant',
        content: response.response,
        issuesReferenced: response.issues_referenced,
        suggestions: response.suggestions,
        timestamp: new Date(),
      }
      addMessage(assistantMessage)
    } catch (err) {
      setError(err.message || 'Failed to get response')
      
      // Add error message to chat
      const errorMessage = {
        id: Date.now() + 1,
        role: 'assistant',
        content: `I'm sorry, I encountered an error: ${err.message || 'Unable to connect to the server'}. Please make sure the backend is running and try again.`,
        isError: true,
        timestamp: new Date(),
      }
      addMessage(errorMessage)
    } finally {
      setIsLoading(false)
      // Refocus input
      inputRef.current?.focus()
    }
  }

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  const handleClear = () => {
    lastIssueIdRef.current = null
    setMessages([
      {
        id: Date.now(),
        role: 'assistant',
        content: "Chat cleared. How can I help you with the code analysis?",
        timestamp: new Date(),
      },
    ])
    setError(null)
    inputRef.current?.focus()
  }

  const handleSuggestedPrompt = (prompt) => {
    handleSend(prompt)
  }

  const handleCopyMessage = (message) => {
    navigator.clipboard.writeText(message.content)
    setCopiedMessageId(message.id)
    setTimeout(() => setCopiedMessageId(null), 2000)
  }

  const handleExportChat = () => {
    const chatContent = messages
      .map(m => {
        const role = m.role === 'user' ? 'You' : 'Assistant'
        const time = formatTimestamp(new Date(m.timestamp))
        return `[${time}] ${role}:\n${m.content}\n`
      })
      .join('\n---\n\n')
    
    const blob = new Blob([chatContent], { type: 'text/plain' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `chat-export-${new Date().toISOString().slice(0, 10)}.txt`
    a.click()
    URL.revokeObjectURL(url)
  }

  const formatMessage = (content) => {
    // Simple markdown-like formatting
    return content.split('\n').map((line, idx) => {
      // Bold text
      let formattedLine = line.split(/\*\*(.*?)\*\*/g).map((part, i) => 
        i % 2 === 1 ? <strong key={i} className="text-zinc-100">{part}</strong> : part
      )
      
      // Inline code
      formattedLine = formattedLine.map((part, i) => {
        if (typeof part === 'string') {
          return part.split(/`(.*?)`/g).map((codePart, j) =>
            j % 2 === 1 ? (
              <code key={`${i}-${j}`} className="bg-zinc-700 px-1.5 py-0.5 rounded text-indigo-300 text-xs font-mono">
                {codePart}
              </code>
            ) : codePart
          )
        }
        return part
      })

      // List items
      if (line.startsWith('- ')) {
        return (
          <div key={idx} className="flex gap-2 ml-2">
            <span className="text-zinc-500">•</span>
            <span>{formattedLine.slice(1)}</span>
          </div>
        )
      }

      // Numbered lists
      const numberedMatch = line.match(/^(\d+)\.\s/)
      if (numberedMatch) {
        return (
          <div key={idx} className="flex gap-2 ml-2">
            <span className="text-zinc-500 font-mono text-xs">{numberedMatch[1]}.</span>
            <span>{formattedLine}</span>
          </div>
        )
      }

      return (
        <span key={idx}>
          {formattedLine}
          {idx < content.split('\n').length - 1 && <br />}
        </span>
      )
    })
  }

  // Group messages by date
  const groupedMessages = messages.reduce((groups, message) => {
    const date = formatDate(message.timestamp)
    if (!groups[date]) {
      groups[date] = []
    }
    groups[date].push(message)
    return groups
  }, {})

  return (
    <div className="flex flex-col h-[calc(100vh-200px)] animate-fade-in">
      {/* Context Banner */}
      {selectedIssue && (
        <div className="card p-3 mb-4 border-indigo-800/50 bg-indigo-950/20">
          <div className="flex items-center gap-2 text-sm">
            <Info className="w-4 h-4 text-indigo-400 flex-shrink-0" />
            <span className="text-zinc-400">Context:</span>
            <span className="text-indigo-300 font-medium truncate">{selectedIssue.title}</span>
            <span className={`badge badge-${selectedIssue.risk_level} ml-auto flex-shrink-0`}>
              {selectedIssue.risk_level}
            </span>
          </div>
        </div>
      )}

      {/* Error Banner */}
      {error && (
        <div className="card p-3 mb-4 border-red-800/50 bg-red-950/20">
          <div className="flex items-center gap-2 text-sm text-red-400">
            <AlertCircle className="w-4 h-4 flex-shrink-0" />
            <span>Connection error. Make sure backend is running.</span>
            <button 
              onClick={() => setError(null)}
              className="ml-auto text-xs hover:underline"
            >
              Dismiss
            </button>
          </div>
        </div>
      )}

      {/* Messages Area */}
      <div className="card flex-1 overflow-hidden flex flex-col">
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {Object.entries(groupedMessages).map(([date, dateMessages]) => (
            <div key={date}>
              {/* Date separator */}
              {messages.length > 3 && (
                <div className="flex items-center gap-3 my-4">
                  <div className="flex-1 h-px bg-zinc-800"></div>
                  <span className="text-xs text-zinc-600">{date}</span>
                  <div className="flex-1 h-px bg-zinc-800"></div>
                </div>
              )}

              {dateMessages.map((message) => (
                <div
                  key={message.id}
                  className={`flex gap-3 animate-slide-up group ${
                    message.role === 'user' ? 'flex-row-reverse' : ''
                  }`}
                >
                  {/* Avatar */}
                  <div
                    className={`
                      flex-shrink-0 w-8 h-8 rounded-lg flex items-center justify-center
                      ${message.role === 'assistant' 
                        ? message.isError 
                          ? 'bg-red-500/20 text-red-400'
                          : 'bg-gradient-to-br from-indigo-500/20 to-purple-500/20 text-indigo-400' 
                        : 'bg-zinc-700 text-zinc-300'
                      }
                    `}
                  >
                    {message.role === 'assistant' ? (
                      message.isError ? <AlertCircle className="w-4 h-4" /> : <Bot className="w-4 h-4" />
                    ) : (
                      <User className="w-4 h-4" />
                    )}
                  </div>

                  {/* Message Bubble */}
                  <div className="flex flex-col max-w-[80%]">
                    <div
                      className={`
                        rounded-2xl px-4 py-3 relative
                        ${message.role === 'assistant'
                          ? message.isError
                            ? 'bg-red-950/30 border border-red-900/50 rounded-tl-sm'
                            : `bg-zinc-800/80 rounded-tl-sm ${message.isContext ? 'border border-indigo-800/30' : ''}`
                          : 'bg-indigo-600 rounded-tr-sm'
                        }
                      `}
                    >
                      {/* Copy button (visible on hover) */}
                      <button
                        onClick={() => handleCopyMessage(message)}
                        className={`
                          absolute top-2 right-2 p-1 rounded opacity-0 group-hover:opacity-100 transition-opacity
                          ${message.role === 'user' ? 'bg-indigo-700 text-indigo-200' : 'bg-zinc-700 text-zinc-400'}
                          hover:text-zinc-200
                        `}
                        title="Copy message"
                      >
                        {copiedMessageId === message.id ? (
                          <Check className="w-3 h-3" />
                        ) : (
                          <Copy className="w-3 h-3" />
                        )}
                      </button>

                      <div className={`
                        text-sm leading-relaxed pr-6
                        ${message.role === 'assistant' 
                          ? message.isError ? 'text-red-300' : 'text-zinc-300' 
                          : 'text-white'
                        }
                      `}>
                        {formatMessage(message.content)}
                      </div>

                      {/* Suggestions */}
                      {message.suggestions && message.suggestions.length > 0 && (
                        <div className="mt-3 pt-3 border-t border-zinc-700">
                          <p className="text-xs text-zinc-500 mb-2">💡 Tip:</p>
                          {message.suggestions.map((suggestion, idx) => (
                            <p key={idx} className="text-xs text-zinc-400">{suggestion}</p>
                          ))}
                        </div>
                      )}
                    </div>

                    {/* Timestamp */}
                    {showTimestamps && message.timestamp && (
                      <div className={`flex items-center gap-1 mt-1 text-xs text-zinc-600 ${message.role === 'user' ? 'justify-end' : ''}`}>
                        <Clock className="w-3 h-3" />
                        {formatTimestamp(new Date(message.timestamp))}
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          ))}

          {/* Loading Indicator */}
          {isLoading && (
            <div className="flex gap-3 animate-slide-up">
              <div className="flex-shrink-0 w-8 h-8 rounded-lg bg-gradient-to-br from-indigo-500/20 to-purple-500/20 flex items-center justify-center">
                <Bot className="w-4 h-4 text-indigo-400" />
              </div>
              <div className="bg-zinc-800/80 rounded-2xl rounded-tl-sm px-4 py-3">
                <div className="flex items-center gap-2 text-zinc-400">
                  <div className="flex gap-1">
                    <span className="w-2 h-2 bg-zinc-500 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></span>
                    <span className="w-2 h-2 bg-zinc-500 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></span>
                    <span className="w-2 h-2 bg-zinc-500 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></span>
                  </div>
                  <span className="text-sm ml-2">Thinking...</span>
                </div>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Suggested Prompts */}
        {messages.length <= 2 && !isLoading && (
          <div className="px-4 pb-2">
            <p className="text-xs text-zinc-500 mb-2">Suggested questions:</p>
            <div className="flex flex-wrap gap-2">
              {SUGGESTED_PROMPTS.map((prompt, idx) => {
                const Icon = prompt.icon
                return (
                  <button
                    key={idx}
                    onClick={() => handleSuggestedPrompt(prompt.text)}
                    className="flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-zinc-800 hover:bg-zinc-700 text-xs text-zinc-300 transition-colors"
                  >
                    <Icon className={`w-3 h-3 ${prompt.color}`} />
                    {prompt.text}
                  </button>
                )
              })}
            </div>
          </div>
        )}

        {/* Input Area */}
        <div className="border-t border-zinc-800 p-4">
          {/* Model Selector */}
          <div className="mb-3">
            <label className="text-xs text-zinc-500 mb-1.5 block">Model</label>
            <div className="relative isolate">
              <select
                value={selectedModel || 'default'}
                onChange={(e) => setSelectedModel(e.target.value === 'default' ? null : e.target.value)}
                disabled={isLoadingModels || isLoading}
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
          <div className="flex gap-3">
            <div className="flex flex-col gap-1">
              <button
                onClick={handleClear}
                className="btn btn-secondary p-2"
                title="Clear chat (Ctrl+L)"
              >
                <Trash2 className="w-4 h-4" />
              </button>
              <button
                onClick={handleExportChat}
                className="btn btn-secondary p-2"
                title="Export chat"
              >
                <Download className="w-4 h-4" />
              </button>
            </div>
            <div className="flex-1 relative flex items-end">
              <textarea
                ref={inputRef}
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={handleKeyPress}
                placeholder="Ask about the code issues..."
                rows={1}
                className="input pr-12 resize-none min-h-[42px] max-h-[120px] w-full"
                disabled={isLoading}
                style={{
                  height: 'auto',
                  overflow: 'hidden',
                }}
                onInput={(e) => {
                  e.target.style.height = 'auto'
                  e.target.style.height = Math.min(e.target.scrollHeight, 120) + 'px'
                }}
              />
              <button
                onClick={() => handleSend()}
                disabled={!input.trim() || isLoading}
                className={`
                  absolute right-2 p-2 rounded-lg
                  transition-all duration-200
                  ${input.trim() && !isLoading
                    ? 'text-indigo-400 hover:bg-indigo-500/20'
                    : 'text-zinc-600 cursor-not-allowed'
                  }
                `}
                style={{ 
                  bottom: '6px',
                  transform: 'translateY(0)'
                }}
              >
                <Send className="w-4 h-4" />
              </button>
            </div>
          </div>
          <div className="flex items-center justify-between mt-2">
            <p className="text-xs text-zinc-600">
              Enter to send • Shift+Enter for new line
            </p>
            <div className="flex items-center gap-3">
              <button
                onClick={() => setShowTimestamps(!showTimestamps)}
                className={`flex items-center gap-1 text-xs ${showTimestamps ? 'text-zinc-400' : 'text-zinc-600'} hover:text-zinc-300`}
              >
                <Clock className="w-3 h-3" />
                {showTimestamps ? 'Hide' : 'Show'} times
              </button>
              <div className="flex items-center gap-1 text-xs text-zinc-600">
                <MessageSquare className="w-3 h-3" />
                {messages.length} messages
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default ChatPanel
