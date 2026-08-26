<script setup lang="ts">
import { computed, markRaw, onMounted, onUnmounted, reactive, ref, shallowRef, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { Icon } from '@iconify/vue';
import { useMessage, useDialog } from 'naive-ui';
import { useThemeStore } from '../stores/theme';
import { useAuthStore } from '../stores/auth';
import { storeToRefs } from 'pinia';
import type MonacoEditor from '../components/MonacoEditor.vue';
import type MarkdownComponent from '../components/MarkdownComponent.vue';
import {
  apiRequest,
  getFavoriteStatus,
  addFavorite,
  removeFavorite,
  listMySubmissions,
} from '../services/api';
import { useProblemStats } from '../composables/useProblemStats';
import { useProblemCode } from '../composables/useProblemCode';

const MonacoEditorComp = shallowRef<typeof MonacoEditor>();
const MarkdownComp = shallowRef<typeof MarkdownComponent>();

interface TestCase {
  input: string;
  output: string;
}
interface Problem {
  id: number;
  sourceNumber?: number;
  category?: string;
  categoryLabel?: string;
  title: string;
  difficulty: '简单' | '中等' | '困难';
  tags: string[];
  description: string;
  inputFormat: string;
  outputFormat: string;
  samples: TestCase[];
  testCaseCount: number;
  interactive?: boolean;
  judgeable?: boolean;
  timeLimit: number;
  memoryLimit: number;
  learningMaterial?: string;
}
interface SubmissionHistoryItem {
  id: number;
  problem_id: number;
  problem_title: string;
  difficulty: string | null;
  language: string;
  status: string;
  time_used: number | null;
  created_at: string | null;
}
interface SubmissionResponse {
  id: number;
  status: string;
  testcase_results?: any[];
  fail_testcase_index?: number | null;
  time_used?: number;
  compile_error?: string;
}
interface TestResult {
  testCaseIndex: number;
  passed: boolean;
  actualOutput: string;
  input: string;
  expected: string;
}

const route = useRoute();
const router = useRouter();
const message = useMessage();
const dialog = useDialog();
const themeStore = useThemeStore();
const authStore = useAuthStore();
const { isDark } = storeToRefs(themeStore);

const problemId = computed(() => Number(route.params.id));

/* ============ 布局状态 ============ */
const leftWidth = ref(30);
const bottomHeight = ref(280);
const isDraggingLeft = ref(false);
const isDraggingBottom = ref(false);
const mainRef = ref<HTMLElement | null>(null);
const isFocusMode = ref(false);

/* ============ 题目数据 ============ */
const problem = ref<Problem | null>(null);
const isProblemLoading = ref(true);
const problemLoadError = ref('');
const activeTab = ref<'desc' | 'submissions' | 'hints'>('desc');

/* ============ 代码 / 编辑器 ============ */
const languageTemplates: Record<string, string> = markRaw({
  c: '#include <stdio.h>\n\nint main(void) {\n  // 在此编写代码\n  return 0;\n}',
  cpp: '#include <iostream>\nusing namespace std;\n\nint main() {\n  // 在此编写代码\n  return 0;\n}',
  python: '# 在此编写代码\n',
  java: 'public class Main {\n  public static void main(String[] args) {\n    // 在此编写代码\n  }\n}',
});
const language = ref('cpp');
const code = ref(languageTemplates['cpp'] || '');
const editorRef = ref<any>(null);

const langOptions = markRaw([
  { value: 'c', label: 'C' },
  { value: 'cpp', label: 'C++' },
  { value: 'python', label: 'Python 3' },
  { value: 'java', label: 'Java 17' },
]);
const filenameMap: Record<string, string> = {
  c: 'main.c',
  cpp: 'main.cpp',
  python: 'main.py',
  java: 'Main.java',
};
const currentFilename = computed(() => filenameMap[language.value] || 'main.txt');
const editorLanguageMap: Record<string, string> = {
  c: 'c',
  cpp: 'cpp',
  python: 'python',
  java: 'java',
};

/* ============ 保存状态 ============ */
type SaveStatus = 'idle' | 'saving' | 'saved' | 'error';
const saveStatus = ref<SaveStatus>('idle');
const lastSavedTime = ref<Date | null>(null);
let saveTimer: ReturnType<typeof setTimeout> | null = null;
const { saveCode, loadCode } = useProblemCode();

const scheduleSave = () => {
  saveStatus.value = 'saving';
  if (saveTimer) clearTimeout(saveTimer);
  saveTimer = setTimeout(async () => {
    try {
      await saveCode(problemId.value, language.value, code.value);
      saveStatus.value = 'saved';
      lastSavedTime.value = new Date();
    } catch {
      saveStatus.value = 'error';
    }
  }, 1200);
};
const saveNow = async () => {
  if (saveTimer) clearTimeout(saveTimer);
  try {
    await saveCode(problemId.value, language.value, code.value);
    saveStatus.value = 'saved';
    lastSavedTime.value = new Date();
    message.success('已保存');
  } catch {
    saveStatus.value = 'error';
    message.error('保存失败，请检查网络');
  }
};
watch(code, scheduleSave);

const langMenuOpen = ref(false);
const updateLanguage = async (lang: string) => {
  if (lang === language.value) {
    langMenuOpen.value = false;
    return;
  }
  const doSwitch = async () => {
    await saveCode(problemId.value, language.value, code.value);
    language.value = lang;
    const saved = await loadCode(problemId.value, lang);
    code.value = saved || languageTemplates[lang] || '';
    submitResult.value = null;
    if (pollTimer.value) {
      clearInterval(pollTimer.value);
      pollTimer.value = null;
    }
    saveStatus.value = 'saved';
    lastSavedTime.value = new Date();
  };
  if (code.value.trim()) {
    dialog.warning({
      title: '切换语言',
      content: '切换语言会加载该语言的初始代码模板，当前代码不会带到新语言。是否继续？',
      positiveText: '继续切换',
      negativeText: '取消',
      onPositiveClick: () => {
        langMenuOpen.value = false;
        doSwitch();
      },
      onNegativeClick: () => {
        langMenuOpen.value = false;
      },
    });
  } else {
    langMenuOpen.value = false;
    await doSwitch();
  }
};

/* ============ 提交 / 判题 ============ */
const isSubmitting = ref(false);
const submitResult = ref<string | null>(null);
const resultVisible = ref(true);
const activeResultTab = ref<'testcases' | 'run' | 'submit'>('submit');
const testResults = ref<TestResult[]>([]);
const currentResultPage = ref(0);
const failedTestCaseIndex = ref<number | null>(null);
const compileErrorMsg = ref('');
const judgePhase = ref<'idle' | 'received' | 'compiling' | 'judging' | 'done'>('idle');

const passedCount = computed(() => testResults.value.filter((t) => t.passed).length);

const pollTimer = ref<ReturnType<typeof setInterval> | null>(null);
const { getStats, incrementSubmissions, incrementAccepted } = useProblemStats();

const submitCode = async () => {
  const p = problem.value;
  if (!p || p.judgeable === false) {
    message.info('这是一道练习题，不参与自动判题。');
    return;
  }
  if (!authStore.isAuthenticated) {
    dialog.warning({
      title: '提示',
      content: '请登录后再提交',
      positiveText: '去登录',
      negativeText: '取消',
      onPositiveClick: () => authStore.startOAuthLogin('iOSClub', route.fullPath, true),
    });
    return;
  }
  if (!code.value.trim()) {
    message.warning('请先编写代码');
    return;
  }
  if (pollTimer.value) {
    clearInterval(pollTimer.value);
    pollTimer.value = null;
  }
  isSubmitting.value = true;
  resultVisible.value = true;
  activeResultTab.value = 'submit';
  submitResult.value = null;
  testResults.value = [];
  failedTestCaseIndex.value = null;
  currentResultPage.value = 0;
  judgePhase.value = 'received';
  try {
    const created = await apiRequest<SubmissionResponse>('/submissions', {
      method: 'POST',
      body: JSON.stringify({
        problem_id: p.id,
        code: code.value,
        language: language.value,
      }),
    });
    incrementSubmissions(p.id);
    judgePhase.value = 'judging';
    if (created.status === 'Pending' || created.status === 'Running') {
      let judged = false;
      pollTimer.value = setInterval(async () => {
        try {
          const res = await apiRequest<SubmissionResponse>(`/submissions/${created.id}`);
          if (judged) return;
          if (res.status !== 'Pending' && res.status !== 'Running') {
            judged = true;
            if (pollTimer.value) {
              clearInterval(pollTimer.value);
              pollTimer.value = null;
            }
            _handleJudgeResult(res, p);
          }
        } catch {
          if (judged) return;
          judged = true;
          if (pollTimer.value) {
            clearInterval(pollTimer.value);
            pollTimer.value = null;
          }
          isSubmitting.value = false;
          judgePhase.value = 'done';
          message.error('查询判题结果失败');
        }
      }, 1000);
    } else {
      _handleJudgeResult(created, p);
    }
  } catch (e: any) {
    message.error(e?.message || '提交失败');
    isSubmitting.value = false;
    judgePhase.value = 'done';
  }
};

const _handleJudgeResult = (res: SubmissionResponse, p: Problem) => {
  const results: TestResult[] = [];
  if (res.testcase_results && res.testcase_results.length > 0) {
    for (const tr of res.testcase_results) {
      results.push({
        testCaseIndex: tr.testCaseIndex ?? 0,
        passed: tr.passed,
        actualOutput: tr.actualOutput || tr.stdout || '',
        input: tr.input || '',
        expected: tr.expected || '',
      });
    }
  } else {
    const total = p.testCaseCount;
    const first = res.fail_testcase_index;
    for (let i = 0; i < total; i++) {
      results.push({
        testCaseIndex: i,
        passed: first == null || first == undefined || i < first,
        actualOutput: '(实际输出未记录)',
        input: '',
        expected: '',
      });
    }
  }
  testResults.value = results;
  if (res.status === 'AC') {
    submitResult.value = 'AC';
    currentResultPage.value = 0;
    incrementAccepted(p.id);
  } else if (res.status === 'CE') {
    submitResult.value = 'CE';
    compileErrorMsg.value = res.compile_error || '';
    currentResultPage.value = 0;
  } else {
    submitResult.value = 'WA';
    const fi = res.fail_testcase_index ?? 0;
    failedTestCaseIndex.value = fi;
    currentResultPage.value = fi;
  }
  isSubmitting.value = false;
  judgePhase.value = 'done';
};

/* ============ 运行（自测） ============ */
const stdin = ref('');
const expectedOutput = ref('');
const selfTestOutput = ref('');
const selfTestStatus = ref('');
const selfTestVerdict = ref<'pass' | 'fail' | null>(null);
const isSelfTesting = ref(false);

const runSelfTest = async () => {
  if (!code.value.trim()) {
    message.warning('请先编写代码');
    return;
  }
  isSelfTesting.value = true;
  selfTestOutput.value = '';
  selfTestStatus.value = '';
  selfTestVerdict.value = null;
  activeResultTab.value = 'run';
  resultVisible.value = true;
  try {
    const endpoint = authStore.isAuthenticated ? '/code/run' : '/code/run/public';
    const res = await apiRequest<any>(endpoint, {
      method: 'POST',
      skipAuth: !authStore.isAuthenticated,
      body: JSON.stringify({
        code: code.value,
        language: editorLanguageMap[language.value] || language.value,
        stdin: stdin.value,
      }),
    });
    const stderr = (res.stderr || '').trim();
    const stdout = (res.stdout || '').trim();
    if (stderr) {
      selfTestOutput.value = stderr;
      selfTestStatus.value = '运行出错';
      selfTestVerdict.value = 'fail';
    } else {
      selfTestOutput.value = stdout;
      const expected = expectedOutput.value.trim();
      if (expected) {
        selfTestVerdict.value = stdout === expected ? 'pass' : 'fail';
        selfTestStatus.value = stdout === expected ? '通过' : '未通过';
      } else {
        selfTestStatus.value = stdout ? '执行成功' : '程序无输出';
      }
    }
  } catch (error) {
    selfTestOutput.value = error instanceof Error ? error.message : '请求失败，请重试';
    selfTestStatus.value = '运行出错';
    selfTestVerdict.value = 'fail';
  } finally {
    isSelfTesting.value = false;
  }
};

const runThisSample = (sample: TestCase) => {
  stdin.value = sample.input;
  expectedOutput.value = sample.output;
  selfTestStatus.value = '';
  selfTestVerdict.value = null;
  selfTestOutput.value = '';
  activeResultTab.value = 'testcases';
  resultVisible.value = true;
  message.info('已将样例输入/输出填入测试区');
};

/* ============ 复制 ============ */
const copyText = async (text: string) => {
  try {
    await navigator.clipboard.writeText(text);
    message.success('已复制');
  } catch {
    message.error('复制失败');
  }
};

/* ============ 收藏 ============ */
const isFavorited = ref(false);
const favoriteBusy = ref(false);
const loadFavoriteStatus = async () => {
  isFavorited.value = false;
  if (!authStore.isAuthenticated) return;
  try {
    const r = await getFavoriteStatus(problemId.value);
    isFavorited.value = r.favorited;
  } catch {
    isFavorited.value = false;
  }
};
const goLogin = () => {
  authStore.startOAuthLogin('iOSClub', router.currentRoute.value.fullPath, true);
};
const toggleFavorite = async () => {
  if (!authStore.isAuthenticated) {
    message.warning('请先登录后再收藏题目');
    goLogin();
    return;
  }
  if (favoriteBusy.value) return;
  favoriteBusy.value = true;
  try {
    const r = isFavorited.value ? await removeFavorite(problemId.value) : await addFavorite(problemId.value);
    isFavorited.value = r.favorited;
    message.success(isFavorited.value ? '已加入收藏题目' : '已取消收藏');
  } catch (e: any) {
    message.error(e?.message || '操作失败，请稍后重试');
  } finally {
    favoriteBusy.value = false;
  }
};

/* ============ 题目加载 ============ */
const loadProblem = async () => {
  isProblemLoading.value = true;
  problemLoadError.value = '';
  problem.value = null;
  try {
    problem.value = await apiRequest<Problem>(`/problems/${problemId.value}`, { skipAuth: true });
  } catch (e: any) {
    problemLoadError.value = e?.message || '题目加载失败，请稍后重试。';
  } finally {
    isProblemLoading.value = false;
  }
  await loadFavoriteStatus();
};

/* ============ 学习资料 / 提示 ============ */
const learningMarkdown = ref<{ content: string } | undefined>();
const isLearningLoading = ref(false);
const learningError = ref('');
// 学习资料 markdown 内相对图片的基准目录
const learningBaseDir = computed(() => {
  const file = problem.value?.learningMaterial || '';
  const parts = file.split('/');
  parts.pop();
  return parts.join('/');
});
const loadLearningMaterial = async () => {
  const file = problem.value?.learningMaterial;
  if (!file) {
    learningMarkdown.value = undefined;
    return;
  }
  isLearningLoading.value = true;
  learningError.value = '';
  try {
    const url = `/learn/${file.split('/').map((s) => encodeURIComponent(s)).join('/')}`;
    const res = await fetch(url);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    learningMarkdown.value = { content: await res.text() };
  } catch {
    learningMarkdown.value = undefined;
    learningError.value = '学习资料加载失败，请稍后重试。';
  } finally {
    isLearningLoading.value = false;
  }
};
const descMarkdown = computed(() => ({ content: problem.value?.description || '' }));

/* ============ 提交记录 ============ */
const problemSubmissions = ref<SubmissionHistoryItem[]>([]);
const submissionsLoading = ref(false);
const loadProblemSubmissions = async () => {
  if (!authStore.isAuthenticated) {
    problemSubmissions.value = [];
    return;
  }
  submissionsLoading.value = true;
  try {
    const res = await listMySubmissions(1, 50);
    problemSubmissions.value = (res.data || []).filter((s) => s.problem_id === problemId.value);
  } catch {
    problemSubmissions.value = [];
  } finally {
    submissionsLoading.value = false;
  }
};

/* ============ 编辑器设置 ============ */
interface EditorSettings {
  fontSize: number;
  tabSize: number;
  wordWrap: 'on' | 'off';
  minimap: boolean;
  theme: 'auto' | 'light' | 'dark';
}
const SETTINGS_KEY = 'editor_settings';
const defaultSettings: EditorSettings = {
  fontSize: 14,
  tabSize: 2,
  wordWrap: 'on',
  minimap: false,
  theme: 'auto',
};
const loadSettings = (): EditorSettings => {
  try {
    const raw = localStorage.getItem(SETTINGS_KEY);
    if (raw) return { ...defaultSettings, ...JSON.parse(raw) };
  } catch {
    /* ignore */
  }
  return { ...defaultSettings };
};
const editorSettings = reactive<EditorSettings>(loadSettings());
watch(
  editorSettings,
  () => {
    try {
      localStorage.setItem(SETTINGS_KEY, JSON.stringify(editorSettings));
    } catch {
      /* ignore */
    }
    applyEditorSettings();
  },
  { deep: true },
);
const effectiveDark = computed(() =>
  editorSettings.theme === 'auto' ? isDark.value : editorSettings.theme === 'dark',
);
const applyEditorSettings = () => {
  const ed = editorRef.value;
  if (!ed) return;
  ed.updateOptions({
    fontSize: editorSettings.fontSize,
    tabSize: editorSettings.tabSize,
    wordWrap: editorSettings.wordWrap,
    minimap: { enabled: editorSettings.minimap },
  });
};
const onEditorReady = (e: any) => {
  editorRef.value = e;
  applyEditorSettings();
};
const settingsOpen = ref(false);

const formatCode = async () => {
  const ed = editorRef.value;
  if (!ed) return;
  const action = ed.getAction('editor.action.formatDocument');
  if (action) {
    await action.run();
    message.success('已格式化代码');
  } else {
    message.info('当前语言暂不支持自动格式化');
  }
};
const resetCode = () => {
  dialog.warning({
    title: '恢复初始代码',
    content: '此操作将用该语言的初始模板覆盖当前代码，且无法撤销。是否继续？',
    positiveText: '确认恢复',
    negativeText: '取消',
    onPositiveClick: () => {
      code.value = languageTemplates[language.value] || '';
      message.success('已恢复初始代码');
    },
  });
};

/* ============ 错误定位 ============ */
const parseErrorParts = (text: string) => {
  if (!text) return [{ text: '(无错误信息)' }];
  const parts: { text: string; line?: number }[] = [];
  const re = /((?:main\.)?\w+\.(?:cpp|c|py|java))(?::(\d+))?|line\s+(\d+)/gi;
  let last = 0;
  let m: RegExpExecArray | null;
  while ((m = re.exec(text))) {
    if (m.index > last) parts.push({ text: text.slice(last, m.index) });
    const line = m[2] ? Number(m[2]) : m[3] ? Number(m[3]) : undefined;
    parts.push({ text: m[0], line });
    last = re.lastIndex;
  }
  if (last < text.length) parts.push({ text: text.slice(last) });
  return parts;
};
const gotoLine = (line: number) => {
  const ed = editorRef.value;
  if (!ed) return;
  ed.revealLineInCenter(line);
  ed.setPosition({ lineNumber: line, column: 1 });
  ed.focus();
};

/* ============ 拖拽分割线 ============ */
const startLeftDrag = (_e: MouseEvent) => {
  if (!mainRef.value) return;
  isDraggingLeft.value = true;
  const rect = mainRef.value.getBoundingClientRect();
  const onMove = (ev: MouseEvent) => {
    const pct = ((ev.clientX - rect.left) / rect.width) * 100;
    leftWidth.value = Math.min(Math.max(pct, 25), 75);
  };
  const onUp = () => {
    isDraggingLeft.value = false;
    document.removeEventListener('mousemove', onMove);
    document.removeEventListener('mouseup', onUp);
  };
  document.addEventListener('mousemove', onMove);
  document.addEventListener('mouseup', onUp);
};
const startBottomDrag = (e: MouseEvent) => {
  isDraggingBottom.value = true;
  const startY = e.clientY;
  const startH = bottomHeight.value;
  const onMove = (ev: MouseEvent) => {
    bottomHeight.value = Math.min(Math.max(startH + (startY - ev.clientY), 120), 560);
  };
  const onUp = () => {
    isDraggingBottom.value = false;
    document.removeEventListener('mousemove', onMove);
    document.removeEventListener('mouseup', onUp);
  };
  document.addEventListener('mousemove', onMove);
  document.addEventListener('mouseup', onUp);
};

/* ============ 专注模式 ============ */
const onFullscreenChange = () => {
  if (!document.fullscreenElement && isFocusMode.value) {
    isFocusMode.value = false;
  }
};
watch(isFocusMode, (v) => {
  if (v) {
    document.documentElement.classList.add('focus-mode');
    document.documentElement.requestFullscreen().catch(() => {});
  } else {
    document.documentElement.classList.remove('focus-mode');
    if (document.fullscreenElement) {
      document.exitFullscreen().catch(() => {});
    }
  }
});

/* ============ 快捷键 ============ */
const handleKeyboard = (e: KeyboardEvent) => {
  const mod = e.ctrlKey || e.metaKey;
  if (mod && e.key === 'Enter') {
    e.preventDefault();
    if (e.shiftKey) submitCode();
    else runSelfTest();
    return;
  }
  if (mod && e.key.toLowerCase() === 's') {
    e.preventDefault();
    saveNow();
    return;
  }
  if (mod && e.shiftKey && e.key.toLowerCase() === 'f') {
    e.preventDefault();
    formatCode();
    return;
  }
};

/* ============ 顶栏用户菜单 ============ */
const userMenuOpen = ref(false);
const goUserPage = async (to: string) => {
  userMenuOpen.value = false;
  await router.push(to);
};
const handleLogout = async () => {
  userMenuOpen.value = false;
  await authStore.logout();
};

/* ============ 标签 / 统计 ============ */
const goTag = (tag: string) => router.push({ path: '/problems', query: { tag } });
const problemStats = computed(() => getStats(problemId.value));

const statusInfo: Record<string, { label: string; cls: string }> = {
  AC: { label: '通过', cls: 'text-emerald-600 dark:text-emerald-400' },
  WA: { label: '答案错误', cls: 'text-rose-600 dark:text-rose-400' },
  CE: { label: '编译错误', cls: 'text-rose-600 dark:text-rose-400' },
  TLE: { label: '超时', cls: 'text-orange-600 dark:text-orange-400' },
  RE: { label: '运行错误', cls: 'text-fuchsia-600 dark:text-fuchsia-400' },
  Running: { label: '判题中', cls: 'text-cyan-600 dark:text-cyan-400' },
  Pending: { label: '排队中', cls: 'text-slate-500 dark:text-slate-400' },
};
const getStatus = (s: string) =>
  statusInfo[s] ?? { label: s || '未知', cls: 'text-slate-500 dark:text-slate-400' };

const difficultyClass = (d: string) =>
  d === '简单'
    ? 'bg-emerald-50 text-emerald-600 dark:bg-emerald-900/30 dark:text-emerald-400'
    : d === '中等'
      ? 'bg-amber-50 text-amber-600 dark:bg-amber-900/30 dark:text-amber-400'
      : 'bg-rose-50 text-rose-600 dark:bg-rose-900/30 dark:text-rose-400';

const fmtTime = (d: Date | null) =>
  d ? d.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit', second: '2-digit' }) : '';

const saveStatusText = computed(() => {
  if (saveStatus.value === 'saving') return '正在保存…';
  if (saveStatus.value === 'saved') return lastSavedTime.value ? `已自动保存 ${fmtTime(lastSavedTime.value)}` : '已保存';
  if (saveStatus.value === 'error') return '保存失败，请检查网络';
  return '未修改';
});

/* ============ 生命周期 ============ */
onMounted(async () => {
  const [monacoMod, mdMod] = await Promise.all([
    import('../components/MonacoEditor.vue'),
    import('../components/MarkdownComponent.vue'),
  ]);
  MonacoEditorComp.value = monacoMod.default;
  MarkdownComp.value = mdMod.default;
  loadProblem();
  const saved = await loadCode(problemId.value, language.value);
  if (saved) code.value = saved;
  window.addEventListener('keydown', handleKeyboard);
  document.addEventListener('fullscreenchange', onFullscreenChange);
});
watch(problemId, () => {
  loadProblem();
  learningMarkdown.value = undefined;
  learningError.value = '';
  submitResult.value = null;
  testResults.value = [];
});
watch(activeTab, (t) => {
  if (t === 'hints') loadLearningMaterial();
  if (t === 'submissions') loadProblemSubmissions();
});
onUnmounted(() => {
  saveCode(problemId.value, language.value, code.value);
  window.removeEventListener('keydown', handleKeyboard);
  document.removeEventListener('fullscreenchange', onFullscreenChange);
  if (pollTimer.value) clearInterval(pollTimer.value);
  document.documentElement.classList.remove('focus-mode');
});
</script>

<template>
  <div
    class="editor-page"
    :class="{ 'editor-page--focus': isFocusMode, 'is-dragging': isDraggingLeft || isDraggingBottom }"
  >
    <!-- 顶栏 -->
    <header class="editor-topbar">
      <div class="topbar-left">
        <button class="icon-btn" title="返回题库" @click="router.push('/problems')">
          <Icon icon="material-symbols:arrow-back" class="h-5 w-5" />
        </button>
        <div class="problem-id">
          <span class="problem-no">#{{ problem?.sourceNumber ?? problem?.id }}</span>
          <span class="problem-name">{{ problem?.title || '加载中…' }}</span>
        </div>
        <button
          class="fav-mini"
          :class="isFavorited ? 'active' : ''"
          :title="isFavorited ? '取消收藏' : '收藏题目'"
          :disabled="favoriteBusy"
          @click.stop="toggleFavorite"
        >
          <Icon
            :icon="isFavorited ? 'material-symbols:star-rounded' : 'material-symbols:star-outline-rounded'"
            class="h-4 w-4"
            :class="isFavorited ? 'text-amber-400 drop-shadow-[0_0_5px_rgba(251,191,36,0.7)]' : ''"
          />
        </button>
      </div>

      <div v-if="!isFocusMode" class="topbar-center">
        <span class="save-chip" :class="`save-${saveStatus}`">
          <Icon
            :icon="saveStatus === 'saving' ? 'material-symbols:sync' : saveStatus === 'error' ? 'material-symbols:error-outline' : 'material-symbols:check-circle'"
            class="h-4 w-4"
            :class="saveStatus === 'saving' ? 'animate-spin' : ''"
          />
          {{ saveStatusText }}
        </span>
      </div>

      <div v-if="!isFocusMode" class="topbar-right">
        <span class="mode-chip">练习模式</span>
        <button class="icon-btn" title="编辑器设置" @click="settingsOpen = !settingsOpen">
          <Icon icon="material-symbols:settings" class="h-5 w-5" />
        </button>
        <button class="icon-btn" title="通知" @click="router.push('/announcements')">
          <Icon icon="material-symbols:notifications" class="h-5 w-5" />
        </button>
        <button class="icon-btn" :title="isDark ? '切换浅色' : '切换深色'" @click="themeStore.toggleTheme()">
          <Icon v-if="!isDark" icon="material-symbols:light-mode" class="h-5 w-5 text-amber-500" />
          <Icon v-else icon="material-symbols:dark-mode" class="h-5 w-5 text-cyan-300" />
        </button>
        <div class="user-wrap">
          <button class="user-avatar" @click="userMenuOpen = !userMenuOpen">
            {{ authStore.userInfo?.name?.[0]?.toUpperCase() || 'U' }}
          </button>
          <div v-if="userMenuOpen" class="user-dropdown">
            <button class="user-dropdown-item" @click="goUserPage('/submissions')">
              <Icon icon="material-symbols:history" class="h-4 w-4" />提交记录
            </button>
            <button class="user-dropdown-item" @click="goUserPage('/favorites')">
              <Icon icon="material-symbols:star" class="h-4 w-4" />收藏题目
            </button>
            <div class="user-dropdown-divider"></div>
            <button class="user-dropdown-item user-dropdown-logout" @click="handleLogout">
              <Icon icon="material-symbols:logout" class="h-4 w-4" />退出登录
            </button>
          </div>
        </div>
      </div>
      <button v-else class="icon-btn" title="退出专注模式" @click="isFocusMode = false">
        <Icon icon="material-symbols:fullscreen-exit" class="h-5 w-5" />
      </button>
    </header>

    <!-- 主体 -->
    <div ref="mainRef" class="editor-main">
      <!-- 左侧题目面板 -->
      <section class="problem-panel" :style="{ width: leftWidth + '%' }">
        <div class="problem-panel-tabs">
          <button :class="{ active: activeTab === 'desc' }" @click="activeTab = 'desc'">题目</button>
          <button :class="{ active: activeTab === 'submissions' }" @click="activeTab = 'submissions'">提交记录</button>
          <button :class="{ active: activeTab === 'hints' }" @click="activeTab = 'hints'">提示</button>
        </div>

        <div class="problem-scroll">
          <div v-if="isProblemLoading" class="state-box">
            <Icon icon="material-symbols:progress-activity" class="h-10 w-10 animate-spin text-[#2563EB]" />
            <p>正在加载题目…</p>
          </div>
          <div v-else-if="problemLoadError || !problem" class="state-box">
            <Icon icon="material-symbols:error-outline" class="h-10 w-10 text-slate-300 dark:text-slate-600" />
            <p>{{ problemLoadError || '题目不存在' }}</p>
            <button class="text-btn" @click="router.push('/problems')">返回题库</button>
          </div>

          <!-- 题目 -->
          <div v-else-if="activeTab === 'desc'">
            <div class="problem-info">
              <div class="problem-info-head">
                <span class="problem-no-lg">#{{ problem.sourceNumber ?? problem.id }}</span>
                <h1 class="problem-title">{{ problem.title }}</h1>
                <span class="diff-tag" :class="difficultyClass(problem.difficulty)">{{ problem.difficulty }}</span>
              </div>
              <div class="problem-meta">
                <span class="meta-item"><Icon icon="material-symbols:timer" class="h-4 w-4" />{{ problem.timeLimit }}ms</span>
                <span class="meta-item"><Icon icon="material-symbols:memory" class="h-4 w-4" />{{ problem.memoryLimit }}MB</span>
              </div>
              <div v-if="problem.tags?.length" class="problem-tags">
                <button v-for="tag in problem.tags" :key="tag" class="tag-pill" @click="goTag(tag)">{{ tag }}</button>
              </div>
              <div class="problem-stat">
                <span>本题提交 <b>{{ problemStats.submissions }}</b> 次</span>
                <span class="dot">·</span>
                <span>通过 <b>{{ problemStats.accepted }}</b> 次</span>
                <span v-if="problemStats.submissions" class="dot">·</span>
                <span v-if="problemStats.submissions">通过率 <b>{{ Math.round((problemStats.accepted / problemStats.submissions) * 100) }}%</b></span>
              </div>
            </div>

            <section class="md-section">
              <div class="md-head">题目描述</div>
              <div class="md-body markdown-body text-sm leading-7">
                <component v-if="MarkdownComp" :is="MarkdownComp" :content="descMarkdown" :show-nav="false" :show-heading-links="false" />
              </div>
            </section>

            <section class="md-section">
              <div class="md-head">输入格式</div>
              <p class="md-body whitespace-pre-line text-sm leading-7 text-slate-700 dark:text-slate-300">{{ problem.inputFormat || '无特别说明' }}</p>
            </section>

            <section class="md-section">
              <div class="md-head">输出格式</div>
              <p class="md-body whitespace-pre-line text-sm leading-7 text-slate-700 dark:text-slate-300">{{ problem.outputFormat || '无特别说明' }}</p>
            </section>

            <section class="md-section" v-if="problem.samples?.length">
              <div class="md-head">样例</div>
              <div class="sample-list space-y-4">
                <div v-for="(sample, i) in problem.samples" :key="i" class="sample-card">
                  <div class="sample-head">
                    <span>样例 #{{ i + 1 }}</span>
                    <button class="sample-run" @click="runThisSample(sample)">
                      <Icon icon="material-symbols:play-arrow" class="h-4 w-4" />运行此样例
                    </button>
                  </div>
                  <div class="sample-io-row">
                    <div class="sample-io">
                      <div class="sample-io-head">输入<button class="copy-btn" @click="copyText(sample.input)">复制</button></div>
                      <pre class="sample-io-body">{{ sample.input }}</pre>
                    </div>
                    <div class="sample-io-divider"></div>
                    <div class="sample-io">
                      <div class="sample-io-head">输出<button class="copy-btn" @click="copyText(sample.output)">复制</button></div>
                      <pre class="sample-io-body">{{ sample.output }}</pre>
                    </div>
                  </div>
                </div>
              </div>
            </section>

            <div v-if="problem.learningMaterial" class="tip-box">
              <Icon icon="material-symbols:lightbulb" class="h-4 w-4 text-amber-500" />
              切换到「提示」可查看本题学习资料，边看边写。
            </div>
          </div>

          <!-- 提交记录 -->
          <div v-else-if="activeTab === 'submissions'">
            <div v-if="!authStore.isAuthenticated" class="state-box">
              <p>登录后可查看本题提交记录</p>
              <button class="text-btn" @click="goLogin">去登录</button>
            </div>
            <div v-else-if="submissionsLoading" class="state-box">
              <Icon icon="material-symbols:progress-activity" class="h-8 w-8 animate-spin text-[#2563EB]" />
            </div>
            <div v-else-if="problemSubmissions.length === 0" class="state-box">
              <Icon icon="material-symbols:inbox" class="h-10 w-10 text-slate-300 dark:text-slate-600" />
              <p>还没有提交记录</p>
            </div>
            <div v-else class="sub-list">
              <div v-for="s in problemSubmissions" :key="s.id" class="sub-row">
                <span class="sub-status" :class="getStatus(s.status).cls">
                  <Icon :icon="s.status === 'AC' ? 'material-symbols:check-circle' : 'material-symbols:cancel'" class="h-4 w-4" />
                  {{ getStatus(s.status).label }}
                </span>
                <span class="sub-lang">{{ s.language }}</span>
                <span class="sub-time">{{ s.created_at ? new Date(s.created_at).toLocaleString('zh-CN') : '' }}</span>
              </div>
            </div>
          </div>

          <!-- 提示 -->
          <div v-else-if="activeTab === 'hints'">
            <div v-if="!problem?.learningMaterial" class="state-box">
              <Icon icon="material-symbols:lightbulb" class="h-10 w-10 text-slate-300 dark:text-slate-600" />
              <p>本题暂无额外提示</p>
            </div>
            <div v-else-if="isLearningLoading" class="state-box">
              <Icon icon="material-symbols:progress-activity" class="h-8 w-8 animate-spin text-[#2563EB]" />
            </div>
            <div v-else-if="learningError" class="state-box">
              <p class="text-rose-500">{{ learningError }}</p>
            </div>
            <div v-else-if="learningMarkdown" class="md-body markdown-body">
              <component v-if="MarkdownComp" :is="MarkdownComp" :content="learningMarkdown" :base-dir="learningBaseDir" :show-nav="false" :show-heading-links="false" />
            </div>
          </div>
        </div>
      </section>

      <!-- 竖向拖拽分割 -->
      <div
        class="v-resizer"
        :class="{ active: isDraggingLeft }"
        title="拖拽调整题目区宽度，双击恢复"
        @mousedown.prevent="startLeftDrag"
        @dblclick="leftWidth = 30"
      >
        <span class="resizer-grip"></span>
      </div>

      <!-- 右侧编辑 + 结果 -->
      <section class="editor-column">
        <!-- 工具栏 -->
        <div class="editor-toolbar">
          <div class="toolbar-left">
            <div class="lang-select">
              <button class="lang-trigger" @click.stop="langMenuOpen = !langMenuOpen">
                <span>{{ langOptions.find((l) => l.value === language)?.label }}</span>
                <Icon icon="material-symbols:expand-more" class="h-4 w-4" />
              </button>
              <div v-if="langMenuOpen" class="lang-menu">
                <button
                  v-for="opt in langOptions"
                  :key="opt.value"
                  class="lang-item"
                  :class="{ active: opt.value === language }"
                  @click="updateLanguage(opt.value)"
                >
                  {{ opt.label }}
                  <Icon v-if="opt.value === language" icon="material-symbols:check" class="h-4 w-4" />
                </button>
              </div>
            </div>
            <div class="file-name">
              <span>{{ currentFilename }}</span>
              <span v-if="saveStatus === 'saving'" class="unsaved-dot" title="有未保存修改"></span>
            </div>
          </div>

          <div class="toolbar-right">
            <button class="tool-btn" title="格式化代码 (Ctrl+Shift+F)" @click="formatCode">
              <Icon icon="material-symbols:format-align-left" class="h-4 w-4" />格式化
            </button>
            <button class="tool-btn tool-danger" title="恢复初始代码" @click="resetCode">
              <Icon icon="material-symbols:restart-alt" class="h-4 w-4" />恢复
            </button>
            <button class="tool-btn" :title="isFocusMode ? '退出专注模式' : '专注模式'" @click="isFocusMode = !isFocusMode">
              <Icon :icon="isFocusMode ? 'material-symbols:fullscreen-exit' : 'material-symbols:fullscreen'" class="h-4 w-4" />
            </button>
          </div>
        </div>

        <!-- 编辑器 -->
        <div class="editor-body">
          <component
            v-if="MonacoEditorComp"
            :is="MonacoEditorComp"
            v-model="code"
            :language="editorLanguageMap[language] || 'cpp'"
            :is-dark="effectiveDark"
            height="100%"
            @ready="onEditorReady"
          />
          <div v-else class="flex h-full items-center justify-center text-sm text-[#94A3B8]">正在加载编辑器…</div>
        </div>

        <!-- 底部结果区 -->
        <div class="result-panel" :class="{ collapsed: !resultVisible }" :style="{ height: resultVisible ? bottomHeight + 'px' : 'auto' }">
          <div class="result-tabs">
            <button :class="{ active: activeResultTab === 'testcases' }" @click="activeResultTab = 'testcases'">测试用例</button>
            <button :class="{ active: activeResultTab === 'run' }" @click="activeResultTab = 'run'">运行结果</button>
            <button :class="{ active: activeResultTab === 'submit' }" @click="activeResultTab = 'submit'">提交结果</button>
            <button class="result-collapse" :title="resultVisible ? '收起' : '展开'" @click="resultVisible = !resultVisible">
              <Icon :icon="resultVisible ? 'material-symbols:expand-more' : 'material-symbols:expand-less'" class="h-5 w-5" />
            </button>
          </div>

          <div v-if="resultVisible" class="result-content">
            <!-- 测试用例 -->
            <div v-show="activeResultTab === 'testcases'" class="result-pane">
              <div class="io-grid">
                <div class="io-block">
                  <div class="io-head">输入数据<button class="copy-btn" @click="stdin = ''">清空</button></div>
                  <textarea v-model="stdin" class="io-textarea" placeholder="在此填写自定义测试输入…"></textarea>
                </div>
                <div class="io-block">
                  <div class="io-head">预期输出（选填）</div>
                  <textarea v-model="expectedOutput" class="io-textarea" placeholder="填写后自动对比实际输出"></textarea>
                </div>
              </div>
              <div class="io-output">
                <div class="io-head">
                  运行输出
                  <span v-if="selfTestVerdict" class="verdict" :class="selfTestVerdict">{{ selfTestVerdict === 'pass' ? '✓ PASS' : '✗ FAILED' }}</span>
                </div>
                <pre v-if="selfTestOutput" class="io-pre" :class="{ err: selfTestVerdict === 'fail' }">{{ selfTestOutput }}</pre>
                <div v-else class="io-placeholder">运行结果和报错都会显示在这里。</div>
                <div v-if="selfTestStatus" class="io-status" :class="selfTestVerdict === 'pass' ? 'ok' : selfTestVerdict === 'fail' ? 'bad' : ''">{{ selfTestStatus }}</div>
              </div>
            </div>

            <!-- 运行结果 -->
            <div v-show="activeResultTab === 'run'" class="result-pane">
              <div v-if="!selfTestOutput && !selfTestStatus" class="state-box">
                <Icon icon="material-symbols:terminal" class="h-9 w-9 text-slate-300 dark:text-slate-600" />
                <p>点击「运行代码」查看输出</p>
              </div>
              <div v-else class="result-pane-scroll">
                <div class="io-head">
                  标准输出
                  <span v-if="selfTestVerdict" class="verdict" :class="selfTestVerdict">{{ selfTestVerdict === 'pass' ? '✓ PASS' : '✗ FAILED' }}</span>
                  <button v-if="selfTestOutput" class="copy-btn" @click="copyText(selfTestOutput)">复制</button>
                </div>
                <pre class="io-pre" :class="{ err: selfTestVerdict === 'fail' }">{{ selfTestOutput }}</pre>
                <div v-if="selfTestStatus" class="io-status" :class="selfTestVerdict === 'pass' ? 'ok' : selfTestVerdict === 'fail' ? 'bad' : ''">{{ selfTestStatus }}</div>
              </div>
            </div>

            <!-- 提交结果 -->
            <div v-show="activeResultTab === 'submit'" class="result-pane">
              <div v-if="judgePhase === 'idle' && !submitResult" class="state-box">
                <Icon icon="material-symbols:gpp-maybe" class="h-9 w-9 text-slate-300 dark:text-slate-600" />
                <p>提交后在此查看判题结果</p>
              </div>
              <div v-else class="result-pane-scroll">
                <div class="judge-banner" :class="submitResult ? getStatus(submitResult).cls : ''">
                  <template v-if="judgePhase === 'received'">已接收，等待评测…</template>
                  <template v-else-if="judgePhase === 'judging'">
                    <Icon icon="material-symbols:progress-activity" class="h-4 w-4 animate-spin" />评测中…
                  </template>
                  <template v-else>
                    <Icon :icon="submitResult === 'AC' ? 'material-symbols:check-circle' : 'material-symbols:cancel'" class="h-5 w-5" />
                    {{ submitResult === 'AC' ? 'Accepted · 全部通过' : submitResult === 'CE' ? 'Compile Error · 编译错误' : 'Wrong Answer · 答案错误' }}
                  </template>
                </div>

                <div v-if="submitResult === 'CE'" class="ce-box">
                  <div class="io-head">编译错误（点击文件名/行号定位）</div>
                  <pre class="io-pre err"><template v-for="(part, i) in parseErrorParts(compileErrorMsg)" :key="i"><span v-if="part.line" class="err-link" @click="gotoLine(part.line)">{{ part.text }}</span><template v-else>{{ part.text }}</template></template></pre>
                </div>

                <div v-else-if="submitResult && testResults.length" class="submit-detail">
                  <div class="test-summary" :class="submitResult === 'AC' ? 'ok' : 'bad'">
                    已通过 {{ passedCount }} / {{ testResults.length }} 个测试点
                  </div>
                  <div class="test-point-list">
                    <button
                      v-for="(tr, i) in testResults"
                      :key="i"
                      class="test-point"
                      :class="{ active: currentResultPage === i, pass: tr.passed, fail: !tr.passed }"
                      @click="currentResultPage = i"
                    >
                      <Icon :icon="tr.passed ? 'material-symbols:check-circle' : 'material-symbols:cancel'" class="h-4 w-4" />
                      #{{ i + 1 }}
                    </button>
                  </div>
                  <div class="test-detail">
                    <div class="io-block">
                      <div class="io-head">输入</div>
                      <pre class="io-pre">{{ testResults[currentResultPage]?.input || '(已隐藏)' }}</pre>
                    </div>
                    <div class="io-block">
                      <div class="io-head">期望输出</div>
                      <pre class="io-pre">{{ testResults[currentResultPage]?.expected || '(已隐藏)' }}</pre>
                    </div>
                    <div class="io-block">
                      <div class="io-head">实际输出<span class="verdict" :class="testResults[currentResultPage]?.passed ? 'pass' : 'fail'">{{ testResults[currentResultPage]?.passed ? '✓ PASS' : '✗ FAILED' }}</span></div>
                      <pre class="io-pre" :class="{ err: !testResults[currentResultPage]?.passed }">{{ testResults[currentResultPage]?.actualOutput }}</pre>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- 横向拖拽分割 -->
          <div
            v-if="resultVisible"
            class="h-resizer"
            :class="{ active: isDraggingBottom }"
            title="拖拽调整结果区高度"
            @mousedown.prevent="startBottomDrag"
          ></div>
        </div>
      </section>
    </div>

    <!-- 底部操作栏 -->
    <footer class="action-bar">
      <div class="action-left">
        <span class="save-chip" :class="`save-${saveStatus}`">
          <Icon
            :icon="saveStatus === 'saving' ? 'material-symbols:sync' : saveStatus === 'error' ? 'material-symbols:error-outline' : 'material-symbols:check-circle'"
            class="h-4 w-4"
            :class="saveStatus === 'saving' ? 'animate-spin' : ''"
          />
          {{ saveStatusText }}
        </span>
      </div>
      <div class="action-center">
        <button v-if="!isFocusMode" class="action-settings" @click="settingsOpen = !settingsOpen">
          <Icon icon="material-symbols:tune" class="h-4 w-4" />编辑器设置
        </button>
      </div>
      <div class="action-right">
        <button class="btn-run" :disabled="isSelfTesting" @click="runSelfTest">
          <Icon :icon="isSelfTesting ? 'material-symbols:hourglass-top' : 'material-symbols:play-arrow'" class="h-4 w-4" :class="{ 'animate-spin': isSelfTesting }" />
          运行代码 <kbd>Ctrl+Enter</kbd>
        </button>
        <button class="btn-submit" :disabled="isSubmitting" @click="submitCode">
          <Icon v-if="isSubmitting" icon="material-symbols:hourglass-top" class="h-4 w-4 animate-spin" />
          {{ isSubmitting ? '正在评测…' : '提交代码' }} <kbd>Ctrl+Shift+Enter</kbd>
        </button>
      </div>
    </footer>

    <!-- 编辑器设置 Popover -->
    <div v-if="settingsOpen" class="settings-backdrop" @click="settingsOpen = false"></div>
    <div v-if="settingsOpen" class="settings-popover">
      <div class="settings-title">编辑器设置</div>
      <div class="settings-row">
        <span>字体大小</span>
        <div class="seg">
          <button v-for="s in [12, 14, 16, 18]" :key="s" :class="{ active: editorSettings.fontSize === s }" @click="editorSettings.fontSize = s">{{ s }}</button>
        </div>
      </div>
      <div class="settings-row">
        <span>Tab 宽度</span>
        <div class="seg">
          <button v-for="t in [2, 4, 8]" :key="t" :class="{ active: editorSettings.tabSize === t }" @click="editorSettings.tabSize = t">{{ t }}</button>
        </div>
      </div>
      <div class="settings-row">
        <span>自动换行</span>
        <button class="switch" :class="{ on: editorSettings.wordWrap === 'on' }" @click="editorSettings.wordWrap = editorSettings.wordWrap === 'on' ? 'off' : 'on'">{{ editorSettings.wordWrap === 'on' ? '开' : '关' }}</button>
      </div>
      <div class="settings-row">
        <span>小地图</span>
        <button class="switch" :class="{ on: editorSettings.minimap }" @click="editorSettings.minimap = !editorSettings.minimap">{{ editorSettings.minimap ? '开' : '关' }}</button>
      </div>
      <div class="settings-row">
        <span>主题</span>
        <div class="seg">
          <button v-for="t in (['auto', 'light', 'dark'] as const)" :key="t" :class="{ active: editorSettings.theme === t }" @click="editorSettings.theme = t">{{ t === 'auto' ? '跟随' : t === 'light' ? '浅色' : '深色' }}</button>
        </div>
      </div>
      <div class="settings-hint">
        <p>快捷键</p>
        <p>Ctrl/⌘+Enter 运行 · Ctrl/⌘+Shift+Enter 提交</p>
        <p>Ctrl/⌘+S 保存 · Ctrl/⌘+Shift+F 格式化</p>
      </div>
    </div>

    <!-- 菜单背景遮罩 -->
    <div v-if="langMenuOpen || userMenuOpen" class="menu-backdrop" @click="langMenuOpen = false; userMenuOpen = false"></div>
  </div>
</template>

<style scoped>
@reference 'tailwindcss';

.editor-page {
  display: flex;
  flex-direction: column;
  height: calc(100dvh - var(--header-h, 5rem));
  min-height: 0;
  background: #f6f8fc;
  color: #1e293b;
  overflow: hidden;
}
:global(.dark) .editor-page {
  background: #0b1120;
  color: #e2e8f0;
}
.editor-page--focus,
:fullscreen .editor-page {
  position: fixed;
  inset: 0;
  z-index: 60;
  height: 100dvh;
}
.editor-page.is-dragging {
  cursor: col-resize;
  user-select: none;
}

/* 顶栏 */
.editor-topbar {
  display: flex;
  align-items: center;
  gap: 1rem;
  height: 60px;
  flex-shrink: 0;
  padding: 0 1rem;
  background: #ffffff;
  border-bottom: 1px solid #e2e8f0;
}
:global(.dark) .editor-topbar {
  background: #0f172a;
  border-color: #1e293b;
}
.topbar-left {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  min-width: 0;
  flex: 1;
}
.topbar-center {
  flex-shrink: 0;
}
.topbar-right {
  display: flex;
  align-items: center;
  gap: 0.25rem;
  flex-shrink: 0;
}
.problem-id {
  display: flex;
  align-items: baseline;
  gap: 0.5rem;
  min-width: 0;
}
.problem-no {
  color: #64748b;
  font-size: 0.8rem;
  font-weight: 700;
  flex-shrink: 0;
}
.problem-name {
  font-weight: 800;
  font-size: 1rem;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  color: #1e293b;
}
:global(.dark) .problem-name {
  color: #e2e8f0;
}
.icon-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 2.25rem;
  height: 2.25rem;
  border-radius: 0.625rem;
  color: #475569;
  transition: background 0.15s, color 0.15s;
}
.icon-btn:hover {
  background: #f1f5f9;
  color: #1e293b;
}
:global(.dark) .icon-btn {
  color: #94a3b8;
}
:global(.dark) .icon-btn:hover {
  background: #1e293b;
  color: #e2e8f0;
}
.fav-mini {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 2rem;
  height: 2rem;
  border-radius: 0.625rem;
  color: #94a3b8;
  transition: background 0.15s, color 0.15s;
}
.fav-mini:hover {
  background: #f1f5f9;
}
.fav-mini.active {
  color: #f59e0b;
}
.mode-chip {
  font-size: 0.75rem;
  font-weight: 700;
  color: #64748b;
  background: #f1f5f9;
  border-radius: 999px;
  padding: 0.25rem 0.75rem;
}
:global(.dark) .mode-chip {
  background: #1e293b;
  color: #94a3b8;
}
.save-chip {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  font-size: 0.8rem;
  font-weight: 600;
  color: #64748b;
}
.save-chip.save-saving {
  color: #2563eb;
}
.save-chip.save-error {
  color: #ef4444;
}
.save-chip.save-saved {
  color: #10b981;
}

