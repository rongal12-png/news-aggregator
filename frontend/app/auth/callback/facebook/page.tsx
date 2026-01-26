'use client';

import { Suspense, useEffect, useState } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { handleFacebookCallback } from '@/lib/auth';

function FacebookCallbackContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const code = searchParams.get('code');
    const errorParam = searchParams.get('error');

    if (errorParam) {
      setError('Facebook login was cancelled or failed');
      return;
    }

    if (!code) {
      setError('No authorization code received');
      return;
    }

    handleFacebookCallback(code)
      .then(() => {
        // Redirect to homepage after successful login
        router.push('/');
      })
      .catch((err) => {
        setError(err.message || 'Login failed');
      });
  }, [searchParams, router]);

  if (error) {
    return (
      <div className="callback-error">
        <h2>Login Failed</h2>
        <p>{error}</p>
        <button onClick={() => router.push('/')}>Return to Homepage</button>
      </div>
    );
  }

  return (
    <div className="callback-loading">
      <div className="spinner"></div>
      <p>Completing login with Facebook...</p>
    </div>
  );
}

export default function FacebookCallbackPage() {
  return (
    <div className="callback-page">
      <Suspense fallback={
        <div className="callback-loading">
          <div className="spinner"></div>
          <p>Loading...</p>
        </div>
      }>
        <FacebookCallbackContent />
      </Suspense>

      <style jsx global>{`
        .callback-page {
          min-height: 100vh;
          display: flex;
          align-items: center;
          justify-content: center;
          padding: 20px;
        }

        .callback-loading,
        .callback-error {
          text-align: center;
          max-width: 400px;
        }

        .spinner {
          width: 48px;
          height: 48px;
          border: 4px solid var(--border-color, #e5e7eb);
          border-top-color: var(--accent-color, #3b82f6);
          border-radius: 50%;
          animation: spin 1s linear infinite;
          margin: 0 auto 20px;
        }

        @keyframes spin {
          to {
            transform: rotate(360deg);
          }
        }

        .callback-loading p {
          color: var(--text-secondary, #6b7280);
          font-size: 1.125rem;
        }

        .callback-error h2 {
          color: #ef4444;
          margin-bottom: 12px;
        }

        .callback-error p {
          color: var(--text-secondary, #6b7280);
          margin-bottom: 20px;
        }

        .callback-error button {
          background: var(--accent-color, #3b82f6);
          color: white;
          border: none;
          padding: 12px 24px;
          border-radius: var(--radius-md, 8px);
          font-size: 1rem;
          cursor: pointer;
          transition: background 0.15s;
        }

        .callback-error button:hover {
          background: var(--accent-hover, #2563eb);
        }
      `}</style>
    </div>
  );
}
