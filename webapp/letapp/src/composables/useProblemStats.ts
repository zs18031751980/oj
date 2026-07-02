import { reactive } from 'vue';

const STORAGE_KEY = 'problem_stats';

interface ProblemStat {
  accepted: number;
  submissions: number;
}

function loadStats(): Record<number, ProblemStat> {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (raw) return JSON.parse(raw);
  } catch {}
  return {};
}

function saveStats(stats: Record<number, ProblemStat>) {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(stats));
  } catch {}
}

const stats = reactive(loadStats());

export function useProblemStats() {
  const getStats = (problemId: number): ProblemStat => {
    if (!stats[problemId]) {
      stats[problemId] = { accepted: 0, submissions: 0 };
    }
    return stats[problemId];
  };

  const incrementSubmissions = (problemId: number) => {
    const s = getStats(problemId);
    s.submissions += 1;
    saveStats(stats);
  };

  const incrementAccepted = (problemId: number) => {
    const s = getStats(problemId);
    s.accepted += 1;
    saveStats(stats);
  };

  return { getStats, incrementSubmissions, incrementAccepted };
}
