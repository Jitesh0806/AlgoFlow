import React from 'react'
import { useStore } from '../lib/store'

const TABS = [
  { id: 'animation',     label: '▶ Animation',      tip: 'Step-by-step execution animation' },
  { id: 'ast',           label: 'AST',               tip: 'Abstract Syntax Tree' },
  { id: 'ir',            label: 'IR',                tip: 'Intermediate Representation (Three-Address Code)' },
  { id: 'cfg',           label: 'CFG',               tip: 'Control Flow Graph' },
  { id: 'optimizations', label: 'Optimizations',     tip: 'Per-pass optimization details' },
  { id: 'metrics',       label: 'Metrics',           tip: 'Performance comparison before/after optimization' },
]

export default function TabBar() {
  const { activeTab, setActiveTab, compileResult } = useStore()

  // Get eliminated count for IR badge
  const eliminated = compileResult
    ? Object.values(compileResult.passes || {}).reduce((acc, fn) =>
        acc + Object.values(fn.passes || {}).reduce((a, p) =>
          a + (p.changes || []).filter(c => c.type === 'eliminated').length, 0), 0)
    : 0

  return (
    <div style={{
      display: 'flex', alignItems: 'center',
      background: 'var(--surface)', borderBottom: '1px solid var(--border)',
      padding: '0 4px', gap: 2, flexShrink: 0, overflow: 'hidden',
    }}>
      {TABS.map(tab => (
        <button
          key={tab.id}
          title={tab.tip}
          onClick={() => setActiveTab(tab.id)}
          style={{
            padding: '11px 14px', border: 'none', background: 'transparent',
            borderBottom: `2px solid ${activeTab === tab.id ? 'var(--accent)' : 'transparent'}`,
            color: activeTab === tab.id ? 'var(--accent)' : 'var(--text2)',
            fontFamily: 'JetBrains Mono', fontSize: '0.72rem',
            cursor: 'pointer', transition: 'all 0.15s', whiteSpace: 'nowrap',
            display: 'flex', alignItems: 'center', gap: 5,
          }}
        >
          {tab.label}
          {tab.id === 'ir' && eliminated > 0 && (
            <span style={{
              display: 'inline-flex', alignItems: 'center', justifyContent: 'center',
              width: 16, height: 16, borderRadius: '50%',
              background: 'var(--accent2)', color: '#fff', fontSize: '0.58rem', fontWeight: 700,
            }}>{eliminated}</span>
          )}
          {tab.id === 'ast' && compileResult && (
            <span className="badge badge-green" style={{ fontSize: '0.58rem', padding: '1px 5px' }}>✓</span>
          )}
        </button>
      ))}
    </div>
  )
}
