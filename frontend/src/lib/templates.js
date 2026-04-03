export const TEMPLATES = {
  bubble: {
    name: 'Bubble Sort', category: 'Sorting',
    complexity: { time: 'O(n²)', space: 'O(1)' },
    source: `function BubbleSort(arr, n):
    i = 0
    while i < n - 1:
        j = 0
        swapped = false
        while j < n - i - 1:
            if arr[j] > arr[j + 1]:
                temp = arr[j]
                arr[j] = arr[j + 1]
                arr[j + 1] = temp
                swapped = true
            j = j + 1
        if swapped == false:
            break
        i = i + 1
    return arr`,
  },
  selection: {
    name: 'Selection Sort', category: 'Sorting',
    complexity: { time: 'O(n²)', space: 'O(1)' },
    source: `function SelectionSort(arr, n):
    i = 0
    while i < n - 1:
        min_idx = i
        j = i + 1
        while j < n:
            if arr[j] < arr[min_idx]:
                min_idx = j
            j = j + 1
        if min_idx != i:
            temp = arr[i]
            arr[i] = arr[min_idx]
            arr[min_idx] = temp
        i = i + 1
    return arr`,
  },
  insertion: {
    name: 'Insertion Sort', category: 'Sorting',
    complexity: { time: 'O(n²)', space: 'O(1)' },
    source: `function InsertionSort(arr, n):
    i = 1
    while i < n:
        key = arr[i]
        j = i - 1
        while j >= 0 and arr[j] > key:
            arr[j + 1] = arr[j]
            j = j - 1
        arr[j + 1] = key
        i = i + 1
    return arr`,
  },
  merge: {
    name: 'Merge Sort', category: 'Sorting',
    complexity: { time: 'O(n log n)', space: 'O(n)' },
    source: `function MergeSort(arr, left, right):
    if left >= right:
        return
    mid = (left + right) / 2
    MergeSort(arr, left, mid)
    MergeSort(arr, mid + 1, right)
    Merge(arr, left, mid, right)

function Merge(arr, left, mid, right):
    i = left
    j = mid + 1
    temp = []
    while i <= mid and j <= right:
        if arr[i] <= arr[j]:
            temp[i] = arr[i]
            i = i + 1
        else:
            temp[i] = arr[j]
            j = j + 1
    while i <= mid:
        temp[i] = arr[i]
        i = i + 1`,
  },
  quick: {
    name: 'Quick Sort', category: 'Sorting',
    complexity: { time: 'O(n log n) avg', space: 'O(log n)' },
    source: `function QuickSort(arr, low, high):
    if low < high:
        pivot = Partition(arr, low, high)
        QuickSort(arr, low, pivot - 1)
        QuickSort(arr, pivot + 1, high)

function Partition(arr, low, high):
    pivot = arr[high]
    i = low - 1
    j = low
    while j < high:
        if arr[j] <= pivot:
            i = i + 1
            temp = arr[i]
            arr[i] = arr[j]
            arr[j] = temp
        j = j + 1
    temp = arr[i + 1]
    arr[i + 1] = arr[high]
    arr[high] = temp
    return i + 1`,
  },
  binary: {
    name: 'Binary Search', category: 'Searching',
    complexity: { time: 'O(log n)', space: 'O(1)' },
    source: `function BinarySearch(arr, target, left, right):
    // Dead variable — DCE will eliminate this
    unused = 999 * 42
    while left <= right:
        mid = (left + right) / 2
        if arr[mid] == target:
            return mid
        if arr[mid] < target:
            left = mid + 1
        else:
            right = mid - 1
    return -1`,
  },
  fib: {
    name: 'Fibonacci (DP)', category: 'Dynamic Programming',
    complexity: { time: 'O(n)', space: 'O(n)' },
    source: `function Fibonacci(n):
    if n <= 1:
        return n
    // CSE candidate: same expression twice
    x = 5 + 3
    y = 5 + 3
    dp = []
    dp[0] = 0
    dp[1] = 1
    i = 2
    while i <= n:
        dp[i] = dp[i - 1] + dp[i - 2]
        i = i + 1
    return dp[n]`,
  },
  bfs: {
    name: 'BFS', category: 'Graph',
    complexity: { time: 'O(V+E)', space: 'O(V)' },
    source: `function BFS(graph, start):
    visited = {}
    queue = [start]
    visited[start] = true
    result = []
    while queue is not empty:
        node = queue[0]
        result[result.length] = node
        i = 0
        while i < graph[node].length:
            neighbor = graph[node][i]
            if not visited[neighbor]:
                visited[neighbor] = true
                queue[queue.length] = neighbor
            i = i + 1
    return result`,
  },
  dfs: {
    name: 'DFS', category: 'Graph',
    complexity: { time: 'O(V+E)', space: 'O(V)' },
    source: `function DFS(graph, node, visited):
    if visited[node]:
        return
    visited[node] = true
    result[result.length] = node
    i = 0
    while i < graph[node].length:
        neighbor = graph[node][i]
        DFS(graph, neighbor, visited)
        i = i + 1`,
  },
  lcs: {
    name: 'Longest Common Subsequence', category: 'Dynamic Programming',
    complexity: { time: 'O(mn)', space: 'O(mn)' },
    source: `function LCS(a, b, m, n):
    dp = []
    i = 0
    while i <= m:
        j = 0
        while j <= n:
            if i == 0 or j == 0:
                dp[i][j] = 0
            else if a[i - 1] == b[j - 1]:
                dp[i][j] = dp[i - 1][j - 1] + 1
            else:
                left = dp[i - 1][j]
                right = dp[i][j - 1]
                if left > right:
                    dp[i][j] = left
                else:
                    dp[i][j] = right
            j = j + 1
        i = i + 1
    return dp[m][n]`,
  },
  knapsack: {
    name: '0/1 Knapsack', category: 'Dynamic Programming',
    complexity: { time: 'O(nW)', space: 'O(nW)' },
    source: `function Knapsack(weights, values, capacity, n):
    dp = []
    i = 0
    while i <= n:
        w = 0
        while w <= capacity:
            if i == 0 or w == 0:
                dp[i][w] = 0
            else if weights[i - 1] <= w:
                include = values[i - 1] + dp[i - 1][w - weights[i - 1]]
                exclude = dp[i - 1][w]
                if include > exclude:
                    dp[i][w] = include
                else:
                    dp[i][w] = exclude
            else:
                dp[i][w] = dp[i - 1][w]
            w = w + 1
        i = i + 1
    return dp[n][capacity]`,
  },
}

export const CATEGORIES = [...new Set(Object.values(TEMPLATES).map(t => t.category))]
