// ─── OptimizationsPanel ──────────────────────────────────────────────────────
import React from 'react'
import { useStore } from '../lib/store'

const PASS_META = {
  CF:   { name: 'Constant Folding',                   color: 'var(--accent3)', icon: '🔢' },
  CP:   { name: 'Constant Propagation',               color: 'var(--accent4)', icon: '📌' },
  CSE:  { name: 'Common Subexpression Elimination',   color: 'var(--accent)',  icon: '♻️' },
  LICM: { name: 'Loop Invariant Code Motion',         color: 'var(--accent2)', icon: '⬆️' },
  DCE:  { name: 'Dead Code Elimination',              color: 'var(--danger)',  icon: '🗑️' },
}

export function OptimizationsPanel() {
  const { compileResult } = useStore()

  if (!compileResult?.ir_after?.length) {
    return <Welcome icon="⚡" title="Optimization Passes" msg="Compile to see per-pass transformation details" />
  }

  const ORDER = ['CF', 'CP', 'CSE', 'LICM', 'DCE']

  return (
    <div style={{ height: '100%', overflow: 'auto', padding: 16, display: 'flex', flexDirection: 'column', gap: 10 }}>
      {compileResult.ir_after.map(funcData => (
        <div key={funcData.function}>
          <div style={{ fontFamily: 'Syne', fontWeight: 700, fontSize: '0.75rem', color: 'var(--accent)', marginBottom: 10 }}>
            function {funcData.function}()
          </div>
          {ORDER.map(passKey => {
            const pass = funcData.passes?.[passKey]
            if (!pass) return null
            const meta   = PASS_META[passKey] || {}
            const changes = pass.changes || []

            return (
              <div key={passKey} style={{
                background: 'var(--surface)', border: `1px solid ${pass.applied && changes.length > 0 ? (meta.color + '40') : 'var(--border)'}`,
                borderRadius: 10, padding: 14, marginBottom: 10,
                opacity: pass.applied ? 1 : 0.5,
              }}>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 6 }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                    <span style={{ fontSize: '1.1rem' }}>{meta.icon}</span>
                    <span style={{ fontFamily: 'Syne', fontWeight: 700, fontSize: '0.82rem' }}>{meta.name}</span>
                  </div>
                  <div style={{ display: 'flex', gap: 6 }}>
                    {!pass.applied && <span className="badge badge-muted">disabled</span>}
                    {pass.applied && changes.length === 0 && <span className="badge badge-muted">no-op</span>}
                    {pass.applied && changes.length > 0 && (
                      <span className="badge" style={{ background: meta.color + '18', color: meta.color, border: `1px solid ${meta.color}40`, fontSize: '0.62rem' }}>
                        ✓ {changes.length} change{changes.length !== 1 ? 's' : ''}
                      </span>
                    )}
                  </div>
                </div>

                <p style={{ fontSize: '0.73rem', color: 'var(--text2)', lineHeight: 1.6, marginBottom: changes.length > 0 ? 8 : 0 }}>
                  {pass.description}
                </p>

                {changes.slice(0, 4).map((c, i) => (
                  <div key={i} style={{
                    background: 'var(--code-bg)', borderRadius: 6, padding: '6px 10px',
                    fontFamily: 'JetBrains Mono', fontSize: '0.7rem', marginTop: 4,
                    borderLeft: `3px solid ${meta.color}`,
                  }}>
                    {c.type === 'folded' && (
                      <>
                        <div style={{ color: 'var(--danger)' }}>- {c.expression}</div>
                        <div style={{ color: 'var(--accent4)' }}>+ {c.result}</div>
                      </>
                    )}
                    {c.type === 'eliminated' && (
                      <div style={{ color: 'var(--danger)', textDecoration: 'line-through' }}>
                        ✗ {c.instruction} <span style={{ color: 'var(--muted)', textDecoration: 'none' }}>({c.reason})</span>
                      </div>
                    )}
                    {c.type === 'eliminated_cse' && (
                      <>
                        <div style={{ color: 'var(--danger)' }}>- {c.original}</div>
                        <div style={{ color: 'var(--accent4)' }}>+ {c.result} = {c.replaced_with}</div>
                      </>
                    )}
                    {c.type === 'substituted' && (
                      <div style={{ color: 'var(--accent)' }}>
                        {c.variable} → {c.replaced_with} (propagated)
                      </div>
                    )}
                    {c.type === 'hoisted' && (
                      <div style={{ color: 'var(--accent2)' }}>
                        ⬆ Hoisted: {c.instruction}
                      </div>
                    )}
                  </div>
                ))}
                {changes.length > 4 && (
                  <div style={{ fontSize: '0.65rem', color: 'var(--muted)', marginTop: 4, fontFamily: 'JetBrains Mono' }}>
                    +{changes.length - 4} more changes…
                  </div>
                )}
              </div>
            )
          })}
        </div>
      ))}
    </div>
  )
}

