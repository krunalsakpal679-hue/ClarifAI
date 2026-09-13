import React, { useState, useEffect } from 'react';
import { Outlet, NavLink, Link, useNavigate, useLocation } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { useAuthStore } from '../store/authStore';
import { authService } from '../services/api';
import { Button } from '../components/ui/Button';
import { UILanguageSwitch } from '../components/ui/UILanguageSwitch';
import { ToastContainer, toast } from '../components/ui/Toast';

export const AppShell: React.FC = () => {
  const { t } = useTranslation();
  const location = useLocation();
  const navigate = useNavigate();
  const { user, isAuthenticated, logout } = useAuthStore();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  // Close mobile drawer on route change & clear logout transition flag
  useEffect(() => {
    setMobileMenuOpen(false);
    if (useAuthStore.getState().isLoggingOut) {
      useAuthStore.getState().setIsLoggingOut(false);
    }
  }, [location.pathname]);

  const handleLogout = async () => {
    try {
      await authService.logout();
    } catch {
      // Ignore network errors on logout
    } finally {
      logout();
      navigate('/', { replace: true });
      toast.info('You have been logged out.');
    }
  };

  const navLinks = isAuthenticated
    ? [
        { path: '/dashboard', label: t('nav.dashboard', 'Dashboard') },
        { path: '/history', label: t('nav.history', 'History') },
        { path: '/upload', label: t('nav.upload', 'Upload') },
        { path: '/compare', label: t('nav.compare', 'Compare') },
        { path: '/settings', label: t('nav.settings', 'Settings') },
      ]
    : [
        { path: '/', label: t('nav.home', 'Home') },
      ];

  return (
    <div className="min-h-screen flex flex-col bg-surface text-secondary-900 font-sans antialiased">
      {/* Accessible Skip to Content Link */}
      <a
        href="#main-content"
        className="sr-only focus:not-sr-only focus:fixed focus:top-3 focus:left-3 focus:z-50 focus:px-4 focus:py-2 focus:bg-primary-900 focus:text-white focus:rounded-md focus:shadow-elevation-3 focus:outline-none focus:ring-2 focus:ring-accent-500 font-medium text-sm"
      >
        Skip to main content
      </a>

      {/* Persistent Legal Disclaimer Banner for Authenticated Sessions */}
      {isAuthenticated && (
        <div
          role="region"
          aria-label="Legal Disclaimer"
          className="bg-amber-50 border-b border-amber-200 text-amber-900 px-4 py-2 text-xs text-center font-medium flex items-center justify-center gap-2"
        >
          <svg
            className="w-4 h-4 text-amber-600 flex-shrink-0"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            aria-hidden="true"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
            />
          </svg>
          <span>
            {t(
              'disclaimer.notice',
              'ClarifAI is an AI-powered legal assistance tool and is not a substitute for professional legal advice.'
            )}
          </span>
        </div>
      )}

      {/* Main Header / Navigation Bar */}
      <header className="sticky top-0 z-40 bg-white/95 backdrop-blur-sm border-b border-secondary-200 shadow-elevation-1">
        <div className="max-w-constrained mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            {/* Left: Brand Identity */}
            <div className="flex items-center gap-8">
              <Link
                to={isAuthenticated ? '/dashboard' : '/'}
                className="flex items-center gap-2 text-primary-900 font-bold text-xl tracking-tight focus:outline-none focus:ring-2 focus:ring-primary-500 rounded-md py-1 px-2"
                aria-label="ClarifAI Home"
              >
                <div className="w-8 h-8 rounded-lg bg-primary-900 text-white flex items-center justify-center font-black text-lg shadow-sm">
                  C
                </div>
                <span>Clarif<span className="text-accent-600">AI</span></span>
              </Link>

              {/* Desktop Nav Links */}
              <nav className="hidden sm:flex items-center gap-1" aria-label="Main Navigation">
                {navLinks.map((link) => (
                  <NavLink
                    key={link.path}
                    to={link.path}
                    end={link.path === '/'}
                    className={({ isActive }) =>
                      `px-3 py-2 rounded-md text-sm font-medium transition-colors focus:outline-none focus:ring-2 focus:ring-primary-500 ${
                        isActive
                          ? 'bg-primary-50 text-primary-900 font-semibold'
                          : 'text-secondary-600 hover:text-primary-900 hover:bg-secondary-50'
                      }`
                    }
                  >
                    {link.label}
                  </NavLink>
                ))}
              </nav>
            </div>

            {/* Right: Language switch & Auth Controls */}
            <div className="flex items-center gap-3">
              <UILanguageSwitch />

              {isAuthenticated ? (
                <div className="hidden sm:flex items-center gap-3">
                  <div className="text-right">
                    <span className="block text-xs font-semibold text-secondary-900">
                      {user?.fullName || 'User'}
                    </span>
                    <span className="block text-[10px] text-secondary-500 truncate max-w-[140px]">
                      {user?.email || 'Verified Account'}
                    </span>
                  </div>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={handleLogout}
                    className="text-secondary-700 hover:text-red-600"
                    aria-label="Log Out"
                  >
                    {t('nav.logout', 'Log Out')}
                  </Button>
                </div>
              ) : (
                <div className="hidden sm:flex items-center gap-2">
                  <Link to="/login">
                    <Button variant="ghost" size="sm">
                      {t('nav.login', 'Log In')}
                    </Button>
                  </Link>
                  <Link to="/signup">
                    <Button variant="primary" size="sm">
                      {t('nav.signup', 'Sign Up')}
                    </Button>
                  </Link>
                </div>
              )}

              {/* Mobile Menu Hamburger Button (<640px) */}
              <button
                type="button"
                className="sm:hidden inline-flex items-center justify-center p-2 rounded-md text-secondary-700 hover:text-primary-900 hover:bg-secondary-100 focus:outline-none focus:ring-2 focus:ring-primary-500"
                aria-controls="mobile-navigation"
                aria-expanded={mobileMenuOpen}
                aria-label={mobileMenuOpen ? 'Close main menu' : 'Open main menu'}
                onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              >
                <svg
                  className="h-6 w-6"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                  aria-hidden="true"
                >
                  {mobileMenuOpen ? (
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  ) : (
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
                  )}
                </svg>
              </button>
            </div>
          </div>
        </div>

        {/* Mobile Navigation Drawer */}
        {mobileMenuOpen && (
          <nav
            id="mobile-navigation"
            className="sm:hidden border-t border-secondary-200 bg-white px-4 pt-2 pb-4 space-y-1 shadow-elevation-2"
            aria-label="Mobile Navigation"
          >
            {navLinks.map((link) => (
              <NavLink
                key={link.path}
                to={link.path}
                end={link.path === '/'}
                className={({ isActive }) =>
                  `block px-3 py-2 rounded-md text-base font-medium transition-colors ${
                    isActive
                      ? 'bg-primary-50 text-primary-900 font-semibold'
                      : 'text-secondary-700 hover:bg-secondary-50 hover:text-primary-900'
                  }`
                }
              >
                {link.label}
              </NavLink>
            ))}

            <div className="pt-4 border-t border-secondary-200 mt-3 space-y-2">
              {isAuthenticated ? (
                <div className="space-y-2">
                  <div className="px-3 py-1">
                    <p className="text-sm font-semibold text-secondary-900">{user?.fullName || 'User'}</p>
                    <p className="text-xs text-secondary-500">{user?.email}</p>
                  </div>
                  <Button
                    variant="outline"
                    size="sm"
                    className="w-full text-red-600 border-red-200 hover:bg-red-50"
                    onClick={handleLogout}
                  >
                    {t('nav.logout', 'Log Out')}
                  </Button>
                </div>
              ) : (
                <div className="grid grid-cols-2 gap-2 pt-1">
                  <Link to="/login" className="w-full">
                    <Button variant="outline" size="sm" className="w-full">
                      {t('nav.login', 'Log In')}
                    </Button>
                  </Link>
                  <Link to="/signup" className="w-full">
                    <Button variant="primary" size="sm" className="w-full">
                      {t('nav.signup', 'Sign Up')}
                    </Button>
                  </Link>
                </div>
              )}
            </div>
          </nav>
        )}
      </header>

      {/* Main Content Area */}
      <main
        id="main-content"
        tabIndex={-1}
        className="flex-1 w-full max-w-constrained mx-auto px-4 sm:px-6 lg:px-8 py-6 outline-none focus:outline-none"
      >
        <Outlet />
      </main>

      {/* Footer */}
      <footer className="border-t border-secondary-200 bg-white py-6 text-xs text-secondary-500">
        <div className="max-w-constrained mx-auto px-4 sm:px-6 lg:px-8 flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <span className="font-semibold text-primary-900">ClarifAI</span>
            <span>&copy; {new Date().getFullYear()} All rights reserved.</span>
          </div>
          <p className="text-center sm:text-right text-[11px] text-secondary-400 max-w-xl">
            {t(
              'disclaimer.notice',
              'ClarifAI is an AI-powered legal assistance tool and is not a substitute for professional legal advice.'
            )}
          </p>
        </div>
      </footer>

      {/* Global Notifications */}
      <ToastContainer />
    </div>
  );
};
