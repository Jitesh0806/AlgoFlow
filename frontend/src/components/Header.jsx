import React from 'react'
import { useStore } from '../lib/store'

const PASSES = [
  { key: 'DCE',  label: 'DCE',  tip: 'Dead Code Elimination' },
  { key: 'CP',   label: 'CP',   tip: 'Constant Propagation' },
  { key: 'CF',   label: 'CF',   tip: 'Constant Folding' },
  { key: 'CSE',  label: 'CSE',  tip: 'Common Subexpression Elimination' },
  { key: 'LICM', label: 'LICM', tip: 'Loop Invariant Code Motion' },
]

export default function Header({ onRun }) {
  const { passes, togglePass, compiling, simulating } = useStore()
  const busy = compiling || simulating

  return (
    <header style={{
      display: 'flex', alignItems: 'center', justifyContent: 'space-between',
      height: 52, padding: '0 20px', flexShrink: 0,
      background: 'var(--surface)', borderBottom: '1px solid var(--border)',
      gap: 12, zIndex: 100,
    }}>
      {/* Logo */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
        <div style={{
          width: 30, height: 30,
          background: 'linear-gradient(135deg, var(--accent), var(--accent2))',
          borderRadius: 7, display: 'flex', alignItems: 'center', justifyContent: 'center',
          fontSize: 13, fontWeight: 700, color: '#000', letterSpacing: -1,
        }}>⟨/⟩</div>
        <span style={{ fontFamily: 'Syne', fontWeight: 800, fontSize: '1.15rem', letterSpacing: '-0.02em' }}>
          Algo<span style={{ color: 'var(--accent)' }}>Flow</span>
        </span>
        <span className="badge badge-blue" style={{ marginLeft: 4 }}>v1.0</span>
      </div>

      {/* Pass toggles */}
      <div style={{ display: 'flex', gap: 5, alignItems: 'center' }}>
        <span style={{ fontSize: '0.65rem', color: 'var(--muted)', fontFamily: 'JetBrains Mono', marginRight: 4 }}>
          PASSES:
        </span>
        {PASSES.map(p => (
          <button
            key={p.key}
            title={p.tip}
            onClick={() => togglePass(p.key)}
            style={{
              padding: '3px 10px', borderRadius: 20,
              border: `1px solid ${passes[p.key] ? 'rgba(0,229,255,0.4)' : 'var(--border)'}`,
              background: passes[p.key] ? 'rgba(0,229,255,0.08)' : 'transparent',
              color: passes[p.key] ? 'var(--accent)' : 'var(--muted)',
              fontFamily: 'JetBrains Mono', fontSize: '0.68rem',
              cursor: 'pointer', transition: 'all 0.15s',
              display: 'flex', alignItems: 'center', gap: 5,
            }}
          >
            <span style={{
              width: 6, height: 6, borderRadius: '50%',
              background: passes[p.key] ? 'var(--accent)' : 'var(--muted)',
              transition: 'background 0.15s',
            }} />
            {p.label}
          </button>
        ))}
      </div>

      {/* Run button */}
      <button
        onClick={onRun}
        disabled={busy}
        style={{
          display: 'flex', alignItems: 'center', gap: 8,
          padding: '7px 18px',
          background: busy ? 'var(--border2)' : 'var(--accent)',
          color: busy ? 'var(--text2)' : '#000',
          border: 'none', borderRadius: 7,
          fontFamily: 'Syne', fontWeight: 700, fontSize: '0.78rem',
          letterSpacing: '0.06em', cursor: busy ? 'not-allowed' : 'pointer',
          transition: 'all 0.15s',
        }}
      >
        {busy ? (
          <span className="animate-spin" style={{ display: 'inline-block', width: 14, height: 14, border: '2px solid #fff3', borderTopColor: 'var(--text2)', borderRadius: '50%' }} />
        ) : (
          <svg width="12" height="12" viewBox="0 0 12 12" fill="currentColor"><path d="M2 1l9 5-9 5V1z"/></svg>
        )}
        {busy ? 'COMPILING…' : 'COMPILE & RUN'}
      </button>
    </header>
  )
}
