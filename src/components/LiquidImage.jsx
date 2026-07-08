/**
 * LiquidImage — WebGL Liquid Scroll Animation
 *
 * Uses Three.js + custom GLSL shaders to create an organic pixel-distortion
 * ("liquid / jelly") effect that fires every time the image enters the viewport.
 *
 * Pipeline:
 *   1. Mount a <canvas> over the container's <img>
 *   2. Create a Three.js Orthographic scene
 *   3. Load the image as a WebGL texture
 *   4. Place the texture on a plane with a custom ShaderMaterial
 *   5. Animate the `uDistortion` uniform 1.0 → 0.0 with GSAP on scroll entry
 *
 * The fragment shader samples the texture with Simplex-like noise displacement:
 *   offset = sin(uv + time) * uDistortion * noiseScale
 *
 * Props:
 *   src        — image URL
 *   alt        — alt text (for the backing <img>)
 *   className  — container className
 *   imgClass   — className forwarded to the <img> (for object-cover etc.)
 */

import { useEffect, useRef } from 'react';
import * as THREE from 'three';
import { gsap } from 'gsap';

/* ─── GLSL Shaders ──────────────────────────────────────────────────────── */

const VERTEX_SHADER = /* glsl */`
  varying vec2 vUv;
  void main() {
    vUv = uv;
    gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
  }
`;

/**
 * Fragment shader — liquid distortion via layered sine/cosine noise.
 * uDistortion: 0.0 = sharp image, 1.0 = heavily distorted liquid.
 * uTime:       increments each frame to make the liquid flow.
 * uResolution: [width, height] of the canvas for aspect-correct UVs.
 */
const FRAGMENT_SHADER = /* glsl */`
  uniform sampler2D uTexture;
  uniform float     uDistortion;
  uniform float     uTime;
  uniform vec2      uResolution;

  varying vec2 vUv;

  /* Pseudo-random based on uv */
  float rand(vec2 co) {
    return fract(sin(dot(co.xy, vec2(12.9898, 78.233))) * 43758.5453);
  }

  /* Smooth noise */
  float noise(vec2 p) {
    vec2 i = floor(p);
    vec2 f = fract(p);
    vec2 u = f * f * (3.0 - 2.0 * f);
    float a = rand(i);
    float b = rand(i + vec2(1.0, 0.0));
    float c = rand(i + vec2(0.0, 1.0));
    float d = rand(i + vec2(1.0, 1.0));
    return mix(mix(a, b, u.x), mix(c, d, u.x), u.y);
  }

  /* Fractal / octave noise for organic, not uniform, distortion */
  float fbm(vec2 p) {
    float value = 0.0;
    float amplitude = 0.5;
    float frequency = 1.0;
    for (int i = 0; i < 4; i++) {
      value += amplitude * noise(p * frequency);
      frequency *= 2.0;
      amplitude *= 0.5;
    }
    return value;
  }

  void main() {
    vec2 uv = vUv;

    /* Keep aspect ratio correct */
    float aspect = uResolution.x / uResolution.y;

    /* Distortion strength — scales down to 0 as animation completes */
    float strength = uDistortion * 0.11;

    /* Flowing noise: two fbm layers offset by time for liquid motion */
    vec2 noiseCoord = uv * 2.8 + vec2(uTime * 0.25);
    float nx = fbm(noiseCoord);
    float ny = fbm(noiseCoord + vec2(5.2, 1.3));

    /* Apply displacement */
    vec2 offset = vec2(nx - 0.5, ny - 0.5) * 2.0 * strength;
    offset.x /= aspect;          /* correct for non-square images */

    vec2 distortedUv = uv + offset;

    /* Clamp so we never sample outside the texture */
    distortedUv = clamp(distortedUv, 0.001, 0.999);

    vec4 color = texture2D(uTexture, distortedUv);
    gl_FragColor = color;
  }
`;

/* ─── Component ─────────────────────────────────────────────────────────── */

