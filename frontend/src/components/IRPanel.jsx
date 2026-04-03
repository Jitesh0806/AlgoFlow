import React from 'react'
import { useStore } from '../lib/store'

const OP_COLORS = {
  ASSIGN: '#f59e0b', ADD: '#10b981', SUB: '#10b981', MUL: '#10b981', DIV: '#10b981', MOD: '#10b981',
  EQ: '#00e5ff', NE: '#00e5ff', LT: '#00e5ff', GT: '#00e5ff', LE: '#00e5ff', GE: '#00e5ff',
  JUMP: '#7c3aed', JUMP_IF: '#7c3aed', JUMP_UNLESS: '#7c3aed',
  LABEL: '#4a6070', RETURN: '#f472b6', CALL: '#7dd3fc',
  LOAD_IDX: '#fcd34d', STORE_IDX: '#fcd34d',
  FUNC_BEGIN: '#00e5ff', FUNC_END: '#00e5ff',
  PARAM: '#f97316', ALLOC: '#f97316',
  NEG: '#10b981', NOT: '#10b981', AND: '#7c3aed', OR: '#7c3aed',
  NOP: '#4a6070', COMMENT: '#4a6070',
}

function IRLine({ inst, highlight }) {
  if (!inst) return null
  const dead  = inst.is_dead || inst.is_eliminated
  const opt   = inst.opt_note && !dead

  const opColor = OP_COLORS[inst.op] || '#dde6f0'

  function fmtInst() {
    const op = inst.op
    if (op === 'LABEL')       return <><span style={{ color: '#4a6070' }}>{inst.label}:</span></>
    if (op === 'FUNC_BEGIN')  return <><span style={{ color: '#00e5ff' }}>// BEGIN {inst.label}</span></>
    if (op === 'FUNC_END')    return <><span style={{ color: '#4a6070' }}>// END {inst.label}</span></>
    if (op === 'COMMENT')     return <><span style={{ color: '#4a6070', fontStyle: 'italic' }}>; {inst.arg1}</span></>
    if (op === 'JUMP')        return <><span style={{ color: opColor }}>JUMP </span><span style={{ color: '#c084fc' }}>→ {inst.label}</span></>
    if (op === 'JUMP_IF')     return <><span style={{ color: opColor }}>JUMP_IF </span><span style={{ color: '#dde6f0' }}>{inst.arg1}</span><span style={{ color: opColor }}> → </span><span style={{ color: '#c084fc' }}>{inst.label}</span></>
    if (op === 'JUMP_UNLESS') return <><span style={{ color: opColor }}>JUMP_UNLESS </span><span style={{ color: '#dde6f0' }}>{inst.arg1}</span><span style={{ color: opColor }}> → </span><span style={{ color: '#c084fc' }}>{inst.label}</span></>
    if (op === 'RETURN')      return <><span style={{ color: '#f472b6' }}>RETURN </span><span style={{ color: '#dde6f0' }}>{inst.arg1 || ''}</span></>
    if (op === 'PARAM')       return <><span style={{ color: opColor }}>PARAM </span><span style={{ color: '#dde6f0' }}>{inst.arg1}</span></>
    if (op === 'CALL')        return <><span style={{ color: '#86efac' }}>{inst.result}</span><span style={{ color: '#dde6f0' }}> = </span><span style={{ color: '#7dd3fc' }}>CALL {inst.arg1}</span><span style={{ color: '#dde6f0' }}>({inst.arg2})</span></>
    if (op === 'LOAD_IDX')    return <><span style={{ color: '#86efac' }}>{inst.result}</span><span style={{ color: '#dde6f0' }}> = </span><span style={{ color: '#fcd34d' }}>{inst.arg1}[{inst.arg2}]</span></>
    if (op === 'STORE_IDX')   return <><span style={{ color: '#fcd34d' }}>{inst.result}[{inst.arg1}]</span><span style={{ color: '#dde6f0' }}> = {inst.arg2}</span></>
    if (op === 'ASSIGN')      return <><span style={{ color: '#86efac' }}>{inst.result}</span><span style={{ color: '#dde6f0' }}> = {inst.arg1}</span></>
    if (op === 'NEG')         return <><span style={{ color: '#86efac' }}>{inst.result}</span><span style={{ color: '#dde6f0' }}> = </span><span style={{ color: opColor }}>-{inst.arg1}</span></>
    if (op === 'ALLOC')       return <><span style={{ color: '#86efac' }}>{inst.result}</span><span style={{ color: '#dde6f0' }}> = </span><span style={{ color: '#f97316' }}>ALLOC({inst.arg1})</span></>

    const SYM = { ADD:'+', SUB:'-', MUL:'*', DIV:'/', MOD:'%', EQ:'==', NE:'!=', LT:'<', GT:'>', LE:'<=', GE:'>=', AND:'&&', OR:'||' }
    const sym = SYM[op]
    if (sym) return <><span style={{ color: '#86efac' }}>{inst.result}</span><span style={{ color: '#dde6f0' }}> = {inst.arg1} </span><span style={{ color: opColor }}>{sym}</span><span style={{ color: '#dde6f0' }}> {inst.arg2}</span></>
    return <span style={{ color: '#dde6f0' }}>{op} {inst.result} {inst.arg1} {inst.arg2}</span>
  }

  return (
    <div style={{
      display: 'flex', alignItems: 'center', gap: 8,
      padding: '2px 6px', borderRadius: 4,
      background: highlight ? 'rgba(0,229,255,0.07)' : 'transparent',
      opacity: dead ? 0.35 : 1,
      textDecoration: dead ? 'line-through' : 'none',
      fontFamily: 'JetBrains Mono', fontSize: '0.73rem', lineHeight: '1.8',
      borderLeft: `2px solid ${opt ? 'var(--accent4)' : dead ? 'var(--danger)' : 'transparent'}`,
      paddingLeft: 10,
    }}>
      <span style={{ color: 'var(--muted)', minWidth: 34, fontSize: '0.62rem' }}>{inst.index ?? ''}</span>
      <span style={{ flex: 1 }}>{fmtInst()}</span>
      {inst.opt_note && (
        <span style={{
          fontSize: '0.6rem', padding: '1px 5px', borderRadius: 10,
          background: dead ? 'rgba(239,68,68,0.1)' : 'rgba(16,185,129,0.1)',
          color: dead ? 'var(--danger)' : 'var(--accent4)',
          whiteSpace: 'nowrap', flexShrink: 0,
        }}>
          {inst.opt_note}
        </span>
      )}
    </div>
  )
}

