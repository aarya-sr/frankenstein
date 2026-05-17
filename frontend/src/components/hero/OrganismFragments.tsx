import { useRef, useMemo } from 'react'
import { useFrame } from '@react-three/fiber'
import * as THREE from 'three'
import { Text } from '@react-three/drei'
import { useLabStore } from '../../store/labState'
import fragmentDisplaceVert from '../../shaders/fragmentDisplace.vert'

const FRAGMENT_FRAG = `
  uniform float uTime;
  uniform vec3 uColor;
  uniform float uGlow;
  varying float vDisplacement;
  varying vec2 vUv;

  void main() {
    vec3 color = uColor * (0.4 + uGlow * 0.6);
    float fresnel = pow(1.0 - abs(dot(vec3(0.0, 0.0, 1.0), vec3(vUv - 0.5, 0.5))), 2.0);
    color += uColor * fresnel * 0.3;
    float pulse = sin(uTime * 1.5 + vUv.x * 3.14) * 0.1 + 0.9;
    color *= pulse;
    gl_FragColor = vec4(color, 0.75);
  }
`

const AGENTS = [
  { name: 'ELICITOR', position: [-2.2, 0.9, 0] as [number, number, number], color: '#22aa10' },
  { name: 'ARCHITECT', position: [0, 1.1, 0] as [number, number, number], color: '#22aa10' },
  { name: 'CRITIC', position: [2.2, 0.9, 0] as [number, number, number], color: '#8b0000' },
  { name: 'BUILDER', position: [-2.2, -0.9, 0] as [number, number, number], color: '#22aa10' },
  { name: 'TESTER', position: [0, -1.1, 0] as [number, number, number], color: '#cc8833' },
  { name: 'LEARNER', position: [2.2, -0.9, 0] as [number, number, number], color: '#22aa10' },
]

const TRAIL_LEN = 20

const TRAIL_VERT = `
  attribute float alpha;
  varying float vAlpha;
  void main() {
    vAlpha = alpha;
    vec4 mvPos = modelViewMatrix * vec4(position, 1.0);
    gl_PointSize = mix(1.0, 3.5, alpha) * (200.0 / -mvPos.z);
    gl_Position = projectionMatrix * mvPos;
  }
`
const TRAIL_FRAG = `
  uniform vec3 uColor;
  varying float vAlpha;
  void main() {
    float d = length(gl_PointCoord - 0.5);
    if (d > 0.5) discard;
    float soft = smoothstep(0.5, 0.05, d);
    gl_FragColor = vec4(uColor, soft * vAlpha * 0.45);
  }
`

