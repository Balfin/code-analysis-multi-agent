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
  ChevronDown,
  GitCompare
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
      content: "Hello! I'm your code analysis assistant. I can help you understand the issues found in your codebase and provide recommendations for fixing them.\n\nYou can ask me questions like:\n- What are the most critical issues?\n- Tell me about security vulnerabilities\n- How do I fix the N+1 query problem?\n\nWhat would you like to know?",
      timestamp: new Date(),
      modelId: 'default',
    },
  ])
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState(null)
  const [copiedMessageId, setCopiedMessageId] = useState(null)
  const [showTimestamps, setShowTimestamps] = useState(true)
  const [selectedModel, setSelectedModel] = useState(null) // null means use default
  const [selectedModel2, setSelectedModel2] = useState(null) // Second model for comparison
  const [comparisonMode, setComparisonMode] = useState(false) // Whether comparison mode is enabled
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
          // Auto-enable comparison mode if 2+ models available (only on initial load)
          if (response.models.length >= 2 && !comparisonMode) {
            const hasBeenInitialized = localStorage.getItem('comparisonModeInitialized') === 'true'
            if (!hasBeenInitialized) {
              setComparisonMode(true)
              localStorage.setItem('comparisonModeInitialized', 'true')
            }
          }
          // Disable comparison mode if less than 2 models
          if (response.models.length < 2 && comparisonMode) {
            setComparisonMode(false)
            setSelectedModel2(null)
          }
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

  // Auto-disable comparison mode if models drop below 2
  useEffect(() => {
    if (availableModels.length < 2 && comparisonMode) {
      setComparisonMode(false)
      setSelectedModel2(null)
    }
  }, [availableModels.length, comparisonMode])

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
        modelId: selectedModel || 'default',
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
      
      // Determine which models to use
      let modelsToUse = null
      if (comparisonMode && selectedModel2 !== null) {
        // Comparison mode: use both models
        const model1 = selectedModel || null
        const model2 = selectedModel2 || null
        modelsToUse = [model1, model2].filter(m => m !== null)
        // If both are null, use ['default', 'default'] but that's redundant
        // Better to use [null, null] and let backend handle it
        if (modelsToUse.length === 0) {
          modelsToUse = [null, null]
        } else if (modelsToUse.length === 1) {
          // If only one model selected, duplicate it for comparison
          modelsToUse = [modelsToUse[0], modelsToUse[0]]
        }
      } else if (comparisonMode) {
        // Comparison mode enabled but only one model selected
        const model1 = selectedModel || null
        modelsToUse = [model1, model1]
      } else {
        // Single model mode
        modelsToUse = selectedModel
      }
      
      const response = await apiClient.sendChatMessage(messageToSend, context, modelsToUse)

      // Handle response format (single or multiple)
      if (response.responses) {
        // Multiple models: add a message for each model
        Object.entries(response.responses).forEach(([modelName, modelResponse]) => {
          const assistantMessage = {
            id: Date.now() + Math.random(), // Unique ID for each model response
            role: 'assistant',
            content: modelResponse.response,
            issuesReferenced: modelResponse.issues_referenced,
            suggestions: modelResponse.suggestions,
            modelId: modelName,
            timestamp: new Date(),
          }
          addMessage(assistantMessage)
        })
      } else {
        // Single model: backward compatible format
        const assistantMessage = {
          id: Date.now() + 1,
          role: 'assistant',
          content: response.response,
          issuesReferenced: response.issues_referenced,
          suggestions: response.suggestions,
          modelId: selectedModel || 'default',
          timestamp: new Date(),
        }
        addMessage(assistantMessage)
      }
    } catch (err) {
      setError(err.message || 'Failed to get response')
      
      // Add error message to chat
      const errorMessage = {
        id: Date.now() + 1,
        role: 'assistant',
        content: `I'm sorry, I encountered an error: ${err.message || 'Unable to connect to the server'}. Please make sure the backend is running and try again.`,
        isError: true,
        timestamp: new Date(),
        modelId: comparisonMode ? (selectedModel || 'default') : (selectedModel || 'default'),
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
    setMessages([])
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
      // List items - handle before other formatting
      if (line.startsWith('- ')) {
        // Remove the '- ' prefix and format the rest
        const listContent = line.substring(2)
        let formattedLine = listContent.split(/\*\*(.*?)\*\*/g).map((part, i) => 
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
        
        return (
          <div key={idx} className="flex gap-2 ml-2">
            <span className="text-zinc-500">•</span>
            <span>{formattedLine}</span>
          </div>
        )
      }

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

  // Organize messages for comparison mode
  const organizeMessagesForComparison = (messages) => {
    const organized = []
    let currentTurn = null
    
    for (const message of messages) {
      if (message.role === 'user') {
        // Start a new turn
        if (currentTurn) {
          organized.push(currentTurn)
        }
        currentTurn = {
          userMessage: message,
          modelResponses: {}
        }
      } else if (message.role === 'assistant') {
        if (currentTurn) {
          // Add assistant response to current turn
          const modelId = message.modelId || 'default'
          if (!currentTurn.modelResponses[modelId]) {
            currentTurn.modelResponses[modelId] = []
          }
          currentTurn.modelResponses[modelId].push(message)
        } else {
          // Standalone assistant message (e.g., initial greeting)
          const modelId = message.modelId || 'default'
          organized.push({
            userMessage: null,
            modelResponses: {
              [modelId]: [message]
            }
          })
        }
      }
    }
    
    if (currentTurn) {
      organized.push(currentTurn)
    }
    
    return organized
  }

  // Get model names for display
  const getModelDisplayName = (modelId) => {
    if (modelId === 'default') return 'Default'
    return modelId || 'Default'
  }

  // Get the two model IDs for comparison
  const getComparisonModelIds = () => {
    const model1 = selectedModel || 'default'
    const model2 = selectedModel2 || 'default'
    return [model1, model2]
  }

  // Render a single message
  const renderMessage = (message, showModelLabel = false) => (
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
        {/* Model label for comparison mode */}
        {showModelLabel && message.role === 'assistant' && message.modelId && (
          <div className="text-xs text-zinc-500 mb-1">
            {getModelDisplayName(message.modelId)}
          </div>
        )}
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
  )

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
        {comparisonMode ? (
          // Split view for comparison mode
          <div className="flex-1 overflow-hidden flex">
            {(() => {
              const [model1Id, model2Id] = getComparisonModelIds()
              
              return (
                <>
                  {/* Model 1 Column */}
                  <div className="flex-1 overflow-y-auto p-4 space-y-4 border-r border-zinc-800">
                    <div className="sticky top-0 bg-zinc-900/95 backdrop-blur-sm z-10 pb-2 mb-2 border-b border-zinc-800">
                      <div className="text-xs font-medium text-zinc-400 flex items-center gap-2">
                        <Bot className="w-3.5 h-3.5 text-indigo-400" />
                        {getModelDisplayName(model1Id)}
                      </div>
                    </div>
                    {Object.entries(groupedMessages).map(([date, dateMessages]) => {
                      const organizedTurns = organizeMessagesForComparison(dateMessages)
                      return (
                        <div key={date}>
                          {messages.length > 3 && (
                            <div className="flex items-center gap-3 my-4">
                              <div className="flex-1 h-px bg-zinc-800"></div>
                              <span className="text-xs text-zinc-600">{date}</span>
                              <div className="flex-1 h-px bg-zinc-800"></div>
                            </div>
                          )}
                          {organizedTurns.map((turn, turnIdx) => (
                            <div key={turnIdx} className="space-y-3">
                              {turn.userMessage && renderMessage(turn.userMessage)}
                              {turn.modelResponses[model1Id]?.map(msg => renderMessage(msg, true))}
                              {!turn.modelResponses[model1Id] && turn.userMessage && isLoading && (
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
                            </div>
                          ))}
                        </div>
                      )
                    })}
                    <div ref={messagesEndRef} />
                  </div>

                  {/* Model 2 Column */}
                  <div className="flex-1 overflow-y-auto p-4 space-y-4">
                    <div className="sticky top-0 bg-zinc-900/95 backdrop-blur-sm z-10 pb-2 mb-2 border-b border-zinc-800">
                      <div className="text-xs font-medium text-zinc-400 flex items-center gap-2">
                        <Bot className="w-3.5 h-3.5 text-purple-400" />
                        {getModelDisplayName(model2Id)}
                      </div>
                    </div>
                    {Object.entries(groupedMessages).map(([date, dateMessages]) => {
                      const organizedTurns = organizeMessagesForComparison(dateMessages)
                      return (
                        <div key={date}>
                          {messages.length > 3 && (
                            <div className="flex items-center gap-3 my-4">
                              <div className="flex-1 h-px bg-zinc-800"></div>
                              <span className="text-xs text-zinc-600">{date}</span>
                              <div className="flex-1 h-px bg-zinc-800"></div>
                            </div>
                          )}
                          {organizedTurns.map((turn, turnIdx) => (
                            <div key={turnIdx} className="space-y-3">
                              {turn.userMessage && renderMessage(turn.userMessage)}
                              {turn.modelResponses[model2Id]?.map(msg => renderMessage(msg, true))}
                              {!turn.modelResponses[model2Id] && turn.userMessage && isLoading && (
                                <div className="flex gap-3 animate-slide-up">
                                  <div className="flex-shrink-0 w-8 h-8 rounded-lg bg-gradient-to-br from-purple-500/20 to-pink-500/20 flex items-center justify-center">
                                    <Bot className="w-4 h-4 text-purple-400" />
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
                            </div>
                          ))}
                        </div>
                      )
                    })}
                    <div ref={messagesEndRef} />
                  </div>
                </>
              )
            })()}
          </div>
        ) : (
          // Single view (original layout)
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

                {dateMessages.map((message) => renderMessage(message))}
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
        )}

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
          {/* Comparison Mode Toggle */}
          {availableModels.length >= 2 && (
            <div className="mb-3 flex items-center gap-2">
              <input
                type="checkbox"
                id="comparison-mode"
                checked={comparisonMode}
                onChange={(e) => {
                  setComparisonMode(e.target.checked)
                  if (!e.target.checked) {
                    setSelectedModel2(null)
                  }
                }}
                disabled={isLoadingModels || isLoading}
                className="w-4 h-4 rounded border-zinc-600 bg-zinc-800 text-indigo-600 focus:ring-2 focus:ring-indigo-500 disabled:opacity-50"
              />
              <label 
                htmlFor="comparison-mode" 
                className="text-xs text-zinc-400 flex items-center gap-1.5 cursor-pointer disabled:opacity-50"
              >
                <GitCompare className="w-3.5 h-3.5" />
                Compare Models
              </label>
            </div>
          )}
          
          {/* Model Selectors */}
          <div className={`mb-3 ${comparisonMode ? 'space-y-3' : ''}`}>
            <div>
              <label className="text-xs text-zinc-500 mb-1.5 block">
                {comparisonMode ? 'Model 1' : 'Model'}
              </label>
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
            
            {/* Second Model Selector (only visible in comparison mode) */}
            {comparisonMode && (
              <div>
                <label className="text-xs text-zinc-500 mb-1.5 block">Model 2</label>
                <div className="relative isolate">
                  <select
                    value={selectedModel2 || 'default'}
                    onChange={(e) => setSelectedModel2(e.target.value === 'default' ? null : e.target.value)}
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
            )}
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
