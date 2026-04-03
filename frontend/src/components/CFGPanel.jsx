import React, { useEffect, useRef } from 'react'
import * as d3 from 'd3'
import { useStore } from '../lib/store'

const BLOCK_COLORS = {
  entry: '#10b981', exit: '#ef4444', cond: '#7c3aed', normal: '#2e3f52',
}
const EDGE_COLORS = {
  true: '#10b981', false: '#ef4444', unconditional: '#4a6070', dead: '#1e2a3a',
}

export default function CFGPanel() {
  const svgRef = useRef(null)
  const { compileResult } = useStore()

  useEffect(() => {
    if (!compileResult?.cfg?.length) return
    const cfgData = compileResult.cfg[0]  // first function

    const el = svgRef.current
    const W  = el.clientWidth  || 800
    const H  = el.clientHeight || 600

    d3.select(el).selectAll('*').remove()

    const svg = d3.select(el).attr('width', W).attr('height', H)

    // Arrowhead marker
    const defs = svg.append('defs')
    ;['unconditional','true','false','dead'].forEach(t => {
      defs.append('marker')
        .attr('id', `arrow-${t}`)
        .attr('markerWidth', 8).attr('markerHeight', 6)
        .attr('refX', 7).attr('refY', 3)
        .attr('orient', 'auto')
        .append('polygon')
        .attr('points', '0 0, 8 3, 0 6')
        .attr('fill', EDGE_COLORS[t] || '#4a6070')
    })

    const g = svg.append('g')

    const blocks = cfgData.blocks || []
    const edges  = cfgData.edges  || []

    // Layout: hierarchical top-down by index
    const BW = 130, BH = 48, GAP_X = 50, GAP_Y = 70
    const cols = Math.ceil(Math.sqrt(blocks.length))

    const nodeById = {}
    blocks.forEach((b, i) => {
      const col = i % cols
      const row = Math.floor(i / cols)
      b._x = 30 + col * (BW + GAP_X)
      b._y = 30 + row * (BH + GAP_Y)
      nodeById[b.id] = b
    })

    // Draw edges
    edges.forEach(edge => {
      const s = nodeById[edge.source], t = nodeById[edge.target]
      if (!s || !t) return
      const color = EDGE_COLORS[edge.type] || '#4a6070'
      const mx = (s._x + BW/2 + t._x + BW/2) / 2
      const my = (s._y + BH/2 + t._y + BH/2) / 2
      g.append('path')
        .attr('d', `M${s._x+BW/2},${s._y+BH} C${s._x+BW/2},${s._y+BH+20} ${t._x+BW/2},${t._y-20} ${t._x+BW/2},${t._y}`)
        .attr('fill', 'none')
        .attr('stroke', color)
        .attr('stroke-width', edge.type === 'dead' ? 1 : 1.5)
        .attr('stroke-dasharray', edge.type === 'dead' ? '4,4' : null)
        .attr('marker-end', `url(#arrow-${edge.type})`)

      // Edge label
      if (edge.type === 'true' || edge.type === 'false') {
        g.append('text')
          .attr('x', mx).attr('y', my)
          .attr('text-anchor', 'middle')
          .attr('fill', color)
          .attr('font-size', 9)
          .attr('font-family', 'JetBrains Mono')
          .text(edge.type === 'true' ? 'T' : 'F')
      }
    })

    // Draw blocks
    blocks.forEach(block => {
      const bg = g.append('g').attr('transform', `translate(${block._x},${block._y})`)

      const stroke = block.is_entry ? BLOCK_COLORS.entry : block.is_exit ? BLOCK_COLORS.exit : '#2e3f52'
      const fill   = block.is_entry ? 'rgba(16,185,129,0.1)' : block.is_exit ? 'rgba(239,68,68,0.08)' : '#141a22'

      bg.append('rect')
        .attr('width', BW).attr('height', BH)
        .attr('rx', 4)
        .attr('fill', fill)
        .attr('stroke', stroke)
        .attr('stroke-width', 1.5)

      // Block ID / label
      bg.append('text')
        .attr('x', BW/2).attr('y', 13)
        .attr('text-anchor', 'middle')
        .attr('fill', stroke)
        .attr('font-size', 9)
        .attr('font-weight', 'bold')
        .attr('font-family', 'JetBrains Mono')
        .text(block.label || block.id)

      // Instructions preview
      const preview = (block.display_lines || []).slice(0, 2)
      preview.forEach((line, i) => {
        bg.append('text')
          .attr('x', BW/2).attr('y', 25 + i * 11)
          .attr('text-anchor', 'middle')
          .attr('fill', '#8ba0b8')
          .attr('font-size', 8)
          .attr('font-family', 'JetBrains Mono')
          .text(line.length > 18 ? line.slice(0,18) + '…' : line)
      })

      if (block.is_entry || block.is_exit) {
        bg.append('text')
          .attr('x', BW - 4).attr('y', BH - 4)
          .attr('text-anchor', 'end')
          .attr('fill', stroke).attr('font-size', 7)
          .attr('font-family', 'JetBrains Mono')
          .text(block.is_entry ? 'ENTRY' : 'EXIT')
      }
    })

    // Pan + zoom
    svg.call(d3.zoom().scaleExtent([0.3, 3]).on('zoom', e => g.attr('transform', e.transform)))

  }, [compileResult])

  if (!compileResult) {
    return <Welcome />
  }

  const cfgData = compileResult.cfg?.[0]
  return (
    <div style={{ height: '100%', overflow: 'hidden', background: 'var(--panel)', position: 'relative' }}>
      {/* Legend */}
      <div style={{ position: 'absolute', top: 10, left: 12, zIndex: 10, display: 'flex', gap: 8, flexWrap: 'wrap' }}>
        {[['Entry', '#10b981'], ['Exit', '#ef4444'], ['Cond', '#7c3aed'], ['Normal', '#2e3f52'],
          ['True edge', '#10b981'], ['False edge', '#ef4444'], ['Dead edge', '#1e2a3a']].map(([l, c]) => (
          <div key={l} style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
            <div style={{ width: 10, height: 10, borderRadius: 2, background: c, border: `1px solid ${c}` }} />
            <span style={{ fontSize: '0.62rem', color: 'var(--text2)', fontFamily: 'JetBrains Mono' }}>{l}</span>
          </div>
        ))}
      </div>
      <div style={{ position: 'absolute', top: 10, right: 12, zIndex: 10 }}>
        <span className="badge badge-muted" style={{ fontSize: '0.6rem' }}>
          {cfgData?.blocks?.length} blocks · {cfgData?.edges?.length} edges · Scroll to zoom
        </span>
      </div>
      <svg ref={svgRef} style={{ width: '100%', height: '100%' }} />
    </div>
  )
}

function Welcome() {
  return (
    <div style={{ height: '100%', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: 10, color: 'var(--muted)' }}>
      <div style={{ fontSize: '3rem', opacity: 0.25 }}>🔀</div>
      <h3 style={{ fontFamily: 'Syne', color: 'var(--text)', fontSize: '1rem' }}>Control Flow Graph</h3>
      <p style={{ fontSize: '0.8rem', color: 'var(--text2)' }}>Compile to visualize the program's control flow</p>
    </div>
  )
}
