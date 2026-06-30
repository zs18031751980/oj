<template>
  <n-config-provider :theme="theme">
    <n-dialog-provider>
      <n-message-provider>
        <router-view v-slot="{ Component }">
          <keep-alive :include="['Home', 'Playground', 'Learn', 'Announcements', 'AdminDashboard', 'AdminUsers']">
            <component :is="Component" />
          </keep-alive>
        </router-view>
      </n-message-provider>
    </n-dialog-provider>
  </n-config-provider>
</template>

<script setup lang="ts">
import {onMounted} from 'vue'
import {NConfigProvider, NDialogProvider, NMessageProvider} from "naive-ui";
import {useThemeStore} from './stores/theme'
import {useAuthStore} from './stores/auth'
import {storeToRefs} from 'pinia'

const themeStore = useThemeStore()
const authStore = useAuthStore()
const {theme} = storeToRefs(themeStore)
const {init} = themeStore

onMounted(() => {
  init()
  void authStore.restoreSession()
})
</script>
