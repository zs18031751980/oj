<template>
  <n-config-provider :theme="theme">
    <n-dialog-provider>
      <n-message-provider>
        <router-view/>
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
const {theme} = storeToRefs(themeStore)
const {init} = themeStore
// 抽奖页是公开活动页：避免受限浏览器因认证存储不可用而在首屏白屏。
const authStore = window.location.pathname === '/chou' ? null : useAuthStore()

onMounted(() => {
  init()
  void authStore?.restoreSession()
})
</script>
