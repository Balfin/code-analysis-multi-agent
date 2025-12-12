import { useState, useEffect } from 'react'
import { 
  Shield, 
  Gauge, 
  Boxes, 
  MessageSquare, 
  FolderSearch, 
  Menu, 
  X,
  Activity,
  FileText
} from 'lucide-react'
import AnalysisDashboard from './components/AnalysisDashboard'
import IssuesList from './components/IssuesList'
import ChatPanel from './components/ChatPanel'
import ReportGenerator from './components/ReportGenerator'

function App() {
  const [activeView, setActiveView] = useState('dashboard')
  const [selectedIssue, setSelectedIssue] = useState(null)
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)
  const [backendStatus, setBackendStatus] = useState('checking')

  const navItems = [
    { id: 'dashboard', label: 'Dashboard', icon: FolderSearch, description: 'Analyze codebase' },
    { id: 'issues', label: 'Issues', icon: Shield, description: 'Browse findings' },
    { id: 'chat', label: 'Chat', icon: MessageSquare, description: 'Ask questions' },
    { id: 'report', label: 'Generate Report', icon: FileText, description: 'Generate issue reports' },
  ]

  // Check backend health
  useEffect(() => {
    const checkBackend = async () => {
      try {
        const response = await fetch('http://localhost:8000/health')
        if (response.ok) {
          setBackendStatus('connected')
        } else {
          setBackendStatus('error')
        }
      } catch {
        setBackendStatus('disconnected')
      }
    }

    checkBackend()
    const interval = setInterval(checkBackend, 30000) // Check every 30s
    return () => clearInterval(interval)
  }, [])

  const handleNavigation = (viewId) => {
    setActiveView(viewId)
    setMobileMenuOpen(false)
  }

  const handleSelectIssue = (issue) => {
    setSelectedIssue(issue)
  }

  const renderView = () => {
    switch (activeView) {
      case 'dashboard':
        return <AnalysisDashboard />
      case 'issues':
        return <IssuesList onSelectIssue={handleSelectIssue} />
      case 'chat':
        return <ChatPanel selectedIssue={selectedIssue} />
      case 'report':
        return <ReportGenerator />
      default:
        return <AnalysisDashboard />
    }
  }

  const getStatusColor = () => {
    switch (backendStatus) {
      case 'connected':
        return 'bg-green-500'
      case 'checking':
        return 'bg-yellow-500 animate-pulse'
      case 'error':
        return 'bg-red-500'
      default:
        return 'bg-zinc-500'
    }
  }

  const getStatusText = () => {
    switch (backendStatus) {
      case 'connected':
        return 'Backend Connected'
      case 'checking':
        return 'Connecting...'
      case 'error':
        return 'Backend Error'
      default:
        return 'Backend Offline'
    }
  }

  return (
    <div className="min-h-screen bg-zinc-950 flex flex-col">
      {/* Header */}
      <header className="bg-zinc-900 border-b border-zinc-800 sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            {/* Logo */}
            <div className="flex items-center gap-3">
              <div className="flex items-center justify-center w-10 h-10 rounded-lg bg-gradient-to-br from-indigo-500 to-purple-600 shadow-lg shadow-indigo-500/20">
                <Boxes className="w-6 h-6 text-white" />
              </div>
              <div className="hidden sm:block">
                <h1 className="text-lg font-semibold text-zinc-100">
                  Code Analyzer
                </h1>
                <p className="text-xs text-zinc-500">
                  Multi-Agent Analysis System
                </p>
              </div>
            </div>

            {/* Desktop Navigation */}
            <nav className="hidden md:flex items-center gap-1">
              {navItems.map((item) => {
                const Icon = item.icon
                const isActive = activeView === item.id
                return (
                  <button
                    key={item.id}
                    onClick={() => handleNavigation(item.id)}
                    className={`
                      flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium
                      transition-all duration-200
                      ${isActive 
                        ? 'bg-zinc-800 text-zinc-100 shadow-lg shadow-zinc-900/50' 
                        : 'text-zinc-400 hover:text-zinc-100 hover:bg-zinc-800/50'
                      }
                    `}
                    title={item.description}
                  >
                    <Icon className="w-4 h-4" />
                    <span>{item.label}</span>
                    {item.id === 'issues' && selectedIssue && isActive && (
                      <span className="w-2 h-2 bg-indigo-500 rounded-full"></span>
                    )}
                  </button>
                )
              })}
            </nav>

            {/* Status indicator & Mobile menu button */}
            <div className="flex items-center gap-3">
              {/* Backend Status */}
              <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-zinc-800/50">
                <span className={`w-2 h-2 rounded-full ${getStatusColor()}`}></span>
                <span className="text-xs text-zinc-500 hidden sm:inline">
                  {getStatusText()}
                </span>
              </div>

              {/* Mobile menu button */}
              <button
                onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
                className="md:hidden p-2 rounded-lg text-zinc-400 hover:text-zinc-100 hover:bg-zinc-800"
              >
                {mobileMenuOpen ? (
                  <X className="w-5 h-5" />
                ) : (
                  <Menu className="w-5 h-5" />
                )}
              </button>
            </div>
          </div>

          {/* Mobile Navigation */}
          {mobileMenuOpen && (
            <div className="md:hidden py-4 border-t border-zinc-800 animate-fade-in">
              <div className="flex flex-col gap-1">
                {navItems.map((item) => {
                  const Icon = item.icon
                  const isActive = activeView === item.id
                  return (
                    <button
                      key={item.id}
                      onClick={() => handleNavigation(item.id)}
                      className={`
                        flex items-center gap-3 px-4 py-3 rounded-lg text-left
                        transition-all duration-200
                        ${isActive 
                          ? 'bg-zinc-800 text-zinc-100' 
                          : 'text-zinc-400 hover:text-zinc-100 hover:bg-zinc-800/50'
                        }
                      `}
                    >
                      <Icon className="w-5 h-5" />
                      <div>
                        <span className="font-medium">{item.label}</span>
                        <p className="text-xs text-zinc-500">{item.description}</p>
                      </div>
                    </button>
                  )
                })}
              </div>
            </div>
          )}
        </div>
      </header>

      {/* Main content */}
      <main className="flex-1 overflow-hidden">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 h-full">
          {renderView()}
        </div>
      </main>

      {/* Footer */}
      <footer className="bg-zinc-900 border-t border-zinc-800 py-4">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex flex-col sm:flex-row items-center justify-between gap-4 text-xs text-zinc-500">
            <p className="flex items-center gap-2">
              <Activity className="w-3 h-3" />
              AI-Powered Code Analysis Multi-Agent System
            </p>
            <div className="flex items-center gap-4">
              <span className="flex items-center gap-1.5">
                <Shield className="w-3 h-3 text-red-400" /> Security
              </span>
              <span className="flex items-center gap-1.5">
                <Gauge className="w-3 h-3 text-amber-400" /> Performance
              </span>
              <span className="flex items-center gap-1.5">
                <Boxes className="w-3 h-3 text-blue-400" /> Architecture
              </span>
            </div>
          </div>
        </div>
      </footer>
    </div>
  )
}

export default App
