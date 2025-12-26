import React, { useState } from 'react'
import { ReportingProvider } from './contexts/ReportingContext'
import ReportRegistrationScreen from './components/ReportRegistrationScreen'
import DiscoveryScreen from './components/DiscoveryScreen'
import RuleEditor from './components/RuleEditor'
import ExecutiveDashboard from './components/ExecutiveDashboard'
import GlobalReportingBar from './components/GlobalReportingBar'
import './App.css'

function App() {
  const [activeTab, setActiveTab] = useState<'registration' | 'discovery' | 'rules' | 'final'>('registration')

  return (
    <ReportingProvider>
      <div className="app">
        <header className="app-header">
          <h1>Finance-Insight</h1>
          <p>Executive Command Center - 4-Tab Self-Service Model</p>
        </header>
        
        {/* Step 4.3: Global Reporting Bar */}
        <GlobalReportingBar />
        
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
          >
            Tab 3: Business Rules
          </button>
          <button
            className={`tab-button ${activeTab === 'final' ? 'active' : ''}`}
            onClick={() => setActiveTab('final')}
          >
            Tab 4: Executive View
          </button>
        </nav>

        <main className="app-main">
          {activeTab === 'registration' && <ReportRegistrationScreen />}
          {activeTab === 'discovery' && <DiscoveryScreen />}
          {activeTab === 'rules' && <RuleEditor />}
          {activeTab === 'final' && <ExecutiveDashboard />}
        </main>
      </div>
    </ReportingProvider>
  )
}

export default App