export default function LiquidImage({ src, alt, className = '', imgClass = '' }) {
  const wrapperRef = useRef(null);
  const canvasRef  = useRef(null);
  const stateRef   = useRef({});   /* mutable Three.js objects, no re-render */

  /* ── Build the Three.js scene once on mount ─────────────────────────── */
  useEffect(() => {
    const wrapper = wrapperRef.current;
    const canvas  = canvasRef.current;
    if (!wrapper || !canvas) return;

    const W = wrapper.clientWidth  || wrapper.offsetWidth  || 600;
    const H = wrapper.clientHeight || wrapper.offsetHeight || 600;

    /* ── Renderer ── */
    const renderer = new THREE.WebGLRenderer({ canvas, alpha: true, antialias: true });
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.setSize(W, H);

    /* ── Scene & camera (orthographic: fills canvas exactly) ── */
    const scene  = new THREE.Scene();
    const camera = new THREE.OrthographicCamera(-1, 1, 1, -1, 0, 1);

    /* ── Texture ── */
    const loader  = new THREE.TextureLoader();
    loader.crossOrigin = 'anonymous';

    const geometry = new THREE.PlaneGeometry(2, 2);   /* fills [-1,1] clip space */

    const uniforms = {
      uTexture:    { value: null },
      uDistortion: { value: 0.0 },
      uTime:       { value: 0.0 },
      uResolution: { value: new THREE.Vector2(W, H) },
    };

    const material = new THREE.ShaderMaterial({
      vertexShader:   VERTEX_SHADER,
      fragmentShader: FRAGMENT_SHADER,
      uniforms,
    });

    const mesh = new THREE.Mesh(geometry, material);
    scene.add(mesh);

    /* ── Load texture ── */
    loader.load(src, (texture) => {
      texture.minFilter = THREE.LinearFilter;
      texture.magFilter = THREE.LinearFilter;
      uniforms.uTexture.value = texture;
    });

    /* ── Animation loop ── */
    let rafId;
    const clock = new THREE.Clock();

    const tick = () => {
      rafId = requestAnimationFrame(tick);
      uniforms.uTime.value = clock.getElapsedTime();
      renderer.render(scene, camera);
    };
    tick();

    /* ── Resize ── */
    const onResize = () => {
      const w = wrapper.clientWidth  || wrapper.offsetWidth;
      const h = wrapper.clientHeight || wrapper.offsetHeight;
      renderer.setSize(w, h);
      uniforms.uResolution.value.set(w, h);
    };
    window.addEventListener('resize', onResize, { passive: true });

    /* ── IntersectionObserver — triggers the animation ── */
    let tween = null;

    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (!entry.isIntersecting) return;
          if (!uniforms.uTexture.value) return;

          /* Kill any running tween */
          if (tween) tween.kill();

          /* Spike distortion to 1, then ease back to 0 */
          uniforms.uDistortion.value = 1.0;

          tween = gsap.to(uniforms.uDistortion, {
            value: 0.0,
            duration: 1.9,
            ease: 'power2.out',
            delay: 0.05,
          });
        });
      },
      { threshold: 0.15 }
    );

    observer.observe(wrapper);

    /* Store refs for cleanup */
    stateRef.current = { renderer, scene, geometry, material, observer, rafId };

    return () => {
      cancelAnimationFrame(rafId);
      observer.disconnect();
      if (tween) tween.kill();
      window.removeEventListener('resize', onResize);
      geometry.dispose();
      material.dispose();
      renderer.dispose();
    };
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [src]);

  return (
    /*
     * The wrapper keeps the same dimensions as the parent container.
     * The <canvas> sits on top of the <img> (both position:absolute, inset:0).
     * The <img> acts as a fallback and also lets the browser handle
     * layout/sizing naturally before Three.js is ready.
     */
    <div ref={wrapperRef} className={`liquid-image-wrap ${className}`}>
      {/* Fallback / sizing reference */}
      <img
        src={src}
        alt={alt}
        className={`liquid-image-fallback ${imgClass}`}
        draggable={false}
      />
      {/* WebGL canvas — overlaid on the image */}
      <canvas ref={canvasRef} className="liquid-image-canvas" aria-hidden="true" />
    </div>
  );
}
