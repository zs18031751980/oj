import { computed, ref } from 'vue';
import { defineStore } from 'pinia';
import { darkTheme } from 'naive-ui';
import { getAuthStorage, updateUserTheme } from '../services/api';

type ThemePreference = 'light' | 'dark' | 'system';
const THEME_STORAGE_KEY = 'appThemePreference';

const readThemePreference = (): ThemePreference => {
  try {
    const preference = localStorage.getItem(THEME_STORAGE_KEY);
    return preference === 'light' || preference === 'dark' || preference === 'system'
      ? preference
      : 'system';
  } catch {
    return 'system';
  }
};

const saveThemePreference = (preference: ThemePreference) => {
  try {
    localStorage.setItem(THEME_STORAGE_KEY, preference);
  } catch {
    // Private and embedded browsers can disable web storage.
  }
};

const getSystemPrefersDark = () => {
  try {
    return typeof window.matchMedia === 'function'
      && window.matchMedia('(prefers-color-scheme: dark)').matches;
  } catch {
    return false;
  }
};

const syncThemeToBackend = async (preference: ThemePreference) => {
  try {
    if (getAuthStorage().getItem('access_token')) {
      await updateUserTheme(preference);
    }
  } catch {
    // Silently ignore backend sync failures
  }
};

export const useThemeStore = defineStore('theme', () => {
  const userPreference = ref<ThemePreference>(readThemePreference());
  const systemPrefersDark = ref(getSystemPrefersDark());

  const updateThemeClass = (dark: boolean) => {
    document.documentElement.classList.toggle('dark', dark);
  };

  const isDark = computed({
    get() {
      if (userPreference.value === 'dark') {
        return true;
      }

      if (userPreference.value === 'light') {
        return false;
      }

      return systemPrefersDark.value;
    },
    set(value: boolean) {
      userPreference.value = value ? 'dark' : 'light';
      saveThemePreference(userPreference.value);
      updateThemeClass(value);
      syncThemeToBackend(userPreference.value);
    },
  });

  const theme = computed(() => (isDark.value ? darkTheme : null));

  const applyUserTheme = (preference?: string) => {
    if (preference && ['light', 'dark', 'system'].includes(preference)) {
      userPreference.value = preference as ThemePreference;
      saveThemePreference(userPreference.value);
      updateThemeClass(isDark.value);
    }
  };

  const setThemePreference = (preference: ThemePreference) => {
    userPreference.value = preference;
    saveThemePreference(preference);
    updateThemeClass(isDark.value);
    syncThemeToBackend(preference);
  };

  const toggleTheme = () => {
    isDark.value = !isDark.value;
  };

  const init = () => {
    if (typeof window.matchMedia !== 'function') {
      updateThemeClass(isDark.value);
      return;
    }
    const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
    const handleChange = (event: MediaQueryListEvent) => {
      systemPrefersDark.value = event.matches;
      if (userPreference.value === 'system') {
        updateThemeClass(isDark.value);
      }
    };
    if (typeof mediaQuery.addEventListener === 'function') {
      mediaQuery.addEventListener('change', handleChange);
    } else {
      mediaQuery.addListener(handleChange);
    }

    updateThemeClass(isDark.value);
  };

  return {
    isDark,
    theme,
    userPreference,
    applyUserTheme,
    setThemePreference,
    toggleTheme,
    init,
  };
});
