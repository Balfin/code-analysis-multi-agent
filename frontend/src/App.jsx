import { useState } from 'react'
import { Shield, Gauge, Boxes, MessageSquare, FolderSearch } from 'lucide-react'
import AnalysisDashboard from './components/AnalysisDashboard'
import IssuesList from './components/IssuesList'
import ChatPanel from './components/ChatPanel'

function App() {
  const [activeView, setActiveView] = useState('dashboard')
  const [selectedIssue, setSelectedIssue] = useState(null)

  const navItems = [
    { id: 'dashboard', label: 'Dashboard', icon: FolderSearch },
    { id: 'issues', label: 'Issues', icon: Shield },
    { id: 'chat', label: 'Chat', icon: MessageSquare },
  ]

  const renderView = () => {
    switch (activeView) {
      case 'dashboard':
        return <AnalysisDashboard />
      case 'issues':
        return <IssuesList onSelectIssue={setSelectedIssue} />
      case 'chat':
        return <ChatPanel selectedIssue={selectedIssue} />
      default:
        return <AnalysisDashboard />
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
              <div className="flex items-center justify-center w-10 h-10 rounded-lg bg-gradient-to-br from-indigo-500 to-purple-600">
                <Boxes className="w-6 h-6 text-white" />
              </div>
              <div>
                <h1 className="text-lg font-semibold text-zinc-100">
                  Code Analyzer
                </h1>
                <p className="text-xs text-zinc-500">
                  Multi-Agent Analysis System
                </p>
              </div>
            </div>

            {/* Navigation */}
            <nav className="flex items-center gap-1">
              {navItems.map((item) => {
                const Icon = item.icon
                const isActive = activeView === item.id
                return (
                  <button
                    key={item.id}
                    onClick={() => setActiveView(item.id)}
                    className={`
                      flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium
                      transition-all duration-200
                      ${isActive 
                        ? 'bg-zinc-800 text-zinc-100' 
                        : 'text-zinc-400 hover:text-zinc-100 hover:bg-zinc-800/50'
                      }
                    `}
                  >
                    <Icon className="w-4 h-4" />
                    <span className="hidden sm:inline">{item.label}</span>
                  </button>
                )
              })}
            </nav>

            {/* Status indicator */}
            <div className="flex items-center gap-2">
              <span className="flex h-2 w-2">
                <span className="animate-ping absolute inline-flex h-2 w-2 rounded-full bg-green-400 opacity-75"></span>
                <span className="relative inline-flex rounded-full h-2 w-2 bg-green-500"></span>
              </span>
              <span className="text-xs text-zinc-500 hidden sm:inline">Ready</span>
            </div>
          </div>
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
          <div className="flex items-center justify-between text-xs text-zinc-500">
            <p>AI-Powered Code Analysis Multi-Agent System</p>
            <div className="flex items-center gap-4">
              <span className="flex items-center gap-1">
                <Shield className="w-3 h-3" /> Security
              </span>
              <span className="flex items-center gap-1">
                <Gauge className="w-3 h-3" /> Performance
              </span>
              <span className="flex items-center gap-1">
                <Boxes className="w-3 h-3" /> Architecture
              </span>
            </div>
          </div>
        </div>
      </footer>
    </div>
  )
}

export default App
