import { apiRequest } from '../services/api';

export function useProblemCode() {
  const saveCode = async (problemId: number, language: string, code: string) => {
    try {
      await apiRequest('/user/code', {
        method: 'PUT',
        body: JSON.stringify({ problem_id: problemId, language, code }),
      });
    } catch {}
  };

  const loadCode = async (problemId: number, language: string): Promise<string | null> => {
    try {
      const res = await apiRequest<{ code: string | null }>(`/user/code/${problemId}?language=${language}`, {
        skipAuth: false,
      });
      return res.code ?? null;
    } catch {
      return null;
    }
  };

  return { saveCode, loadCode };
}
