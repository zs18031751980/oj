import { computed, ref } from 'vue';
import { defineStore } from 'pinia';
import {
  API_BASE_URL,
  ApiError,
  apiRequest,
  clearAuthStorageMode,
  getAuthStorage,
  getAuthStorageMode,
  setAuthStorageMode,
  type AuthStorageMode,
  type TokenResponse,
  type UserInfo,
} from '../services/api';

const ACCESS_TOKEN_KEY = 'access_token';
const REFRESH_TOKEN_KEY = 'refresh_token';
const USER_INFO_KEY = 'user_info';
const OAUTH_REMEMBER_KEY = 'oauth_login_remember';

type SessionPayload = TokenResponse | {
  access_token: string;
  refresh_token: string;
  expires_in?: number;
  token_type?: string;
  user_info?: UserInfo;
};

interface PasswordLoginResponse {
  success: boolean;
  user_info?: UserInfo;
  tokens: TokenResponse;
}

const readQueryValue = (value: unknown): string => {
  if (Array.isArray(value)) {
    return String(value[0] ?? '');
  }

  if (value === null || value === undefined) {
    return '';
  }

  return String(value);
};

const readJson = <T>(key: string, storage: Storage = getAuthStorage()): T | null => {
  const value = storage.getItem(key);
  if (!value) {
    return null;
  }

  try {
    return JSON.parse(value) as T;
  } catch {
    storage.removeItem(key);
    return null;
  }
};

const clearStoredSession = () => {
  for (const storage of [localStorage, sessionStorage]) {
    storage.removeItem(ACCESS_TOKEN_KEY);
    storage.removeItem(REFRESH_TOKEN_KEY);
    storage.removeItem(USER_INFO_KEY);
  }

  sessionStorage.removeItem(OAUTH_REMEMBER_KEY);
  clearAuthStorageMode();
};

