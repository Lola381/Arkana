import { useState } from 'react';
import { TransitionLink } from '../components/TransitionContext';

export default function Login() {
  const [isRegister, setIsRegister] = useState(false);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    alert(isRegister ? 'Account creation simulated!' : 'Sign in simulated!');
  };

  const toggleAuthMode = (e) => {
    e.preventDefault();
    setIsRegister((prev) => !prev);
  };

  return (
    <div className="min-h-screen flex items-center justify-center p-5 md:p-20 bg-[#fbf9f5] pt-20 text-[#1b1c1a] font-['Inter']">
      <div className="w-full max-w-md mx-auto animate-fade-in-up">
        {/* Header */}
        <div className="text-center mb-12">
          <TransitionLink
            to="/"
            className="font-['Playfair_Display'] text-[32px] italic text-[#1b1c1a] mb-6 block hover:opacity-70 transition-opacity"
          >
            ARKANA.
          </TransitionLink>
          <h1 className="font-['Playfair_Display'] text-[28px] font-medium text-[#1b1c1a] mb-2">
            {isRegister ? 'Create an Account' : 'Welcome to Arkana'}
          </h1>
          <p className="text-[14px] text-[#4e4637]">
            {isRegister ? 'Join us to save your explorations' : 'Sign in to save your explorations'}
          </p>
        </div>

        {/* Auth Card */}
        <div className="bg-white rounded shadow-[0_1px_3px_rgba(0,0,0,0.06)] border border-[#d1c5b2]/50 p-8">
          <form id="auth-form" onSubmit={handleSubmit} className="space-y-6">
            <div>
              <label className="block text-[12px] font-medium text-[#4e4637] uppercase tracking-wide mb-2" htmlFor="email">
                Email Address
              </label>
              <input
                className="w-full bg-transparent border-0 border-b border-[#d1c5b2] py-3 px-0 text-[16px] text-[#1b1c1a] placeholder:text-[#807665]/50 focus:ring-0 focus:outline-none focus:border-[#8b6914] transition-colors"
                id="email"
                name="email"
                placeholder="Enter your email"
                type="email"
                autoComplete="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
              />
            </div>
            <div>
              <div className="flex justify-between items-center mb-2">
                <label className="block text-[12px] font-medium text-[#4e4637] uppercase tracking-wide" htmlFor="password">
                  Password
                </label>
                {!isRegister && (
                  <a
                    href="#"
                    onClick={(e) => e.preventDefault()}
                    className="text-[12px] font-medium text-[#8b6914] heritage-link"
                  >
                    Forgot?
                  </a>
                )}
              </div>
              <input
                className="w-full bg-transparent border-0 border-b border-[#d1c5b2] py-3 px-0 text-[16px] text-[#1b1c1a] placeholder:text-[#807665]/50 focus:ring-0 focus:outline-none focus:border-[#8b6914] transition-colors"
                id="password"
                name="password"
                placeholder="Enter your password"
                type="password"
                autoComplete={isRegister ? 'new-password' : 'current-password'}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
              />
            </div>
            <button
              className="w-full flex items-center justify-center py-3 px-4 border border-[#1b1c1a] rounded bg-[#1b1c1a] text-[#FAF8F4] text-[16px] font-semibold transition-colors duration-300 hover:bg-transparent hover:text-[#1b1c1a] mt-8"
              type="submit"
            >
              {isRegister ? 'Create Account' : 'Sign In'}
            </button>
          </form>

          {/* Social Divider */}
          <div className="mt-8 flex items-center justify-center">
            <span className="h-px bg-[#d1c5b2] flex-1"></span>
            <span className="px-4 text-[11px] font-medium text-[#4e4637] uppercase tracking-widest whitespace-nowrap">
              Or continue with
            </span>
            <span className="h-px bg-[#d1c5b2] flex-1"></span>
          </div>

          {/* Social Button */}
          <div className="mt-8">
            <button
              className="w-full flex items-center justify-center gap-3 py-3 px-4 border border-[#d1c5b2] rounded bg-white text-[#1b1c1a] text-[16px] font-medium transition-colors duration-300 hover:bg-[#f5f3ef] hover:border-[#807665]"
              type="button"
              onClick={() => alert('Google Sign In simulated!')}
              aria-label="Continue with Google"
            >
              <svg className="w-5 h-5 flex-shrink-0" viewBox="0 0 24 24">
                <path
                  d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
                  fill="#4285F4"
                />
                <path
                  d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
                  fill="#34A853"
                />
                <path
                  d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"
                  fill="#FBBC05"
                />
                <path
                  d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
                  fill="#EA4335"
                />
              </svg>
              Continue with Google
            </button>
          </div>
        </div>

        {/* Mode Toggle Link */}
        <div className="mt-8 text-center">
          <p className="text-[16px] text-[#4e4637]">
            {isRegister ? 'Already have an account?' : "Don't have an account?"}
            <a href="#" onClick={toggleAuthMode} className="heritage-link ml-1 text-[#8b6914] font-medium" id="toggle-auth">
              {isRegister ? 'Sign in' : 'Register'}
            </a>
          </p>
        </div>
      </div>
    </div>
  );
}
