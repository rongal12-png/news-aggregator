'use client';

import { useState } from 'react';
import { login as loginApi, register as registerApi, getGoogleAuthUrl, getFacebookAuthUrl } from '@/lib/auth';
import { useAuth } from './AuthProvider';
import { Locale, t } from '@/lib/i18n';

interface AuthModalProps {
  isOpen: boolean;
  onClose: () => void;
  locale: Locale;
}

export default function AuthModal({ isOpen, onClose, locale }: AuthModalProps) {
  const [mode, setMode] = useState<'login' | 'register'>('login');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [name, setName] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const { login } = useAuth();

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      if (mode === 'login') {
        const response = await loginApi(email, password);
        login(response.user);
      } else {
        const response = await registerApi(email, password, name, locale);
        login(response.user);
      }
      onClose();
      // Reset form
      setEmail('');
      setPassword('');
      setName('');
    } catch (err: any) {
      setError(err.message || 'An error occurred');
    } finally {
      setLoading(false);
    }
  };

  const switchMode = () => {
    setMode(mode === 'login' ? 'register' : 'login');
    setError('');
  };

  const texts = {
    login: locale === 'he' ? 'התחברות' : 'Login',
    register: locale === 'he' ? 'הרשמה' : 'Sign Up',
    email: locale === 'he' ? 'אימייל' : 'Email',
    password: locale === 'he' ? 'סיסמה' : 'Password',
    name: locale === 'he' ? 'שם (אופציונלי)' : 'Name (optional)',
    submit: mode === 'login'
      ? (locale === 'he' ? 'התחבר' : 'Login')
      : (locale === 'he' ? 'הירשם' : 'Sign Up'),
    switchToRegister: locale === 'he' ? 'אין לך חשבון? הירשם' : "Don't have an account? Sign up",
    switchToLogin: locale === 'he' ? 'יש לך חשבון? התחבר' : 'Already have an account? Login',
    close: locale === 'he' ? 'סגור' : 'Close',
    or: locale === 'he' ? 'או' : 'or',
    continueWithGoogle: locale === 'he' ? 'המשך עם Google' : 'Continue with Google',
    continueWithFacebook: locale === 'he' ? 'המשך עם Facebook' : 'Continue with Facebook',
  };

  const handleGoogleLogin = async () => {
    try {
      setLoading(true);
      const authUrl = await getGoogleAuthUrl();
      window.location.href = authUrl;
    } catch (err: any) {
      setError(err.message || 'Failed to connect to Google');
      setLoading(false);
    }
  };

  const handleFacebookLogin = async () => {
    try {
      setLoading(true);
      const authUrl = await getFacebookAuthUrl();
      window.location.href = authUrl;
    } catch (err: any) {
      setError(err.message || 'Failed to connect to Facebook');
      setLoading(false);
    }
  };

  return (
    <div className="auth-modal-overlay" onClick={onClose}>
      <div className="auth-modal" onClick={(e) => e.stopPropagation()}>
        <button className="auth-modal-close" onClick={onClose}>
          &times;
        </button>

        <h2 className="auth-modal-title">
          {mode === 'login' ? texts.login : texts.register}
        </h2>

        {error && <div className="auth-error">{error}</div>}

        <form className="auth-form" onSubmit={handleSubmit}>
          {mode === 'register' && (
            <div className="auth-field">
              <label>{texts.name}</label>
              <input
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder={texts.name}
              />
            </div>
          )}

          <div className="auth-field">
            <label>{texts.email}</label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder={texts.email}
              required
            />
          </div>

          <div className="auth-field">
            <label>{texts.password}</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder={texts.password}
              required
              minLength={6}
            />
          </div>

          <button
            type="submit"
            className="auth-submit"
            disabled={loading}
          >
            {loading ? '...' : texts.submit}
          </button>
        </form>

        <div className="auth-divider">
          <span>{texts.or}</span>
        </div>

        <div className="oauth-buttons">
          <button
            className="oauth-btn google-btn"
            onClick={handleGoogleLogin}
            disabled={loading}
          >
            <svg viewBox="0 0 24 24" width="20" height="20">
              <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
              <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
              <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
              <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
            </svg>
            {texts.continueWithGoogle}
          </button>

          <button
            className="oauth-btn facebook-btn"
            onClick={handleFacebookLogin}
            disabled={loading}
          >
            <svg viewBox="0 0 24 24" width="20" height="20">
              <path fill="#1877F2" d="M24 12.073c0-6.627-5.373-12-12-12s-12 5.373-12 12c0 5.99 4.388 10.954 10.125 11.854v-8.385H7.078v-3.47h3.047V9.43c0-3.007 1.792-4.669 4.533-4.669 1.312 0 2.686.235 2.686.235v2.953H15.83c-1.491 0-1.956.925-1.956 1.874v2.25h3.328l-.532 3.47h-2.796v8.385C19.612 23.027 24 18.062 24 12.073z"/>
            </svg>
            {texts.continueWithFacebook}
          </button>
        </div>

        <button className="auth-switch" onClick={switchMode}>
          {mode === 'login' ? texts.switchToRegister : texts.switchToLogin}
        </button>
      </div>

      <style jsx>{`
        .auth-modal-overlay {
          position: fixed;
          inset: 0;
          background: rgba(0, 0, 0, 0.6);
          display: flex;
          align-items: center;
          justify-content: center;
          z-index: 1000;
          backdrop-filter: blur(4px);
        }

        .auth-modal {
          background: var(--bg-card);
          border-radius: var(--radius-lg);
          padding: var(--spacing-xl);
          width: 90%;
          max-width: 400px;
          position: relative;
          box-shadow: var(--shadow-xl);
          animation: modalSlideIn 0.3s ease-out;
        }

        @keyframes modalSlideIn {
          from {
            opacity: 0;
            transform: translateY(-20px) scale(0.95);
          }
          to {
            opacity: 1;
            transform: translateY(0) scale(1);
          }
        }

        .auth-modal-close {
          position: absolute;
          top: 12px;
          inset-inline-end: 12px;
          background: none;
          border: none;
          font-size: 1.5rem;
          color: var(--text-muted);
          cursor: pointer;
          padding: 4px 8px;
          border-radius: var(--radius-sm);
          transition: all var(--transition-fast);
        }

        .auth-modal-close:hover {
          background: var(--bg-hover);
          color: var(--text-primary);
        }

        .auth-modal-title {
          font-size: 1.5rem;
          font-weight: 700;
          color: var(--text-primary);
          margin-bottom: var(--spacing-lg);
          text-align: center;
        }

        .auth-error {
          background: rgba(239, 68, 68, 0.1);
          border: 1px solid rgba(239, 68, 68, 0.3);
          color: #ef4444;
          padding: 10px 14px;
          border-radius: var(--radius-md);
          margin-bottom: var(--spacing-md);
          font-size: 0.875rem;
        }

        .auth-form {
          display: flex;
          flex-direction: column;
          gap: var(--spacing-md);
        }

        .auth-field {
          display: flex;
          flex-direction: column;
          gap: 6px;
        }

        .auth-field label {
          font-size: 0.875rem;
          font-weight: 500;
          color: var(--text-secondary);
        }

        .auth-field input {
          padding: 12px 14px;
          border: 1.5px solid var(--border-color);
          border-radius: var(--radius-md);
          background: var(--bg-primary);
          color: var(--text-primary);
          font-size: 1rem;
          transition: border-color var(--transition-fast);
        }

        .auth-field input:focus {
          outline: none;
          border-color: var(--accent-color);
        }

        .auth-submit {
          background: var(--accent-color);
          color: white;
          border: none;
          padding: 14px;
          border-radius: var(--radius-md);
          font-size: 1rem;
          font-weight: 600;
          cursor: pointer;
          transition: all var(--transition-fast);
          margin-top: var(--spacing-sm);
        }

        .auth-submit:hover:not(:disabled) {
          background: var(--accent-hover);
          transform: translateY(-1px);
        }

        .auth-submit:disabled {
          opacity: 0.7;
          cursor: not-allowed;
        }

        .auth-switch {
          background: none;
          border: none;
          color: var(--accent-color);
          font-size: 0.875rem;
          cursor: pointer;
          margin-top: var(--spacing-lg);
          padding: 8px;
          width: 100%;
          text-align: center;
          transition: color var(--transition-fast);
        }

        .auth-switch:hover {
          color: var(--accent-hover);
          text-decoration: underline;
        }

        .auth-divider {
          display: flex;
          align-items: center;
          margin: var(--spacing-lg) 0;
          color: var(--text-muted);
          font-size: 0.875rem;
        }

        .auth-divider::before,
        .auth-divider::after {
          content: '';
          flex: 1;
          height: 1px;
          background: var(--border-color);
        }

        .auth-divider span {
          padding: 0 var(--spacing-md);
        }

        .oauth-buttons {
          display: flex;
          flex-direction: column;
          gap: var(--spacing-sm);
        }

        .oauth-btn {
          display: flex;
          align-items: center;
          justify-content: center;
          gap: 10px;
          padding: 12px 16px;
          border-radius: var(--radius-md);
          font-size: 0.9375rem;
          font-weight: 500;
          cursor: pointer;
          transition: all var(--transition-fast);
          border: 1.5px solid var(--border-color);
          background: var(--bg-primary);
          color: var(--text-primary);
        }

        .oauth-btn:hover:not(:disabled) {
          background: var(--bg-hover);
          border-color: var(--text-muted);
        }

        .oauth-btn:disabled {
          opacity: 0.6;
          cursor: not-allowed;
        }

        .oauth-btn svg {
          flex-shrink: 0;
        }

        .google-btn:hover:not(:disabled) {
          border-color: #4285F4;
        }

        .facebook-btn:hover:not(:disabled) {
          border-color: #1877F2;
        }
      `}</style>
    </div>
  );
}
