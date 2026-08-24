import { reactive } from 'vue';

const STORAGE_KEY = 'problem_stats';

interface ProblemStat {
  accepted: number;
  submissions: number;
  attempted: boolean;
}

function loadStats(): Record<number, ProblemStat> {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (raw) {
      const parsed = JSON.parse(raw);
      // migrate: add attempted field if missing
      for (const key of Object.keys(parsed)) {
        const s = parsed[key];
        if (s.attempted === undefined) {
          s.attempted = s.submissions > 0 && s.accepted === 0;
        }
      }
      return parsed;
    }
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
      stats[problemId] = { accepted: 0, submissions: 0, attempted: false };
    }
    return stats[problemId];
  };

  const incrementSubmissions = (problemId: number) => {
    const s = getStats(problemId);
    s.submissions += 1;
    s.attempted = s.submissions > 0 && s.accepted === 0;
    saveStats(stats);
  };

  const incrementAccepted = (problemId: number) => {
    const s = getStats(problemId);
    s.accepted += 1;
    s.attempted = s.submissions > 0 && s.accepted === 0;
    saveStats(stats);
  };

  return { getStats, incrementSubmissions, incrementAccepted };
}
