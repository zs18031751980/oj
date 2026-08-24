/**
 * 防抖函数：延迟执行，连续触发时重置计时器
 */
export function debounce<T extends (...args: never[]) => void>(fn: T, ms: number): T & { cancel: () => void } {
  let timer: ReturnType<typeof setTimeout> | null = null;
  const debounced = ((...args: never[]) => {
    if (timer) clearTimeout(timer);
    timer = setTimeout(() => fn(...args), ms);
  }) as T & { cancel: () => void };
  debounced.cancel = () => {
    if (timer) { clearTimeout(timer); timer = null; }
  };
  return debounced;
}

/**
 * 节流函数：固定间隔内只执行一次
 */
export function throttle<T extends (...args: never[]) => void>(fn: T, ms: number): T {
  let last = 0;
  return ((...args: never[]) => {
    const now = Date.now();
    if (now - last >= ms) {
      last = now;
      fn(...args);
    }
  }) as T;
}
