import React, { useState } from 'react'
import { useStore } from '../lib/store'

const CATEGORIES = {
  KEYWORD:     { label: 'keyword',     color: '#7F77DD', bg: '#EEEDFE' },
  IDENTIFIER:  { label: 'identifier',  color: '#0F6E56', bg: '#E1F5EE' },
  INTEGER:     { label: 'literal',     color: '#854F0B', bg: '#FAEEDA' },
  FLOAT:       { label: 'literal',     color: '#854F0B', bg: '#FAEEDA' },
  STRING:      { label: 'literal',     color: '#854F0B', bg: '#FAEEDA' },
  PLUS:        { label: 'operator',    color: '#993C1D', bg: '#FAECE7' },
  MINUS:       { label: 'operator',    color: '#993C1D', bg: '#FAECE7' },
  STAR:        { label: 'operator',    color: '#993C1D', bg: '#FAECE7' },
  SLASH:       { label: 'operator',    color: '#993C1D', bg: '#FAECE7' },
  PERCENT:     { label: 'operator',    color: '#993C1D', bg: '#FAECE7' },
  EQEQ:        { label: 'operator',    color: '#993C1D', bg: '#FAECE7' },
  NEQ:         { label: 'operator',    color: '#993C1D', bg: '#FAECE7' },
  LT:          { label: 'operator',    color: '#993C1D', bg: '#FAECE7' },
  GT:          { label: 'operator',    color: '#993C1D', bg: '#FAECE7' },
  LTE:         { label: 'operator',    color: '#993C1D', bg: '#FAECE7' },
  GTE:         { label: 'operator',    color: '#993C1D', bg: '#FAECE7' },
  ASSIGN:      { label: 'operator',    color: '#993C1D', bg: '#FAECE7' },
}

function getCat(type) {
  return CATEGORIES[type] || { label: 'punctuation', color: '#5F5E5A', bg: '#F1EFE8' }
}

const FILTER_LABELS = ['keyword', 'identifier', 'literal', 'operator', 'punctuation']
const FILTER_COLORS = {
  keyword:     { color: '#7F77DD', bg: '#EEEDFE' },
  identifier:  { color: '#0F6E56', bg: '#E1F5EE' },
  literal:     { color: '#854F0B', bg: '#FAEEDA' },
  operator:    { color: '#993C1D', bg: '#FAECE7' },
  punctuation: { color: '#5F5E5A', bg: '#F1EFE8' },
}

