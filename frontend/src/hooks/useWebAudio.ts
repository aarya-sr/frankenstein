import { useCallback, useRef } from "react"
import { useLabStore } from "../store/labState"

type SoundName = "click" | "stage_complete" | "critic_alert" | "alive"

let audioCtx: AudioContext | null = null

function getContext(): AudioContext {
  if (!audioCtx) {
    audioCtx = new AudioContext()
  }
  return audioCtx
}

function playTone(freq: number, duration: number, type: OscillatorType = "sine", gain = 0.15) {
  const ctx = getContext()
  const osc = ctx.createOscillator()
  const g = ctx.createGain()
  osc.type = type
  osc.frequency.value = freq
  g.gain.setValueAtTime(gain, ctx.currentTime)
  g.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + duration)
  osc.connect(g)
  g.connect(ctx.destination)
  osc.start(ctx.currentTime)
  osc.stop(ctx.currentTime + duration)
}

function playNoise(duration: number, gain = 0.05) {
  const ctx = getContext()
  const bufferSize = ctx.sampleRate * duration
  const buffer = ctx.createBuffer(1, bufferSize, ctx.sampleRate)
  const data = buffer.getChannelData(0)
  for (let i = 0; i < bufferSize; i++) {
    data[i] = Math.random() * 2 - 1
  }
  const source = ctx.createBufferSource()
  source.buffer = buffer
  const g = ctx.createGain()
  g.gain.setValueAtTime(gain, ctx.currentTime)
  g.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + duration)
  const filter = ctx.createBiquadFilter()
  filter.type = "lowpass"
  filter.frequency.value = 200
  source.connect(filter)
  filter.connect(g)
  g.connect(ctx.destination)
  source.start()
}

const SOUNDS: Record<SoundName, () => void> = {
  click: () => {
    playNoise(0.005, 0.08)
  },
  stage_complete: () => {
    const ctx = getContext()
    const freqs = [440, 523, 659]
    freqs.forEach((freq, i) => {
      const osc = ctx.createOscillator()
      const g = ctx.createGain()
      osc.type = "sine"
      osc.frequency.value = freq
      g.gain.setValueAtTime(0, ctx.currentTime + i * 0.2)
      g.gain.linearRampToValueAtTime(0.12, ctx.currentTime + i * 0.2 + 0.05)
      g.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + i * 0.2 + 0.2)
      osc.connect(g)
      g.connect(ctx.destination)
      osc.start(ctx.currentTime + i * 0.2)
      osc.stop(ctx.currentTime + i * 0.2 + 0.25)
    })
  },
  critic_alert: () => {
    playTone(311, 0.15, "sawtooth", 0.08)
    playTone(440, 0.15, "sawtooth", 0.08)
  },
  alive: () => {
    const ctx = getContext()
    const freqs = [261.63, 329.63, 392]
    freqs.forEach((freq) => {
      const osc = ctx.createOscillator()
      const g = ctx.createGain()
      osc.type = "sine"
      osc.frequency.value = freq
      g.gain.setValueAtTime(0, ctx.currentTime)
      g.gain.linearRampToValueAtTime(0.1, ctx.currentTime + 0.3)
      g.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 1.0)
      osc.connect(g)
      g.connect(ctx.destination)
      osc.start()
      osc.stop(ctx.currentTime + 1.0)
    })
  },
}

export function useWebAudio() {
  const audioMuted = useLabStore((s) => s.audioMuted)
  const lastPlayedRef = useRef<Record<string, number>>({})

  const play = useCallback((name: SoundName) => {
    if (audioMuted) return
    // Debounce: don't play same sound more than once per 200ms
    const now = Date.now()
    if (now - (lastPlayedRef.current[name] || 0) < 200) return
    lastPlayedRef.current[name] = now
    try {
      SOUNDS[name]?.()
    } catch {
      // AudioContext might not be available
    }
  }, [audioMuted])

  return { play }
}
