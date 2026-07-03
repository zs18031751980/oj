const resolveApiBaseUrl = () => {
  const envBaseUrl = String(import.meta.env.VITE_API_BASE_URL || '').trim();
  if (envBaseUrl) {
    return envBaseUrl;
  }

  return 'http://localhost:6173';
};

export const API_BASE_URL = resolveApiBaseUrl();

export interface UserInfo {
  id: string;
  username: string;
  email: string;
  name?: string;
  avatar_url?: string;
  provider?: string;
  role?: string;
  theme_preference?: string;
  created_at?: string;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  expires_in: number;
  token_type: string;
  user_info?: UserInfo;
}

interface ApiRequestOptions extends RequestInit {
  skipAuth?: boolean;
}

export type AuthStorageMode = 'local' | 'session';

const AUTH_STORAGE_MODE_KEY = 'auth_storage_mode';

export class ApiError extends Error {
  status: number;
  payload: unknown;

  constructor(message: string, status: number, payload: unknown) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.payload = payload;
  }
}

export const getAuthStorageMode = (): AuthStorageMode => (
  localStorage.getItem(AUTH_STORAGE_MODE_KEY) === 'session' ? 'session' : 'local'
);

export const setAuthStorageMode = (mode: AuthStorageMode) => {
  localStorage.setItem(AUTH_STORAGE_MODE_KEY, mode);
};

export const clearAuthStorageMode = () => {
  localStorage.removeItem(AUTH_STORAGE_MODE_KEY);
};

export const getAuthStorage = (mode: AuthStorageMode = getAuthStorageMode()) => (
  mode === 'session' ? sessionStorage : localStorage
);

const getStoredAccessToken = () => getAuthStorage().getItem('access_token');
const getStoredRefreshToken = () => getAuthStorage().getItem('refresh_token');

let isRefreshing = false;

const tryRefreshToken = async (): Promise<boolean> => {
  if (isRefreshing) return false;
  isRefreshing = true;
  try {
    const refreshToken = getStoredRefreshToken();
    if (!refreshToken) return false;
    const res = await fetch(`${API_BASE_URL}/auth/refresh`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refresh_token: refreshToken }),
    });
    if (!res.ok) return false;
    const data = await res.json();
    const storage = getAuthStorage();
    storage.setItem('access_token', data.access_token);
    storage.setItem('refresh_token', data.refresh_token);
    if (data.user_info) {
      storage.setItem('user_info', JSON.stringify(data.user_info));
    }
    return true;
  } catch {
    return false;
  } finally {
    isRefreshing = false;
  }
};

const parseResponse = async (response: Response) => {
  const contentType = response.headers.get('content-type') || '';

  if (contentType.includes('application/json')) {
    return response.json();
  }

  const text = await response.text();
  return text ? { message: text } : {};
};

export async function apiRequest<T>(path: string, options: ApiRequestOptions = {}): Promise<T> {
  const { skipAuth, headers, body, ...init } = options;
  const requestHeaders = new Headers(headers);

  if (body && !(body instanceof FormData) && !requestHeaders.has('Content-Type')) {
    requestHeaders.set('Content-Type', 'application/json');
  }

  if (!skipAuth) {
    const token = getStoredAccessToken();
    if (token && !requestHeaders.has('Authorization')) {
      requestHeaders.set('Authorization', `Bearer ${token}`);
    }
  }

  let response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    body,
    headers: requestHeaders,
  });

  // 401 且非 skipAuth 时，尝试刷新令牌后重试一次
  if (response.status === 401 && !skipAuth && !path.startsWith('/auth/refresh')) {
    const refreshed = await tryRefreshToken();
    if (refreshed) {
      const newToken = getStoredAccessToken();
      if (newToken) {
        requestHeaders.set('Authorization', `Bearer ${newToken}`);
      }
      response = await fetch(`${API_BASE_URL}${path}`, {
        ...init,
        body,
        headers: requestHeaders,
      });
    }
  }

  const payload = await parseResponse(response);

  if (!response.ok) {
    const message = typeof payload === 'object' && payload && 'error' in payload
      ? String((payload as { error: unknown }).error)
      : `请求失败，状态码 ${response.status}`;

    throw new ApiError(message, response.status, payload);
  }

  return payload as T;
}

export const updateUserTheme = (themePreference: 'light' | 'dark' | 'system') =>
  apiRequest<{ success: boolean }>('/auth/theme', {
    method: 'PATCH',
    body: JSON.stringify({ theme_preference: themePreference }),
  });
