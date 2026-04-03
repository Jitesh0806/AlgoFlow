"""
AlgoFlow CFG Builder — Constructs a Control Flow Graph from IR instructions.

Basic Block formation rules:
  - A new block starts at: function entry, any LABEL target, instruction after a JUMP
  - A block ends at: JUMP, JUMP_IF, JUMP_UNLESS, RETURN
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Set
from copy import deepcopy

from ..ir.ir import IRInstruction, IROpCode, IRFunction


@dataclass
class BasicBlock:
    id:           str
    label:        Optional[str]
    instructions: List[IRInstruction] = field(default_factory=list)
    successors:   List[str] = field(default_factory=list)   # block ids
    predecessors: List[str] = field(default_factory=list)
    is_entry:     bool = False
    is_exit:      bool = False
    has_dead_edge: bool = False

    def to_dict(self) -> dict:
        # Short display label
        display_lines = []
        for inst in self.instructions:
            if inst.op == IROpCode.COMMENT:
                continue
            s = str(inst).strip()
            if s:
                display_lines.append(s[:40])   # truncate long lines

        return {
            "id":           self.id,
            "label":        self.label,
            "display_lines": display_lines[:4],   # max 4 lines shown
            "successors":   self.successors,
            "predecessors": self.predecessors,
            "is_entry":     self.is_entry,
            "is_exit":      self.is_exit,
            "instruction_count": len(self.instructions),
        }


@dataclass
class CFGEdge:
    source: str
    target: str
    type:   str = "unconditional"   # "true", "false", "unconditional", "dead"

    def to_dict(self) -> dict:
        return {"source": self.source, "target": self.target, "type": self.type}


@dataclass
class CFG:
    function_name: str
    blocks: List[BasicBlock] = field(default_factory=list)
    edges:  List[CFGEdge]    = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "function_name": self.function_name,
            "blocks": [b.to_dict() for b in self.blocks],
            "edges":  [e.to_dict() for e in self.edges],
        }


class CFGBuilder:
    def build(self, func: IRFunction) -> CFG:
        insts = [i for i in func.instructions if not i.is_eliminated]
        cfg   = CFG(function_name=func.name)

        # ── Step 1: Find all block leaders ────────────────────────────────
        leaders: Set[int] = {0}
        for i, inst in enumerate(insts):
            if inst.op in (IROpCode.JUMP, IROpCode.JUMP_IF, IROpCode.JUMP_UNLESS,
                           IROpCode.RETURN):
                if i + 1 < len(insts):
                    leaders.add(i + 1)
            if inst.op == IROpCode.LABEL:
                leaders.add(i)

        leaders_sorted = sorted(leaders)

        # ── Step 2: Build basic blocks ─────────────────────────────────────
        label_to_block: Dict[str, str] = {}
        block_by_id:    Dict[str, BasicBlock] = {}

        for idx, start in enumerate(leaders_sorted):
            end = leaders_sorted[idx + 1] if idx + 1 < len(leaders_sorted) else len(insts)
            block_insts = insts[start:end]

            # Determine label for this block
            lbl = None
            if block_insts and block_insts[0].op == IROpCode.LABEL:
                lbl = block_insts[0].label

            block_id = lbl or f"BB{idx}"
            bb = BasicBlock(
                id=block_id,
                label=lbl,
                instructions=block_insts,
                is_entry=(idx == 0),
            )
            cfg.blocks.append(bb)
            block_by_id[block_id] = bb
            if lbl:
                label_to_block[lbl] = block_id

        # ── Step 3: Add edges ──────────────────────────────────────────────
        for idx, bb in enumerate(cfg.blocks):
            if not bb.instructions:
                continue
            last = bb.instructions[-1]

            next_block = cfg.blocks[idx + 1].id if idx + 1 < len(cfg.blocks) else None

            if last.op == IROpCode.JUMP:
                tgt = label_to_block.get(last.label, last.label)
                cfg.edges.append(CFGEdge(bb.id, tgt, "unconditional"))
                bb.successors.append(tgt)

            elif last.op in (IROpCode.JUMP_IF, IROpCode.JUMP_UNLESS):
                tgt = label_to_block.get(last.label, last.label)
                # true edge → jump target, false edge → fall-through
                if last.op == IROpCode.JUMP_IF:
                    cfg.edges.append(CFGEdge(bb.id, tgt, "true"))
                    bb.successors.append(tgt)
                    if next_block:
                        cfg.edges.append(CFGEdge(bb.id, next_block, "false"))
                        bb.successors.append(next_block)
                else:  # JUMP_UNLESS
                    cfg.edges.append(CFGEdge(bb.id, tgt, "false"))
                    bb.successors.append(tgt)
                    if next_block:
                        cfg.edges.append(CFGEdge(bb.id, next_block, "true"))
                        bb.successors.append(next_block)

            elif last.op == IROpCode.RETURN:
                bb.is_exit = True

            else:
                # Fall-through
                if next_block:
                    cfg.edges.append(CFGEdge(bb.id, next_block, "unconditional"))
                    bb.successors.append(next_block)

        # ── Step 4: Compute predecessors ──────────────────────────────────
        for edge in cfg.edges:
            tgt_bb = block_by_id.get(edge.target)
            if tgt_bb and edge.source not in tgt_bb.predecessors:
                tgt_bb.predecessors.append(edge.source)

        # ── Step 5: Mark unreachable blocks ────────────────────────────────
        reachable = self._reachable(cfg)
        for bb in cfg.blocks:
            if bb.id not in reachable and not bb.is_entry:
                for edge in cfg.edges:
                    if edge.source == bb.id or edge.target == bb.id:
                        edge.type = "dead"

        return cfg

    def _reachable(self, cfg: CFG) -> Set[str]:
        if not cfg.blocks:
            return set()
        visited: Set[str] = set()
        queue = [cfg.blocks[0].id]
        adj: Dict[str, List[str]] = {b.id: b.successors for b in cfg.blocks}
        while queue:
            cur = queue.pop()
            if cur in visited:
                continue
            visited.add(cur)
            queue.extend(adj.get(cur, []))
        return visited
