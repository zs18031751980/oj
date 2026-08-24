/**
 * 轻量性能监控 - 收集 Web Vitals 和页面加载指标
 * 仅在生产环境采集，开发环境静默
 */

interface PerfMetric {
  name: string;
  value: number;
  rating: 'good' | 'needs-improvement' | 'poor';
  page: string;
  timestamp: number;
}

const isDev = import.meta.env.DEV;

function getPageName(): string {
  return window.location.pathname;
}

function classify(name: string, value: number): 'good' | 'needs-improvement' | 'poor' {
  const thresholds: Record<string, [number, number]> = {
    LCP: [2500, 4000],
    FID: [100, 300],
    CLS: [0.1, 0.25],
    INP: [200, 500],
    FCP: [1800, 3000],
    TTFB: [800, 1800],
  };
  const t = thresholds[name];
  if (!t) return 'good';
  if (value <= t[0]) return 'good';
  if (value <= t[1]) return 'needs-improvement';
  return 'poor';
}

function report(metric: PerfMetric) {
  if (isDev) {
    console.log(`[Perf] ${metric.name}: ${metric.value.toFixed(0)}ms (${metric.rating}) @ ${metric.page}`);
    return;
  }
  // 生产环境可上报到分析服务
  try {
    const blob = new Blob([JSON.stringify(metric)], { type: 'application/json' });
    navigator.sendBeacon('/api/perf', blob);
  } catch { /* 静默 */ }
}

function observeEntry(type: string, cb: (entry: PerformanceEntry) => void) {
  try {
    const po = new PerformanceObserver((list) => {
      for (const entry of list.getEntries()) cb(entry);
    });
    po.observe({ type, buffered: true });
  } catch { /* 不支持 */ }
}

/** 初始化性能监控，应在 main.ts 中调用一次 */
export function initPerfMonitor() {
  if (isDev || typeof window === 'undefined') return;

  // LCP
  observeEntry('largest-contentful-paint', (entry) => {
    report({ name: 'LCP', value: entry.startTime, rating: classify('LCP', entry.startTime), page: getPageName(), timestamp: Date.now() });
  });

  // FCP
  observeEntry('paint', (entry) => {
    if (entry.name === 'first-contentful-paint') {
      report({ name: 'FCP', value: entry.startTime, rating: classify('FCP', entry.startTime), page: getPageName(), timestamp: Date.now() });
    }
  });

  // TTFB
  observeEntry('navigation', (entry) => {
    const nav = entry as PerformanceNavigationTiming;
    const ttfb = nav.responseStart - nav.requestStart;
    if (ttfb > 0) {
      report({ name: 'TTFB', value: ttfb, rating: classify('TTFB', ttfb), page: getPageName(), timestamp: Date.now() });
    }
  });

  // CLS
  let clsValue = 0;
  observeEntry('layout-shift', (entry) => {
    const e = entry as any;
    if (!e.hadRecentInput) {
      clsValue += e.value;
      report({ name: 'CLS', value: clsValue, rating: classify('CLS', clsValue), page: getPageName(), timestamp: Date.now() });
    }
  });

  // INP (通过 Event Timing)
  observeEntry('event', (entry) => {
    const e = entry as PerformanceEventTiming;
    if (e.duration > 50) {
      report({ name: 'INP', value: e.duration, rating: classify('INP', e.duration), page: getPageName(), timestamp: Date.now() });
    }
  });

  // JS 异常
  window.addEventListener('error', () => {
    report({ name: 'JS_Error', value: 0, rating: 'poor', page: getPageName(), timestamp: Date.now() });
  });

  // 资源加载统计
  window.addEventListener('load', () => {
    setTimeout(() => {
      const entries = performance.getEntriesByType('resource');
      const slowResources = entries.filter(e => e.duration > 500).map(e => ({ name: e.name.split('/').pop(), duration: Math.round(e.duration) }));
      if (slowResources.length > 0) {
        report({ name: 'SlowResources', value: slowResources.length, rating: 'needs-improvement', page: getPageName(), timestamp: Date.now() });
      }
    }, 0);
  });
}
