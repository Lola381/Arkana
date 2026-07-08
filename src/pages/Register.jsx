import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { TransitionLink } from '../components/TransitionContext';
import kailasaBg from '../assets/kailasa_bg.png';

/* ─── Reusable clip-reveal line ────────────────────────────────────────── */
function RevealLine({ children, delay = 0, revealed, tag: Tag = 'span', className = '', style: extraStyle = {} }) {
  return (
    <div className="overflow-hidden leading-normal">
      <Tag
        className={className}
        style={{
          display: 'block',
          transform: revealed ? 'translateY(0)' : 'translateY(110%)',
          transition: `transform 0.9s cubic-bezier(0.16, 1, 0.3, 1) ${delay}ms`,
          willChange: 'transform',
          ...extraStyle,
        }}
      >
        {children}
      </Tag>
    </div>
  );
}

/* ─── Elegant underline input ───────────────────────────────────────────── */
function LineInput({ id, label, type = 'text', value, onChange, autoComplete }) {
  const [focused, setFocused] = useState(false);
  return (
    <div className="relative group">
      <label
        htmlFor={id}
        className={`absolute left-0 text-[11px] font-semibold uppercase tracking-[0.18em] transition-all duration-300 pointer-events-none ${
          focused || value
            ? 'top-0 text-[#8b6914]'
            : 'top-5 text-[#807665]'
        }`}
      >
        {label}
      </label>
      <input
        id={id}
        type={type}
        value={value}
        onChange={onChange}
        autoComplete={autoComplete}
        onFocus={() => setFocused(true)}
        onBlur={() => setFocused(false)}
        className="w-full pt-6 pb-3 bg-transparent border-0 border-b text-[16px] text-[#1b1c1a] focus:outline-none transition-colors duration-300"
        style={{
          borderColor: focused ? '#8b6914' : '#d1c5b2',
        }}
      />
    </div>
  );
}

