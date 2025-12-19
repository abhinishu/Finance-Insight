import React from 'react'
import DiscoveryScreen from './components/DiscoveryScreen'
import './App.css'

function App() {
  return (
    <div className="app">
      <header className="app-header">
        <h1>Finance-Insight</h1>
        <p>Self-Service Discovery</p>
      </header>
      <main className="app-main">
        <DiscoveryScreen />
      </main>
    </div>
  )
}

export default App

