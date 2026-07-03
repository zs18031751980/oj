import { computed, ref } from 'vue';
import { defineStore } from 'pinia';
import { darkTheme } from 'naive-ui';
import { updateUserTheme } from '../services/api';

type ThemePreference = 'light' | 'dark' | 'system';

const syncThemeToBackend = async (preference: ThemePreference) => {
  try {
    const { useAuthStore } = await import('../stores/auth');
    const authStore = useAuthStore();
    if (authStore.isAuthenticated) {
      await updateUserTheme(preference);
    }
  } catch {
    // Silently ignore backend sync failures
  }
};

export const useThemeStore = defineStore('theme', () => {
  const LOCAL_STORAGE_THEME_KEY = 'appThemePreference';
  const userPreference = ref<ThemePreference>(
    (localStorage.getItem(LOCAL_STORAGE_THEME_KEY) as ThemePreference | null) || 'system',
  );
  const systemPrefersDark = ref(window.matchMedia('(prefers-color-scheme: dark)').matches);

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
      localStorage.setItem(LOCAL_STORAGE_THEME_KEY, userPreference.value);
      updateThemeClass(value);
      syncThemeToBackend(userPreference.value);
    },
  });

  const theme = computed(() => (isDark.value ? darkTheme : null));

  const applyUserTheme = (preference?: string) => {
    if (preference && ['light', 'dark', 'system'].includes(preference)) {
      userPreference.value = preference as ThemePreference;
      localStorage.setItem(LOCAL_STORAGE_THEME_KEY, preference);
      updateThemeClass(isDark.value);
    }
  };

  const setThemePreference = (preference: ThemePreference) => {
    userPreference.value = preference;
    localStorage.setItem(LOCAL_STORAGE_THEME_KEY, preference);
    updateThemeClass(isDark.value);
    syncThemeToBackend(preference);
  };

  const toggleTheme = () => {
    isDark.value = !isDark.value;
  };

  const init = () => {
    const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
    mediaQuery.addEventListener('change', (event) => {
      systemPrefersDark.value = event.matches;
      if (userPreference.value === 'system') {
        updateThemeClass(isDark.value);
      }
    });

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
