// File: src/App.jsx
import { useState, useEffect } from 'react'
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import AuthCallback from './components/AuthCallback'

function App() {
  const [user, setUser] = useState(null)
  const [query, setQuery] = useState('')
  const [chatResponse, setChatResponse] = useState('')
  const [business, setBusiness] = useState(null)
  const [lastUpdateTime, setLastUpdateTime] = useState({})
  const [isLoading, setIsLoading] = useState(false)
  const [isSidebarOpen, setIsSidebarOpen] = useState(true)

  useEffect(() => {
    checkAuth()
  }, [])

  const checkAuth = async () => {
    try {
      const response = await fetch(`${import.meta.env.VITE_API_BASE || 'http://localhost:8000'}/auth/check`, {
        credentials: 'include'
      })
      if (response.ok) {
        const data = await response.json()
        setUser(data.user)
      }
    } catch (error) {
      console.error('Auth check failed:', error)
      setUser(null)
    }
  }

  const loginWithGoogle = () => {
    window.location.href = `${import.meta.env.VITE_API_BASE || 'http://localhost:8000'}/auth/login`
  }

  const logout = async () => {
    try {
      await fetch(`${import.meta.env.VITE_API_BASE || 'http://localhost:8000'}/auth/logout`, {
        method: 'POST',
        credentials: 'include'
      })
      setUser(null)
    } catch (error) {
      console.error('Logout failed:', error)
    }
  }

  const askChatbot = () => {
    if (!query.trim()) return

    setIsLoading(true)
    setChatResponse('')

    setTimeout(() => {
      setChatResponse(`Mock reply for: "${query}" (no backend connected)`)
      setIsLoading(false)
    }, 1000)
  }

  const LoginPage = () => (
    <div className="min-h-screen bg-slate-900 text-gray-100 flex items-center justify-center">
      <div className="max-w-md w-full p-8 bg-slate-800 rounded-xl shadow-xl">
        <h1 className="text-3xl font-bold text-center mb-8">Welcome to Map2Map™</h1>
        <p className="text-gray-400 text-center mb-8">
          Sign in to manage your business information and locations
        </p>
        <button
          onClick={loginWithGoogle}
          className="w-full flex items-center justify-center gap-3 bg-white text-gray-900 hover:bg-gray-100 px-4 py-3 rounded-lg transition-colors duration-200"
        >
          <svg className="w-5 h-5" viewBox="0 0 24 24" fill="currentColor">
            <path d="M12.545,10.239v3.821h5.445c-0.712,2.315-2.647,3.972-5.445,3.972c-3.332,0-6.033-2.701-6.033-6.032s2.701-6.032,6.033-6.032c1.498,0,2.866,0.549,3.921,1.453l2.814-2.814C17.503,2.988,15.139,2,12.545,2C7.021,2,2.543,6.477,2.543,12s4.478,10,10.002,10c8.396,0,10.249-7.85,9.426-11.748L12.545,10.239z"/>
          </svg>
          Sign in with Google
        </button>
      </div>
    </div>
  )

  const Dashboard = () => (
    <div className="min-h-screen bg-gray-100">
      <div className={`fixed inset-y-0 left-0 z-50 w-64 bg-white shadow-lg transform ${isSidebarOpen ? 'translate-x-0' : '-translate-x-full'} transition-transform duration-300 ease-in-out lg:translate-x-0`}>
        <aside className="w-64 bg-slate-800 p-4 hidden sm:block h-screen sticky top-0 shadow-xl">
          <h2 className="text-2xl font-bold text-white mb-8">Map2Map</h2>
          <nav className="space-y-4">
            <div className="text-gray-400 hover:text-white cursor-pointer">Dashboard</div>
            <div className="text-gray-400 hover:text-white cursor-pointer">Locations</div>
            <div className="text-gray-400 hover:text-white cursor-pointer">Reviews</div>
            <div className="text-gray-400 hover:text-white cursor-pointer">Profile</div>
          </nav>
          <div className="absolute bottom-4 left-4 right-4">
            <button
              onClick={logout}
              className="w-full text-gray-400 hover:text-white text-left py-2"
            >
              Sign out
            </button>
          </div>
        </aside>
      </div>

      <div className="lg:pl-64">
        <div className="max-w-7xl mx-auto">
          <div className="flex justify-between items-center mb-8">
            <h1 className="text-3xl font-bold text-white">Customer Portal</h1>
            <div className="flex items-center gap-4">
              <div className="text-right">
                <p className="text-sm text-gray-400">{user.email}</p>
                <p className="text-white">{user.name}</p>
              </div>
              {user.picture && (
                <img
                  src={user.picture}
                  alt={user.name}
                  className="w-10 h-10 rounded-full"
                />
              )}
            </div>
          </div>

          <section className="space-y-10">
            <div className="bg-slate-800 p-4 rounded-xl">
              <h2 className="text-xl font-semibold">Welcome, {user.name}</h2>
              <p className="text-sm text-gray-400">{user.email}</p>
            </div>

            <div className="bg-slate-800 p-4 rounded-xl">
              <h3 className="text-lg font-bold mb-2">Chatbot Assistant</h3>
              <div className="flex gap-2">
                <input
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && askChatbot()}
                  className="flex-1 rounded bg-slate-900 border border-slate-600 px-3 py-2"
                  placeholder="Ask something about your business..."
                />
                <button
                  onClick={askChatbot}
                  disabled={isLoading}
                  className="bg-indigo-600 hover:bg-indigo-700 px-4 py-2 rounded text-white"
                >
                  {isLoading ? 'Thinking...' : 'Ask'}
                </button>
              </div>
              {chatResponse && (
                <div className="mt-4 p-3 bg-slate-900 border border-slate-700 rounded">
                  <strong>Bot:</strong> {chatResponse}
                </div>
              )}
            </div>

            {business && (
              <div className="bg-slate-800 p-4 rounded-xl">
                <h3 className="text-lg font-bold mb-2">Business Info</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="text-sm">Name</label>
                    <input value={business.name} readOnly className="w-full mt-1 rounded bg-slate-900 border border-slate-700 px-3 py-2" />
                  </div>
                  <div>
                    <label className="text-sm">Phone</label>
                    <input value={business.phone} readOnly className="w-full mt-1 rounded bg-slate-900 border border-slate-700 px-3 py-2" />
                  </div>
                  <div className="md:col-span-2">
                    <label className="text-sm">Address</label>
                    <textarea value={business.address} readOnly className="w-full mt-1 rounded bg-slate-900 border border-slate-700 px-3 py-2"></textarea>
                  </div>
                </div>
              </div>
            )}
          </section>
        </div>
      </div>
    </div>
  )

  return (
    <Router basename={import.meta.env.PROD ? '' : '/'}>
      <Routes>
        <Route path="/auth/callback" element={<AuthCallback />} />
        <Route path="/" element={user ? <Dashboard /> : <LoginPage />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </Router>
  )
}

export default App