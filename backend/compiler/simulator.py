"""
AlgoFlow Execution Simulator

Interprets the compiled IR (or falls back to direct algorithm simulation)
to produce step-by-step execution traces for the frontend visualizer.

Each step contains:
  - state:        current data structure snapshot
  - action:       what just happened (compare, swap, recurse, etc.)
  - highlights:   indices/nodes to highlight
  - description:  human-readable explanation
  - metrics:      running counters (comparisons, swaps, accesses, etc.)
  - ir_index:     which IR instruction is currently executing
"""

from __future__ import annotations
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
import copy


@dataclass
class ExecutionStep:
    step_number:  int
    action:       str                    # "compare", "swap", "assign", "call", "return", ...
    description:  str
    array:        Optional[List]  = None # current array state
    dp_table:     Optional[List]  = None # for DP algorithms
    graph_state:  Optional[Dict]  = None # for graph algorithms
    highlights:   List[int]       = field(default_factory=list)
    comparisons:  int             = 0
    swaps:        int             = 0
    accesses:     int             = 0
    ir_index:     int             = -1
    extra:        Dict[str, Any]  = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "step_number":  self.step_number,
            "action":       self.action,
            "description":  self.description,
            "array":        self.array,
            "dp_table":     self.dp_table,
            "graph_state":  self.graph_state,
            "highlights":   self.highlights,
            "comparisons":  self.comparisons,
            "swaps":        self.swaps,
            "accesses":     self.accesses,
            "ir_index":     self.ir_index,
            "extra":        self.extra,
        }