function FunctionIR({ funcData, side }) {
  const insts = side === 'before' ? funcData.before : funcData.after
  return (
    <div style={{ marginBottom: 16 }}>
      <div style={{
        fontFamily: 'JetBrains Mono', fontSize: '0.68rem', color: 'var(--accent)',
        padding: '4px 8px', marginBottom: 4,
        borderBottom: '1px solid var(--border)', background: 'rgba(0,229,255,0.04)',
      }}>
        function {funcData.function}
      </div>
      {insts?.map((inst, i) => <IRLine key={i} inst={inst} />)}
    </div>
  )
}

export default function IRPanel() {
  const { compileResult } = useStore()

  if (!compileResult) {
    return <Welcome icon="📋" title="Intermediate Representation" msg="Compile to view Three-Address Code" />
  }

  const irAfter = compileResult.ir_after || []

  return (
    <div style={{ display: 'flex', height: '100%', overflow: 'hidden' }}>
      {/* Before */}
      <div style={{ flex: 1, overflow: 'auto', padding: 14, borderRight: '1px solid var(--border)' }}>
        <div style={{ fontFamily: 'Syne', fontWeight: 700, fontSize: '0.7rem', color: 'var(--text2)', textTransform: 'uppercase', letterSpacing: '0.1em', marginBottom: 12, borderBottom: '1px solid var(--border)', paddingBottom: 6 }}>
          Before Optimization
          <span className="badge badge-orange" style={{ marginLeft: 8, fontSize: '0.6rem' }}>
            {compileResult.stats?.ir_before_count} instr
          </span>
        </div>
        {irAfter.map((fd, i) => <FunctionIR key={i} funcData={fd} side="before" />)}
      </div>

      {/* After */}
      <div style={{ flex: 1, overflow: 'auto', padding: 14 }}>
        <div style={{ fontFamily: 'Syne', fontWeight: 700, fontSize: '0.7rem', color: 'var(--text2)', textTransform: 'uppercase', letterSpacing: '0.1em', marginBottom: 12, borderBottom: '1px solid var(--border)', paddingBottom: 6 }}>
          After Optimization
          <span className="badge badge-green" style={{ marginLeft: 8, fontSize: '0.6rem' }}>
            {compileResult.stats?.ir_after_count} instr
          </span>
          <span className="badge badge-purple" style={{ marginLeft: 6, fontSize: '0.6rem' }}>
            -{compileResult.stats?.reduction_pct}%
          </span>
        </div>
        {irAfter.map((fd, i) => <FunctionIR key={i} funcData={fd} side="after" />)}
      </div>
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
