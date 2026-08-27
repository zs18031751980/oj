/**
 * ACM 判题状态元数据
 *
 * 集中定义各判题状态的中文标签、配色与样式类，
 * 供「提交结果」面板与「比赛题目列表」着色统一使用。
 *
 * 颜色约定（贴近常见 ACM/ICPC 计分板）：
 * - AC   通过       绿色
 * - WA   答案错误   红色
 * - TLE  超时       琥珀/黄色
 * - RE   运行错误   紫红色
 * - CE   编译错误   石板灰
 * - MLE  内存超限   橙色
 * - PE   格式错误   青色
 * - OLE  输出超限   粉色
 * - Partial 部分通过 蓝色
 * - 其他  待判/无用例/异常 灰色
 */

export type JudgeStatus =
  | 'AC' | 'WA' | 'TLE' | 'RE' | 'CE' | 'MLE'
  | 'PE' | 'OLE' | 'Partial' | 'NoTestcases' | 'Error'
  | 'Pending' | 'Judging' | 'Empty' | 'NoProblem' | 'Unauthorized' | string;

export interface JudgeStatusMeta {
  /** 中文标签 */
  label: string;
  /** 简短英文缩写（已是缩写时直接用） */
  short: string;
  /** 文字颜色类（Tailwind，含 dark 变体） */
  text: string;
  /** 浅色背景类（用于表格行/卡片底色） */
  bg: string;
  /** 边框/徽标背景类 */
  badge: string;
  /** 状态圆点背景色 */
  dot: string;
  /** 是否为「通过/已解决」状态 */
  solved: boolean;
}

const META: Record<string, JudgeStatusMeta> = {
  AC: {
    label: '通过', short: 'AC',
    text: 'text-emerald-600 dark:text-emerald-400',
    bg: 'bg-emerald-50 dark:bg-emerald-950/40',
    badge: 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/60 dark:text-emerald-300',
    dot: 'bg-emerald-500', solved: true,
  },
  WA: {
    label: '答案错误', short: 'WA',
    text: 'text-red-600 dark:text-red-400',
    bg: 'bg-red-50 dark:bg-red-950/40',
    badge: 'bg-red-100 text-red-700 dark:bg-red-900/60 dark:text-red-300',
    dot: 'bg-red-500', solved: false,
  },
  TLE: {
    label: '超时', short: 'TLE',
    text: 'text-amber-600 dark:text-amber-400',
    bg: 'bg-amber-50 dark:bg-amber-950/40',
    badge: 'bg-amber-100 text-amber-700 dark:bg-amber-900/60 dark:text-amber-300',
    dot: 'bg-amber-500', solved: false,
  },
  RE: {
    label: '运行错误', short: 'RE',
    text: 'text-fuchsia-600 dark:text-fuchsia-400',
    bg: 'bg-fuchsia-50 dark:bg-fuchsia-950/40',
    badge: 'bg-fuchsia-100 text-fuchsia-700 dark:bg-fuchsia-900/60 dark:text-fuchsia-300',
    dot: 'bg-fuchsia-500', solved: false,
  },
  CE: {
    label: '编译错误', short: 'CE',
    text: 'text-slate-500 dark:text-slate-400',
    bg: 'bg-slate-100 dark:bg-slate-800/60',
    badge: 'bg-slate-200 text-slate-600 dark:bg-slate-700/60 dark:text-slate-300',
    dot: 'bg-slate-400', solved: false,
  },
  MLE: {
    label: '内存超限', short: 'MLE',
    text: 'text-orange-600 dark:text-orange-400',
    bg: 'bg-orange-50 dark:bg-orange-950/40',
    badge: 'bg-orange-100 text-orange-700 dark:bg-orange-900/60 dark:text-orange-300',
    dot: 'bg-orange-500', solved: false,
  },
  PE: {
    label: '格式错误', short: 'PE',
    text: 'text-teal-600 dark:text-teal-400',
    bg: 'bg-teal-50 dark:bg-teal-950/40',
    badge: 'bg-teal-100 text-teal-700 dark:bg-teal-900/60 dark:text-teal-300',
    dot: 'bg-teal-500', solved: false,
  },
  OLE: {
    label: '输出超限', short: 'OLE',
    text: 'text-pink-600 dark:text-pink-400',
    bg: 'bg-pink-50 dark:bg-pink-950/40',
    badge: 'bg-pink-100 text-pink-700 dark:bg-pink-900/60 dark:text-pink-300',
    dot: 'bg-pink-500', solved: false,
  },
  Partial: {
    label: '部分通过', short: 'Partial',
    text: 'text-blue-600 dark:text-blue-400',
    bg: 'bg-blue-50 dark:bg-blue-950/40',
    badge: 'bg-blue-100 text-blue-700 dark:bg-blue-900/60 dark:text-blue-300',
    dot: 'bg-blue-500', solved: false,
  },
  NoTestcases: {
    label: '无测试用例', short: '—',
    text: 'text-slate-500 dark:text-slate-400',
    bg: 'bg-slate-100 dark:bg-slate-800/60',
    badge: 'bg-slate-200 text-slate-600 dark:bg-slate-700/60 dark:text-slate-300',
    dot: 'bg-slate-400', solved: false,
  },
  Error: {
    label: '判题异常', short: 'ERR',
    text: 'text-slate-500 dark:text-slate-400',
    bg: 'bg-slate-100 dark:bg-slate-800/60',
    badge: 'bg-slate-200 text-slate-600 dark:bg-slate-700/60 dark:text-slate-300',
    dot: 'bg-slate-400', solved: false,
  },
  Pending: {
    label: '等待判题', short: '···',
    text: 'text-sky-600 dark:text-sky-400',
    bg: 'bg-sky-50 dark:bg-sky-950/40',
    badge: 'bg-sky-100 text-sky-700 dark:bg-sky-900/60 dark:text-sky-300',
    dot: 'bg-sky-500', solved: false,
  },
  Judging: {
    label: '判题中', short: '···',
    text: 'text-sky-600 dark:text-sky-400',
    bg: 'bg-sky-50 dark:bg-sky-950/40',
    badge: 'bg-sky-100 text-sky-700 dark:bg-sky-900/60 dark:text-sky-300',
    dot: 'bg-sky-500', solved: false,
  },
};

const FALLBACK: JudgeStatusMeta = {
  label: '未知状态', short: '?',
  text: 'text-slate-500 dark:text-slate-400',
  bg: 'bg-slate-100 dark:bg-slate-800/60',
  badge: 'bg-slate-200 text-slate-600 dark:bg-slate-700/60 dark:text-slate-300',
  dot: 'bg-slate-400', solved: false,
};

export function getJudgeStatus(status: JudgeStatus): JudgeStatusMeta {
  if (!status) return FALLBACK;
  return META[status] ?? { ...FALLBACK, label: String(status), short: String(status) };
}
