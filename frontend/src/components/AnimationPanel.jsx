import React, { useRef, useEffect } from 'react'
import { useStore } from '../lib/store'

export default function AnimationPanel() {
  const canvasRef = useRef(null)
  const { simResult, currentStep, compileResult } = useStore()

  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return
    const ctx = canvas.getContext('2d')

    function resize() {
      canvas.width  = canvas.offsetWidth
      canvas.height = canvas.offsetHeight
      draw()
    }

    function draw() {
      const W = canvas.width, H = canvas.height
      ctx.clearRect(0, 0, W, H)
      ctx.fillStyle = '#090d12'
      ctx.fillRect(0, 0, W, H)

      // Grid lines
      ctx.strokeStyle = 'rgba(30,42,58,0.6)'
      ctx.lineWidth = 1
      for (let x = 0; x < W; x += 44) { ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, H); ctx.stroke() }
      for (let y = 0; y < H; y += 44) { ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(W, y); ctx.stroke() }

      if (!simResult || !simResult.steps.length) {
        drawWelcome(ctx, W, H); return
      }

      const step = simResult.steps[currentStep]
      if (!step) return

      if (step.dp_table) { drawDP(ctx, W, H, step); return }
      if (step.graph_state) { drawGraph(ctx, W, H, step); return }
      if (step.extra?.dp)   { drawLCS(ctx, W, H, step); return }
      if (step.array)       { drawArray(ctx, W, H, step); return }

      drawWelcome(ctx, W, H)
    }

    resize()
    const ro = new ResizeObserver(resize)
    ro.observe(canvas.parentElement)
    return () => ro.disconnect()
  }, [simResult, currentStep])

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%', background: 'var(--panel)' }}>
      {/* Step info overlay */}
      {simResult && simResult.steps[currentStep] && (
        <div style={{
          padding: '10px 16px', borderBottom: '1px solid var(--border)',
          display: 'flex', alignItems: 'center', gap: 12, flexShrink: 0,
          background: 'var(--surface)',
        }}>
          <span style={{
            fontFamily: 'JetBrains Mono', fontSize: '0.68rem', color: 'var(--accent)',
            minWidth: 90,
          }}>
            Step {currentStep + 1} / {simResult.steps.length}
          </span>
          <span style={{
            fontFamily: 'JetBrains Mono', fontSize: '0.7rem',
            padding: '2px 8px', borderRadius: 12,
            background: actionColor(simResult.steps[currentStep].action, 0.15),
            color: actionColor(simResult.steps[currentStep].action),
          }}>
            {simResult.steps[currentStep].action?.toUpperCase()}
          </span>
          <span style={{ fontSize: '0.78rem', color: 'var(--text)', flex: 1 }}>
            {simResult.steps[currentStep].description}
          </span>
          <div style={{ display: 'flex', gap: 12, flexShrink: 0 }}>
            <Metric label="CMP" value={simResult.steps[currentStep].comparisons} color="var(--accent)" />
            <Metric label="SWP" value={simResult.steps[currentStep].swaps} color="var(--accent3)" />
            <Metric label="ACC" value={simResult.steps[currentStep].accesses} color="var(--accent4)" />
          </div>
        </div>
      )}

      {/* Canvas */}
      <div style={{ flex: 1, position: 'relative', overflow: 'hidden' }}>
        <canvas ref={canvasRef} style={{ width: '100%', height: '100%', display: 'block' }} />
      </div>

      {/* IR stats row */}
      {compileResult && (
        <div style={{
          display: 'flex', gap: 20, padding: '8px 16px',
          background: 'var(--surface)', borderTop: '1px solid var(--border)', flexShrink: 0,
        }}>
          <Metric label="IR Before" value={compileResult.stats?.ir_before_count} color="var(--text2)" />
          <Metric label="IR After"  value={compileResult.stats?.ir_after_count}  color="var(--accent4)" />
          <Metric label="Eliminated" value={compileResult.stats?.ir_eliminated}  color="var(--accent3)" />
          <Metric label="Reduction"  value={compileResult.stats?.reduction_pct != null ? compileResult.stats.reduction_pct + '%' : '—'} color="var(--accent2)" />
          <Metric label="Blocks"    value={compileResult.stats?.total_blocks}    color="var(--muted)" />
          {simResult && <Metric label="Complexity" value={simResult.metrics?.complexity?.time} color="var(--accent3)" />}
        </div>
      )}
    </div>
  )
}