/* 用户菜单 */
.user-wrap {
  position: relative;
}
.user-avatar {
  width: 2.25rem;
  height: 2.25rem;
  border-radius: 999px;
  background: #2563eb;
  color: #fff;
  font-weight: 800;
  font-size: 0.9rem;
}
.user-dropdown {
  position: absolute;
  right: 0;
  top: calc(100% + 0.5rem);
  z-index: 70;
  display: grid;
  min-width: 12rem;
  gap: 0.2rem;
  border: 1px solid #e2e8f0;
  border-radius: 1rem;
  background: #fff;
  padding: 0.4rem;
  box-shadow: 0 18px 40px rgba(15, 23, 42, 0.16);
}
:global(.dark) .user-dropdown {
  background: #0f172a;
  border-color: #1e293b;
  box-shadow: 0 18px 40px rgba(0, 0, 0, 0.5);
}
.user-dropdown-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  width: 100%;
  padding: 0.55rem 0.75rem;
  border-radius: 0.75rem;
  text-align: left;
  font-size: 0.85rem;
  font-weight: 700;
  color: #334155;
  transition: background 0.15s, color 0.15s;
}
.user-dropdown-item:hover {
  background: #e0f2fe;
  color: #0e7490;
}
:global(.dark) .user-dropdown-item {
  color: #e2e8f0;
}
:global(.dark) .user-dropdown-item:hover {
  background: #082f49;
  color: #67e8f9;
}
.user-dropdown-divider {
  height: 1px;
  margin: 0.1rem 0.5rem;
  background: #e2e8f0;
}
:global(.dark) .user-dropdown-divider {
  background: #1e293b;
}
.user-dropdown-logout:hover {
  background: #fee2e2 !important;
  color: #b91c1c !important;
}
:global(.dark) .user-dropdown-logout:hover {
  background: #450a0a !important;
  color: #fca5a5 !important;
}