function OrganismFragment({
  name,
  basePosition,
  color,
  index,
}: {
  name: string
  basePosition: [number, number, number]
  color: string
  index: number
}) {
  const groupRef = useRef<THREE.Group>(null)
  const meshRef = useRef<THREE.Mesh>(null)
  const trailRef = useRef<THREE.Points>(null)
  const assemblyPhase = useLabStore((s) => s.assemblyPhase)
  const voltageIntensity = useLabStore((s) => s.voltageIntensity)
  const originalColor = useMemo(() => new THREE.Color(color), [color])
  const trailHead = useRef(0)
  const frameCount = useRef(0)

  const uniforms = useMemo(
    () => ({
      uTime: { value: 0 },
      uIntensity: { value: 0.5 },
      uColor: { value: new THREE.Color(color) },
      uGlow: { value: 0.3 },
    }),
    [color]
  )

  const trailUniforms = useMemo(
    () => ({ uColor: { value: new THREE.Color(color) } }),
    [color]
  )

  // Pre-allocate trail buffers
  const trailPositions = useMemo(() => new Float32Array(TRAIL_LEN * 3), [])
  const trailAlphas = useMemo(() => new Float32Array(TRAIL_LEN), [])

  useFrame((state, delta) => {
    if (!groupRef.current || !meshRef.current) return
    const mat = meshRef.current.material as THREE.ShaderMaterial
    mat.uniforms.uTime.value += delta
    mat.uniforms.uIntensity.value = voltageIntensity * 0.4

    const t = state.clock.elapsedTime
    frameCount.current++

    if (assemblyPhase === 'idle' || assemblyPhase === 'orbiting') {
      groupRef.current.position.x =
        basePosition[0] + Math.sin(t * 0.4 + index * 1.047) * 0.15
      groupRef.current.position.y =
        basePosition[1] + Math.cos(t * 0.35 + index * 0.8) * 0.1
      groupRef.current.position.z =
        basePosition[2] + Math.sin(t * 0.25 + index * 0.5) * 0.08
      meshRef.current.rotation.x = Math.sin(t * 0.15 + index) * 0.08
      meshRef.current.rotation.y = t * 0.1 + index
      mat.uniforms.uGlow.value = 0.3
      mat.uniforms.uColor.value.copy(originalColor)
      groupRef.current.scale.setScalar(1)

      // Record trail every 3 frames
      if (frameCount.current % 3 === 0) {
        const h = trailHead.current % TRAIL_LEN
        trailPositions[h * 3] = groupRef.current.position.x
        trailPositions[h * 3 + 1] = groupRef.current.position.y
        trailPositions[h * 3 + 2] = groupRef.current.position.z
        trailHead.current++
      }
    } else if (assemblyPhase === 'pulling') {
      groupRef.current.position.x = THREE.MathUtils.lerp(groupRef.current.position.x, 0, delta * 2.5)
      groupRef.current.position.y = THREE.MathUtils.lerp(groupRef.current.position.y, 0, delta * 2.5)
      groupRef.current.position.z = THREE.MathUtils.lerp(groupRef.current.position.z, 0, delta * 2.5)
    } else if (assemblyPhase === 'stitching') {
      const radius = 0.15
      const angle = (index / AGENTS.length) * Math.PI * 2 + t * 8
      groupRef.current.position.x = Math.cos(angle) * radius
      groupRef.current.position.y = Math.sin(angle) * radius
      groupRef.current.position.z = 0
      mat.uniforms.uGlow.value = 0.6
    } else if (assemblyPhase === 'lightning') {
      groupRef.current.position.set(0, 0, 0)
      mat.uniforms.uGlow.value = 2.0
      mat.uniforms.uColor.value.setRGB(1, 1, 1)
    } else if (assemblyPhase === 'alive') {
      const bpm = 72
      const beat = Math.sin(t * ((bpm / 60) * Math.PI * 2)) * 0.5 + 0.5
      const scale = 1.0 + beat * 0.015
      const radius = 0.2
      const angle = (index / AGENTS.length) * Math.PI * 2
      groupRef.current.position.x = Math.cos(angle) * radius
      groupRef.current.position.y = Math.sin(angle) * radius
      groupRef.current.position.z = 0
      groupRef.current.scale.setScalar(scale)
      mat.uniforms.uColor.value.copy(originalColor)
      mat.uniforms.uGlow.value = 0.35 + beat * 0.2
    }

    // Update trail alphas (newest = bright, oldest = gone)
    if (trailRef.current) {
      const geo = trailRef.current.geometry
      const posAttr = geo.getAttribute('position') as THREE.BufferAttribute
      const alphaAttr = geo.getAttribute('alpha') as THREE.BufferAttribute
      const head = trailHead.current % TRAIL_LEN
      for (let i = 0; i < TRAIL_LEN; i++) {
        const age = ((head - i + TRAIL_LEN) % TRAIL_LEN) / TRAIL_LEN
        alphaAttr.setX(i, Math.max(0, 1.0 - age))
      }
      posAttr.needsUpdate = true
      alphaAttr.needsUpdate = true
    }
  })

  const geometries: Record<string, React.JSX.Element> = {
    ELICITOR: <sphereGeometry args={[0.22, 24, 24]} />,
    ARCHITECT: <boxGeometry args={[0.35, 0.35, 0.35]} />,
    CRITIC: <octahedronGeometry args={[0.22]} />,
    BUILDER: <cylinderGeometry args={[0.18, 0.22, 0.35, 6]} />,
    TESTER: <dodecahedronGeometry args={[0.2]} />,
    LEARNER: <icosahedronGeometry args={[0.2]} />,
  }

  const showLabel = assemblyPhase === 'idle' || assemblyPhase === 'orbiting'

  return (
    <>
      {/* Particle trail */}
      <points ref={trailRef} frustumCulled={false}>
        <bufferGeometry>
          {/* @ts-expect-error R3F bufferAttribute typing mismatch */}
          <bufferAttribute attach="attributes-position" count={TRAIL_LEN} array={trailPositions} itemSize={3} />
          {/* @ts-expect-error R3F bufferAttribute typing mismatch */}
          <bufferAttribute attach="attributes-alpha" count={TRAIL_LEN} array={trailAlphas} itemSize={1} />
        </bufferGeometry>
        <shaderMaterial
          transparent
          depthWrite={false}
          blending={THREE.AdditiveBlending}
          vertexShader={TRAIL_VERT}
          fragmentShader={TRAIL_FRAG}
          uniforms={trailUniforms}
        />
      </points>

      <group ref={groupRef} position={basePosition}>
        <mesh ref={meshRef}>
          {geometries[name] || <sphereGeometry args={[0.2, 24, 24]} />}
          <shaderMaterial
            vertexShader={fragmentDisplaceVert}
            fragmentShader={FRAGMENT_FRAG}
            uniforms={uniforms}
            transparent
            side={THREE.DoubleSide}
          />
        </mesh>
        {showLabel && (
          <Text
            position={[0, -0.4, 0]}
            fontSize={0.09}
            font="https://fonts.gstatic.com/s/ibmplexmono/v19/-F63fjptAgt5VM-kVkqdyU8n5ig.woff2"
            color="#39ff14"
            anchorX="center"
            anchorY="top"
            letterSpacing={0.15}
          >
            {name}
          </Text>
        )}
      </group>
    </>
  )
}