class Simulator:
    """Generates animation traces for supported algorithm types."""

    def simulate(self, algorithm: str, input_data: List[int]) -> Dict[str, Any]:
        handlers = {
            "bubble":     self._bubble_sort,
            "selection":  self._selection_sort,
            "insertion":  self._insertion_sort,
            "merge":      self._merge_sort,
            "quick":      self._quick_sort,
            "binary":     self._binary_search,
            "linear":     self._linear_search,
            "bfs":        self._bfs,
            "dfs":        self._dfs,
            "fib":        self._fibonacci_dp,
            "lcs":        self._lcs,
            "knapsack":   self._knapsack,
        }
        handler = handlers.get(algorithm, self._bubble_sort)
        steps, metrics = handler(input_data)
        return {
            "steps":   [s.to_dict() for s in steps],
            "metrics": metrics,
            "algorithm": algorithm,
            "input":   input_data,
        }

    # ── Helpers ──────────────────────────────────────────────────────────

    def _step(self, n: int, action: str, desc: str, arr: list,
              highlights=None, **extra) -> ExecutionStep:
        return ExecutionStep(
            step_number=n, action=action, description=desc,
            array=copy.copy(arr),
            highlights=highlights or [],
            extra=extra
        )

    # ── Bubble Sort ──────────────────────────────────────────────────────

    def _bubble_sort(self, arr: List[int]):
        a = list(arr)
        n = len(a)
        steps = []
        sn    = 0
        cmps  = 0
        swps  = 0
        accs  = 0

        steps.append(ExecutionStep(sn, "init", f"Start Bubble Sort  n={n}", array=copy.copy(a),
                                   extra={"sorted_indices": []}))
        sorted_idx = []

        for i in range(n - 1):
            early_exit = True
            for j in range(n - i - 1):
                accs += 2; cmps += 1; sn += 1
                s = ExecutionStep(sn, "compare",
                    f"Compare arr[{j}]={a[j]} vs arr[{j+1}]={a[j+1]}",
                    array=copy.copy(a), highlights=[j, j+1],
                    comparisons=cmps, swaps=swps, accesses=accs,
                    extra={"sorted_indices": list(sorted_idx), "pass": i})
                steps.append(s)

                if a[j] > a[j + 1]:
                    a[j], a[j+1] = a[j+1], a[j]
                    swps += 1; sn += 1
                    s2 = ExecutionStep(sn, "swap",
                        f"Swap arr[{j}]↔arr[{j+1}]  (now {a[j]}, {a[j+1]})",
                        array=copy.copy(a), highlights=[j, j+1],
                        comparisons=cmps, swaps=swps, accesses=accs,
                        extra={"sorted_indices": list(sorted_idx), "pass": i})
                    steps.append(s2)
                    early_exit = False

            sorted_idx.append(n - 1 - i)
            sn += 1
            steps.append(ExecutionStep(sn, "pass_done",
                f"Pass {i+1} complete — element {a[n-1-i]} settled at index {n-1-i}",
                array=copy.copy(a), highlights=[n-1-i],
                comparisons=cmps, swaps=swps, accesses=accs,
                extra={"sorted_indices": list(sorted_idx), "pass": i}))

            if early_exit:
                sn += 1
                sorted_idx = list(range(n))
                steps.append(ExecutionStep(sn, "early_exit",
                    "No swaps in this pass — array is sorted (early exit triggered!)",
                    array=copy.copy(a), highlights=list(range(n)),
                    comparisons=cmps, swaps=swps, accesses=accs,
                    extra={"sorted_indices": sorted_idx}))
                break

        sn += 1
        steps.append(ExecutionStep(sn, "done", "Bubble Sort complete ✓",
            array=copy.copy(a), highlights=list(range(n)),
            comparisons=cmps, swaps=swps, accesses=accs,
            extra={"sorted_indices": list(range(n))}))

        return steps, {"comparisons": cmps, "swaps": swps, "accesses": accs,
                       "complexity": {"time": "O(n²)", "space": "O(1)"}}

    # ── Selection Sort ───────────────────────────────────────────────────

    def _selection_sort(self, arr: List[int]):
        a = list(arr); n = len(a)
        steps = []; sn = 0; cmps = 0; swps = 0; accs = 0
        sorted_idx = []

        steps.append(ExecutionStep(sn, "init", f"Start Selection Sort  n={n}", array=copy.copy(a)))

        for i in range(n):
            min_idx = i
            for j in range(i+1, n):
                accs += 2; cmps += 1; sn += 1
                steps.append(ExecutionStep(sn, "compare",
                    f"Compare arr[{j}]={a[j]} with current min arr[{min_idx}]={a[min_idx]}",
                    array=copy.copy(a), highlights=[j, min_idx],
                    comparisons=cmps, swaps=swps, accesses=accs,
                    extra={"sorted_indices": sorted_idx, "min_idx": min_idx}))
                if a[j] < a[min_idx]:
                    min_idx = j

            if min_idx != i:
                a[i], a[min_idx] = a[min_idx], a[i]; swps += 1; sn += 1
                steps.append(ExecutionStep(sn, "swap",
                    f"Swap minimum {a[i]} to position {i}",
                    array=copy.copy(a), highlights=[i, min_idx],
                    comparisons=cmps, swaps=swps, accesses=accs,
                    extra={"sorted_indices": sorted_idx}))
            sorted_idx.append(i)

        steps.append(ExecutionStep(sn+1, "done", "Selection Sort complete ✓",
            array=copy.copy(a), highlights=list(range(n)),
            comparisons=cmps, swaps=swps, accesses=accs,
            extra={"sorted_indices": list(range(n))}))

        return steps, {"comparisons": cmps, "swaps": swps, "accesses": accs,
                       "complexity": {"time": "O(n²)", "space": "O(1)"}}

    # ── Insertion Sort ───────────────────────────────────────────────────

    def _insertion_sort(self, arr: List[int]):
        a = list(arr); n = len(a)
        steps = []; sn = 0; cmps = 0; swps = 0; accs = 0

        steps.append(ExecutionStep(sn, "init", f"Start Insertion Sort  n={n}", array=copy.copy(a)))

        for i in range(1, n):
            key = a[i]; j = i - 1; sn += 1
            steps.append(ExecutionStep(sn, "pick",
                f"Pick key={key} at index {i}",
                array=copy.copy(a), highlights=[i],
                comparisons=cmps, swaps=swps, accesses=accs))
            while j >= 0 and a[j] > key:
                cmps += 1; accs += 1; sn += 1
                a[j+1] = a[j]; swps += 1; j -= 1
                steps.append(ExecutionStep(sn, "shift",
                    f"Shift arr[{j+1}]={a[j+1]} right",
                    array=copy.copy(a), highlights=[j+1, j+2],
                    comparisons=cmps, swaps=swps, accesses=accs))
            a[j+1] = key; sn += 1
            steps.append(ExecutionStep(sn, "insert",
                f"Insert key={key} at position {j+1}",
                array=copy.copy(a), highlights=[j+1],
                comparisons=cmps, swaps=swps, accesses=accs))

        steps.append(ExecutionStep(sn+1, "done", "Insertion Sort complete ✓",
            array=copy.copy(a), highlights=list(range(n)),
            comparisons=cmps, swaps=swps, accesses=accs))

        return steps, {"comparisons": cmps, "swaps": swps, "accesses": accs,
                       "complexity": {"time": "O(n²)", "space": "O(1)"}}

    # ── Merge Sort ───────────────────────────────────────────────────────

    def _merge_sort(self, arr: List[int]):
        a = list(arr); n = len(a)
        steps = []; sn_box = [0]; cmps_box = [0]; swps_box = [0]; accs_box = [0]

        steps.append(ExecutionStep(sn_box[0], "init", f"Start Merge Sort  n={n}", array=copy.copy(a)))

        def merge(a, lo, mid, hi):
            left  = a[lo:mid+1]
            right = a[mid+1:hi+1]
            i = j = 0; k = lo
            while i < len(left) and j < len(right):
                accs_box[0] += 2; cmps_box[0] += 1; sn_box[0] += 1
                if left[i] <= right[j]:
                    a[k] = left[i]; i += 1
                else:
                    a[k] = right[j]; j += 1
                swps_box[0] += 1; k += 1
                steps.append(ExecutionStep(sn_box[0], "merge",
                    f"Merge: placed {a[k-1]} at index {k-1}",
                    array=copy.copy(a), highlights=[k-1],
                    comparisons=cmps_box[0], swaps=swps_box[0], accesses=accs_box[0],
                    extra={"lo": lo, "mid": mid, "hi": hi}))
            while i < len(left):  a[k] = left[i];  i += 1; k += 1
            while j < len(right): a[k] = right[j]; j += 1; k += 1

        def msort(a, lo, hi):
            if lo >= hi: return
            mid = (lo + hi) // 2
            sn_box[0] += 1
            steps.append(ExecutionStep(sn_box[0], "divide",
                f"Divide [{lo}..{hi}] at mid={mid}",
                array=copy.copy(a), highlights=[lo, hi],
                comparisons=cmps_box[0], swaps=swps_box[0], accesses=accs_box[0],
                extra={"lo": lo, "hi": hi, "mid": mid}))
            msort(a, lo, mid)
            msort(a, mid+1, hi)
            merge(a, lo, mid, hi)

        msort(a, 0, n-1)
        steps.append(ExecutionStep(sn_box[0]+1, "done", "Merge Sort complete ✓",
            array=copy.copy(a), highlights=list(range(n)),
            comparisons=cmps_box[0], swaps=swps_box[0], accesses=accs_box[0]))

        return steps, {"comparisons": cmps_box[0], "swaps": swps_box[0],
                       "accesses": accs_box[0], "complexity": {"time": "O(n log n)", "space": "O(n)"}}

    # ── Quick Sort ───────────────────────────────────────────────────────

    def _quick_sort(self, arr: List[int]):
        a = list(arr); n = len(a)
        steps = []; sn_b = [0]; c_b = [0]; s_b = [0]; ac_b = [0]

        steps.append(ExecutionStep(sn_b[0], "init", f"Start Quick Sort  n={n}", array=copy.copy(a)))

        def partition(a, lo, hi):
            pivot = a[hi]; i = lo - 1
            sn_b[0] += 1
            steps.append(ExecutionStep(sn_b[0], "pivot",
                f"Choose pivot={pivot} at index {hi}",
                array=copy.copy(a), highlights=[hi],
                comparisons=c_b[0], swaps=s_b[0], accesses=ac_b[0],
                extra={"pivot_idx": hi, "lo": lo, "hi": hi}))
            for j in range(lo, hi):
                ac_b[0] += 2; c_b[0] += 1; sn_b[0] += 1
                steps.append(ExecutionStep(sn_b[0], "compare",
                    f"arr[{j}]={a[j]} vs pivot={pivot}",
                    array=copy.copy(a), highlights=[j, hi],
                    comparisons=c_b[0], swaps=s_b[0], accesses=ac_b[0],
                    extra={"pivot_idx": hi, "lo": lo, "hi": hi, "i": i}))
                if a[j] <= pivot:
                    i += 1
                    if i != j:
                        a[i], a[j] = a[j], a[i]; s_b[0] += 1; sn_b[0] += 1
                        steps.append(ExecutionStep(sn_b[0], "swap",
                            f"Swap arr[{i}]↔arr[{j}]",
                            array=copy.copy(a), highlights=[i, j],
                            comparisons=c_b[0], swaps=s_b[0], accesses=ac_b[0],
                            extra={"pivot_idx": hi}))
            a[i+1], a[hi] = a[hi], a[i+1]; s_b[0] += 1; sn_b[0] += 1
            steps.append(ExecutionStep(sn_b[0], "place_pivot",
                f"Place pivot {pivot} at index {i+1}",
                array=copy.copy(a), highlights=[i+1],
                comparisons=c_b[0], swaps=s_b[0], accesses=ac_b[0],
                extra={"pivot_idx": i+1}))
            return i + 1

        def qsort(a, lo, hi):
            if lo < hi:
                p = partition(a, lo, hi)
                qsort(a, lo, p-1)
                qsort(a, p+1, hi)

        qsort(a, 0, n-1)
        steps.append(ExecutionStep(sn_b[0]+1, "done", "Quick Sort complete ✓",
            array=copy.copy(a), highlights=list(range(n)),
            comparisons=c_b[0], swaps=s_b[0], accesses=ac_b[0]))

        return steps, {"comparisons": c_b[0], "swaps": s_b[0],
                       "accesses": ac_b[0], "complexity": {"time": "O(n log n) avg", "space": "O(log n)"}}

    # ── Binary Search ────────────────────────────────────────────────────

    def _binary_search(self, arr: List[int]):
        a = sorted(arr); n = len(a)
        target = a[n // 2]
        steps = []; sn = 0; cmps = 0; accs = 0
        lo, hi = 0, n - 1

        steps.append(ExecutionStep(sn, "init",
            f"Binary Search: target={target}  (sorted array)",
            array=copy.copy(a), extra={"target": target, "lo": lo, "hi": hi}))

        while lo <= hi:
            mid = (lo + hi) // 2; accs += 1; cmps += 1; sn += 1
            steps.append(ExecutionStep(sn, "compare",
                f"mid={mid}  arr[mid]={a[mid]}  target={target}",
                array=copy.copy(a), highlights=[mid],
                comparisons=cmps, accesses=accs,
                extra={"target": target, "lo": lo, "hi": hi, "mid": mid}))

            if a[mid] == target:
                sn += 1
                steps.append(ExecutionStep(sn, "found",
                    f"Found target {target} at index {mid} ✓",
                    array=copy.copy(a), highlights=[mid],
                    comparisons=cmps, accesses=accs,
                    extra={"target": target, "found_idx": mid}))
                break
            elif a[mid] < target:
                lo = mid + 1; sn += 1
                steps.append(ExecutionStep(sn, "narrow",
                    f"{a[mid]} < {target} → search right half [{lo}..{hi}]",
                    array=copy.copy(a), highlights=list(range(lo, hi+1)),
                    comparisons=cmps, accesses=accs,
                    extra={"target": target, "lo": lo, "hi": hi}))
            else:
                hi = mid - 1; sn += 1
                steps.append(ExecutionStep(sn, "narrow",
                    f"{a[mid]} > {target} → search left half [{lo}..{hi}]",
                    array=copy.copy(a), highlights=list(range(lo, hi+1)),
                    comparisons=cmps, accesses=accs,
                    extra={"target": target, "lo": lo, "hi": hi}))

        return steps, {"comparisons": cmps, "swaps": 0, "accesses": accs,
                       "complexity": {"time": "O(log n)", "space": "O(1)"}}

    # ── Linear Search ────────────────────────────────────────────────────

    def _linear_search(self, arr: List[int]):
        a = list(arr); target = a[len(a)//3]
        steps = []; sn = 0; cmps = 0; accs = 0
        steps.append(ExecutionStep(sn, "init", f"Linear Search: target={target}",
            array=copy.copy(a), extra={"target": target}))

        for i, v in enumerate(a):
            accs += 1; cmps += 1; sn += 1
            if v == target:
                steps.append(ExecutionStep(sn, "found", f"Found {target} at index {i} ✓",
                    array=copy.copy(a), highlights=[i],
                    comparisons=cmps, accesses=accs,
                    extra={"target": target, "found_idx": i}))
                break
            steps.append(ExecutionStep(sn, "compare", f"arr[{i}]={v} ≠ {target}",
                array=copy.copy(a), highlights=[i],
                comparisons=cmps, accesses=accs,
                extra={"target": target}))

        return steps, {"comparisons": cmps, "swaps": 0, "accesses": accs,
                       "complexity": {"time": "O(n)", "space": "O(1)"}}

    # ── BFS ──────────────────────────────────────────────────────────────

    def _bfs(self, arr: List[int]):
        n = min(len(arr), 7)
        # Build a simple adjacency graph from input as edge weights
        graph = {i: [] for i in range(n)}
        for i in range(n-1):
            graph[i].append(i+1)
            if i+2 < n: graph[i].append(i+2)

        steps = []; sn = 0
        visited = set(); queue = [0]; visited.add(0); order = []

        steps.append(ExecutionStep(sn, "init", f"BFS from node 0  (graph has {n} nodes)",
            graph_state={"graph": graph, "visited": [], "queue": [0], "current": -1}))

        while queue:
            node = queue.pop(0); order.append(node); sn += 1
            gs = {"graph": graph, "visited": list(visited), "queue": list(queue),
                  "current": node, "order": list(order)}
            steps.append(ExecutionStep(sn, "visit", f"Visit node {node}",
                graph_state=gs, highlights=[node]))

            for nbr in graph[node]:
                sn += 1
                if nbr not in visited:
                    visited.add(nbr); queue.append(nbr)
                    gs2 = {"graph": graph, "visited": list(visited), "queue": list(queue),
                           "current": node, "order": list(order)}
                    steps.append(ExecutionStep(sn, "enqueue",
                        f"Enqueue neighbor {nbr} of node {node}",
                        graph_state=gs2, highlights=[nbr]))

        steps.append(ExecutionStep(sn+1, "done",
            f"BFS complete. Order: {order}",
            graph_state={"graph": graph, "visited": list(visited),
                          "queue": [], "current": -1, "order": order}))

        return steps, {"comparisons": 0, "swaps": 0, "accesses": len(order),
                       "complexity": {"time": "O(V+E)", "space": "O(V)"}}

    # ── DFS ──────────────────────────────────────────────────────────────

    def _dfs(self, arr: List[int]):
        n = min(len(arr), 7)
        graph = {i: [] for i in range(n)}
        for i in range(n-1):
            graph[i].append(i+1)
            if i+2 < n: graph[i].append(i+2)

        steps = []; sn_b = [0]; visited = set(); order = []

        steps.append(ExecutionStep(0, "init", f"DFS from node 0  (graph has {n} nodes)",
            graph_state={"graph": graph, "visited": [], "stack": [0], "current": -1}))

        def dfs(node):
            visited.add(node); order.append(node); sn_b[0] += 1
            steps.append(ExecutionStep(sn_b[0], "visit", f"Visit node {node} (stack frame)",
                graph_state={"graph": graph, "visited": list(visited),
                              "stack": [], "current": node, "order": list(order)},
                highlights=[node]))
            for nbr in graph[node]:
                if nbr not in visited:
                    sn_b[0] += 1
                    steps.append(ExecutionStep(sn_b[0], "recurse",
                        f"Recurse into neighbor {nbr}",
                        graph_state={"graph": graph, "visited": list(visited),
                                      "stack": [], "current": nbr, "order": list(order)},
                        highlights=[nbr]))
                    dfs(nbr)

        dfs(0)
        steps.append(ExecutionStep(sn_b[0]+1, "done", f"DFS complete. Order: {order}",
            graph_state={"graph": graph, "visited": list(visited),
                          "stack": [], "current": -1, "order": order}))

        return steps, {"comparisons": 0, "swaps": 0, "accesses": len(order),
                       "complexity": {"time": "O(V+E)", "space": "O(V)"}}

    # ── Fibonacci DP ─────────────────────────────────────────────────────

    def _fibonacci_dp(self, arr: List[int]):
        n = min(max(arr) if arr else 8, 15)
        dp = [0] * (n + 1)
        steps = []; sn = 0; cmps = 0; accs = 0

        dp[0] = 0
        if n >= 1: dp[1] = 1

        steps.append(ExecutionStep(sn, "init",
            f"Fibonacci DP  n={n}  — initialize dp[0]=0, dp[1]=1",
            dp_table=copy.copy(dp),
            extra={"current": -1, "n": n}))

        for i in range(2, n+1):
            dp[i] = dp[i-1] + dp[i-2]; cmps += 1; accs += 2; sn += 1
            steps.append(ExecutionStep(sn, "compute",
                f"dp[{i}] = dp[{i-1}] + dp[{i-2}] = {dp[i-1]} + {dp[i-2]} = {dp[i]}",
                dp_table=copy.copy(dp),
                comparisons=cmps, accesses=accs,
                extra={"current": i, "n": n, "prev1": i-1, "prev2": i-2}))

        steps.append(ExecutionStep(sn+1, "done",
            f"Fibonacci({n}) = {dp[n]} ✓",
            dp_table=copy.copy(dp),
            comparisons=cmps, accesses=accs,
            extra={"current": n, "n": n, "result": dp[n]}))

        return steps, {"comparisons": cmps, "swaps": 0, "accesses": accs,
                       "complexity": {"time": "O(n)", "space": "O(n)"}}

    # ── LCS ──────────────────────────────────────────────────────────────

    def _lcs(self, arr: List[int]):
        # Use the array values to form two sequences
        a = arr[:len(arr)//2] if len(arr) >= 4 else arr
        b = arr[len(arr)//2:] if len(arr) >= 4 else arr[::-1]
        m, n = len(a), len(b)
        dp = [[0]*(n+1) for _ in range(m+1)]
        steps = []; sn = 0; cmps = 0; accs = 0

        steps.append(ExecutionStep(sn, "init",
            f"LCS: A={a}, B={b}",
            extra={"dp": copy.deepcopy(dp), "m": m, "n": n, "a": a, "b": b}))

        for i in range(1, m+1):
            for j in range(1, n+1):
                cmps += 1; accs += 2; sn += 1
                if a[i-1] == b[j-1]:
                    dp[i][j] = dp[i-1][j-1] + 1
                    action = "match"
                    desc = f"Match: A[{i-1}]={a[i-1]} == B[{j-1}]={b[j-1]}  dp[{i}][{j}]={dp[i][j]}"
                else:
                    dp[i][j] = max(dp[i-1][j], dp[i][j-1])
                    action = "no_match"
                    desc = f"No match: dp[{i}][{j}] = max(dp[{i-1}][{j}], dp[{i}][{j-1}]) = {dp[i][j]}"
                steps.append(ExecutionStep(sn, action, desc,
                    comparisons=cmps, accesses=accs,
                    extra={"dp": copy.deepcopy(dp), "i": i, "j": j,
                            "m": m, "n": n, "a": a, "b": b}))

        steps.append(ExecutionStep(sn+1, "done", f"LCS length = {dp[m][n]} ✓",
            extra={"dp": dp, "result": dp[m][n], "m": m, "n": n, "a": a, "b": b}))

        return steps, {"comparisons": cmps, "swaps": 0, "accesses": accs,
                       "complexity": {"time": "O(mn)", "space": "O(mn)"}}

    # ── Knapsack ─────────────────────────────────────────────────────────

    def _knapsack(self, arr: List[int]):
        items = min(len(arr), 5)
        weights = arr[:items]
        values  = [v * 2 + 1 for v in arr[:items]]
        capacity = sum(weights) // 2 or 10

        dp = [[0]*(capacity+1) for _ in range(items+1)]
        steps = []; sn = 0; cmps = 0; accs = 0

        steps.append(ExecutionStep(sn, "init",
            f"Knapsack: {items} items, capacity={capacity}",
            extra={"dp": copy.deepcopy(dp), "items": items,
                    "capacity": capacity, "weights": weights, "values": values}))

        for i in range(1, items+1):
            for w in range(capacity+1):
                cmps += 1; accs += 2; sn += 1
                if weights[i-1] <= w:
                    dp[i][w] = max(values[i-1] + dp[i-1][w-weights[i-1]], dp[i-1][w])
                    desc = f"Include item {i}: dp[{i}][{w}] = max({values[i-1]}+dp[{i-1}][{w-weights[i-1]}], dp[{i-1}][{w}]) = {dp[i][w]}"
                else:
                    dp[i][w] = dp[i-1][w]
                    desc = f"Skip item {i} (too heavy): dp[{i}][{w}] = {dp[i][w]}"
                if w == capacity:   # only record column of interest
                    steps.append(ExecutionStep(sn, "fill",
                        desc, comparisons=cmps, accesses=accs,
                        extra={"dp": copy.deepcopy(dp), "i": i, "w": w,
                                "items": items, "capacity": capacity,
                                "weights": weights, "values": values}))

        steps.append(ExecutionStep(sn+1, "done",
            f"Optimal value = {dp[items][capacity]} ✓",
            extra={"dp": dp, "result": dp[items][capacity],
                    "items": items, "capacity": capacity}))

        return steps, {"comparisons": cmps, "swaps": 0, "accesses": accs,
                       "complexity": {"time": "O(nW)", "space": "O(nW)"}}