/* 主体 */
.editor-main {
  display: flex;
  flex: 1;
  min-height: 0;
}
.problem-panel {
  display: flex;
  flex-direction: column;
  min-width: 0;
  background: #fff;
  border-right: 1px solid #e2e8f0;
}
:global(.dark) .problem-panel {
  background: #0f172a;
  border-color: #1e293b;
}
.problem-panel-tabs {
  display: flex;
  gap: 0.25rem;
  padding: 0.5rem 0.75rem;
  border-bottom: 1px solid #e2e8f0;
  flex-shrink: 0;
}
:global(.dark) .problem-panel-tabs {
  border-color: #1e293b;
}
.problem-panel-tabs button {
  padding: 0.4rem 0.9rem;
  border-radius: 0.625rem;
  font-size: 0.85rem;
  font-weight: 700;
  color: #64748b;
  transition: background 0.15s, color 0.15s;
}
.problem-panel-tabs button:hover {
  background: #f1f5f9;
}
.problem-panel-tabs button.active {
  background: #eff6ff;
  color: #2563eb;
}
:global(.dark) .problem-panel-tabs button {
  color: #94a3b8;
}
:global(.dark) .problem-panel-tabs button:hover {
  background: #1e293b;
}
:global(.dark) .problem-panel-tabs button.active {
  background: #1e3a8a;
  color: #bfdbfe;
}
.problem-scroll {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  padding: 1.25rem;
}

