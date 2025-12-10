import { useState, useRef, useEffect } from 'react'
import { Send, Bot, User, Loader2, Info, Trash2 } from 'lucide-react'

function ChatPanel({ selectedIssue }) {
  const [messages, setMessages] = useState([
    {
      id: 1,
      role: 'assistant',
      content: "Hello! I'm your code analysis assistant. I can help you understand the issues found in your codebase and provide recommendations for fixing them. What would you like to know?",
    },
  ])
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const messagesEndRef = useRef(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const handleSend = async () => {
    if (!input.trim() || isLoading) return

    const userMessage = {
      id: Date.now(),
      role: 'user',
      content: input,
    }

    setMessages((prev) => [...prev, userMessage])
    setInput('')
    setIsLoading(true)

    // TODO: Implement actual API call in Phase 7
    // Simulating response for now
    setTimeout(() => {
      const assistantMessage = {
        id: Date.now() + 1,
        role: 'assistant',
        content: `I understand you're asking about "${input.slice(0, 50)}${input.length > 50 ? '...' : ''}". 

Based on the analysis results, I can help you with:
- **Security issues**: SQL injection, hardcoded credentials, XSS vulnerabilities
- **Performance issues**: N+1 queries, blocking operations, memory leaks
- **Architecture issues**: SOLID violations, code duplication, tight coupling

What specific aspect would you like to explore?`,
      }
      setMessages((prev) => [...prev, assistantMessage])
      setIsLoading(false)
    }, 1500)
  }

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  const handleClear = () => {
    setMessages([
      {
        id: Date.now(),
        role: 'assistant',
        content: "Chat cleared. How can I help you with the code analysis?",
      },
    ])
  }

  return (
    <div className="flex flex-col h-[calc(100vh-200px)] animate-fade-in">
      {/* Context Banner */}
      {selectedIssue && (
        <div className="card p-3 mb-4 border-indigo-800/50 bg-indigo-950/30">
          <div className="flex items-center gap-2 text-sm">
            <Info className="w-4 h-4 text-indigo-400" />
            <span className="text-zinc-400">Context:</span>
            <span className="text-indigo-300 font-medium">{selectedIssue.title}</span>
            <code className="text-xs text-zinc-500 font-mono ml-auto">
              {selectedIssue.id}
            </code>
          </div>
        </div>
      )}

      {/* Messages Area */}
      <div className="card flex-1 overflow-hidden flex flex-col">
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {messages.map((message) => (
            <div
              key={message.id}
              className={`flex gap-3 animate-slide-up ${
                message.role === 'user' ? 'flex-row-reverse' : ''
              }`}
            >
              {/* Avatar */}
              <div
                className={`
                  flex-shrink-0 w-8 h-8 rounded-lg flex items-center justify-center
                  ${message.role === 'assistant' 
                    ? 'bg-indigo-500/20 text-indigo-400' 
                    : 'bg-zinc-700 text-zinc-300'
                  }
                `}
              >
                {message.role === 'assistant' ? (
                  <Bot className="w-4 h-4" />
                ) : (
                  <User className="w-4 h-4" />
                )}
              </div>

              {/* Message Bubble */}
              <div
                className={`
                  max-w-[75%] rounded-2xl px-4 py-3
                  ${message.role === 'assistant'
                    ? 'bg-zinc-800 rounded-tl-sm'
                    : 'bg-indigo-600 rounded-tr-sm'
                  }
                `}
              >
                <div className={`
                  text-sm leading-relaxed whitespace-pre-wrap
                  ${message.role === 'assistant' ? 'text-zinc-300' : 'text-white'}
                `}>
                  {message.content.split('**').map((part, i) => 
                    i % 2 === 1 ? <strong key={i}>{part}</strong> : part
                  )}
                </div>
              </div>
            </div>
          ))}

          {/* Loading Indicator */}
          {isLoading && (
            <div className="flex gap-3 animate-slide-up">
              <div className="flex-shrink-0 w-8 h-8 rounded-lg bg-indigo-500/20 flex items-center justify-center">
                <Bot className="w-4 h-4 text-indigo-400" />
              </div>
              <div className="bg-zinc-800 rounded-2xl rounded-tl-sm px-4 py-3">
                <div className="flex items-center gap-2 text-zinc-400">
                  <Loader2 className="w-4 h-4 animate-spin" />
                  <span className="text-sm">Thinking...</span>
                </div>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Input Area */}
        <div className="border-t border-zinc-800 p-4">
          <div className="flex gap-3">
            <button
              onClick={handleClear}
              className="btn btn-secondary p-2"
              title="Clear chat"
            >
              <Trash2 className="w-4 h-4" />
            </button>
            <div className="flex-1 relative">
              <textarea
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={handleKeyPress}
                placeholder="Ask about the code issues..."
                rows={1}
                className="input pr-12 resize-none"
                disabled={isLoading}
              />
              <button
                onClick={handleSend}
                disabled={!input.trim() || isLoading}
                className={`
                  absolute right-2 top-1/2 -translate-y-1/2 p-2 rounded-lg
                  transition-colors duration-200
                  ${input.trim() && !isLoading
                    ? 'text-indigo-400 hover:bg-indigo-500/20'
                    : 'text-zinc-600 cursor-not-allowed'
                  }
                `}
              >
                <Send className="w-4 h-4" />
              </button>
            </div>
          </div>
          <p className="text-xs text-zinc-600 mt-2">
            Press Enter to send • Shift+Enter for new line
          </p>
        </div>
      </div>
    </div>
  )
}

export default ChatPanel

