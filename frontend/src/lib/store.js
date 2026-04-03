// AlgoFlow — Global State (Zustand)
import { create } from 'zustand'

const DEFAULT_PASSES = { DCE: true, CP: true, CF: true, CSE: true, LICM: true }

export const useStore = create((set, get) => ({
  // ── Editor ──────────────────────────────────────────────
  source:    '',
  algorithm: 'bubble',
  inputData: [64, 34, 25, 12, 22, 11, 90],
  passes:    { ...DEFAULT_PASSES },

  setSource:    (s)  => set({ source: s }),
  setAlgorithm: (a)  => set({ algorithm: a }),
  setInputData: (d)  => set({ inputData: d }),
  togglePass:   (p)  => set(s => ({ passes: { ...s.passes, [p]: !s.passes[p] } })),

  // ── Compilation Result ──────────────────────────────────
  compileResult: null,
  compileError:  null,
  compiling:     false,

  setCompiling:     (v) => set({ compiling: v }),
  setCompileResult: (r) => set({ compileResult: r, compileError: null }),
  setCompileError:  (e) => set({ compileError: e, compileResult: null }),

  // ── Simulation ──────────────────────────────────────────
  simResult:    null,
  simError:     null,
  simulating:   false,
  currentStep:  0,
  playing:      false,
  playSpeed:    500,   // ms per step

  setSimResult:   (r) => set({ simResult: r, simError: null, currentStep: 0, playing: false }),
  setSimError:    (e) => set({ simError: e }),
  setSimulating:  (v) => set({ simulating: v }),
  setCurrentStep: (n) => set({ currentStep: n }),
  setPlaying:     (v) => set({ playing: v }),
  setPlaySpeed:   (v) => set({ playSpeed: v }),

  stepForward: () => {
    const { simResult, currentStep } = get()
    if (!simResult) return
    const max = simResult.steps.length - 1
    if (currentStep < max) set({ currentStep: currentStep + 1 })
    else set({ playing: false })
  },
  stepBack: () => {
    const { currentStep } = get()
    if (currentStep > 0) set({ currentStep: currentStep - 1 })
  },

  // ── Active tab ──────────────────────────────────────────
  activeTab: 'animation',
  setActiveTab: (t) => set({ activeTab: t }),

  // ── Selected IR instruction (for CFG sync) ──────────────
  selectedIRIndex: -1,
  setSelectedIRIndex: (i) => set({ selectedIRIndex: i }),
}))