/* 题目信息 */
.problem-info {
  margin-bottom: 1.25rem;
}
.problem-info-head {
  display: flex;
  align-items: center;
  gap: 0.6rem;
  flex-wrap: wrap;
}
.problem-no-lg {
  color: #94a3b8;
  font-weight: 700;
  font-size: 0.95rem;
}
:global(.dark) .problem-no-lg {
  color: #64748b;
}
.problem-title {
  font-size: 1.4rem;
  font-weight: 800;
  line-height: 1.3;
  color: #1e293b;
}
:global(.dark) .problem-title {
  color: #e2e8f0;
}
.diff-tag {
  margin-left: auto;
  font-size: 0.75rem;
  font-weight: 700;
  border-radius: 999px;
  padding: 0.2rem 0.7rem;
}
.problem-meta {
  display: flex;
  gap: 1rem;
  margin-top: 0.6rem;
}
.meta-item {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  font-size: 0.85rem;
  font-weight: 600;
  color: #64748b;
}
:global(.dark) .meta-item {
  color: #94a3b8;
}
.problem-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 0.4rem;
  margin-top: 0.7rem;
}
.tag-pill {
  font-size: 0.75rem;
  font-weight: 700;
  color: #475569;
  background: #f1f5f9;
  border-radius: 999px;
  padding: 0.2rem 0.7rem;
  transition: background 0.15s, color 0.15s;
}
.tag-pill:hover {
  background: #e0f2fe;
  color: #0e7490;
}
:global(.dark) .tag-pill {
  background: #1e293b;
  color: #cbd5e1;
}
.problem-stat {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.4rem;
  margin-top: 0.7rem;
  font-size: 0.78rem;
  color: #64748b;
}
:global(.dark) .problem-stat {
  color: #94a3b8;
}
.problem-stat b {
  color: #1e293b;
}
:global(.dark) .problem-stat b {
  color: #e2e8f0;
}
.problem-stat .dot {
  color: #cbd5e1;
}

