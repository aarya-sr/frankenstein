import { useRef, useMemo, useState, useEffect } from 'react'
import { useFrame } from '@react-three/fiber'
import * as THREE from 'three'
import { useLabStore } from '../../store/labState'

function createHeartShape(scale: number): THREE.Shape {
  const shape = new THREE.Shape()
  const steps = 128

  for (let i = 0; i <= steps; i++) {
    const t = (i / steps) * Math.PI * 2
    const x = 16 * Math.pow(Math.sin(t), 3) * scale
    const y =
      (13 * Math.cos(t) -
        5 * Math.cos(2 * t) -
        2 * Math.cos(3 * t) -
        Math.cos(4 * t)) *
      scale

    if (i === 0) shape.moveTo(x, y)
    else shape.lineTo(x, y)
  }

  return shape
}

export function WireframeHeart() {
  const groupRef = useRef<THREE.Group>(null)
  const linesRef = useRef<THREE.LineSegments>(null)
  const assemblyPhase = useLabStore((s) => s.assemblyPhase)
  const userPrompt = useLabStore((s) => s.userPrompt)
  const [alive, setAlive] = useState(false)
  const heroScroll = useRef(0)

  // Heart comes alive after headline finishes (~4.5s)
  useEffect(() => {
    const timer = setTimeout(() => setAlive(true), 4500)
    return () => clearTimeout(timer)
  }, [])

  // Track scroll relative to hero section (0 at top, 1 when hero fully scrolled out)
  useEffect(() => {
    const onScroll = () => {
      heroScroll.current = Math.min(window.scrollY / window.innerHeight, 1)
    }
    window.addEventListener('scroll', onScroll, { passive: true })
    return () => window.removeEventListener('scroll', onScroll)
  }, [])

  const { geometry, explosionOffsets, originalPositions, vertexCount } =
    useMemo(() => {
      const shape = createHeartShape(0.055)
      const extrudeGeo = new THREE.ExtrudeGeometry(shape, {
        depth: 0.25,
        bevelEnabled: true,
        bevelThickness: 0.04,
        bevelSize: 0.03,
        bevelSegments: 2,
      })
      extrudeGeo.center()

      const edges = new THREE.EdgesGeometry(extrudeGeo, 15)
      const posAttr = edges.getAttribute('position')
      const count = posAttr.count

      // Store original positions
      const originals = new Float32Array(posAttr.array)

      // Pre-compute explosion offset per edge segment
      const offsets = new Float32Array(count * 3)

      for (let i = 0; i < count; i += 2) {
        const mx = (posAttr.getX(i) + posAttr.getX(i + 1)) / 2
        const my = (posAttr.getY(i) + posAttr.getY(i + 1)) / 2
        const mz = (posAttr.getZ(i) + posAttr.getZ(i + 1)) / 2

        // Direction away from center + random jitter
        const dir = new THREE.Vector3(mx, my, mz).normalize()
        dir.x += (Math.random() - 0.5) * 0.6
        dir.y += (Math.random() - 0.5) * 0.6
        dir.z += (Math.random() - 0.5) * 0.4
        dir.normalize()

        const dist = 3 + Math.random() * 4

        // Both vertices of segment share same offset
        offsets[i * 3] = dir.x * dist
        offsets[i * 3 + 1] = dir.y * dist
        offsets[i * 3 + 2] = dir.z * dist
        offsets[(i + 1) * 3] = dir.x * dist
        offsets[(i + 1) * 3 + 1] = dir.y * dist
        offsets[(i + 1) * 3 + 2] = dir.z * dist
      }

      extrudeGeo.dispose()

      return {
        geometry: edges,
        explosionOffsets: offsets,
        originalPositions: originals,
        vertexCount: count,
      }
    }, [])

  useFrame((state) => {
    if (!groupRef.current || !linesRef.current) return
    const t = state.clock.elapsedTime
    const mat = linesRef.current.material as THREE.LineBasicMaterial
    const posAttr = geometry.getAttribute('position') as THREE.BufferAttribute

    // Scroll explosion — starts early, finishes at 40% scroll
    const scroll = Math.min(heroScroll.current / 0.4, 1)
    const explode = scroll * scroll // quadratic ease-in

    // Apply explosion to each vertex
    for (let i = 0; i < vertexCount; i++) {
      const idx = i * 3
      posAttr.setXYZ(
        i,
        originalPositions[idx] + explosionOffsets[idx] * explode,
        originalPositions[idx + 1] + explosionOffsets[idx + 1] * explode,
        originalPositions[idx + 2] + explosionOffsets[idx + 2] * explode,
      )
    }
    posAttr.needsUpdate = true

    if (!alive) {
      mat.opacity = THREE.MathUtils.lerp(mat.opacity, 0.02, 0.02)
      groupRef.current.scale.setScalar(1)
      return
    }

    // Heartbeat
    const isAssembling =
      assemblyPhase === 'pulling' ||
      assemblyPhase === 'stitching' ||
      assemblyPhase === 'lightning'
    const hasPrompt = userPrompt.trim().length > 0
    const bpm = isAssembling ? 120 : hasPrompt ? 80 : 60
    const beatPhase = (t * (bpm / 60)) % 1

    let beatScale = 1.0
    if (beatPhase < 0.08) {
      beatScale = 1.0 + 0.035 * (beatPhase / 0.08)
    } else if (beatPhase < 0.16) {
      beatScale = 1.035 - 0.035 * ((beatPhase - 0.08) / 0.08)
    }

    if (isAssembling) beatScale *= 1.1

    groupRef.current.scale.setScalar(beatScale)

    // Opacity — fade as scroll explodes
    const baseOpacity = isAssembling ? 0.2 : 0.1
    const scrollFade = 1 - explode
    mat.opacity = THREE.MathUtils.lerp(
      mat.opacity,
      baseOpacity * scrollFade,
      0.05,
    )

    // Gentle sway
    groupRef.current.rotation.y = Math.sin(t * 0.1) * 0.12
  })

  return (
    <group ref={groupRef} position={[0, 0.3, -1]}>
      <lineSegments ref={linesRef} geometry={geometry}>
        <lineBasicMaterial
          color="#39ff14"
          transparent
          opacity={0.02}
          blending={THREE.AdditiveBlending}
          depthWrite={false}
        />
      </lineSegments>
    </group>
  )
}
