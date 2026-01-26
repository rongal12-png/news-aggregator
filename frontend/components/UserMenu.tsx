'use client';

import { useState, useRef, useEffect } from 'react';
import Link from 'next/link';
import { useAuth } from './AuthProvider';
import AuthModal from './AuthModal';
import { Locale } from '@/lib/i18n';

interface UserMenuProps {
  locale: Locale;
}

export default function UserMenu({ locale }: UserMenuProps) {
  const { user, loading, logout } = useAuth();
  const [showModal, setShowModal] = useState(false);
  const [showDropdown, setShowDropdown] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  // Close dropdown when clicking outside
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setShowDropdown(false);
      }
    }

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const texts = {
    login: locale === 'he' ? 'התחבר' : 'Login',
    favorites: locale === 'he' ? 'מועדפים' : 'Favorites',
    logout: locale === 'he' ? 'התנתק' : 'Logout',
    loading: locale === 'he' ? '...' : '...',
  };

  if (loading) {
    return <div className="user-menu-loading">{texts.loading}</div>;
  }

  if (!user) {
    return (
      <>
        <button className="login-btn" onClick={() => setShowModal(true)}>
          {texts.login}
        </button>
        <AuthModal
          isOpen={showModal}
          onClose={() => setShowModal(false)}
          locale={locale}
        />
        <style jsx>{`
          .login-btn {
            padding: 8px 16px;
            background: var(--accent-color);
            color: white;
            border: none;
            border-radius: var(--radius-md);
            font-size: 0.875rem;
            font-weight: 600;
            cursor: pointer;
            transition: all var(--transition-fast);
          }
          .login-btn:hover {
            background: var(--accent-hover);
            transform: translateY(-1px);
          }
        `}</style>
      </>
    );
  }

  const initials = user.name
    ? user.name.split(' ').map(n => n[0]).join('').toUpperCase().slice(0, 2)
    : user.email[0].toUpperCase();

  return (
    <div className="user-menu" ref={dropdownRef}>
      <button
        className="user-avatar"
        onClick={() => setShowDropdown(!showDropdown)}
        title={user.name || user.email}
      >
        {user.avatar_url ? (
          <img src={user.avatar_url} alt={user.name || 'User'} />
        ) : (
          <span>{initials}</span>
        )}
      </button>

      {showDropdown && (
        <div className="user-dropdown">
          <div className="user-info">
            <span className="user-name">{user.name || user.email}</span>
            {user.name && <span className="user-email">{user.email}</span>}
          </div>
          <div className="dropdown-divider" />
          <Link
            href={`/${locale}/favorites`}
            className="dropdown-item"
            onClick={() => setShowDropdown(false)}
          >
            <span className="dropdown-icon">&#9829;</span>
            {texts.favorites}
          </Link>
          <button
            className="dropdown-item logout"
            onClick={() => {
              logout();
              setShowDropdown(false);
            }}
          >
            <span className="dropdown-icon">&#x2192;</span>
            {texts.logout}
          </button>
        </div>
      )}

      <style jsx>{`
        .user-menu {
          position: relative;
        }

        .user-avatar {
          width: 36px;
          height: 36px;
          border-radius: 50%;
          background: var(--accent-gradient);
          color: white;
          border: 2px solid var(--border-color);
          display: flex;
          align-items: center;
          justify-content: center;
          font-size: 0.875rem;
          font-weight: 600;
          cursor: pointer;
          overflow: hidden;
          transition: all var(--transition-fast);
        }

        .user-avatar:hover {
          border-color: var(--accent-color);
          transform: scale(1.05);
        }

        .user-avatar img {
          width: 100%;
          height: 100%;
          object-fit: cover;
        }

        .user-dropdown {
          position: absolute;
          top: calc(100% + 8px);
          inset-inline-end: 0;
          min-width: 220px;
          background: var(--bg-card);
          border: 1px solid var(--border-color);
          border-radius: var(--radius-md);
          box-shadow: var(--shadow-lg);
          z-index: 100;
          animation: dropdownFadeIn 0.15s ease-out;
          overflow: hidden;
        }

        @keyframes dropdownFadeIn {
          from {
            opacity: 0;
            transform: translateY(-8px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }

        .user-info {
          padding: 12px 16px;
          display: flex;
          flex-direction: column;
          gap: 2px;
        }

        .user-name {
          font-weight: 600;
          color: var(--text-primary);
          font-size: 0.9375rem;
        }

        .user-email {
          font-size: 0.8125rem;
          color: var(--text-muted);
        }

        .dropdown-divider {
          height: 1px;
          background: var(--border-color);
          margin: 4px 0;
        }

        .dropdown-item {
          display: flex;
          align-items: center;
          gap: 10px;
          padding: 10px 16px;
          color: var(--text-secondary);
          font-size: 0.875rem;
          cursor: pointer;
          transition: all var(--transition-fast);
          width: 100%;
          background: none;
          border: none;
          text-align: start;
        }

        .dropdown-item:hover {
          background: var(--bg-hover);
          color: var(--text-primary);
        }

        .dropdown-item.logout:hover {
          color: #ef4444;
        }

        .dropdown-icon {
          font-size: 1rem;
          width: 20px;
          text-align: center;
        }

        .user-menu-loading {
          width: 36px;
          height: 36px;
          border-radius: 50%;
          background: var(--bg-hover);
          display: flex;
          align-items: center;
          justify-content: center;
          font-size: 0.75rem;
          color: var(--text-muted);
        }
      `}</style>
    </div>
  );
}