/* markdown 区块 */
.md-section {
  margin-bottom: 1.25rem;
}
.md-head {
  font-size: 1rem;
  font-weight: 800;
  color: #1e293b;
  padding-left: 0.6rem;
  border-left: 3px solid #2563eb;
  margin-bottom: 0.6rem;
}
:global(.dark) .md-head {
  color: #e2e8f0;
}
.md-body {
  color: #334155;
}
:global(.dark) .md-body {
  color: #cbd5e1;
}

/* 样例 */
.sample-card {
  border: 1px solid #e2e8f0;
  border-radius: 0.75rem;
  overflow: hidden;
}
:global(.dark) .sample-card {
  border-color: #1e293b;
}
.sample-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.5rem 0.75rem;
  font-size: 0.8rem;
  font-weight: 700;
  color: #475569;
  background: #f8fafc;
  border-bottom: 1px solid #e2e8f0;
}
:global(.dark) .sample-head {
  background: #1e293b;
  color: #cbd5e1;
  border-color: #1e293b;
}
.sample-run {
  display: inline-flex;
  align-items: center;
  gap: 0.25rem;
  font-size: 0.78rem;
  font-weight: 700;
  color: #2563eb;
  padding: 0.2rem 0.6rem;
  border-radius: 0.5rem;
  transition: background 0.15s;
}
.sample-run:hover {
  background: #eff6ff;
}
:global(.dark) .sample-run {
  color: #60a5fa;
}
:global(.dark) .sample-run:hover {
  background: #172554;
}
.sample-io-row {
  display: flex;
  min-height: 6rem;
}
.sample-io-row .sample-io {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
}
.sample-io-row .sample-io-body {
  flex: 1;
}
.sample-io-divider {
  width: 1px;
  background: #e2e8f0;
  align-self: stretch;
}
:global(.dark) .sample-io-divider {
  background: #1e293b;
}
@media (max-width: 480px) {
  .sample-io-row {
    flex-direction: column;
    min-height: auto;
  }
  .sample-io-divider {
    width: 100%;
    height: 1px;
  }
}
.sample-io {
  display: flex;
  flex-direction: column;
  min-width: 0;
}
.sample-io-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.35rem 0.6rem;
  font-size: 0.72rem;
  font-weight: 800;
  color: #64748b;
  background: #f1f5f9;
}
:global(.dark) .sample-io-head {
  background: #1e293b;
  color: #94a3b8;
}
.sample-io-body,
.io-pre {
  margin: 0;
  padding: 0.6rem;
  font-family: ui-monospace, SFMono-Regular, 'SF Mono', Menlo, Consolas, monospace;
  font-size: 0.8rem;
  line-height: 1.6;
  white-space: pre-wrap;
  word-break: break-word;
  background: #f1f5f9;
  color: #334155;
  overflow: auto;
}
:global(.dark) .sample-io-body,
:global(.dark) .io-pre {
  background: #0f172a;
  color: #6ee7b7;
}
.sample-io-body.err,
.io-pre.err {
  color: #dc2626;
}
:global(.dark) .sample-io-body.err,
:global(.dark) .io-pre.err {
  color: #fca5a5;
}
.copy-btn {
  font-size: 0.7rem;
  font-weight: 700;
  color: #64748b;
  padding: 0.1rem 0.45rem;
  border-radius: 0.35rem;
  transition: background 0.15s;
}
.copy-btn:hover {
  background: #e2e8f0;
}
:global(.dark) .copy-btn {
  color: #94a3b8;
}
:global(.dark) .copy-btn:hover {
  background: #334155;
}
.tip-box {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.75rem;
  border-radius: 0.75rem;
  background: #fffbeb;
  color: #92400e;
  font-size: 0.85rem;
  font-weight: 600;
}
:global(.dark) .tip-box {
  background: #422006;
  color: #fcd34d;
}