/* ─── Register Page ─────────────────────────────────────────────────────── */
export default function Register() {
  const navigate = useNavigate();
  const [revealed, setRevealed] = useState(false);
  const [formRevealed, setFormRevealed] = useState(false);
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [showPass, setShowPass] = useState(false);

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  /* Stagger: left panel reveals first, form panel slightly after */
  useEffect(() => {
    // Redirect if already logged in
    if (localStorage.getItem('token')) {
      window.location.href = '/';
      return;
    }
    const t1 = setTimeout(() => setRevealed(true), 120);
    const t2 = setTimeout(() => setFormRevealed(true), 340);
    return () => { clearTimeout(t1); clearTimeout(t2); };
  }, []);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setSuccess('');

    if (!name.trim() || !email.trim() || !password.trim()) {
      setError('Please fill in all required fields.');
      return;
    }

    if (password !== confirmPassword) {
      setError('Passwords do not match.');
      return;
    }

    if (password.length < 6) {
      setError('Password must be at least 6 characters long.');
      return;
    }

    setLoading(true);

    try {
      const response = await fetch('/api/auth/register', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ name, email, password }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.message || 'Account registration failed.');
      }

      setSuccess('Account created successfully! Redirecting...');
      localStorage.setItem('token', data.token);
      localStorage.setItem('user', JSON.stringify(data.user));

      setTimeout(() => {
        window.location.href = '/';
      }, 1000);
    } catch (err) {
      setError(err.message || 'Something went wrong. Please try again.');
    } finally {
      setLoading(false);
    }
  };


  return (
    <div className="min-h-screen flex overflow-hidden" style={{ fontFamily: 'Inter, sans-serif' }}>

      {/* ══════════════════════════════════════════
          LEFT PANEL — Dark editorial
          ══════════════════════════════════════════ */}
      <div className="hidden lg:flex flex-col w-[54%] relative overflow-hidden flex-shrink-0">

        {/* Background artifact image */}
        <img
          src={kailasaBg}
          alt="Kailasa cave painting"
          className="absolute inset-0 w-full h-full object-cover object-center scale-105"
          style={{ filter: 'brightness(0.48) saturate(1.1)' }}
          draggable={false}
        />

        {/* Grain texture overlay */}
        <div
          className="absolute inset-0 opacity-30 pointer-events-none"
          style={{
            backgroundImage: `url("data:image/svg+xml,%3Csvg viewBox='0 0 200 200' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.75' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)' opacity='1'/%3E%3C/svg%3E")`,
            backgroundSize: '200px 200px',
          }}
        />

        {/* Vignette */}
        <div
          className="absolute inset-0 pointer-events-none"
          style={{
            background: 'radial-gradient(ellipse at 60% 40%, transparent 30%, rgba(15,14,13,0.6) 100%)',
          }}
        />

        {/* Content layer */}
        <div className="relative z-10 flex flex-col h-full p-14 pb-12">

          {/* Logo */}
          <TransitionLink to="/" className="self-start">
            <span
              className="font-['Playfair_Display'] text-[22px] italic text-white/90 tracking-tight"
              style={{
                opacity: revealed ? 1 : 0,
                transform: revealed ? 'translateY(0)' : 'translateY(-8px)',
                transition: 'opacity 0.6s ease, transform 0.6s ease',
              }}
            >
              ARKANA.
            </span>
          </TransitionLink>

          {/* Hero headline — each word pops from below */}
          <div className="flex-1 flex flex-col justify-center gap-4 mt-auto mb-auto">
            <RevealLine
              delay={0}
              revealed={revealed}
              tag="h1"
              className="font-['Playfair_Display'] font-bold text-white leading-[1.1] tracking-[-0.02em] text-[clamp(56px,7vw,88px)]"
            >
              JOIN
            </RevealLine>
            <RevealLine
              delay={110}
              revealed={revealed}
              tag="span"
              className="font-['Playfair_Display'] font-bold text-white leading-[1.1] tracking-[-0.02em] text-[clamp(56px,7vw,88px)]"
            >
              THE
            </RevealLine>
            <RevealLine
              delay={220}
              revealed={revealed}
              tag="span"
              className="font-['Playfair_Display'] font-bold leading-[1.1] tracking-[-0.02em] text-[#c9a227] text-[clamp(56px,7vw,88px)]"
            >
              LEGACY
            </RevealLine>

            {/* Subtext */}
            <div className="mt-10 overflow-hidden">
              <p
                className="text-[15px] text-white/50 leading-relaxed max-w-[300px]"
                style={{
                  transform: revealed ? 'translateY(0)' : 'translateY(40px)',
                  opacity: revealed ? 1 : 0,
                  transition: 'transform 0.8s cubic-bezier(0.16,1,0.3,1) 380ms, opacity 0.8s ease 380ms',
                }}
              >
                Create an account to start curating and saving your favorite artifacts.
              </p>
            </div>
          </div>

          {/* Footer meta */}
          <div
            className="flex items-center gap-6"
            style={{
              opacity: revealed ? 0.35 : 0,
              transition: 'opacity 0.8s ease 600ms',
            }}
          >
            <span className="text-[11px] text-white uppercase tracking-[0.18em]">© 2026 ARKANA</span>
            <div className="h-px flex-1 bg-white/20" />
            <span className="text-[11px] text-white uppercase tracking-[0.18em]">Preserving India's Legacy</span>
          </div>
        </div>
      </div>

      {/* ══════════════════════════════════════════
          RIGHT PANEL — Sign-up form
          ══════════════════════════════════════════ */}
      <div className="flex-1 flex flex-col justify-center items-center px-8 bg-[#fbf9f5] relative min-h-screen">

        {/* Mobile logo */}
        <div className="lg:hidden absolute top-8 left-8">
          <TransitionLink to="/" className="font-['Playfair_Display'] text-[20px] italic text-[#1b1c1a]">
            ARKANA.
          </TransitionLink>
        </div>

        {/* Decorative corner artifact thumbnail */}
        <div
          className="hidden lg:block absolute top-10 right-10 w-16 h-20 overflow-hidden border border-[#d1c5b2] rounded"
          style={{
            opacity: formRevealed ? 0.6 : 0,
            transition: 'opacity 1s ease 800ms',
          }}
        >
          <img
            src="https://lh3.googleusercontent.com/aida-public/AB6AXuApO_jE8us-Xp_A0aTWB7s_sR-3c64OlEY6wG1rL0t4cTQOv_fZDedEVEmf7tUurs8Dq-leO9N_u3J-vRkhL3AdlR8xJZE_vA_oGS0asCoxz2XfIx3zisdsND5_Iq6t7rpckdbOiUGO5a6RlPwMpxYvlAzroVVbh5qnx_kSiLV76kZek1Hp9aW0YvqB-urGwKDtktHX-8l5vi39kVZfqpUY9u7khLvvk7NTgC-S3P93ALnQVmJB5xb8lt92AqP4WhAZEDtqG1Ryhw"
            alt=""
            className="w-full h-full object-cover"
          />
        </div>

        <div className="w-full max-w-[380px] py-12">

          {/* Heading */}
          <div className="mb-8">
            <RevealLine
              delay={0}
              revealed={formRevealed}
              tag="h2"
              className="font-['Playfair_Display'] text-[36px] font-semibold text-[#1b1c1a] leading-tight mb-3"
            >
              Create account
            </RevealLine>
            <div className="overflow-hidden">
              <p
                className="text-[14px] text-[#807665]"
                style={{
                  transform: formRevealed ? 'translateY(0)' : 'translateY(20px)',
                  opacity: formRevealed ? 1 : 0,
                  transition: 'transform 0.7s cubic-bezier(0.16,1,0.3,1) 140ms, opacity 0.7s ease 140ms',
                }}
              >
                Join the platform and start saving cultural exhibits.
              </p>
            </div>
          </div>

          {/* Form */}
          <form
            className="flex flex-col gap-6"
            onSubmit={handleSubmit}
            style={{
              opacity: formRevealed ? 1 : 0,
              transform: formRevealed ? 'translateY(0)' : 'translateY(24px)',
              transition: 'opacity 0.7s ease 260ms, transform 0.7s cubic-bezier(0.16,1,0.3,1) 260ms',
            }}
          >
            {error && (
              <div className="p-3 bg-red-950/20 border border-red-900/30 text-red-900 text-[13px] rounded tracking-wide font-medium">
                {error}
              </div>
            )}
            {success && (
              <div className="p-3 bg-green-950/10 border border-green-900/20 text-green-900 text-[13px] rounded tracking-wide font-medium">
                {success}
              </div>
            )}

            <LineInput
              id="register-name"
              label="Full Name"
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              autoComplete="name"
            />

            <LineInput
              id="register-email"
              label="Email address"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              autoComplete="email"
            />

            <LineInput
              id="register-password"
              label="Password"
              type={showPass ? 'text' : 'password'}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              autoComplete="new-password"
            />

            <LineInput
              id="register-confirm-password"
              label="Confirm Password"
              type={showPass ? 'text' : 'password'}
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              autoComplete="new-password"
            />

            <div className="flex justify-between items-center">
              <button
                type="button"
                onClick={() => setShowPass((p) => !p)}
                className="text-[12px] text-[#807665] hover:text-[#1b1c1a] transition-colors"
              >
                {showPass ? 'Hide passwords' : 'Show passwords'}
              </button>
            </div>

            {/* Primary CTA */}
            <button
              type="submit"
              id="register-submit-btn"
              disabled={loading}
              className="w-full py-4 bg-[#1b1c1a] text-[#fbf9f5] text-[13px] font-semibold uppercase tracking-[0.14em] rounded hover:bg-[#2d2f2c] active:bg-[#0f0e0d] transition-all duration-200 mt-2 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? 'Signing Up...' : 'Sign Up'}
            </button>

            {/* Divider */}
            <div className="flex items-center gap-4">
              <div className="h-px flex-1 bg-[#d1c5b2]" />
              <span className="text-[11px] text-[#807665] uppercase tracking-widest">or</span>
              <div className="h-px flex-1 bg-[#d1c5b2]" />
            </div>

            {/* Google sign-in */}
            <button
              type="button"
              id="register-google-btn"
              className="w-full py-3.5 border border-[#d1c5b2] rounded bg-white text-[13px] font-medium text-[#1b1c1a] tracking-wide hover:border-[#1b1c1a] hover:shadow-sm transition-all duration-200 flex items-center justify-center gap-3"
            >
              {/* Google SVG icon */}
              <svg width="18" height="18" viewBox="0 0 18 18" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M17.64 9.205c0-.639-.057-1.252-.164-1.841H9v3.481h4.844a4.14 4.14 0 0 1-1.796 2.716v2.259h2.908c1.702-1.567 2.684-3.875 2.684-6.615Z" fill="#4285F4"/>
                <path d="M9 18c2.43 0 4.467-.806 5.956-2.18l-2.908-2.259c-.806.54-1.837.86-3.048.86-2.344 0-4.328-1.584-5.036-3.711H.957v2.332A8.997 8.997 0 0 0 9 18Z" fill="#34A853"/>
                <path d="M3.964 10.71A5.41 5.41 0 0 1 3.682 9c0-.593.102-1.17.282-1.71V4.958H.957A8.996 8.996 0 0 0 0 9c0 1.452.348 2.827.957 4.042l3.007-2.332Z" fill="#FBBC05"/>
                <path d="M9 3.58c1.321 0 2.508.454 3.44 1.345l2.582-2.58C13.463.891 11.426 0 9 0A8.997 8.997 0 0 0 .957 4.958L3.964 7.29C4.672 5.163 6.656 3.58 9 3.58Z" fill="#EA4335"/>
              </svg>
              Continue with Google
            </button>
          </form>

          {/* Switch back to sign-in */}
          <div
            className="mt-8 text-center"
            style={{
              opacity: formRevealed ? 1 : 0,
              transition: 'opacity 0.7s ease 500ms',
            }}
          >
            <span className="text-[13px] text-[#807665]">Already have an account? </span>
            <TransitionLink
              to="/login"
              className="text-[13px] font-semibold text-[#1b1c1a] hover:text-[#8b6914] transition-colors underline underline-offset-2"
            >
              Sign In
            </TransitionLink>
          </div>
        </div>

        {/* Bottom attribution */}
        <div
          className="absolute bottom-8 text-[11px] text-[#807665] uppercase tracking-widest lg:hidden"
          style={{
            opacity: formRevealed ? 0.5 : 0,
            transition: 'opacity 0.8s ease 700ms',
          }}
        >
          © 2026 ARKANA
        </div>
      </div>
    </div>
  );
}
