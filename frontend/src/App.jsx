import React, { useEffect, useRef } from 'react'
import { useStore } from './lib/store'
import { api } from './lib/api'
import { TEMPLATES } from './lib/templates'
import Header from './components/Header'
import LeftPanel from './components/LeftPanel'
import TabBar from './components/TabBar'
import AnimationPanel from './components/AnimationPanel'
import ASTPanel from './components/ASTPanel'
import IRPanel from './components/IRPanel'
import CFGPanel from './components/CFGPanel'
import OptimizationsPanel from './components/OptimizationsPanel'
import MetricsPanel from './components/MetricsPanel'
import PlayBar from './components/PlayBar'
import StatusBar from './components/StatusBar'
import './styles/globals.css'

export default function App() {
  const {
    source, algorithm, inputData, passes,
    setSource, setAlgorithm,
    setCompiling, setCompileResult, setCompileError,
    setSimulating, setSimResult,
    compileResult, compileError,
    activeTab, playing, currentStep, playSpeed,
    stepForward, setPlaying,
  } = useStore()

  const playRef = useRef(null)

  // Load default template on mount
  useEffect(() => {
    const tmpl = TEMPLATES[algorithm]
    if (tmpl && !source) setSource(tmpl.source)
  }, [])

  // Auto-play timer
  useEffect(() => {
    if (playing) {
      playRef.current = setInterval(stepForward, playSpeed)
    } else {
      clearInterval(playRef.current)
    }
    return () => clearInterval(playRef.current)
  }, [playing, playSpeed, currentStep])

  async function handleCompileAndRun() {
    if (!source.trim()) return

    setCompiling(true)
    setPlaying(false)

    try {
      // 1. Compile
      const result = await api.compile(source, passes)
      setCompileResult(result)

      // 2. Simulate
      setSimulating(true)
      const arr = inputData.length > 0 ? inputData : [5, 3, 1, 4, 2]
      const simRes = await api.simulate(algorithm, arr)
      setSimResult(simRes)
    } catch (err) {
      setCompileError(err)
    } finally {
      setCompiling(false)
      setSimulating(false)
    }
  }

  const TAB_PANELS = {
    animation:     <AnimationPanel />,
    ast:           <ASTPanel />,
    ir:            <IRPanel />,
    cfg:           <CFGPanel />,
    optimizations: <OptimizationsPanel />,
    metrics:       <MetricsPanel />,
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100vh', overflow: 'hidden' }}>
      <Header onRun={handleCompileAndRun} />

      <div style={{ display: 'flex', flex: 1, overflow: 'hidden' }}>
        {/* Left: Editor + controls */}
        <LeftPanel onRun={handleCompileAndRun} />

        {/* Right: Tab panels */}
        <div style={{ display: 'flex', flexDirection: 'column', flex: 1, overflow: 'hidden' }}>
          <TabBar />
          <div style={{ flex: 1, overflow: 'hidden', position: 'relative' }}>
            {TAB_PANELS[activeTab] || TAB_PANELS.animation}
          </div>
          <PlayBar />
        </div>
      </div>

      <StatusBar />
    </div>
  )
}