/* 状态盒 */
.state-box {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  padding: 3rem 1rem;
  color: #64748b;
  text-align: center;
  font-size: 0.9rem;
}
:global(.dark) .state-box {
  color: #94a3b8;
}
.text-btn {
  margin-top: 0.5rem;
  color: #2563eb;
  font-weight: 700;
}
:global(.dark) .text-btn {
  color: #60a5fa;
}

/* 提交记录 */
.sub-list {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}
.sub-row {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.6rem 0.75rem;
  border: 1px solid #e2e8f0;
  border-radius: 0.75rem;
  font-size: 0.85rem;
}
:global(.dark) .sub-row {
  border-color: #1e293b;
  background: #0f172a;
}
.sub-status {
  display: inline-flex;
  align-items: center;
  gap: 0.3rem;
  font-weight: 700;
}
.sub-lang {
  color: #64748b;
  font-weight: 600;
}
:global(.dark) .sub-lang {
  color: #94a3b8;
}
.sub-time {
  margin-left: auto;
  color: #94a3b8;
  font-size: 0.78rem;
}

/* 分割线 */
.v-resizer {
  width: 6px;
  flex-shrink: 0;
  cursor: col-resize;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #e2e8f0;
  transition: background 0.15s;
}
.v-resizer:hover,
.v-resizer.active {
  background: #2563eb;
}
.resizer-grip {
  width: 2px;
  height: 2rem;
  border-radius: 2px;
  background: #94a3b8;
}
:global(.dark) .v-resizer {
  background: #1e293b;
}
:global(.dark) .v-resizer:hover,
:global(.dark) .v-resizer.active {
  background: #2563eb;
}
.editor-page.is-dragging .v-resizer.active {
  cursor: col-resize;
}

