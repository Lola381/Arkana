import { useState, useEffect } from 'react';
import { TransitionLink, TransitionNavLink } from './TransitionContext';

export default function Navbar() {
  const [scrolled, setScrolled] = useState(false);
  const [menuOpen, setMenuOpen] = useState(false);
  const [user, setUser] = useState(null);

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 40);
    window.addEventListener('scroll', onScroll, { passive: true });

    const storedUser = localStorage.getItem('user');
    if (storedUser) {
      try {
        setUser(JSON.parse(storedUser));
      } catch (e) {
        console.error('Failed to parse user', e);
      }
    }

    return () => window.removeEventListener('scroll', onScroll);
  }, []);

  const handleLogout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    setUser(null);
    window.location.href = '/';
  };

  const linkBase = "text-[#4e4637] hover:text-[#6f5100] transition-colors duration-300 font-['Inter'] text-[16px]";

  const navItems = [
    { to: '/explore', label: 'Explore' },
    { to: '/culture', label: 'Cultures' },
    { to: '/browse', label: 'Browse' },
    { to: '/identify', label: 'Identify' },
    { to: '/explore', label: 'Ask Arkana' },
  ];

  return (
    <>
      {/* Desktop + Mobile Navbar */}
      <nav
        className={`fixed top-0 w-full z-50 backdrop-blur-md border-b transition-all duration-300 ${
          scrolled
            ? 'bg-[#fbf9f5]/95 border-[#d1c5b2]'
            : 'bg-[#fbf9f5]/80 border-transparent'
        }`}
        role="navigation"
        aria-label="Main navigation"
      >
        <div className="flex justify-between items-center px-5 md:px-20 h-20 w-full max-w-[1280px] mx-auto">
          {/* Logo */}
          <TransitionLink
            to="/"
            className="font-['Playfair_Display'] text-[32px] italic font-medium text-[#1b1c1a] tracking-widest hover:opacity-70 transition-opacity"
          >
            ARKANA.
          </TransitionLink>

          {/* Desktop Links */}
          <div className="hidden md:flex items-center gap-8">
            {navItems.map(({ to, label }) => (
              <TransitionNavLink
                key={label}
                to={to}
                className={linkBase}
              >
                {label}
              </TransitionNavLink>
            ))}
          </div>

          {/* Right actions */}
          <div className="flex items-center gap-4 text-[#8b6914]">
            <button aria-label="Search" className="hover:opacity-70 transition-opacity">
              <span className="material-symbols-outlined">search</span>
            </button>
            {user ? (
              <div className="relative group hidden md:block">
                <button
                  aria-label="User menu"
                  className="flex items-center gap-2 hover:opacity-80 transition-opacity py-2 focus:outline-none"
                >
                  <div className="w-8 h-8 rounded-full bg-[#efeeea] border border-[#8b6914] flex items-center justify-center">
                    <span className="material-symbols-outlined text-[18px] text-[#8b6914]">person</span>
                  </div>
                  <span className="text-sm font-medium text-[#4e4637]">{user.name}</span>
                </button>
                {/* Artsy hover dropdown */}
                <div className="absolute right-0 mt-1 w-48 bg-[#fbf9f5] border border-[#d1c5b2] rounded shadow-xl opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all duration-200 z-50 py-1">
                  <div className="px-4 py-2 border-b border-[#d1c5b2] text-[10px] text-[#807665] uppercase tracking-[0.15em] font-semibold">
                    Account Detail
                  </div>
                  <div className="px-4 py-2 text-sm text-[#1b1c1a] font-medium truncate">
                    {user.name}
                  </div>
                  <button
                    onClick={handleLogout}
                    className="w-full text-left px-4 py-2.5 text-sm text-red-700 hover:bg-[#efeeea] transition-colors flex items-center gap-2 font-medium"
                  >
                    <span className="material-symbols-outlined text-[18px]">logout</span>
                    Sign Out
                  </button>
                </div>
              </div>
            ) : (
              <TransitionLink to="/login" className="hidden md:block">
                <div className="w-8 h-8 rounded-full bg-[#efeeea] border border-[#d1c5b2] flex items-center justify-center hover:border-[#8b6914] transition-colors">
                  <span className="material-symbols-outlined text-[18px] text-[#4e4637]">person</span>
                </div>
              </TransitionLink>
            )}
            <button
              className="md:hidden text-[#1b1c1a] hover:text-[#8b6914] transition-colors"
              onClick={() => setMenuOpen(true)}
              aria-label="Open menu"
            >
              <span className="material-symbols-outlined">menu</span>
            </button>
          </div>
        </div>
      </nav>

      {/* Mobile Full-screen Menu */}
      <div
        className={`fixed inset-0 z-[9990] bg-[#fbf9f5] flex flex-col items-center justify-center gap-10 transition-opacity duration-400 ${
          menuOpen ? 'opacity-100 pointer-events-auto' : 'opacity-0 pointer-events-none'
        }`}
        role="dialog"
        aria-modal="true"
      >
        <button
          className="absolute top-6 right-6 text-[#1b1c1a]"
          onClick={() => setMenuOpen(false)}
          aria-label="Close menu"
        >
          <span className="material-symbols-outlined text-3xl">close</span>
        </button>
        
        {/* Render user greeting on mobile if logged in */}
        {user && (
          <div className="text-center -mb-4">
            <span className="text-[11px] uppercase tracking-[0.2em] text-[#807665]">Logged in as</span>
            <div className="font-['Playfair_Display'] text-[24px] font-semibold text-[#1b1c1a]">{user.name}</div>
          </div>
        )}

        {[
          { to: '/', label: 'Home' },
          ...navItems.slice(0, 4),
          user 
            ? { label: 'Sign Out', onClick: handleLogout }
            : { to: '/login', label: 'Sign In' }
        ].map((item) => {
          if (item.onClick) {
            return (
              <button
                key={item.label}
                onClick={() => {
                  setMenuOpen(false);
                  item.onClick();
                }}
                className="font-['Playfair_Display'] text-[32px] font-medium text-red-700 hover:text-red-800 transition-colors"
              >
                {item.label}
              </button>
            );
          }
          return (
            <TransitionLink
              key={item.label}
              to={item.to}
              className="font-['Playfair_Display'] text-[32px] font-medium text-[#1b1c1a] hover:text-[#8b6914] transition-colors"
              onClick={() => setMenuOpen(false)}
            >
              {item.label}
            </TransitionLink>
          );
        })}
      </div>
    </>
  );
}
