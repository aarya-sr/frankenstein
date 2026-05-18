export async function createSession(): Promise<string> {
  const res = await fetch("/api/sessions", { method: "POST" })
  if (!res.ok) throw new Error(`Server error: ${res.status}`)
  const body = await res.json()
  return body.session_id
}

export async function approveCheckpoint(
  sessionId: string,
  checkpoint: "requirements" | "spec",
  approved: boolean,
  feedback?: string
): Promise<{ status: "resumed" | "revision_requested" }> {
  const res = await fetch(`/api/sessions/${sessionId}/approve`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ checkpoint, approved, feedback: feedback ?? null }),
  })
  if (!res.ok) {
    throw new Error(`Approve request failed: ${res.status}`)
  }
  return res.json()
}

export async function fetchAgentFiles(sessionId: string): Promise<Record<string, string>> {
  const res = await fetch(`/api/sessions/${sessionId}/files`)
  if (!res.ok) throw new Error(`Fetch files failed: ${res.status}`)
  const body = await res.json()
  return body.files
}

export async function aiAssist(
  sessionId: string,
  prompt: string,
  questions: string[]
): Promise<string[]> {
  const res = await fetch(`/api/sessions/${sessionId}/ai-assist`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ prompt, questions }),
  })
  if (!res.ok) throw new Error(`AI assist failed: ${res.status}`)
  const body = await res.json()
  return body.answers
}

export async function downloadAgent(sessionId: string): Promise<void> {
  const res = await fetch(`/api/sessions/${sessionId}/download`)
  if (!res.ok) {
    throw new Error(`Download failed: ${res.status}`)
  }
  const blob = await res.blob()
  const url = URL.createObjectURL(blob)
  const a = document.createElement("a")
  a.href = url
  a.download = `agent_${sessionId.slice(0, 8)}.zip`
  document.body.appendChild(a)
  a.click()
  a.remove()
  URL.revokeObjectURL(url)
}
