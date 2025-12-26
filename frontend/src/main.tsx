// Note: Using manual tree implementation - no Enterprise required
import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.tsx'
import './index.css'

// CRITICAL: Purge localStorage to remove any cached "Zombie" data from previous weeks
// This ensures fresh data is fetched from unified_pnl_service
try {
  localStorage.clear()
  console.log('✅ localStorage cleared - all cached data removed')
} catch (e) {
  console.warn('⚠️ Failed to clear localStorage:', e)
}

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)