function Metric({ label, value, color }) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 1, minWidth: 60 }}>
      <span style={{ fontSize: '0.6rem', color: 'var(--muted)', fontFamily: 'JetBrains Mono', textTransform: 'uppercase', letterSpacing: '0.08em' }}>{label}</span>
      <span style={{ fontSize: '0.9rem', fontFamily: 'JetBrains Mono', fontWeight: 600, color: color || 'var(--text)' }}>{value ?? '—'}</span>
    </div>
  )
}

function actionColor(action, alpha) {
  const map = {
    compare: '#00e5ff', swap: '#f59e0b', pass_done: '#10b981', done: '#10b981',
    init: '#7c3aed', pivot: '#7c3aed', place_pivot: '#f59e0b', narrow: '#00e5ff',
    divide: '#7c3aed', merge: '#10b981', found: '#10b981', enqueue: '#00e5ff',
    visit: '#10b981', recurse: '#7c3aed', compute: '#00e5ff', fill: '#7c3aed',
    shift: '#f59e0b', insert: '#10b981', pick: '#00e5ff', early_exit: '#10b981',
    match: '#10b981', no_match: '#64748b',
  }
  const hex = map[action] || '#64748b'
  if (alpha) {
    const r = parseInt(hex.slice(1,3),16), g = parseInt(hex.slice(3,5),16), b = parseInt(hex.slice(5,7),16)
    return `rgba(${r},${g},${b},${alpha})`
  }
  return hex
}

// ─── Canvas Drawers ───────────────────────────────────────────────────────────

function drawWelcome(ctx, W, H) {
  ctx.fillStyle = 'rgba(74,96,112,0.4)'
  ctx.font = '500 15px "DM Sans"'
  ctx.textAlign = 'center'
  ctx.fillText('Select an algorithm and press COMPILE & RUN', W/2, H/2)
  ctx.font = '11px "JetBrains Mono"'
  ctx.fillStyle = 'rgba(74,96,112,0.25)'
  ctx.fillText('AlgoFlow — Interactive Compiler + Algorithm Visualizer', W/2, H/2 + 22)
}

function roundRect(ctx, x, y, w, h, r) {
  ctx.beginPath()
  ctx.moveTo(x+r, y)
  ctx.lineTo(x+w-r, y)
  ctx.quadraticCurveTo(x+w, y, x+w, y+r)
  ctx.lineTo(x+w, y+h-r)
  ctx.quadraticCurveTo(x+w, y+h, x+w-r, y+h)
  ctx.lineTo(x+r, y+h)
  ctx.quadraticCurveTo(x, y+h, x, y+h-r)
  ctx.lineTo(x, y+r)
  ctx.quadraticCurveTo(x, y, x+r, y)
  ctx.closePath()
}