// ─── MetricsPanel ────────────────────────────────────────────────────────────

export function MetricsPanel() {
  const { compileResult, simResult } = useStore()

  if (!compileResult) {
    return <Welcome icon="📊" title="Performance Metrics" msg="Compile to see optimization impact metrics" />
  }

  const s = compileResult.stats || {}
  const m = simResult?.metrics || {}

  const metricCards = [
    { label: 'IR Before',      value: s.ir_before_count, color: 'var(--accent3)',  sub: 'instructions' },
    { label: 'IR After',       value: s.ir_after_count,  color: 'var(--accent4)',  sub: 'instructions' },
    { label: 'Eliminated',     value: s.ir_eliminated,   color: 'var(--danger)',   sub: 'dead instr' },
    { label: 'Reduction',      value: s.reduction_pct != null ? s.reduction_pct + '%' : '—', color: 'var(--accent2)', sub: 'smaller' },
    { label: 'CFG Blocks',     value: s.total_blocks,    color: 'var(--accent)',   sub: 'basic blocks' },
    { label: 'CFG Edges',      value: s.total_edges,     color: 'var(--muted)',    sub: 'edges' },
    { label: 'Token Count',    value: s.token_count,     color: 'var(--accent3)',  sub: 'tokens' },
    { label: 'Compile Time',   value: s.total_time_ms != null ? s.total_time_ms + 'ms' : '—', color: 'var(--accent4)', sub: 'total' },
  ]

  if (m.comparisons != null) {
    metricCards.push(
      { label: 'Comparisons',  value: m.comparisons, color: 'var(--accent)',  sub: simResult?.algorithm },
      { label: 'Swaps',        value: m.swaps,       color: 'var(--accent3)', sub: 'data moves' },
      { label: 'Complexity',   value: m.complexity?.time, color: 'var(--accent2)', sub: 'time complexity' },
      { label: 'Space',        value: m.complexity?.space, color: 'var(--accent4)', sub: 'space complexity' },
    )
  }

  return (
    <div style={{ height: '100%', overflow: 'auto', padding: 16 }}>
      {/* Metric cards grid */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(160px, 1fr))', gap: 10, marginBottom: 16 }}>
        {metricCards.map((mc, i) => (
          <div key={i} style={{
            background: 'var(--surface)', border: '1px solid var(--border)',
            borderRadius: 10, padding: '12px 14px',
          }}>
            <div style={{ fontSize: '0.6rem', color: 'var(--muted)', textTransform: 'uppercase', letterSpacing: '0.1em', fontFamily: 'JetBrains Mono', marginBottom: 6 }}>
              {mc.label}
            </div>
            <div style={{ fontSize: '1.4rem', fontWeight: 700, fontFamily: 'JetBrains Mono', color: mc.color }}>
              {mc.value ?? '—'}
            </div>
            <div style={{ fontSize: '0.62rem', color: 'var(--muted)', marginTop: 2 }}>{mc.sub}</div>
          </div>
        ))}
      </div>

      {/* IR size bar comparison */}
      {s.ir_before_count && (
        <div style={{ background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: 10, padding: 14, marginBottom: 12 }}>
          <div style={{ fontFamily: 'Syne', fontWeight: 700, fontSize: '0.7rem', color: 'var(--text2)', textTransform: 'uppercase', letterSpacing: '0.1em', marginBottom: 12 }}>
            IR Size Comparison
          </div>
          {[
            { label: 'Before optimization', val: s.ir_before_count, max: s.ir_before_count, color: 'var(--accent3)' },
            { label: 'After optimization',  val: s.ir_after_count,  max: s.ir_before_count, color: 'var(--accent4)' },
          ].map(bar => (
            <div key={bar.label} style={{ marginBottom: 10 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.7rem', fontFamily: 'JetBrains Mono', marginBottom: 4 }}>
                <span style={{ color: 'var(--text2)' }}>{bar.label}</span>
                <span style={{ color: bar.color }}>{bar.val} instr</span>
              </div>
              <div style={{ height: 8, background: 'var(--border)', borderRadius: 4, overflow: 'hidden' }}>
                <div style={{ height: '100%', width: `${(bar.val / bar.max) * 100}%`, background: bar.color, borderRadius: 4, transition: 'width 0.4s ease' }} />
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Pass timings */}
      <div style={{ background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: 10, padding: 14 }}>
        <div style={{ fontFamily: 'Syne', fontWeight: 700, fontSize: '0.7rem', color: 'var(--text2)', textTransform: 'uppercase', letterSpacing: '0.1em', marginBottom: 10 }}>
          Pipeline Timings
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
          {Object.entries(compileResult.timings || {}).map(([stage, ms]) => (
            <div key={stage} style={{ display: 'flex', justifyContent: 'space-between', fontFamily: 'JetBrains Mono', fontSize: '0.72rem' }}>
              <span style={{ color: 'var(--text2)' }}>{stage}</span>
              <span style={{ color: 'var(--accent4)' }}>{ms}ms</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

// ─── PlayBar ─────────────────────────────────────────────────────────────────

export function PlayBar() {
  const { simResult, currentStep, playing, playSpeed, setPlaying, setPlaySpeed, stepForward, stepBack, setCurrentStep } = useStore()
  const total = simResult?.steps?.length || 0

  return (
    <div style={{
      display: 'flex', alignItems: 'center', gap: 10,
      padding: '8px 16px', background: 'var(--surface)', borderTop: '1px solid var(--border)',
      flexShrink: 0,
    }}>
      {/* Step back */}
      <button onClick={stepBack} disabled={!simResult || currentStep === 0}
        style={btnStyle(false)}>
        <svg width="11" height="11" viewBox="0 0 11 11" fill="currentColor"><path d="M8 1L2 5.5l6 4.5V1z"/></svg>
      </button>

      {/* Play/Pause */}
      <button onClick={() => setPlaying(!playing)} disabled={!simResult}
        style={{ ...btnStyle(true), background: 'var(--accent)', color: '#000', width: 32, height: 32, borderRadius: '50%', border: 'none' }}>
        {playing
          ? <svg width="12" height="12" viewBox="0 0 12 12" fill="currentColor"><rect x="2" y="1" width="3" height="10"/><rect x="7" y="1" width="3" height="10"/></svg>
          : <svg width="12" height="12" viewBox="0 0 12 12" fill="currentColor"><path d="M2 1l8 5-8 5V1z"/></svg>
        }
      </button>

      {/* Step forward */}
      <button onClick={stepForward} disabled={!simResult || currentStep >= total - 1}
        style={btnStyle(false)}>
        <svg width="11" height="11" viewBox="0 0 11 11" fill="currentColor"><path d="M3 1l6 4.5L3 10V1z"/></svg>
      </button>

      {/* Progress */}
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: 3 }}>
        <span style={{ fontFamily: 'JetBrains Mono', fontSize: '0.68rem', color: 'var(--muted)' }}>
          Step {total > 0 ? currentStep + 1 : 0} / {total}
        </span>
        <div
          style={{ height: 4, background: 'var(--border)', borderRadius: 2, cursor: 'pointer', position: 'relative' }}
          onClick={e => {
            if (!simResult) return
            const rect = e.currentTarget.getBoundingClientRect()
            const pct  = (e.clientX - rect.left) / rect.width
            setCurrentStep(Math.round(pct * (total - 1)))
          }}
        >
          <div style={{
            height: '100%', borderRadius: 2, transition: 'width 0.1s',
            background: 'linear-gradient(90deg, var(--accent), var(--accent2))',
            width: total > 1 ? `${(currentStep / (total - 1)) * 100}%` : '0%',
          }} />
        </div>
      </div>

      {/* Speed */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
        <span style={{ fontSize: '0.68rem', color: 'var(--muted)' }}>Speed</span>
        <select value={playSpeed} onChange={e => setPlaySpeed(Number(e.target.value))}
          style={{ background: 'var(--panel)', border: '1px solid var(--border)', color: 'var(--text)', padding: '2px 6px', borderRadius: 5, fontFamily: 'JetBrains Mono', fontSize: '0.7rem', outline: 'none', cursor: 'pointer' }}>
          <option value={900}>0.5×</option>
          <option value={500}>1×</option>
          <option value={250}>2×</option>
          <option value={100}>4×</option>
          <option value={40}>8×</option>
        </select>
      </div>
    </div>
  )
}

function btnStyle(primary) {
  return {
    width: 28, height: 28, borderRadius: 6, border: '1px solid var(--border)',
    background: 'var(--panel)', color: 'var(--text)',
    cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center',
    transition: 'all 0.15s', flexShrink: 0,
  }
}

// ─── StatusBar ───────────────────────────────────────────────────────────────

export function StatusBar() {
  const { compileResult, compileError, compiling, simResult, passes, algorithm } = useStore()

  const activeCount = Object.values(passes).filter(Boolean).length

  let statusText = 'Ready'
  let statusColor = 'var(--accent4)'
  if (compiling)      { statusText = 'Compiling…'; statusColor = 'var(--accent3)' }
  if (compileError)   { statusText = 'Error'; statusColor = 'var(--danger)' }
  if (compileResult)  { statusText = `Compiled — ${compileResult.stats?.total_time_ms}ms`; statusColor = 'var(--accent4)' }

  return (
    <div style={{
      height: 24, display: 'flex', alignItems: 'center', gap: 20,
      padding: '0 14px', background: 'var(--surface)', borderTop: '1px solid var(--border)',
      flexShrink: 0,
    }}>
      <StatusItem dot={statusColor} text={statusText} />
      <StatusItem dot="var(--accent)" text={`${activeCount}/5 passes enabled`} />
      <StatusItem dot="var(--accent3)" text={algorithm} />
      {compileResult && <StatusItem dot="var(--accent2)" text={`${compileResult.stats?.ir_before_count}→${compileResult.stats?.ir_after_count} IR instr`} />}
      {simResult && <StatusItem dot="var(--accent4)" text={`${simResult.steps?.length} animation steps`} />}
    </div>
  )
}

function StatusItem({ dot, text }) {
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 5, fontFamily: 'JetBrains Mono', fontSize: '0.63rem', color: 'var(--muted)' }}>
      <div style={{ width: 6, height: 6, borderRadius: '50%', background: dot }} />
      {text}
    </div>
  )
}

function Welcome({ icon, title, msg }) {
  return (
    <div style={{ height: '100%', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: 10, color: 'var(--muted)' }}>
      <div style={{ fontSize: '3rem', opacity: 0.25 }}>{icon}</div>
      <h3 style={{ fontFamily: 'Syne', color: 'var(--text)', fontSize: '1rem' }}>{title}</h3>
      <p style={{ fontSize: '0.8rem', color: 'var(--text2)' }}>{msg}</p>
    </div>
  )
}
