// AlgoFlow — API Client
const BASE = '/api'

async function post(url, body) {
  const res = await fetch(BASE + url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
  const data = await res.json()
  if (!res.ok) throw data.detail || data
  return data
}

async function get(url) {
  const res = await fetch(BASE + url)
  const data = await res.json()
  if (!res.ok) throw data.detail || data
  return data
}

export const api = {
  compile:   (source, passes) => post('/compile', { source, passes }),
  simulate:  (algorithm, input_data) => post('/simulate', { algorithm, input_data }),
  templates: () => get('/templates'),
  health:    () => get('/health'),
}
