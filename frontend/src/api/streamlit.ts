export async function startStreamlit(sessionId: string): Promise<{ url: string; port: number; container_id: string }> {
  const res = await fetch(`/api/sessions/${sessionId}/streamlit/start`, { method: "POST" })
  if (res.status === 404) throw new Error("No app.py found")
  if (res.status === 409) throw new Error("Already running")
  if (res.status === 503) throw new Error("Docker not available")
  if (!res.ok) throw new Error(`Failed to start Streamlit: ${res.status}`)
  return res.json()
}

export async function stopStreamlit(sessionId: string): Promise<void> {
  const res = await fetch(`/api/sessions/${sessionId}/streamlit/stop`, { method: "POST" })
  if (!res.ok && res.status !== 404) throw new Error(`Failed to stop: ${res.status}`)
}

export async function getStreamlitStatus(sessionId: string): Promise<{ running: boolean; url: string | null }> {
  const res = await fetch(`/api/sessions/${sessionId}/streamlit/status`)
  if (!res.ok) throw new Error(`Status check failed: ${res.status}`)
  return res.json()
}