function drawArray(ctx, W, H, step) {
  const arr = step.array
  if (!arr || !arr.length) return
  const n = arr.length
  const maxV = Math.max(...arr, 1)
  const bw = Math.min(62, (W - 120) / n)
  const gap = Math.max(3, bw * 0.18)
  const totalW = n * (bw + gap) - gap
  const sx = (W - totalW) / 2
  const maxH = H * 0.52
  const baseY = H * 0.76

  const sorted    = step.extra?.sorted_indices || []
  const comparing = step.highlights || []
  const swapping  = step.action === 'swap' ? step.highlights : []
  const pivot     = step.extra?.pivot_idx

  arr.forEach((val, i) => {
    const bh = Math.max(4, (val / maxV) * maxH)
    const x  = sx + i * (bw + gap)
    const y  = baseY - bh

    let fill = '#1e2a3a', stroke = '#2e3f52', textC = '#4a6070'
    if (sorted.includes(i))    { fill = 'rgba(16,185,129,0.18)';  stroke = '#10b981'; textC = '#10b981' }
    if (comparing.includes(i)) { fill = 'rgba(0,229,255,0.18)';   stroke = '#00e5ff'; textC = '#00e5ff' }
    if (swapping.includes(i))  { fill = 'rgba(245,158,11,0.22)';  stroke = '#f59e0b'; textC = '#f59e0b' }
    if (pivot === i)           { fill = 'rgba(124,58,237,0.22)';  stroke = '#7c3aed'; textC = '#c084fc' }

    ctx.shadowColor = stroke; ctx.shadowBlur = comparing.includes(i) || swapping.includes(i) ? 14 : 0
    const g = ctx.createLinearGradient(x, y, x, baseY)
    g.addColorStop(0, stroke + '88'); g.addColorStop(1, fill)
    ctx.fillStyle = g; ctx.strokeStyle = stroke; ctx.lineWidth = 1.5
    roundRect(ctx, x, y, bw, bh, 4); ctx.fill(); ctx.stroke()
    ctx.shadowBlur = 0

    ctx.fillStyle = textC
    ctx.font = `600 ${Math.min(12, bw * 0.36)}px "JetBrains Mono"`
    ctx.textAlign = 'center'
    ctx.fillText(val, x + bw/2, y - 6)
    ctx.fillStyle = 'rgba(74,96,112,0.8)'
    ctx.font = `${Math.min(10, bw * 0.30)}px "JetBrains Mono"`
    ctx.fillText(i, x + bw/2, baseY + 16)
  })

  // Binary search range bracket
  if (step.extra?.lo != null && step.extra?.hi != null && step.action !== 'found') {
    const lo = step.extra.lo, hi = step.extra.hi
    const lx = sx + lo * (bw + gap) - 4
    const rx = sx + hi * (bw + gap) + bw + 4
    ctx.strokeStyle = 'rgba(0,229,255,0.3)'
    ctx.lineWidth = 2; ctx.setLineDash([4,4])
    ctx.strokeRect(lx, baseY - maxH - 20, rx - lx, maxH + 12)
    ctx.setLineDash([])
    ctx.fillStyle = 'rgba(0,229,255,0.5)'
    ctx.font = '10px "JetBrains Mono"'
    ctx.textAlign = 'left'
    ctx.fillText(`search [${lo}..${hi}]`, lx, baseY - maxH - 26)
  }

  // Legend
  const legend = [
    { color: '#00e5ff', label: 'Comparing'  },
    { color: '#f59e0b', label: 'Swapping'   },
    { color: '#10b981', label: 'Sorted'     },
    { color: '#7c3aed', label: 'Pivot'      },
  ]
  legend.forEach((item, i) => {
    ctx.fillStyle = item.color
    ctx.fillRect(18, 18 + i * 20, 10, 10)
    ctx.fillStyle = 'rgba(221,230,240,0.55)'
    ctx.font = '11px "DM Sans"'; ctx.textAlign = 'left'
    ctx.fillText(item.label, 34, 28 + i * 20)
  })

  // Divider mid marker for merge
  if (step.extra?.mid != null) {
    const mx = sx + step.extra.mid * (bw + gap) + bw/2
    ctx.strokeStyle = 'rgba(124,58,237,0.5)'
    ctx.lineWidth = 1.5; ctx.setLineDash([3,3])
    ctx.beginPath(); ctx.moveTo(mx, baseY - maxH - 10); ctx.lineTo(mx, baseY); ctx.stroke()
    ctx.setLineDash([])
  }
}