export const useAuthStore = defineStore('auth', () => {
  const storageMode = ref<AuthStorageMode>(getAuthStorageMode());
  const accessToken = ref(getAuthStorage(storageMode.value).getItem(ACCESS_TOKEN_KEY) || '');
  const refreshToken = ref(getAuthStorage(storageMode.value).getItem(REFRESH_TOKEN_KEY) || '');
  const userInfo = ref<UserInfo | null>(readJson<UserInfo>(USER_INFO_KEY, getAuthStorage(storageMode.value)));
  const supportedProviders = ref<string[]>([]);
  const isVerifying = ref(false);
  const isLoadingProviders = ref(false);

  const isAuthenticated = computed(() => Boolean(accessToken.value));
  const displayName = computed(() => (
    userInfo.value?.name || userInfo.value?.username || userInfo.value?.email || '已登录用户'
  ));

  const shouldClearAuthState = (error: unknown) => (
    error instanceof ApiError && [400, 401, 403].includes(error.status)
  );

  const setSession = (
    tokens: SessionPayload,
    options: { remember?: boolean; storageMode?: AuthStorageMode } = {},
  ) => {
    const resolvedMode = options.storageMode
      ?? (options.remember === undefined ? getAuthStorageMode() : options.remember ? 'local' : 'session');

    clearStoredSession();
    setAuthStorageMode(resolvedMode);
    storageMode.value = resolvedMode;

    const storage = getAuthStorage(resolvedMode);
    accessToken.value = tokens.access_token;
    refreshToken.value = tokens.refresh_token;
    userInfo.value = tokens.user_info ?? null;

    storage.setItem(ACCESS_TOKEN_KEY, tokens.access_token);
    storage.setItem(REFRESH_TOKEN_KEY, tokens.refresh_token);

    if (tokens.user_info) {
      storage.setItem(USER_INFO_KEY, JSON.stringify(tokens.user_info));
    } else {
      storage.removeItem(USER_INFO_KEY);
    }
  };

  const clearSession = () => {
    accessToken.value = '';
    refreshToken.value = '';
    userInfo.value = null;
    storageMode.value = 'local';
    clearStoredSession();
  };

  const startOAuthLogin = (provider: string, next = '/', remember = true) => {
    sessionStorage.setItem(OAUTH_REMEMBER_KEY, remember ? '1' : '0');
    const safeNext = next.startsWith('/') ? next : '/';
    window.location.href = `${API_BASE_URL}/auth/login/${encodeURIComponent(provider)}?next=${encodeURIComponent(safeNext)}`;
  };

  const startGithubLogin = (next = '/', remember = true) => {
    startOAuthLogin('github', next, remember);
  };

  const completeOAuthCallback = (query: Record<string, unknown>) => {
    const error = readQueryValue(query.error);
    if (error) {
      const errorDescription = readQueryValue(query.error_description);
      sessionStorage.removeItem(OAUTH_REMEMBER_KEY);
      throw new Error(errorDescription || error);
    }

    const token = readQueryValue(query.access_token);
    const refresh = readQueryValue(query.refresh_token);

    if (!token || !refresh) {
      sessionStorage.removeItem(OAUTH_REMEMBER_KEY);
      throw new Error('缺少登录令牌');
    }

    let parsedUser: UserInfo | undefined;
    const rawUser = readQueryValue(query.user_info);
    if (rawUser) {
      try {
        parsedUser = JSON.parse(rawUser) as UserInfo;
      } catch {
        try {
          parsedUser = JSON.parse(decodeURIComponent(rawUser)) as UserInfo;
        } catch {
          parsedUser = undefined;
        }
      }
    }

    const rememberHint = readQueryValue(sessionStorage.getItem(OAUTH_REMEMBER_KEY));
    sessionStorage.removeItem(OAUTH_REMEMBER_KEY);

    const remember = rememberHint === '1' ? true : rememberHint === '0' ? false : undefined;
    setSession(
      {
        access_token: token,
        refresh_token: refresh,
        expires_in: Number(readQueryValue(query.expires_in) || 0),
        token_type: readQueryValue(query.token_type) || 'Bearer',
        user_info: parsedUser,
      },
      remember === undefined ? {} : { remember },
    );
  };

  const loginWithPassword = async (identifier: string, password: string, remember = true) => {
    const result = await apiRequest<PasswordLoginResponse>('/auth/login/password', {
      method: 'POST',
      skipAuth: true,
      body: JSON.stringify({ identifier, password }),
    });

    const tokens = {
      ...result.tokens,
      user_info: result.tokens.user_info ?? result.user_info,
    };
    setSession(tokens, { remember });
    return tokens;
  };

  const loadSupportedProviders = async () => {
    isLoadingProviders.value = true;
    try {
      const result = await apiRequest<{ providers: string[] }>('/auth/providers', {
        skipAuth: true,
      });
      supportedProviders.value = Array.isArray(result.providers) ? result.providers : [];
      return supportedProviders.value;
    } catch {
      supportedProviders.value = [];
      return [];
    } finally {
      isLoadingProviders.value = false;
    }
  };

  const verify = async (options: { clearOnFailure?: boolean } = {}) => {
    if (!accessToken.value) {
      return false;
    }

    isVerifying.value = true;
    try {
      const result = await apiRequest<{ valid: boolean; user_info?: UserInfo }>('/auth/verify');
      if (result.user_info) {
        userInfo.value = result.user_info;
        getAuthStorage(storageMode.value).setItem(USER_INFO_KEY, JSON.stringify(result.user_info));
      }
      return result.valid;
    } catch (error) {
      if (options.clearOnFailure !== false && shouldClearAuthState(error)) {
        clearSession();
      }
      return false;
    } finally {
      isVerifying.value = false;
    }
  };

  const refresh = async () => {
    if (!refreshToken.value) {
      clearSession();
      return false;
    }

    try {
      const tokens = await apiRequest<TokenResponse>('/auth/refresh', {
        method: 'POST',
        skipAuth: true,
        body: JSON.stringify({ refresh_token: refreshToken.value }),
      });
      setSession(tokens, { storageMode: storageMode.value });
      return true;
    } catch (error) {
      if (shouldClearAuthState(error)) {
        clearSession();
      }
      return false;
    }
  };

  const restoreSession = async () => {
    if (!accessToken.value && !refreshToken.value) {
      return false;
    }

    const verified = accessToken.value ? await verify({ clearOnFailure: false }) : false;
    if (verified) {
      return true;
    }

    if (refreshToken.value) {
      return refresh();
    }

    clearSession();
    return false;
  };

  const logout = async () => {
    if (accessToken.value) {
      try {
        await apiRequest('/auth/logout', { method: 'POST' });
      } catch {
        // Prefer local logout even if the backend revoke request fails.
      }
    }

    clearSession();
  };

  return {
    accessToken,
    refreshToken,
    userInfo,
    supportedProviders,
    isAuthenticated,
    isVerifying,
    isLoadingProviders,
    displayName,
    setSession,
    clearSession,
    startOAuthLogin,
    startGithubLogin,
    completeOAuthCallback,
    loginWithPassword,
    loadSupportedProviders,
    verify,
    refresh,
    restoreSession,
    logout,
  };
});
