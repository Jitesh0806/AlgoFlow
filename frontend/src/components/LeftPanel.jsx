import React, { useState } from 'react'
import { useStore } from '../lib/store'
import { TEMPLATES, CATEGORIES } from '../lib/templates'

export default function LeftPanel({ onRun }) {
  const { source, setSource, algorithm, setAlgorithm, inputData, setInputData } = useStore()
  const [inputRaw, setInputRaw] = useState(inputData.join(', '))
  const [filterCat, setFilterCat] = useState('All')

  function handleAlgoChange(key) {
    setAlgorithm(key)
    setSource(TEMPLATES[key].source)
  }

  function handleInputChange(val) {
    setInputRaw(val)
    const nums = val.split(',').map(s => parseInt(s.trim())).filter(n => !isNaN(n))
    if (nums.length > 0) setInputData(nums)
  }

  const filtered = Object.entries(TEMPLATES).filter(
    ([, t]) => filterCat === 'All' || t.category === filterCat
  )

  const cats = ['All', ...CATEGORIES]

  return (
    <div style={{
      width: 310, display: 'flex', flexDirection: 'column', flexShrink: 0,
      background: 'var(--surface)', borderRight: '1px solid var(--border)',
      overflow: 'hidden',
    }}>
      {/* Panel header */}
      <div style={{
        padding: '10px 14px', borderBottom: '1px solid var(--border)',
        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
        flexShrink: 0,
      }}>
        <span style={{ fontFamily: 'Syne', fontWeight: 700, fontSize: '0.68rem', letterSpacing: '0.12em', color: 'var(--text2)', textTransform: 'uppercase' }}>
          Pseudocode Editor
        </span>
        <span className="badge badge-blue" style={{ fontSize: '0.6rem' }}>ANTLR4</span>
      </div>

      {/* Category filter */}
      <div style={{ padding: '8px 12px', borderBottom: '1px solid var(--border)', flexShrink: 0 }}>
        <div style={{ display: 'flex', gap: 4, flexWrap: 'wrap' }}>
          {cats.map(c => (
            <button key={c} onClick={() => setFilterCat(c)} style={{
              padding: '2px 8px', borderRadius: 12,
              border: `1px solid ${filterCat === c ? 'var(--accent2)' : 'var(--border)'}`,
              background: filterCat === c ? 'rgba(124,58,237,0.12)' : 'transparent',
              color: filterCat === c ? 'var(--accent2)' : 'var(--muted)',
              fontFamily: 'JetBrains Mono', fontSize: '0.62rem', cursor: 'pointer',
            }}>{c}</button>
          ))}
        </div>
      </div>

      {/* Algorithm picker */}
      <div style={{ padding: '8px 12px', borderBottom: '1px solid var(--border)', flexShrink: 0 }}>
        <label style={{ display: 'block', fontSize: '0.65rem', color: 'var(--muted)', fontFamily: 'JetBrains Mono', marginBottom: 5 }}>
          // select algorithm
        </label>
        <select
          value={algorithm}
          onChange={e => handleAlgoChange(e.target.value)}
          style={{
            width: '100%', background: 'var(--panel)', border: '1px solid var(--border)',
            color: 'var(--text)', padding: '6px 10px', borderRadius: 6,
            fontFamily: 'JetBrains Mono', fontSize: '0.75rem', outline: 'none', cursor: 'pointer',
          }}
        >
          {filtered.map(([key, t]) => (
            <option key={key} value={key}>{t.name}</option>
          ))}
        </select>

        {/* Complexity badges */}
        {TEMPLATES[algorithm] && (
          <div style={{ display: 'flex', gap: 6, marginTop: 6 }}>
            <span className="badge badge-orange">⏱ {TEMPLATES[algorithm].complexity.time}</span>
            <span className="badge badge-purple">🧠 {TEMPLATES[algorithm].complexity.space}</span>
            <span className="badge badge-muted">{TEMPLATES[algorithm].category}</span>
          </div>
        )}
      </div>

      {/* Code editor */}
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', padding: '10px 12px', gap: 6, overflow: 'hidden' }}>
        <label style={{ fontSize: '0.65rem', color: 'var(--muted)', fontFamily: 'JetBrains Mono', flexShrink: 0 }}>
          // pseudocode
        </label>
        <textarea
          value={source}
          onChange={e => setSource(e.target.value)}
          spellCheck={false}
          style={{
            flex: 1, background: 'var(--code-bg)', border: '1px solid var(--border)',
            borderRadius: 7, color: 'var(--text)', padding: '12px 14px',
            fontFamily: 'JetBrains Mono', fontSize: '0.78rem', lineHeight: 1.8,
            resize: 'none', outline: 'none', transition: 'border-color 0.15s',
          }}
          onFocus={e => e.target.style.borderColor = 'rgba(0,229,255,0.3)'}
          onBlur={e => e.target.style.borderColor = 'var(--border)'}
          placeholder="Write pseudocode here…"
        />
      </div>

      {/* Input configuration */}
      <div style={{
        padding: '10px 12px', borderTop: '1px solid var(--border)', flexShrink: 0,
        display: 'flex', flexDirection: 'column', gap: 6,
      }}>
        <label style={{ fontSize: '0.65rem', color: 'var(--muted)', fontFamily: 'JetBrains Mono' }}>
          // input array
        </label>
        <input
          value={inputRaw}
          onChange={e => handleInputChange(e.target.value)}
          style={{
            background: 'var(--panel)', border: '1px solid var(--border)',
            color: 'var(--text)', padding: '6px 10px', borderRadius: 6,
            fontFamily: 'JetBrains Mono', fontSize: '0.75rem', outline: 'none',
            width: '100%',
          }}
          placeholder="64, 34, 25, 12, 22…"
          onFocus={e => e.target.style.borderColor = 'var(--accent)'}
          onBlur={e => e.target.style.borderColor = 'var(--border)'}
        />
        <div style={{ display: 'flex', gap: 4, flexWrap: 'wrap' }}>
          {inputData.map((v, i) => (
            <span key={i} className="badge badge-muted" style={{ fontSize: '0.65rem' }}>{v}</span>
          ))}
        </div>
      </div>

      {/* Quick run button */}
      <div style={{ padding: '10px 12px', borderTop: '1px solid var(--border)', flexShrink: 0 }}>
        <button onClick={onRun} style={{
          width: '100%', padding: '9px', background: 'rgba(0,229,255,0.06)',
          border: '1px solid rgba(0,229,255,0.2)', color: 'var(--accent)',
          borderRadius: 7, fontFamily: 'Syne', fontWeight: 700, fontSize: '0.78rem',
          letterSpacing: '0.06em', cursor: 'pointer', transition: 'all 0.15s',
        }}
          onMouseEnter={e => { e.target.style.background = 'rgba(0,229,255,0.12)' }}
          onMouseLeave={e => { e.target.style.background = 'rgba(0,229,255,0.06)' }}
        >
          ▶ COMPILE & RUN
        </button>
      </div>
    </div>
  )
}
