// Laboratory Void — fragment shader
// Organic simplex noise, green-tinted, vignette

uniform float uTime;
uniform float uScrollOffset;
uniform float uConcentration;
uniform vec2 uResolution;

varying vec2 vUv;

#include "biologicalNoise.glsl"

void main() {
  vec2 uv = vUv;
  vec2 center = uv - 0.5;

  // Organic noise layers
  float noise1 = snoise(vec3(uv * 3.0, uTime * 0.08 + uScrollOffset * 0.5));
  float noise2 = snoise(vec3(uv * 6.0, uTime * 0.12 + 100.0));
  float noise3 = snoise(vec3(uv * 12.0, uTime * 0.04 + 200.0));

  float combined = noise1 * 0.5 + noise2 * 0.3 + noise3 * 0.2;

  // Base color: very dark, almost black
  vec3 baseColor = vec3(0.02, 0.025, 0.018);
  vec3 greenTint = vec3(0.008, 0.025, 0.004) * uConcentration;

  // Noise-driven color variation — very subtle
  vec3 color = baseColor + greenTint * (combined * 0.3 + 0.5);

  // Formaldehyde wisps — barely visible
  float wisps = smoothstep(0.5, 0.85, combined);
  color += vec3(0.004, 0.015, 0.002) * wisps;

  // Vignette — tighter, darker edges
  float vignette = 1.0 - length(center * vec2(1.4, 1.8));
  vignette = smoothstep(-0.1, 0.6, vignette);

  // Bottom glow — very subtle
  float bottomGlow = smoothstep(1.0, 0.3, uv.y);
  color += vec3(0.004, 0.012, 0.002) * bottomGlow * 0.3;

  color *= vignette;

  gl_FragColor = vec4(color, 1.0);
}
