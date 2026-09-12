export function startPolling<T>(
  task: (signal: AbortSignal) => Promise<T>,
  receive: (value: T) => boolean,
  fail: (error: unknown) => void,
  interval = 1000,
  maxDuration = 10 * 60 * 1000,
) {
  const controller = new AbortController();
  let timer: ReturnType<typeof setTimeout> | undefined;
  let errors = 0;
  const started = Date.now();
  const stop = () => { controller.abort(); clearTimeout(timer); };
  const tick = async () => {
    if (controller.signal.aborted) return;
    if (Date.now() - started > maxDuration) { stop(); fail(new Error('等待判题超时，请稍后查看提交记录')); return; }
    try {
      const value = await task(controller.signal);
      if (controller.signal.aborted) return;
      errors = 0;
      if (receive(value)) { stop(); return; }
    } catch (error) {
      if (controller.signal.aborted) return;
      errors += 1;
      const status = (error as { status?: number })?.status;
      if (errors >= 5 || (status && status < 500 && status !== 429)) { stop(); fail(error); return; }
    }
    timer = setTimeout(tick, Math.min(interval * 2 ** errors, 15000));
  };
  void tick();
  return stop;
}

export const PENDING_JUDGE_STATES = new Set(['Pending', 'Queued', 'Judging', 'Claimed', 'Compiling', 'Compiled', 'Running', 'Checking']);

export function waitForJudgement<T extends { status: string }>(task: (signal: AbortSignal) => Promise<T>, signal: AbortSignal): Promise<T> {
  return new Promise((resolve, reject) => {
    if (signal.aborted) { reject(signal.reason); return; }
    const stop = startPolling(task, value => {
      if (PENDING_JUDGE_STATES.has(value.status)) return false;
      signal.removeEventListener('abort', abort); resolve(value); return true;
    }, error => { signal.removeEventListener('abort', abort); reject(error); });
    const abort = () => { stop(); reject(signal.reason); };
    signal.addEventListener('abort', abort, { once: true });
  });
}
