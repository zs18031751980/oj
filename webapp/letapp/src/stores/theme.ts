// stores/theme.js
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { darkTheme } from 'naive-ui'

export const useThemeStore = defineStore('theme', () => {
    const LOCAL_STORAGE_THEME_KEY = 'appThemePreference'

    const userPreference = ref(localStorage.getItem(LOCAL_STORAGE_THEME_KEY) || 'system')
    const systemPrefersDark = ref(window.matchMedia('(prefers-color-scheme: dark)').matches)

    const isDark = computed({
        get() {
            if (userPreference.value === 'dark') return true
            if (userPreference.value === 'light') return false
            return systemPrefersDark.value
        },
        set(val) {
            userPreference.value = val ? 'dark' : 'light'
            localStorage.setItem(LOCAL_STORAGE_THEME_KEY, userPreference.value)
            updateThemeClass(val)
        }
    })

    const theme = computed(() => (isDark.value ? darkTheme : null))

    function updateThemeClass(dark: boolean) {
        if (dark) {
            document.documentElement.classList.add('dark')
        } else {
            document.documentElement.classList.remove('dark')
        }
    }

    function setThemePreference(preference: 'light' | 'dark' | 'system') {
        userPreference.value = preference
        localStorage.setItem(LOCAL_STORAGE_THEME_KEY, preference)
        updateThemeClass(isDark.value)
    }

    function toggleTheme() {
        isDark.value = !isDark.value
    }

    // 初始化
    function init() {
        const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)')
        mediaQuery.addEventListener('change', (e) => {
            systemPrefersDark.value = e.matches
            if (userPreference.value === 'system') {
                updateThemeClass(isDark.value)
            }
        })
        updateThemeClass(isDark.value)
    }

    return {
        isDark,
        theme,
        userPreference,
        setThemePreference,
        toggleTheme,
        init
    }
})