function drawDP(ctx, W, H, step) {
  const dp = step.dp_table; if (!dp) return
  const n = dp.length
  const cellW = Math.min(70, (W - 80) / n)
  const cellH = 52
  const sx = (W - n * cellW) / 2
  const sy = H / 2 - cellH / 2

  ctx.fillStyle = 'rgba(74,96,112,0.4)'; ctx.font = '13px "Syne"'; ctx.textAlign = 'center'
  ctx.fillText('Dynamic Programming Table', W/2, sy - 30)

  dp.forEach((val, i) => {
    const x = sx + i * cellW
    const cur  = step.extra?.current === i
    const p1   = step.extra?.current > 1 && i === step.extra.current - 1
    const p2   = step.extra?.current > 1 && i === step.extra.current - 2

    let bg = '#1e2a3a', stroke = '#2e3f52', textC = '#dde6f0'
    if (cur) { bg = 'rgba(0,229,255,0.15)'; stroke = '#00e5ff'; textC = '#00e5ff' }
    else if (p1 || p2) { bg = 'rgba(124,58,237,0.15)'; stroke = '#7c3aed'; textC = '#a78bfa' }
    else if (val > 0)  { bg = 'rgba(16,185,129,0.08)'; stroke = '#2e3f52'; textC = '#86efac' }

    ctx.shadowColor = stroke; ctx.shadowBlur = cur ? 16 : 0
    ctx.fillStyle = bg; ctx.strokeStyle = stroke; ctx.lineWidth = 1.5
    roundRect(ctx, x+2, sy, cellW-4, cellH, 6); ctx.fill(); ctx.stroke()
    ctx.shadowBlur = 0

    ctx.fillStyle = 'rgba(74,96,112,0.7)'; ctx.font = '10px "JetBrains Mono"'
    ctx.textAlign = 'center'; ctx.fillText(`dp[${i}]`, x + cellW/2, sy - 8)
    ctx.fillStyle = textC; ctx.font = `bold ${val > 99 ? 13 : 16}px "JetBrains Mono"`
    ctx.fillText(val === 0 && i > 1 && step.extra?.current < i ? '?' : val, x + cellW/2, sy + cellH/2 + 6)
  })

  // Draw arrows showing which cells are summed
  const cur = step.extra?.current
  if (cur > 1 && cur < dp.length) {
    const c1x = sx + (cur-1) * cellW + cellW/2
    const c2x = sx + (cur-2) * cellW + cellW/2
    const ccx = sx + cur * cellW + cellW/2
    const ay  = sy + cellH + 22

    ctx.strokeStyle = 'rgba(124,58,237,0.5)'; ctx.lineWidth = 1.5; ctx.setLineDash([3,3])
    ctx.beginPath(); ctx.moveTo(c1x, sy+cellH); ctx.lineTo(c1x, ay); ctx.lineTo(ccx, ay); ctx.lineTo(ccx, sy+cellH); ctx.stroke()
    ctx.beginPath(); ctx.moveTo(c2x, sy+cellH); ctx.lineTo(c2x, ay+10); ctx.lineTo(ccx, ay+10); ctx.lineTo(ccx, sy+cellH); ctx.stroke()
    ctx.setLineDash([])
    ctx.fillStyle = 'rgba(124,58,237,0.8)'; ctx.font = '11px "JetBrains Mono"'; ctx.textAlign = 'center'
    ctx.fillText(`dp[${cur-1}] + dp[${cur-2}] = ${dp[cur]}`, ccx, ay + 26)
  }
}

