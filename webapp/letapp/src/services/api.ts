export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:6173';

export interface UserInfo {
  id: string;
  username: string;
  email: string;
  name?: string;
  avatar_url?: string;
  provider?: string;
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

  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    body,
    headers: requestHeaders,
  });

  const payload = await parseResponse(response);

  if (!response.ok) {
    const message = typeof payload === 'object' && payload && 'error' in payload
      ? String((payload as { error: unknown }).error)
      : `请求失败，状态码 ${response.status}`;

    throw new ApiError(message, response.status, payload);
  }

  return payload as T;
}
