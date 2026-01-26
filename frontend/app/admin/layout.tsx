import '../globals.css';
import './admin.css';

export const metadata = {
  title: 'Briefer Admin',
  description: 'Back Office Dashboard',
};

export default function AdminLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>
        <div className="admin-layout">
          <aside className="admin-sidebar">
            <div className="admin-logo">
              <svg width="32" height="32" viewBox="0 0 32 32" fill="none" xmlns="http://www.w3.org/2000/svg">
                <rect width="32" height="32" rx="8" fill="url(#briefer-gradient-admin)"/>
                <path d="M8 10h16M8 16h12M8 22h14" stroke="white" strokeWidth="2.5" strokeLinecap="round"/>
                <circle cx="24" cy="22" r="3" fill="#fbbf24"/>
                <defs>
                  <linearGradient id="briefer-gradient-admin" x1="0" y1="0" x2="32" y2="32">
                    <stop stopColor="#3b82f6"/>
                    <stop offset="1" stopColor="#8b5cf6"/>
                  </linearGradient>
                </defs>
              </svg>
              <span>Briefer Admin</span>
            </div>
            <nav className="admin-nav">
              <a href="/admin" className="nav-item">
                <span className="nav-icon">📊</span>
                Dashboard
              </a>
              <a href="/admin/stories" className="nav-item">
                <span className="nav-icon">📰</span>
                ניהול סיפורים
              </a>
              <a href="/admin/sources" className="nav-item">
                <span className="nav-icon">📡</span>
                Sources
              </a>
              <a href="/admin/categories" className="nav-item">
                <span className="nav-icon">🏷️</span>
                Categories
              </a>
              <a href="/admin/analytics" className="nav-item">
                <span className="nav-icon">📈</span>
                Analytics
              </a>
              <a href="/admin/settings" className="nav-item">
                <span className="nav-icon">⚙️</span>
                Settings
              </a>
              <div className="nav-divider"></div>
              <a href="/en" className="nav-item" target="_blank">
                <span className="nav-icon">🌐</span>
                View Site
              </a>
            </nav>
          </aside>
          <main className="admin-main">
            {children}
          </main>
        </div>
      </body>
    </html>
  );
}
