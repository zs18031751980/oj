<template>
  <main class="page-shell">
    <section class="hero">
      <div class="brand-mark">
        <img src="/chou/logo.jpg" alt="iOS Club XAUAT" />
      </div>
      <div class="brand-name">iOS CLUB · XAUAT</div>
      <span class="eyebrow">LUCKY DRAW / 2026</span>
      <h1>{{ config.title }}</h1>
      <p>{{ config.subtitle }}</p>
    </section>

    <section class="draw-card" aria-live="polite">
      <div class="orb orb-one"></div><div class="orb orb-two"></div>
      <div class="result">{{ result }}</div>
      <button type="button" :disabled="buttonDisabled" @click="draw">{{ buttonText }} <span>→</span></button>
      <div v-if="status" class="status">{{ status }}</div>
    </section>

    <section class="prizes-section">
      <div class="section-heading"><span>PRIZES</span><strong>奖品一览</strong></div>
      <div class="prize-grid">
        <article v-for="(item, index) in config.items" :key="item.name" class="prize">
          <div class="prize-icon">{{ icons[index % icons.length] }}</div>
          <div><div class="prize-name">{{ item.name }}</div></div>
        </article>
      </div>
    </section>
    <footer>Powered by Lottery Builder · 祝你好运</footer>
  </main>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, ref } from 'vue';
import './LuckyDraw.css';

type Prize = { name: string; weight: number };
const config = {
  title: '春日惊喜抽奖',
  subtitle: '玩数码，学编程，来iOSClub!',
  items: [
    { name: 'iOS主题钥匙扣', weight: 25 },
    { name: 'iOS主题扇子', weight: 20 },
    { name: 'iOS主题应援周边', weight: 30 },
    { name: 'iOS主题手账本', weight: 10 },
    { name: '花粉徽章', weight: 20 },
  ] satisfies Prize[],
};
const icons = ['✦', '◆', '●', '◇', '＋', '★'];
const cooldownMs = 24 * 60 * 60 * 1000;
const cooldownKey = `lottery:last-draw:${config.title}`;
const result = ref('准备好了吗？');
const status = ref('');
const coolingDown = ref(false);
const buttonText = computed(() => coolingDown.value ? '暂不可抽奖' : '开始抽奖');
const buttonDisabled = computed(() => coolingDown.value || !config.items.length);
let cooldownTimer: number | undefined;
let drawTimer: number | undefined;
const memoryStorage = new Map<string, string>();

function readLastDraw() {
  try {
    return localStorage.getItem(cooldownKey) || memoryStorage.get(cooldownKey) || '';
  } catch {
    return memoryStorage.get(cooldownKey) || '';
  }
}

function saveLastDraw(value: string) {
  memoryStorage.set(cooldownKey, value);
  try {
    localStorage.setItem(cooldownKey, value);
  } catch {
    // Some private or embedded browsers disable storage; memory fallback is enough.
  }
}

function secureRandom() {
  try {
    const cryptoApi = globalThis.crypto;
    if (cryptoApi?.getRandomValues) {
      const bytes = cryptoApi.getRandomValues(new Uint32Array(1));
      return bytes[0]! / 4294967296;
    }
  } catch {
    // Fall back for older or restricted browsers.
  }
  return Math.random();
}

function updateCooldown() {
  const lastDraw = Number(readLastDraw() || 0);
  const remaining = lastDraw + cooldownMs - Date.now();
  coolingDown.value = remaining > 0;
  status.value = coolingDown.value ? '抽奖资格冷却中' : '';
  if (!coolingDown.value && cooldownTimer) window.clearInterval(cooldownTimer);
}

function pickPrize() {
  const totalWeight = config.items.reduce((sum, item) => sum + item.weight, 0);
  let cursor = secureRandom() * totalWeight;
  for (const item of config.items) {
    cursor -= item.weight;
    if (cursor < 0) return item.name;
  }
  return config.items[config.items.length - 1]?.name || '暂无奖品';
}

function startCooldown() {
  saveLastDraw(String(Date.now()));
  updateCooldown();
  cooldownTimer = window.setInterval(updateCooldown, 1000);
}

function draw() {
  if (buttonDisabled.value || coolingDown.value) return;
  startCooldown();
  status.value = '正在抽取 · GOOD LUCK';
  let ticks = 0;
  drawTimer = window.setInterval(() => {
    result.value = config.items[Math.floor(Math.random() * config.items.length)]!.name;
    ticks += 1;
    if (ticks >= 13 && drawTimer) {
      window.clearInterval(drawTimer);
      result.value = pickPrize();
      status.value = '抽取完成 · 抽奖资格冷却中';
    }
  }, 75);
}

updateCooldown();
onBeforeUnmount(() => {
  if (cooldownTimer) window.clearInterval(cooldownTimer);
  if (drawTimer) window.clearInterval(drawTimer);
});
</script>