export default function LexerPanel() {
  const { compileResult } = useStore()
  const [selected, setSelected] = useState(null)
  const [view, setView] = useState('stream')
  const [activeFilters, setActiveFilters] = useState(new Set(FILTER_LABELS))

  if (!compileResult) {
    return (
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%', color: 'var(--text2)', fontFamily: 'JetBrains Mono', fontSize: '0.8rem' }}>
        Run the compiler to see the token stream
      </div>
    )
  }

  const tokens = compileResult.tokens || []
  const filtered = tokens.filter(t => activeFilters.has(getCat(t.type).label))

  const counts = {}
  FILTER_LABELS.forEach(l => { counts[l] = tokens.filter(t => getCat(t.type).label === l).length })

  function toggleFilter(label) {
    setActiveFilters(prev => {
      const next = new Set(prev)
      next.has(label) ? next.delete(label) : next.add(label)
      return next
    })
    setSelected(null)
  }

  return (
    <div style={{ height: '100%', overflow: 'auto', padding: 16, fontFamily: 'JetBrains Mono', fontSize: '0.75rem', boxSizing: 'border-box' }}>

      {/* Stats row */}
      <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', marginBottom: 12 }}>
        {[['total', tokens.length, '#888'], ...FILTER_LABELS.map(l => [l, counts[l], FILTER_COLORS[l].color])].map(([label, count, color]) => (
          <div key={label} style={{ background: 'var(--surface2)', borderRadius: 6, padding: '4px 12px', color: 'var(--text2)' }}>
            {label} <span style={{ color, fontWeight: 700 }}>{count}</span>
          </div>
        ))}
      </div>

      {/* Filter badges */}
      <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap', marginBottom: 12 }}>
        {FILTER_LABELS.map(label => {
          const { color, bg } = FILTER_COLORS[label]
          const on = activeFilters.has(label)
          return (
            <span key={label} onClick={() => toggleFilter(label)} style={{
              padding: '3px 10px', borderRadius: 20, cursor: 'pointer', fontSize: '0.7rem', fontWeight: 600,
              background: on ? bg : 'transparent',
              color: on ? color : 'var(--text3)',
              border: `1px solid ${on ? color : 'var(--border)'}`,
              opacity: on ? 1 : 0.5, transition: 'all 0.15s',
            }}>{label}</span>
          )
        })}
      </div>

      {/* View toggle */}
      <div style={{ display: 'flex', marginBottom: 12, border: '1px solid var(--border)', borderRadius: 6, overflow: 'hidden', width: 'fit-content' }}>
        {['stream', 'table'].map(v => (
          <button key={v} onClick={() => setView(v)} style={{
            padding: '4px 14px', border: 'none', cursor: 'pointer', fontSize: '0.7rem',
            background: view === v ? 'var(--surface2)' : 'transparent',
            color: view === v ? 'var(--text)' : 'var(--text2)',
            fontFamily: 'JetBrains Mono', fontWeight: view === v ? 600 : 400,
          }}>{v}</button>
        ))}
      </div>

      {/* Stream view */}
      {view === 'stream' && (
        <>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6, padding: 12, background: 'var(--surface2)', borderRadius: 8, marginBottom: 12, minHeight: 52 }}>
            {filtered.map((t, i) => {
              const { color, bg } = getCat(t.type)
              const isSelected = selected?.index === i
              return (
                <span key={i} onClick={() => setSelected({ ...t, index: i })} style={{
                  padding: '3px 9px', borderRadius: 20, cursor: 'pointer', fontSize: '0.72rem', fontWeight: 600,
                  background: bg, color,
                  border: `1px solid ${isSelected ? color : 'transparent'}`,
                  outline: isSelected ? `2px solid ${color}` : 'none',
                  outlineOffset: 1, transition: 'transform 0.1s',
                }}>{t.value}</span>
              )
            })}
          </div>

          {/* Detail box */}
          <div style={{ background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: 8, padding: '10px 14px', minHeight: 44 }}>
            {selected ? (
              <div style={{ display: 'grid', gridTemplateColumns: '90px 1fr', gap: '4px 12px' }}>
                {[['type', selected.type], ['value', selected.value], ['category', getCat(selected.type).label], ['line', selected.line], ['col', selected.col]].map(([k, v]) => (
                  <React.Fragment key={k}>
                    <span style={{ color: 'var(--text2)' }}>{k}</span>
                    <span style={{ color: 'var(--text)', fontWeight: 600 }}>{v}</span>
                  </React.Fragment>
                ))}
              </div>
            ) : (
              <span style={{ color: 'var(--text3)' }}>Click any token to inspect it</span>
            )}
          </div>
        </>
      )}

      {/* Table view */}
      {view === 'table' && (
        <table style={{ width: '100%', borderCollapse: 'collapse' }}>
          <thead>
            <tr>{['#', 'type', 'value', 'line', 'col'].map(h => (
              <th key={h} style={{ textAlign: 'left', color: 'var(--text2)', fontWeight: 600, fontSize: '0.68rem', padding: '5px 10px', borderBottom: '1px solid var(--border)' }}>{h}</th>
            ))}</tr>
          </thead>
          <tbody>
            {filtered.map((t, i) => {
              const { color, bg } = getCat(t.type)
              return (
                <tr key={i} style={{ background: i % 2 === 0 ? 'transparent' : 'var(--surface2)' }}>
                  <td style={{ padding: '5px 10px', color: 'var(--text3)' }}>{i + 1}</td>
                  <td style={{ padding: '5px 10px' }}>
                    <span style={{ background: bg, color, padding: '2px 8px', borderRadius: 20, fontSize: '0.68rem', fontWeight: 600 }}>{t.type}</span>
                  </td>
                  <td style={{ padding: '5px 10px', color: 'var(--text)', fontWeight: 600 }}>{t.value}</td>
                  <td style={{ padding: '5px 10px', color: 'var(--text2)' }}>{t.line}</td>
                  <td style={{ padding: '5px 10px', color: 'var(--text2)' }}>{t.col}</td>
                </tr>
              )
            })}
          </tbody>
        </table>
      )}
    </div>
  )
}