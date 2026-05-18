export async function fetchFiles(sessionId: string): Promise<Record<string, string>> {
  const res = await fetch(`/api/sessions/${sessionId}/files`)
  if (!res.ok) throw new Error(`Failed to fetch files: ${res.status}`)
  const body = await res.json()
  return body.files
}

export async function triggerRun(sessionId: string): Promise<void> {
  const res = await fetch(`/api/sessions/${sessionId}/preview/run`, { method: "POST" })
  if (res.status === 503) throw new Error("Docker not available")
  if (res.status === 409) throw new Error("Already running")
  if (!res.ok) throw new Error(`Failed to start run: ${res.status}`)
}
