import { useRef, useMemo, useEffect } from 'react'
import { useFrame } from '@react-three/fiber'
import * as THREE from 'three'
import { useLabStore } from '../../store/labState'

const EDGES: [number, number][] = [
  [0, 1], [1, 2], [2, 3], [3, 4], [4, 5],
]

const AGENT_POSITIONS: [number, number, number][] = [
  [-3.8, 1.6, -3.0],
  [-1.2, 2.8, -3.5],
  [3.8, 1.6, -3.0],
  [-3.8, -1.6, -3.0],
  [1.2, -2.8, -3.5],
  [3.8, -1.6, -3.0],
]

const POINTS_PER_EDGE = 30

export function EnergyConnections() {
  const groupRef = useRef<THREE.Group>(null)
  const assemblyPhase = useLabStore((s) => s.assemblyPhase)

  const edgeObjects = useMemo(() => {
    return EDGES.map(([from, to]) => {
      // Line
      const lineGeo = new THREE.BufferGeometry()
      const positions = new Float32Array(POINTS_PER_EDGE * 3)
      const start = new THREE.Vector3(...AGENT_POSITIONS[from])
      const end = new THREE.Vector3(...AGENT_POSITIONS[to])

      for (let i = 0; i < POINTS_PER_EDGE; i++) {
        const t = i / (POINTS_PER_EDGE - 1)
        const p = new THREE.Vector3().lerpVectors(start, end, t)
        positions[i * 3] = p.x
        positions[i * 3 + 1] = p.y
        positions[i * 3 + 2] = p.z
      }
      lineGeo.setAttribute('position', new THREE.BufferAttribute(positions, 3))

      const lineMat = new THREE.LineBasicMaterial({
        color: 0x39ff14,
        transparent: true,
        opacity: 0.03,
        blending: THREE.AdditiveBlending,
      })
      const line = new THREE.Line(lineGeo, lineMat)

      // Pulse point
      const pulseGeo = new THREE.BufferGeometry()
      const pulsePos = new Float32Array(3)
      pulseGeo.setAttribute('position', new THREE.BufferAttribute(pulsePos, 3))

      const pulseMat = new THREE.PointsMaterial({
        color: 0x39ff14,
        size: 0.03,
        transparent: true,
        opacity: 0.2,
        blending: THREE.AdditiveBlending,
        sizeAttenuation: true,
      })
      const pulse = new THREE.Points(pulseGeo, pulseMat)

      return { line, pulse, from, to }
    })
  }, [])

  // Add/remove from group
  useEffect(() => {
    const group = groupRef.current
    if (!group) return
    edgeObjects.forEach(({ line, pulse }) => {
      group.add(line)
      group.add(pulse)
    })
    return () => {
      edgeObjects.forEach(({ line, pulse }) => {
        group.remove(line)
        group.remove(pulse)
        line.geometry.dispose()
        ;(line.material as THREE.Material).dispose()
        pulse.geometry.dispose()
        ;(pulse.material as THREE.Material).dispose()
      })
    }
  }, [edgeObjects])

  useFrame((state) => {
    if (!groupRef.current) return

    const visible = assemblyPhase === 'idle' || assemblyPhase === 'orbiting'
    groupRef.current.visible = visible
    if (!visible) return

    const t = state.clock.elapsedTime

    edgeObjects.forEach(({ line, pulse, from, to }, edgeIdx) => {
      const posAttr = line.geometry.getAttribute('position') as THREE.BufferAttribute
      const fromPos = AGENT_POSITIONS[from]
      const toPos = AGENT_POSITIONS[to]

      for (let i = 0; i < POINTS_PER_EDGE; i++) {
        const frac = i / (POINTS_PER_EDGE - 1)
        const x = fromPos[0] + (toPos[0] - fromPos[0]) * frac
        const y = fromPos[1] + (toPos[1] - fromPos[1]) * frac
        const z = fromPos[2] + (toPos[2] - fromPos[2]) * frac
        const wave = Math.sin(frac * Math.PI * 3 + t * 2 + edgeIdx) * 0.04
        const midBulge = Math.sin(frac * Math.PI) * 0.02
        posAttr.setXYZ(i, x + wave * 0.3, y + wave + midBulge, z)
      }
      posAttr.needsUpdate = true

      // Traveling pulse
      const pulseT = ((t * 0.4 + edgeIdx * 0.5) % 1)
      const px = fromPos[0] + (toPos[0] - fromPos[0]) * pulseT
      const py = fromPos[1] + (toPos[1] - fromPos[1]) * pulseT
      const pz = fromPos[2] + (toPos[2] - fromPos[2]) * pulseT
      const pulsePosAttr = pulse.geometry.getAttribute('position') as THREE.BufferAttribute
      pulsePosAttr.setXYZ(0, px, py, pz)
      pulsePosAttr.needsUpdate = true
    })
  })

  return <group ref={groupRef} />
}
