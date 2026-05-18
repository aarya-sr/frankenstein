interface BioluminescentGlowProps {
  color?: string
  size?: number
  intensity?: number
  className?: string
}

export function BioluminescentGlow({
  color = 'var(--formaldehyde)',
  size = 200,
  intensity = 0.3,
  className = '',
}: BioluminescentGlowProps) {
  return (
    <div
      className={`bioluminescent-glow ${className}`}
      style={{
        position: 'absolute',
        width: size,
        height: size,
        borderRadius: '50%',
        background: `radial-gradient(circle, ${color} 0%, transparent 70%)`,
        opacity: intensity,
        pointerEvents: 'none',
        filter: 'blur(40px)',
      }}
    />
  )
}
