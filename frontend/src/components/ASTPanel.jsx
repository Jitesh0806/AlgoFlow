import React, { useEffect, useRef } from 'react'
import * as d3 from 'd3'
import { useStore } from '../lib/store'

const NODE_COLORS = {
  Program: '#7c3aed', FunctionDecl: '#00e5ff', WhileStmt: '#f59e0b',
  ForStmt: '#f59e0b', IfStmt: '#ef4444', AssignStmt: '#10b981',
  ReturnStmt: '#f472b6', BinaryExpr: '#67e8f9', UnaryExpr: '#67e8f9',
  CallExpr: '#7dd3fc', IndexExpr: '#fcd34d', Identifier: '#dde6f0',
  IntLiteral: '#fcd34d', FloatLiteral: '#fcd34d', BoolLiteral: '#c084fc',
  ExprStmt: '#8ba0b8', MemberExpr: '#86efac', ArrayLiteral: '#f97316',
  BreakStmt: '#ef4444', ContinueStmt: '#ef4444',
}

function astToD3(node, depth = 0) {
  if (!node) return null
  const children = []

  const childFields = ['body', 'then_body', 'else_body', 'elif_clauses',
                       'elements', 'args', 'params']
  const exprFields  = ['condition', 'value', 'target', 'left', 'right',
                       'operand', 'obj', 'index', 'iterable', 'expr']

  exprFields.forEach(f => { if (node[f]) children.push(astToD3(node[f], depth+1)) })
  childFields.forEach(f => {
    if (Array.isArray(node[f])) {
      node[f].forEach(c => {
        if (c && typeof c === 'object' && c.node_type) children.push(astToD3(c, depth+1))
      })
    }
  })

  let label = node.node_type || '?'
  if (node.name)         label += `\n${node.name}`
  else if (node.op)      label += `\n${node.op}`
  else if (node.value !== undefined && typeof node.value !== 'object') label += `\n${node.value}`

  return {
    name:     label,
    type:     node.node_type,
    line:     node.line,
    children: children.filter(Boolean),
    _raw:     node,
  }
}

export default function ASTPanel() {
  const svgRef = useRef(null)
  const { compileResult } = useStore()

  useEffect(() => {
    if (!compileResult?.ast) return
    const root = astToD3(compileResult.ast)
    if (!root) return

    const el = svgRef.current
    const W  = el.clientWidth  || 800
    const H  = el.clientHeight || 600

    d3.select(el).selectAll('*').remove()

    const svg = d3.select(el)
      .attr('width', W).attr('height', H)

    const g = svg.append('g').attr('transform', 'translate(40, 20)')

    const tree = d3.tree().size([H - 40, W - 160])
    const hier = d3.hierarchy(root)
    tree(hier)

    // Links
    g.selectAll('.link')
      .data(hier.links())
      .join('path')
      .attr('class', 'link')
      .attr('d', d3.linkHorizontal().x(d => d.y).y(d => d.x))
      .attr('fill', 'none')
      .attr('stroke', '#1e2a3a')
      .attr('stroke-width', 1.5)

    // Nodes
    const node = g.selectAll('.node')
      .data(hier.descendants())
      .join('g')
      .attr('class', 'node')
      .attr('transform', d => `translate(${d.y},${d.x})`)

    // Boxes
    node.append('rect')
      .attr('x', -52).attr('y', -14).attr('width', 104).attr('height', 28)
      .attr('rx', 5)
      .attr('fill', '#141a22')
      .attr('stroke', d => NODE_COLORS[d.data.type] || '#2e3f52')
      .attr('stroke-width', 1.5)

    // Type label (top line)
    node.append('text')
      .attr('dy', -3)
      .attr('text-anchor', 'middle')
      .attr('fill', d => NODE_COLORS[d.data.type] || '#7c3aed')
      .attr('font-family', 'JetBrains Mono')
      .attr('font-size', 8)
      .text(d => d.data.name.split('\n')[0])

    // Value label (bottom line)
    node.append('text')
      .attr('dy', 10)
      .attr('text-anchor', 'middle')
      .attr('fill', '#dde6f0')
      .attr('font-family', 'JetBrains Mono')
      .attr('font-size', 9)
      .text(d => {
        const parts = d.data.name.split('\n')
        return parts[1] ? parts[1].substring(0, 12) : ''
      })

    // Zoom
    svg.call(d3.zoom().scaleExtent([0.3, 3]).on('zoom', e => {
      g.attr('transform', e.transform)
    }))

  }, [compileResult])

  if (!compileResult) return <Welcome icon="🌳" title="Abstract Syntax Tree" msg="Compile to view the parse tree" />

  return (
    <div style={{ height: '100%', overflow: 'hidden', background: 'var(--panel)', position: 'relative' }}>
      <div style={{ position: 'absolute', top: 10, right: 12, zIndex: 10 }}>
        <span className="badge badge-muted" style={{ fontSize: '0.6rem' }}>Scroll to zoom · Drag to pan</span>
      </div>
      <svg ref={svgRef} style={{ width: '100%', height: '100%' }} />
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