// Sparse depth particles — float through the scene for atmosphere
const DEPTH_COUNT = 40

function DepthParticles() {
  const ref = useRef<THREE.Points>(null)

  const positions = useMemo(() => {
    const pos = new Float32Array(DEPTH_COUNT * 3)
    for (let i = 0; i < DEPTH_COUNT; i++) {
      pos[i * 3] = (Math.random() - 0.5) * 8
      pos[i * 3 + 1] = (Math.random() - 0.5) * 5
      pos[i * 3 + 2] = (Math.random() - 0.5) * 6 - 1
    }
    return pos
  }, [])

  useFrame((state) => {
    if (!ref.current) return
    const t = state.clock.elapsedTime
    const mat = ref.current.material as THREE.ShaderMaterial
    mat.uniforms.uTime.value = t
    ref.current.rotation.y = t * 0.015
    ref.current.rotation.x = Math.sin(t * 0.05) * 0.02
  })

  return (
    <points ref={ref} frustumCulled={false}>
      <bufferGeometry>
        {/* @ts-expect-error R3F bufferAttribute typing mismatch */}
        <bufferAttribute attach="attributes-position" count={DEPTH_COUNT} array={positions} itemSize={3} />
      </bufferGeometry>
      <shaderMaterial
        transparent
        depthWrite={false}
        blending={THREE.AdditiveBlending}
        vertexShader={`
          uniform float uTime;
          varying float vDepth;
          void main() {
            vec3 pos = position;
            pos.y += sin(uTime * 0.2 + position.x * 0.5) * 0.15;
            pos.x += cos(uTime * 0.15 + position.z) * 0.1;
            vec4 mvPos = modelViewMatrix * vec4(pos, 1.0);
            vDepth = clamp(-mvPos.z / 8.0, 0.0, 1.0);
            gl_PointSize = mix(1.5, 3.5, 1.0 - vDepth) * (200.0 / -mvPos.z);
            gl_Position = projectionMatrix * mvPos;
          }
        `}
        fragmentShader={`
          varying float vDepth;
          void main() {
            float d = length(gl_PointCoord - 0.5);
            if (d > 0.5) discard;
            float soft = smoothstep(0.5, 0.0, d);
            float alpha = soft * mix(0.2, 0.05, vDepth);
            vec3 color = mix(vec3(0.22, 1.0, 0.08), vec3(0.72, 0.45, 0.2), vDepth);
            gl_FragColor = vec4(color, alpha);
          }
        `}
        uniforms={{ uTime: { value: 0 } }}
      />
    </points>
  )
}

export { AGENTS }

export function OrganismFragments() {
  return (
    <group>
      {AGENTS.map((agent, i) => (
        <OrganismFragment
          key={agent.name}
          name={agent.name}
          basePosition={agent.position}
          color={agent.color}
          index={i}
        />
      ))}
      <DepthParticles />
    </group>
  )
}