/* 右侧列 */
.editor-column {
  display: flex;
  flex-direction: column;
  flex: 1;
  min-width: 0;
}
.editor-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.5rem;
  height: 52px;
  flex-shrink: 0;
  padding: 0 0.75rem;
  background: #fff;
  border-bottom: 1px solid #e2e8f0;
}
:global(.dark) .editor-toolbar {
  background: #0f172a;
  border-color: #1e293b;
}
.toolbar-left,
.toolbar-right {
  display: flex;
  align-items: center;
  gap: 0.4rem;
}
.lang-select {
  position: relative;
}
.lang-trigger {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  height: 2.1rem;
  padding: 0 0.75rem;
  border: 1px solid #e2e8f0;
  border-radius: 0.625rem;
  font-size: 0.85rem;
  font-weight: 700;
  color: #1e293b;
  background: #fff;
}
.lang-trigger:hover {
  border-color: #2563eb;
}
:global(.dark) .lang-trigger {
  background: #1e293b;
  border-color: #334155;
  color: #e2e8f0;
}
.lang-menu {
  position: absolute;
  top: calc(100% + 0.4rem);
  left: 0;
  z-index: 70;
  min-width: 9rem;
  border: 1px solid #e2e8f0;
  border-radius: 0.75rem;
  background: #fff;
  padding: 0.3rem;
  box-shadow: 0 18px 40px rgba(15, 23, 42, 0.16);
}
:global(.dark) .lang-menu {
  background: #0f172a;
  border-color: #1e293b;
}
.lang-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
  padding: 0.5rem 0.75rem;
  border-radius: 0.5rem;
  font-size: 0.85rem;
  font-weight: 700;
  color: #334155;
  transition: background 0.15s;
}
.lang-item:hover {
  background: #f1f5f9;
}
.lang-item.active {
  color: #2563eb;
}
.file-name {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  font-size: 0.8rem;
  font-weight: 600;
  color: #64748b;
}
.unsaved-dot {
  width: 0.5rem;
  height: 0.5rem;
  border-radius: 999px;
  background: #f59e0b;
}
.tool-btn {
  display: inline-flex;
  align-items: center;
  gap: 0.3rem;
  height: 2.1rem;
  padding: 0 0.7rem;
  border: 1px solid #e2e8f0;
  border-radius: 0.625rem;
  font-size: 0.8rem;
  font-weight: 700;
  color: #475569;
  background: #fff;
  transition: all 0.15s;
}
.tool-btn:hover {
  border-color: #2563eb;
  color: #2563eb;
}
.tool-danger:hover {
  border-color: #ef4444;
  color: #ef4444;
}
:global(.dark) .tool-btn {
  background: #1e293b;
  border-color: #334155;
  color: #cbd5e1;
}

/* 编辑器 */
.editor-body {
  flex: 1;
  min-height: 0;
  background: #ffffff;
}
:global(.dark) .editor-body {
  background: #1e1e1e;
}

/* 结果区 */
.result-panel {
  display: flex;
  flex-direction: column;
  flex-shrink: 0;
  background: #fff;
  border-top: 1px solid #e2e8f0;
  min-height: 0;
}
:global(.dark) .result-panel {
  background: #0f172a;
  border-color: #1e293b;
}
.result-panel.collapsed {
  border-top: 1px solid #e2e8f0;
}
.result-tabs {
  display: flex;
  align-items: center;
  gap: 0.25rem;
  padding: 0 0.5rem;
  height: 44px;
  flex-shrink: 0;
  border-bottom: 1px solid #e2e8f0;
}
:global(.dark) .result-tabs {
  border-color: #1e293b;
}
.result-tabs button {
  padding: 0.35rem 0.85rem;
  border-radius: 0.5rem;
  font-size: 0.82rem;
  font-weight: 700;
  color: #64748b;
  transition: background 0.15s, color 0.15s;
}
.result-tabs button:hover {
  background: #f1f5f9;
}
.result-tabs button.active {
  background: #eff6ff;
  color: #2563eb;
}
:global(.dark) .result-tabs button.active {
  background: #1e3a8a;
  color: #bfdbfe;
}
.result-collapse {
  margin-left: auto;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 2rem;
  height: 2rem;
  border-radius: 0.5rem;
  color: #64748b;
}
.result-collapse:hover {
  background: #f1f5f9;
}
.result-content {
  flex: 1;
  min-height: 0;
  overflow: hidden;
}
.result-pane {
  height: 100%;
  overflow-y: auto;
  padding: 0.75rem;
}
.result-pane-scroll {
  height: 100%;
  overflow-y: auto;
}
.io-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  grid-template-rows: 1fr;
  gap: 0.75rem;
  align-items: stretch;
}
@media (max-width: 640px) {
  .io-grid {
    grid-template-columns: 1fr;
  }
}
.io-block {
  display: flex;
  flex-direction: column;
  min-width: 0;
}
.io-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.5rem;
  padding: 0.35rem 0.6rem;
  font-size: 0.75rem;
  font-weight: 800;
  color: #475569;
  background: #f1f5f9;
  border-radius: 0.5rem 0.5rem 0 0;
}
:global(.dark) .io-head {
  background: #1e293b;
  color: #cbd5e1;
}
.io-textarea {
  width: 100%;
  min-height: 120px;
  height: 100%;
  flex: 1;
  resize: vertical;
  border: 1px solid #e2e8f0;
  border-top: none;
  border-radius: 0 0 0.5rem 0.5rem;
  padding: 0.6rem;
  font-family: ui-monospace, SFMono-Regular, 'SF Mono', Menlo, Consolas, monospace;
  font-size: 0.8rem;
  line-height: 1.6;
  background: #fff;
  color: #1e293b;
  outline: none;
  box-sizing: border-box;
}
.io-textarea:focus {
  border-color: #2563eb;
}
:global(.dark) .io-textarea {
  background: #1e293b;
  border-color: #334155;
  color: #e2e8f0;
}
.io-output {
  margin-top: 0.75rem;
}
.io-placeholder {
  padding: 1rem;
  text-align: center;
  color: #94a3b8;
  font-size: 0.85rem;
}
.io-status {
  padding: 0.4rem 0.6rem;
  font-size: 0.8rem;
  font-weight: 700;
  background: #f1f5f9;
  color: #475569;
}
:global(.dark) .io-status {
  background: #1e293b;
  color: #cbd5e1;
}
.io-status.ok {
  background: #ecfdf5;
  color: #059669;
}
:global(.dark) .io-status.ok {
  background: #064e3b;
  color: #34d399;
}
.io-status.bad {
  background: #fef2f2;
  color: #dc2626;
}
:global(.dark) .io-status.bad {
  background: #450a0a;
  color: #fca5a5;
}
.verdict {
  font-size: 0.7rem;
  font-weight: 900;
  letter-spacing: 0.05em;
  padding: 0.1rem 0.5rem;
  border-radius: 999px;
}
.verdict.pass {
  color: #10b981;
  background: rgba(16, 185, 129, 0.15);
}
.verdict.fail {
  color: #ef4444;
  background: rgba(239, 68, 68, 0.15);
}
.io-pre {
  margin: 0;
  padding: 0.6rem;
  background: #f1f5f9;
  color: #334155;
  border-radius: 0 0 0.5rem 0.5rem;
  max-height: 14rem;
  overflow: auto;
}
:global(.dark) .io-pre {
  background: #0f172a;
  color: #6ee7b7;
}
.io-pre.err {
  color: #dc2626;
}
:global(.dark) .io-pre.err {
  color: #fca5a5;
}
.err-link {
  color: #fca5a5;
  cursor: pointer;
  text-decoration: underline dotted;
}
.err-link:hover {
  color: #f87171;
}

/* 提交结果 */
.judge-banner {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.6rem 0.85rem;
  border-radius: 0.75rem;
  font-size: 0.9rem;
  font-weight: 800;
  margin-bottom: 0.75rem;
  background: #f1f5f9;
  color: #64748b;
}
.judge-banner.text-emerald-600,
.judge-banner :deep(.text-emerald-600) {
  background: #ecfdf5;
  color: #059669;
}
.judge-banner.text-rose-600 {
  background: #fef2f2;
  color: #dc2626;
}
.ce-box {
  border: 1px solid #fecaca;
  border-radius: 0.75rem;
  overflow: hidden;
}
:global(.dark) .ce-box {
  border-color: #7f1d1d;
}
.test-summary {
  padding: 0.5rem 0.75rem;
  border-radius: 0.75rem;
  font-weight: 800;
  margin-bottom: 0.6rem;
}
.test-summary.ok {
  background: #ecfdf5;
  color: #059669;
}
.test-summary.bad {
  background: #fef2f2;
  color: #dc2626;
}
.test-point-list {
  display: flex;
  flex-wrap: wrap;
  gap: 0.4rem;
  margin-bottom: 0.75rem;
}
.test-point {
  display: inline-flex;
  align-items: center;
  gap: 0.25rem;
  padding: 0.35rem 0.6rem;
  border-radius: 0.5rem;
  font-size: 0.78rem;
  font-weight: 700;
  border: 1px solid #e2e8f0;
  color: #64748b;
  transition: all 0.15s;
}
.test-point.pass {
  color: #10b981;
}
.test-point.fail {
  color: #ef4444;
}
.test-point.active {
  border-color: #2563eb;
  background: #eff6ff;
}
.test-detail {
  display: grid;
  gap: 0.6rem;
}
.test-detail .io-block .io-pre {
  max-height: 10rem;
}

/* 横向分割 */
.h-resizer {
  height: 6px;
  flex-shrink: 0;
  cursor: row-resize;
  background: #e2e8f0;
  transition: background 0.15s;
}
.h-resizer:hover,
.h-resizer.active {
  background: #2563eb;
}
:global(.dark) .h-resizer {
  background: #1e293b;
}
:global(.dark) .h-resizer:hover,
:global(.dark) .h-resizer.active {
  background: #2563eb;
}

/* 底部操作栏 */
.action-bar {
  display: flex;
  align-items: center;
  gap: 1rem;
  height: 56px;
  flex-shrink: 0;
  padding: 0 1rem;
  background: #fff;
  border-top: 1px solid #e2e8f0;
}
:global(.dark) .action-bar {
  background: #0f172a;
  border-color: #1e293b;
}
.action-left {
  flex-shrink: 0;
}
.action-center {
  flex: 1;
  display: flex;
  justify-content: center;
}
.action-right {
  display: flex;
  gap: 0.6rem;
  flex-shrink: 0;
}
.action-settings {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  padding: 0.5rem 1rem;
  border-radius: 0.625rem;
  font-size: 0.82rem;
  font-weight: 700;
  color: #475569;
  border: 1px solid #e2e8f0;
  transition: all 0.15s;
}
.action-settings:hover {
  border-color: #2563eb;
  color: #2563eb;
}
:global(.dark) .action-settings {
  background: #1e293b;
  border-color: #334155;
  color: #cbd5e1;
}
.btn-run {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  height: 2.4rem;
  padding: 0 1.1rem;
  border-radius: 0.625rem;
  font-size: 0.88rem;
  font-weight: 800;
  color: #334155;
  background: #f1f5f9;
  border: 1px solid #e2e8f0;
  transition: all 0.15s;
}
.btn-run:hover:not(:disabled) {
  background: #e2e8f0;
}
.btn-run:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}
:global(.dark) .btn-run {
  background: #1e293b;
  border-color: #334155;
  color: #e2e8f0;
}
.btn-submit {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  height: 2.4rem;
  padding: 0 1.2rem;
  border-radius: 0.625rem;
  font-size: 0.88rem;
  font-weight: 800;
  color: #fff;
  background: #2563eb;
  transition: background 0.15s;
}
.btn-submit:hover:not(:disabled) {
  background: #1d4ed8;
}
.btn-submit:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}
.btn-run kbd,
.btn-submit kbd {
  font-size: 0.68rem;
  font-weight: 700;
  padding: 0.05rem 0.35rem;
  border-radius: 0.3rem;
  background: rgba(255, 255, 255, 0.25);
  color: inherit;
}
.btn-run kbd {
  background: rgba(0, 0, 0, 0.08);
}