function drawGraph(ctx, W, H, step) {
  const gs = step.graph_state; if (!gs) return
  const { graph, visited = [], current, order = [] } = gs
  const nodes = Object.keys(graph).map(Number)
  const n = nodes.length
  const r = Math.min(W, H) * 0.28
  const cx = W / 2, cy = H / 2 - 20
  const radius = 22

  // Node positions in a circle
  const pos = {}
  nodes.forEach((node, i) => {
    const angle = (2 * Math.PI * i) / n - Math.PI / 2
    pos[node] = { x: cx + r * Math.cos(angle), y: cy + r * Math.sin(angle) }
  })

  // Draw edges
  nodes.forEach(node => {
    ;(graph[node] || []).forEach(nbr => {
      const s = pos[node], t = pos[nbr]
      const dx = t.x - s.x, dy = t.y - s.y
      const dist = Math.sqrt(dx*dx + dy*dy)
      const ux = dx/dist * radius, uy = dy/dist * radius
      ctx.strokeStyle = 'rgba(46,63,82,0.9)'; ctx.lineWidth = 1.5
      ctx.beginPath(); ctx.moveTo(s.x + ux, s.y + uy); ctx.lineTo(t.x - ux, t.y - uy); ctx.stroke()
    })
  })

  // Draw nodes
  nodes.forEach(node => {
    const p = pos[node]
    const isVisited = visited.includes(node)
    const isCurrent = node === current

    ctx.shadowColor = isCurrent ? '#00e5ff' : isVisited ? '#10b981' : 'transparent'
    ctx.shadowBlur = isCurrent ? 20 : isVisited ? 10 : 0
    ctx.fillStyle = isCurrent ? 'rgba(0,229,255,0.25)' : isVisited ? 'rgba(16,185,129,0.2)' : '#1e2a3a'
    ctx.strokeStyle = isCurrent ? '#00e5ff' : isVisited ? '#10b981' : '#2e3f52'
    ctx.lineWidth = 2
    ctx.beginPath(); ctx.arc(p.x, p.y, radius, 0, Math.PI*2); ctx.fill(); ctx.stroke()
    ctx.shadowBlur = 0

    ctx.fillStyle = isCurrent ? '#00e5ff' : isVisited ? '#10b981' : '#dde6f0'
    ctx.font = 'bold 13px "JetBrains Mono"'; ctx.textAlign = 'center'
    ctx.fillText(node, p.x, p.y + 5)
  })

  // Order display
  if (order.length > 0) {
    ctx.fillStyle = 'rgba(74,96,112,0.6)'; ctx.font = '11px "JetBrains Mono"'; ctx.textAlign = 'center'
    ctx.fillText(`Visit order: ${order.join(' → ')}`, W/2, H - 30)
  }
}

function drawLCS(ctx, W, H, step) {
  const { dp, i: ri, j: rj, a, b } = step.extra || {}
  if (!dp || !a || !b) { drawWelcome(ctx, W, H); return }
  const rows = dp.length, cols = dp[0].length
  const cw = Math.min(36, (W - 100) / cols)
  const ch = Math.min(34, (H - 120) / rows)
  const sx = (W - cols * cw) / 2, sy = (H - rows * ch) / 2

  ctx.fillStyle = 'rgba(74,96,112,0.4)'; ctx.font = '12px "Syne"'; ctx.textAlign = 'center'
  ctx.fillText('LCS Dynamic Programming Table', W/2, sy - 20)

  dp.forEach((row, i) => {
    row.forEach((val, j) => {
      const x = sx + j * cw, y = sy + i * ch
      const active = (i === ri && j === rj)
      ctx.fillStyle = active ? 'rgba(0,229,255,0.15)' : val > 0 ? 'rgba(16,185,129,0.08)' : 'var(--panel)'
      ctx.strokeStyle = active ? '#00e5ff' : '#1e2a3a'
      ctx.lineWidth = active ? 1.5 : 0.5
      roundRect(ctx, x+1, y+1, cw-2, ch-2, 3); ctx.fill(); ctx.stroke()
      ctx.fillStyle = active ? '#00e5ff' : val > 0 ? '#10b981' : '#4a6070'
      ctx.font = `${cw > 28 ? 11 : 9}px "JetBrains Mono"'; ctx.textAlign = 'center'`
      ctx.fillText(val, x + cw/2, y + ch/2 + 4)
    })
  })
}
