// Auth API client and context
const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export interface User {
  id: number;
  email: string;
  name: string | null;
  locale: string;
  avatar_url: string | null;
  is_admin?: boolean;
}

export interface AuthResponse {
  message: string;
  token: string;
  user: User;
}

export interface FavoriteStory {
  story_id: number;
  title: string;
  category: string;
  published_at: string;
  favorited_at: string;
}

// Token storage
const TOKEN_KEY = 'briefer_auth_token';
const USER_KEY = 'briefer_user';

export function getToken(): string | null {
  if (typeof window === 'undefined') return null;
  return localStorage.getItem(TOKEN_KEY);
}

export function setToken(token: string): void {
  if (typeof window === 'undefined') return;
  localStorage.setItem(TOKEN_KEY, token);
}

export function clearToken(): void {
  if (typeof window === 'undefined') return;
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(USER_KEY);
}

export function getStoredUser(): User | null {
  if (typeof window === 'undefined') return null;
  const data = localStorage.getItem(USER_KEY);
  return data ? JSON.parse(data) : null;
}

export function setStoredUser(user: User): void {
  if (typeof window === 'undefined') return;
  localStorage.setItem(USER_KEY, JSON.stringify(user));
}

// Auth headers helper
export function authHeaders(): HeadersInit {
  const token = getToken();
  return token ? { Authorization: `Bearer ${token}` } : {};
}

// API functions
export async function register(
  email: string,
  password: string,
  name?: string,
  locale: string = 'en'
): Promise<AuthResponse> {
  const params = new URLSearchParams({
    email,
    password,
    locale,
    ...(name && { name }),
  });

  const res = await fetch(`${API_URL}/auth/register?${params}`, {
    method: 'POST',
  });

  if (!res.ok) {
    const error = await res.json();
    throw new Error(error.detail || 'Registration failed');
  }

  const data = await res.json();
  setToken(data.token);
  setStoredUser(data.user);
  return data;
}

export async function login(email: string, password: string): Promise<AuthResponse> {
  const params = new URLSearchParams({ email, password });

  const res = await fetch(`${API_URL}/auth/login?${params}`, {
    method: 'POST',
  });

  if (!res.ok) {
    const error = await res.json();
    throw new Error(error.detail || 'Login failed');
  }

  const data = await res.json();
  setToken(data.token);
  setStoredUser(data.user);
  return data;
}

export async function logout(): Promise<void> {
  const token = getToken();
  if (token) {
    try {
      await fetch(`${API_URL}/auth/logout`, {
        method: 'POST',
        headers: authHeaders(),
      });
    } catch {
      // Ignore errors on logout
    }
  }
  clearToken();
}

export async function getMe(): Promise<User | null> {
  const token = getToken();
  if (!token) return null;

  try {
    const res = await fetch(`${API_URL}/auth/me`, {
      headers: authHeaders(),
    });

    if (!res.ok) {
      if (res.status === 401) {
        clearToken();
        return null;
      }
      throw new Error('Failed to get user');
    }

    const user = await res.json();
    setStoredUser(user);
    return user;
  } catch {
    return null;
  }
}

export async function updateProfile(name?: string, locale?: string): Promise<void> {
  const params = new URLSearchParams();
  if (name) params.append('name', name);
  if (locale) params.append('locale', locale);

  const res = await fetch(`${API_URL}/auth/me?${params}`, {
    method: 'PUT',
    headers: authHeaders(),
  });

  if (!res.ok) {
    const error = await res.json();
    throw new Error(error.detail || 'Update failed');
  }
}

// Favorites
export async function getFavorites(): Promise<FavoriteStory[]> {
  const res = await fetch(`${API_URL}/auth/favorites`, {
    headers: authHeaders(),
  });

  if (!res.ok) {
    if (res.status === 401) return [];
    throw new Error('Failed to get favorites');
  }

  const data = await res.json();
  return data.favorites;
}

export async function addFavorite(storyId: number): Promise<boolean> {
  const res = await fetch(`${API_URL}/auth/favorites/${storyId}`, {
    method: 'POST',
    headers: authHeaders(),
  });

  if (!res.ok) {
    throw new Error('Failed to add favorite');
  }

  const data = await res.json();
  return data.is_favorite;
}

export async function removeFavorite(storyId: number): Promise<boolean> {
  const res = await fetch(`${API_URL}/auth/favorites/${storyId}`, {
    method: 'DELETE',
    headers: authHeaders(),
  });

  if (!res.ok) {
    throw new Error('Failed to remove favorite');
  }

  const data = await res.json();
  return data.is_favorite;
}

export async function checkFavorite(storyId: number): Promise<boolean> {
  const token = getToken();
  if (!token) return false;

  try {
    const res = await fetch(`${API_URL}/auth/favorites/${storyId}/check`, {
      headers: authHeaders(),
    });

    if (!res.ok) return false;

    const data = await res.json();
    return data.is_favorite;
  } catch {
    return false;
  }
}

// ============ OAuth Functions ============

export async function getGoogleAuthUrl(): Promise<string> {
  const res = await fetch(`${API_URL}/auth/google`);

  if (!res.ok) {
    const error = await res.json();
    throw new Error(error.detail || 'Failed to get Google auth URL');
  }

  const data = await res.json();
  return data.auth_url;
}

export async function handleGoogleCallback(code: string): Promise<AuthResponse> {
  const params = new URLSearchParams({ code });

  const res = await fetch(`${API_URL}/auth/google/callback?${params}`, {
    method: 'POST',
  });

  if (!res.ok) {
    const error = await res.json();
    throw new Error(error.detail || 'Google login failed');
  }

  const data = await res.json();
  setToken(data.token);
  setStoredUser(data.user);
  return data;
}

export async function getFacebookAuthUrl(): Promise<string> {
  const res = await fetch(`${API_URL}/auth/facebook`);

  if (!res.ok) {
    const error = await res.json();
    throw new Error(error.detail || 'Failed to get Facebook auth URL');
  }

  const data = await res.json();
  return data.auth_url;
}

export async function handleFacebookCallback(code: string): Promise<AuthResponse> {
  const params = new URLSearchParams({ code });

  const res = await fetch(`${API_URL}/auth/facebook/callback?${params}`, {
    method: 'POST',
  });

  if (!res.ok) {
    const error = await res.json();
    throw new Error(error.detail || 'Facebook login failed');
  }

  const data = await res.json();
  setToken(data.token);
  setStoredUser(data.user);
  return data;
}