/* 设置 Popover */
.settings-backdrop,
.menu-backdrop {
  position: fixed;
  inset: 0;
  z-index: 65;
}
.settings-popover {
  position: fixed;
  right: 1rem;
  bottom: 4.5rem;
  z-index: 70;
  width: 18rem;
  border: 1px solid #e2e8f0;
  border-radius: 1rem;
  background: #fff;
  padding: 1rem;
  box-shadow: 0 24px 50px rgba(15, 23, 42, 0.2);
}
:global(.dark) .settings-popover {
  background: #0f172a;
  border-color: #1e293b;
}
.settings-title {
  font-size: 0.95rem;
  font-weight: 800;
  margin-bottom: 0.75rem;
}
.settings-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 0.6rem;
  font-size: 0.85rem;
  font-weight: 600;
  color: #475569;
}
:global(.dark) .settings-row {
  color: #cbd5e1;
}
.seg {
  display: inline-flex;
  border: 1px solid #e2e8f0;
  border-radius: 0.5rem;
  overflow: hidden;
}
:global(.dark) .seg {
  border-color: #334155;
}
.seg button {
  padding: 0.3rem 0.6rem;
  font-size: 0.78rem;
  font-weight: 700;
  color: #64748b;
  background: #fff;
  transition: all 0.15s;
}
.seg button + button {
  border-left: 1px solid #e2e8f0;
}
.seg button.active {
  background: #2563eb;
  color: #fff;
}
:global(.dark) .seg button {
  background: #1e293b;
  color: #cbd5e1;
}
:global(.dark) .seg button + button {
  border-color: #334155;
}
.switch {
  padding: 0.3rem 0.9rem;
  border-radius: 999px;
  font-size: 0.78rem;
  font-weight: 700;
  color: #64748b;
  background: #f1f5f9;
  border: 1px solid #e2e8f0;
}
.switch.on {
  background: #2563eb;
  color: #fff;
  border-color: #2563eb;
}
.settings-hint {
  margin-top: 0.5rem;
  padding-top: 0.6rem;
  border-top: 1px solid #e2e8f0;
  font-size: 0.75rem;
  color: #94a3b8;
  line-height: 1.7;
}
.settings-hint p:first-child {
  font-weight: 800;
  color: #475569;
}
:global(.dark) .settings-hint {
  border-color: #1e293b;
}
:global(.dark) .settings-hint p:first-child {
  color: #cbd5e1;
}

/* markdown 代码块等 */
.markdown-body :deep(pre) {
  background: #0f172a;
  color: #e2e8f0;
  border-radius: 0.6rem;
  padding: 0.8rem;
  overflow: auto;
}
.markdown-body :deep(code) {
  font-family: ui-monospace, SFMono-Regular, 'SF Mono', Menlo, Consolas, monospace;
}
.markdown-body :deep(table) {
  border-collapse: collapse;
  width: 100%;
}
.markdown-body :deep(th),
.markdown-body :deep(td) {
  border: 1px solid #e2e8f0;
  padding: 0.4rem 0.6rem;
}
</style>

<!--
  非 scoped <style>：深色模式全局覆盖。
  scoped CSS + :global(.dark) 无法可靠穿透 MarkdownComponent 内部的
  prose / v-html 生成节点，因此必须用无作用域的全局选择器 + !important
  来强制覆盖。
-->
<style>
/* ===== 编辑器页面 - 深色模式全局覆盖 ===== */

/* 顶栏 */
html.dark .editor-topbar {
  background: #0f172a;
  border-color: #1e293b;
}

/* 题目面板 */
html.dark .problem-panel {
  background: #0f172a;
  border-color: #1e293b;
}
html.dark .problem-panel-tabs {
  border-color: #1e293b;
}
html.dark .problem-panel-tabs button {
  color: #94a3b8;
}
html.dark .problem-panel-tabs button:hover {
  background: #1e293b;
}
html.dark .problem-panel-tabs button.active {
  background: #1e3a8a;
  color: #bfdbfe;
}

/* 题目信息 */
html.dark .problem-no-lg {
  color: #64748b;
}
html.dark .problem-title {
  color: #e2e8f0;
}
html.dark .problem-name {
  color: #e2e8f0;
}
html.dark .meta-item {
  color: #94a3b8;
}
html.dark .tag-pill {
  background: #1e293b;
  color: #cbd5e1;
}
html.dark .tag-pill:hover {
  background: #334155;
  color: #67e8f9;
}
html.dark .problem-stat {
  color: #94a3b8;
}
html.dark .problem-stat b {
  color: #e2e8f0;
}

/* Markdown 区块标题 */
html.dark .md-head {
  color: #e2e8f0;
}
html.dark .md-body {
  color: #cbd5e1;
}

/* 样例卡片 */
html.dark .sample-card {
  border-color: #1e293b;
}
html.dark .sample-head {
  background: #1e293b;
  color: #cbd5e1;
  border-color: #1e293b;
}
html.dark .sample-run {
  color: #60a5fa;
}
html.dark .sample-run:hover {
  background: #172554;
}
html.dark .sample-io-head {
  background: #1e293b;
  color: #94a3b8;
}
html.dark .sample-io-body,
html.dark .io-pre {
  background: #0f172a;
  color: #6ee7b7;
}
html.dark .sample-io-body.err,
html.dark .io-pre.err {
  color: #fca5a5;
}
html.dark .copy-btn {
  color: #94a3b8;
}
html.dark .copy-btn:hover {
  background: #334155;
}

/* 提示框 */
html.dark .tip-box {
  background: #422006;
  color: #fcd34d;
}

/* 状态盒 */
html.dark .state-box {
  color: #94a3b8;
}
html.dark .text-btn {
  color: #60a5fa;
}

/* 提交记录 */
html.dark .sub-row {
  border-color: #1e293b;
  background: #0f172a;
}
html.dark .sub-lang {
  color: #94a3b8;
}

/* 右侧编辑器 */
html.dark .editor-toolbar {
  background: #0f172a;
  border-color: #1e293b;
}
html.dark .lang-trigger {
  background: #1e293b;
  border-color: #334155;
  color: #e2e8f0;
}
html.dark .lang-menu {
  background: #0f172a;
  border-color: #1e293b;
}
html.dark .lang-item {
  color: #e2e8f0;
}
html.dark .lang-item:hover {
  background: #1e293b;
}
html.dark .tool-btn {
  background: #1e293b;
  border-color: #334155;
  color: #cbd5e1;
}
html.dark .editor-body {
  background: #1e1e1e;
}

/* 结果区 */
html.dark .result-panel {
  background: #0f172a;
  border-color: #1e293b;
}
html.dark .result-tabs {
  border-color: #1e293b;
}
html.dark .result-tabs button {
  color: #94a3b8;
}
html.dark .result-tabs button:hover {
  background: #1e293b;
}
html.dark .result-tabs button.active {
  background: #1e3a8a;
  color: #bfdbfe;
}
html.dark .result-collapse {
  color: #94a3b8;
}
html.dark .result-collapse:hover {
  background: #1e293b;
}

/* IO 区块 */
html.dark .io-head {
  background: #1e293b;
  color: #cbd5e1;
}
html.dark .io-textarea {
  background: #1e293b;
  border-color: #334155;
  color: #e2e8f0;
}
html.dark .io-textarea:focus {
  border-color: #2563eb;
}
html.dark .io-status {
  background: #1e293b;
  color: #cbd5e1;
}
html.dark .io-status.ok {
  background: #064e3b;
  color: #34d399;
}
html.dark .io-status.bad {
  background: #450a0a;
  color: #fca5a5;
}

/* 判题结果 */
html.dark .judge-banner {
  background: #1e293b;
  color: #94a3b8;
}
html.dark .test-point {
  border-color: #334155;
  color: #94a3b8;
}
html.dark .test-point.active {
  border-color: #2563eb;
  background: #172554;
}

/* 底部操作栏 */
html.dark .action-bar {
  background: #0f172a;
  border-color: #1e293b;
}
html.dark .action-settings {
  background: #1e293b;
  border-color: #334155;
  color: #cbd5e1;
}
html.dark .btn-run {
  background: #1e293b;
  border-color: #334155;
  color: #e2e8f0;
}

/* 设置弹窗 */
html.dark .settings-popover {
  background: #0f172a;
  border-color: #1e293b;
}
html.dark .settings-row {
  color: #cbd5e1;
}
html.dark .seg {
  border-color: #334155;
}
html.dark .seg button {
  background: #1e293b;
  color: #cbd5e1;
}
html.dark .seg button + button {
  border-color: #334155;
}
html.dark .settings-hint {
  border-color: #1e293b;
  color: #94a3b8;
}
html.dark .settings-hint p:first-child {
  color: #cbd5e1;
}

/* 分割线 */
html.dark .v-resizer {
  background: #1e293b;
}
html.dark .h-resizer {
  background: #1e293b;
}

/* 用户菜单 */
html.dark .user-dropdown {
  background: #0f172a;
  border-color: #1e293b;
  box-shadow: 0 18px 40px rgba(0, 0, 0, 0.5);
}
html.dark .user-dropdown-item {
  color: #e2e8f0;
}
html.dark .user-dropdown-item:hover {
  background: #082f49;
  color: #67e8f9;
}
html.dark .user-dropdown-divider {
  background: #1e293b;
}
html.dark .user-dropdown-logout:hover {
  background: #450a0a !important;
  color: #fca5a5 !important;
}

/* 导航菜单 */
html.dark .icon-btn {
  color: #94a3b8;
}
html.dark .icon-btn:hover {
  background: #1e293b;
  color: #e2e8f0;
}
html.dark .mode-chip {
  background: #1e293b;
  color: #94a3b8;
}

/* Markdown prose 深色覆盖 */
html.dark .markdown-article {
  color: #f8fafc;
}
html.dark .markdown-article .markdown-content :is(p, li, blockquote, td, th, dd, dt, figcaption, span, strong, em) {
  color: #cbd5e1;
}
html.dark .markdown-article .markdown-content :is(h1, h2, h3, h4, h5, h6) {
  color: #ffffff;
}
html.dark .markdown-article .markdown-content :is(a, a:visited) {
  color: #67e8f9;
}
html.dark .markdown-article .markdown-content :is(code):not(pre code) {
  color: #e2e8f0;
}
html.dark .markdown-article header {
  color: #f8fafc;
}
html.dark .markdown-article header time,
html.dark .markdown-article header span {
  color: #94a3b8;
}
</style>
