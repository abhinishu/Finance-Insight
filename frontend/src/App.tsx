import React, { useState } from 'react'
import ReportRegistrationScreen from './components/ReportRegistrationScreen'
import DiscoveryScreen from './components/DiscoveryScreen'
import './App.css'

function App() {
  const [activeTab, setActiveTab] = useState<'registration' | 'discovery' | 'rules' | 'final'>('registration')

  return (
    <div className="app">
      <header className="app-header">
        <h1>Finance-Insight</h1>
        <p>Executive Command Center - 4-Tab Self-Service Model</p>
      </header>
      
      <nav className="tab-navigation">
        <button
          className={`tab-button ${activeTab === 'registration' ? 'active' : ''}`}
          onClick={() => setActiveTab('registration')}
        >
          Tab 1: Report Registration
        </button>
        <button
          className={`tab-button ${activeTab === 'discovery' ? 'active' : ''}`}
          onClick={() => setActiveTab('discovery')}
        >
          Tab 2: Input Report (Discovery)
        </button>
        <button
          className={`tab-button ${activeTab === 'rules' ? 'active' : ''}`}
          onClick={() => setActiveTab('rules')}
          disabled
        >
          Tab 3: Business Rules
        </button>
        <button
          className={`tab-button ${activeTab === 'final' ? 'active' : ''}`}
          onClick={() => setActiveTab('final')}
          disabled
        >
          Tab 4: Final Report
        </button>
      </nav>

      <main className="app-main">
        {activeTab === 'registration' && <ReportRegistrationScreen />}
        {activeTab === 'discovery' && <DiscoveryScreen />}
        {activeTab === 'rules' && (
          <div className="coming-soon">
            <h2>Tab 3: Business Rules</h2>
            <p>Coming soon - Define and preview GenAI logic overlays</p>
          </div>
        )}
        {activeTab === 'final' && (
          <div className="coming-soon">
            <h2>Tab 4: Final Report</h2>
            <p>Coming soon - Side-by-side reconciliation (Natural vs. Custom) with Recon Plugs</p>
          </div>
        )}
      </main>
    </div>
  )
}

export default App
