const resolveApiBaseUrl = () => {
  const envBaseUrl = String(import.meta.env.VITE_API_BASE_URL || '').trim();
  if (envBaseUrl) {
    return envBaseUrl;
  }

  // 生产环境：自动使用当前页面的 host，端口改为 6173
  if (typeof window !== 'undefined') {
    const { protocol, hostname } = window.location;
    return `${protocol}//${hostname}:6173`;
  }

  return 'http://localhost:6173';
};

export const API_BASE_URL = resolveApiBaseUrl();

export interface UserInfo {
  id: string;
  username: string;
  email: string;
  name?: string;
  avatar_url?: string;
  provider?: string;
  role?: string;
  is_active?: boolean;
  last_login?: string;
  theme_preference?: string;
  created_at?: string;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  expires_in: number;
  token_type: string;
  user_info?: UserInfo;
}

interface ApiRequestOptions extends RequestInit {
  skipAuth?: boolean;
}

export type AuthStorageMode = 'local' | 'session';

const AUTH_STORAGE_MODE_KEY = 'auth_storage_mode';

export class ApiError extends Error {
  status: number;
  payload: unknown;

  constructor(message: string, status: number, payload: unknown) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.payload = payload;
  }
}

export const getAuthStorageMode = (): AuthStorageMode => (
  localStorage.getItem(AUTH_STORAGE_MODE_KEY) === 'session' ? 'session' : 'local'
);

export const setAuthStorageMode = (mode: AuthStorageMode) => {
  localStorage.setItem(AUTH_STORAGE_MODE_KEY, mode);
};

export const clearAuthStorageMode = () => {
  localStorage.removeItem(AUTH_STORAGE_MODE_KEY);
};

export const getAuthStorage = (mode: AuthStorageMode = getAuthStorageMode()) => (
  mode === 'session' ? sessionStorage : localStorage
);

const getStoredAccessToken = () => getAuthStorage().getItem('access_token');
const getStoredRefreshToken = () => getAuthStorage().getItem('refresh_token');

let isRefreshing = false;

const tryRefreshToken = async (): Promise<boolean> => {
  if (isRefreshing) return false;
  isRefreshing = true;
  try {
    const refreshToken = getStoredRefreshToken();
    if (!refreshToken) return false;
    const res = await fetch(`${API_BASE_URL}/auth/refresh`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refresh_token: refreshToken }),
    });
    if (!res.ok) return false;
    const data = await res.json();
    const storage = getAuthStorage();
    storage.setItem('access_token', data.access_token);
    storage.setItem('refresh_token', data.refresh_token);
    if (data.user_info) {
      storage.setItem('user_info', JSON.stringify(data.user_info));
      try {
        const { useAuthStore } = await import('../stores/auth');
        useAuthStore().userInfo = data.user_info;
      } catch { /* store not available */ }
    }
    return true;
  } catch {
    return false;
  } finally {
    isRefreshing = false;
  }
};

const parseResponse = async (response: Response) => {
  const contentType = response.headers.get('content-type') || '';

  if (contentType.includes('application/json')) {
    return response.json();
  }

  const text = await response.text();
  return text ? { message: text } : {};
};

export async function apiRequest<T>(path: string, options: ApiRequestOptions = {}): Promise<T> {
  const { skipAuth, headers, body, ...init } = options;
  const requestHeaders = new Headers(headers);

  if (body && !(body instanceof FormData) && !requestHeaders.has('Content-Type')) {
    requestHeaders.set('Content-Type', 'application/json');
  }

  if (!skipAuth) {
    const token = getStoredAccessToken();
    if (token && !requestHeaders.has('Authorization')) {
      requestHeaders.set('Authorization', `Bearer ${token}`);
    }
  }

  let response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    body,
    headers: requestHeaders,
  });

  // 401 且非 skipAuth 时，尝试刷新令牌后重试一次
  if (response.status === 401 && !skipAuth && !path.startsWith('/auth/refresh')) {
    const refreshed = await tryRefreshToken();
    if (refreshed) {
      const newToken = getStoredAccessToken();
      if (newToken) {
        requestHeaders.set('Authorization', `Bearer ${newToken}`);
      }
      response = await fetch(`${API_BASE_URL}${path}`, {
        ...init,
        body,
        headers: requestHeaders,
      });
    }
  }

  const payload = await parseResponse(response);

  if (!response.ok) {
    const message = typeof payload === 'object' && payload && 'error' in payload
      ? String((payload as { error: unknown }).error)
      : `请求失败，状态码 ${response.status}`;

    throw new ApiError(message, response.status, payload);
  }

  return payload as T;
}

export const updateUserTheme = (themePreference: 'light' | 'dark' | 'system') =>
  apiRequest<{ success: boolean }>('/auth/theme', {
    method: 'PATCH',
    body: JSON.stringify({ theme_preference: themePreference }),
  });

export interface UserProfileUpdate {
  name?: string;
  email?: string;
  bio?: string;
}

export const updateUserProfile = (data: UserProfileUpdate) =>
  apiRequest<{ success: boolean; user_info: UserInfo }>('/users/me', {
    method: 'PATCH',
    body: JSON.stringify(data),
  });

export const uploadAvatar = (file: File) => {
  const formData = new FormData();
  formData.append('avatar', file);
  return apiRequest<{ success: boolean; avatar_url: string }>('/users/me/avatar', {
    method: 'POST',
    body: formData,
    headers: {},
  });
};

export const getUserProfile = () =>
  apiRequest<UserInfo>('/users/me');

export interface AnnouncementData {
  id: number;
  title: string;
  content: string;
  category?: string;
  permission?: string;
  is_published: boolean;
  published_at?: string;
  created_at?: string;
  updated_at?: string;
}

export interface AnnouncementForm {
  id: number;
  title: string;
  content: string;
  category: string;
  permission: string;
  is_published: boolean;
}

export type AnnouncementInput = Omit<AnnouncementForm, 'id'>;

export const listAnnouncements = (options: { includeUnpublished?: boolean } = {}) => {
  const includeUnpublished = options.includeUnpublished === true;
  return apiRequest<AnnouncementData[]>(
    `/announcement/${includeUnpublished ? '?include_unpublished=true' : ''}`,
    { skipAuth: !includeUnpublished },
  );
};

export const getAnnouncement = (id: number) =>
  apiRequest<AnnouncementData>(`/announcement/${id}`, { skipAuth: true });

export const createAnnouncement = (data: AnnouncementInput) =>
  apiRequest<AnnouncementData>('/announcement/', {
    method: 'POST',
    body: JSON.stringify(data),
  });

export const updateAnnouncement = (id: number, data: Partial<AnnouncementInput>) =>
  apiRequest<AnnouncementData>(`/announcement/${id}`, {
    method: 'PUT',
    body: JSON.stringify(data),
  });

export const deleteAnnouncement = (id: number) =>
  apiRequest<{ success: boolean }>(`/announcement/${id}`, { method: 'DELETE' });

export interface AdminRecentUser {
  id: number;
  username: string | null;
  email: string | null;
  role: string;
  is_active: boolean;
  created_at: string | null;
}

export interface AdminRecentAnnouncement {
  id: number;
  title: string;
  is_published: boolean;
  created_at: string | null;
}

export interface AdminStats {
  total_users: number;
  active_users: number;
  total_submissions: number;
  total_announcements: number;
  recent_users: AdminRecentUser[];
  recent_announcements: AdminRecentAnnouncement[];
}

export const getAdminStats = () => apiRequest<AdminStats>('/admin/stats');

export interface AdminUserData {
  id: number;
  username: string | null;
  email: string | null;
  role: string;
  is_active: boolean;
  provider: string | null;
  created_at: string | null;
  last_login: string | null;
}

export interface AdminUserListParams {
  page?: number;
  per_page?: number;
  search?: string;
  role?: string;
  status?: string;
}

export interface AdminUserListResult {
  total: number;
  page: number;
  per_page: number;
  data: AdminUserData[];
}

export const listAdminUsers = (params: AdminUserListParams = {}) => {
  const query = new URLSearchParams();
  if (params.page != null) query.set('page', String(params.page));
  if (params.per_page != null) query.set('per_page', String(params.per_page));
  if (params.search?.trim()) query.set('search', params.search.trim());
  if (params.role && params.role !== 'all') query.set('role', params.role);
  if (params.status && params.status !== 'all') query.set('status', params.status);
  const qs = query.toString();
  return apiRequest<AdminUserListResult>(`/admin/users${qs ? `?${qs}` : ''}`);
};

export const updateAdminUserStatus = (userId: number, isActive: boolean) =>
  apiRequest<{ success: boolean; id: number; is_active: boolean }>(
    `/admin/users/${userId}/status`,
    {
      method: 'PATCH',
      body: JSON.stringify({ is_active: isActive }),
    },
  );

export const deleteAdminUser = (userId: number) =>
  apiRequest<{ success: boolean; id: number }>(`/admin/users/${userId}`, {
    method: 'DELETE',
  });

// ---------- 提交记录 ----------

export interface SubmissionHistoryItem {
  id: number;
  problem_id: number;
  problem_title: string;
  difficulty: string | null;
  language: string;
  status: string;
  time_used: number | null;
  created_at: string | null;
}

export interface SubmissionHistoryResult {
  total: number;
  page: number;
  per_page: number;
  data: SubmissionHistoryItem[];
}

export const listMySubmissions = (page = 1, perPage = 20) =>
  apiRequest<SubmissionHistoryResult>(
    `/submissions?page=${page}&per_page=${perPage}`,
  );

// ---------- 题目收藏 ----------

export interface FavoriteItem {
  problem_id: number;
  problem_title: string;
  difficulty: string | null;
  tags: string[];
  favorited_at: string | null;
}

export const listFavorites = () =>
  apiRequest<{ data: FavoriteItem[]; total: number }>('/favorites');

export const addFavorite = (problemId: number) =>
  apiRequest<{ success: boolean; favorited: boolean }>(`/favorites/${problemId}`, {
    method: 'POST',
  });

export const removeFavorite = (problemId: number) =>
  apiRequest<{ success: boolean; favorited: boolean }>(`/favorites/${problemId}`, {
    method: 'DELETE',
  });

export const getFavoriteStatus = (problemId: number) =>
  apiRequest<{ favorited: boolean }>(`/favorites/${problemId}/status`);

// ---------- 比赛 ----------

export interface ContestData {
  id: number;
  title: string;
  description: string;
  contest_type: string;
  status: string;
  start_time: string | null;
  end_time: string | null;
  participants_count: number;
  created_at: string;
}

export const listContests = (status?: string) =>
  apiRequest<ContestData[]>(`/contests/${status ? `?status=${status}` : ''}`);

export const getContest = (id: number) =>
  apiRequest<ContestData>(`/contests/${id}`);

export const createContest = (data: { title: string; description?: string; contest_type?: string; start_time?: string; end_time?: string }) =>
  apiRequest<ContestData>('/contests/', {
    method: 'POST',
    body: JSON.stringify(data),
  });

export const joinContest = (id: number) =>
  apiRequest<{ success: boolean }>(`/contests/${id}/join`, { method: 'POST' });

// ---------- 讨论 ----------

export interface DiscussionData {
  id: number;
  title: string;
  content: string;
  author_id: number;
  author_name: string;
  category: string;
  tags: string;
  reply_count: number;
  like_count: number;
  view_count: number;
  is_pinned: boolean;
  is_liked: boolean;
  created_at: string;
  replies?: DiscussionReplyData[];
}

export interface DiscussionReplyData {
  id: number;
  content: string;
  author_id: number;
  author_name: string;
  like_count: number;
  is_liked: boolean;
  created_at: string;
}

export const listDiscussions = (category?: string) =>
  apiRequest<DiscussionData[]>(`/discussions/${category ? `?category=${encodeURIComponent(category)}` : ''}`);

export const getDiscussion = (id: number) =>
  apiRequest<DiscussionData>(`/discussions/${id}`);

export const createDiscussion = (data: { title: string; content: string; category?: string; tags?: string }) =>
  apiRequest<DiscussionData>('/discussions/', {
    method: 'POST',
    body: JSON.stringify(data),
  });

export const likeDiscussion = (discussionId: number) =>
  apiRequest<{ liked: boolean; like_count: number }>(`/discussions/${discussionId}/like`, {
    method: 'POST',
  });

export const replyToDiscussion = (discussionId: number, content: string) =>
  apiRequest<DiscussionReplyData>(`/discussions/${discussionId}/replies`, {
    method: 'POST',
    body: JSON.stringify({ content }),
  });

export const likeDiscussionReply = (replyId: number) =>
  apiRequest<{ liked: boolean; like_count: number }>(`/discussions/replies/${replyId}/like`, {
    method: 'POST',
  });

export const deleteDiscussion = (discussionId: number) =>
  apiRequest<{ success: boolean }>(`/discussions/${discussionId}`, {
    method: 'DELETE',
  });

export const deleteDiscussionReply = (replyId: number) =>
  apiRequest<{ success: boolean }>(`/discussions/replies/${replyId}`, {
    method: 'DELETE',
  });

// ---------- 排行榜 ----------

export interface RankingData {
  rank: number;
  user_id: number;
  username: string;
  avatar_url: string;
  solved_count: number;
  rating: number;
}

export const listRankings = () =>
  apiRequest<RankingData[]>('/rankings/');

// ---------- 比赛题目管理 ----------

export interface ContestProblemData {
  id: number;
  contest_id: number;
  problem_index: string;
  title: string;
  description: string;
  input_desc: string;
  output_desc: string;
  correct_answer: string;
  time_limit: number;
  memory_limit: number;
  difficulty: string;
  testcase_count: number;
  samples?: Array<{ input: string; output: string }>;
}

export const listContestProblems = (contestId: number) =>
  apiRequest<ContestProblemData[]>(`/contests/${contestId}/problems`);

export interface ContestProblemStatus {
  status: string;
  solved: boolean;
}

export const getContestStatuses = (contestId: number) =>
  apiRequest<Record<string, ContestProblemStatus>>(`/contests/${contestId}/statuses`);

export const getContestProblem = (id: number) =>
  apiRequest<ContestProblemData>(`/contests/problems/${id}`);

// ---------- 比赛实时排行榜 ----------

export interface ContestProblemResult {
  problem_index: string;
  solved: boolean;
  passed: number;
  total: number;
  score: number;
  status: string;
  submissions: number;
}

export interface ContestRankingData {
  rank: number;
  user_id: number;
  username: string;
  avatar_url: string;
  solved_count: number;
  penalty: number;
  score: number;
  problems: ContestProblemResult[];
}

export interface ContestRankingsData {
  mode: string;
  contest_type: string;
  problem_indexes: string[];
  rankings: ContestRankingData[];
}

export const listContestRankings = (contestId: number) =>
  apiRequest<ContestRankingsData>(`/contests/${contestId}/rankings`);

export interface ProblemDetailData {
  id: number;
  title: string;
  difficulty: string;
  description: string;
  inputFormat: string;
  outputFormat: string;
  samples?: Array<{ input: string; output: string }>;
  timeLimit: number;
  memoryLimit: number;
  category?: string;
  categoryLabel?: string;
  tags?: string[];
  testCaseCount?: number;
  isLibrary?: boolean;
  contestProblemId?: number;
  contestId?: number;
  contestTitle?: string;
}

export const getProblem = (id: number) =>
  apiRequest<ProblemDetailData>(`/problems/${id}`, { skipAuth: true });

export interface LibrarySubmitResponse {
  submission_id: number;
  status: string;
}

/** 提交已结束比赛并入题库的题目（复用比赛判题队列） */
export const submitLibraryProblem = (data: {
  contest_problem_id: number;
  code: string;
  language: string;
}) => apiRequest<LibrarySubmitResponse>(`/problems/library/submit`, {
  method: 'POST',
  body: JSON.stringify(data),
});

/** 比赛题库题目判题结果结构（与通用提交结果一致） */
export interface SubmissionResponse {
  id: number;
  status: string;
  time_used: number | null;
  memory_used: number | null;
  testcase_results: Array<{
    testCaseIndex: number;
    passed: boolean;
    stdout: string;
    stderr: string;
    expected: string;
    input: string;
    actualOutput?: string;
  }>;
  fail_testcase_index: number | null;
  compile_error: string | null;
}

/** 轮询比赛题库题目的判题结果 */
export const getLibrarySubmission = (submissionId: number) =>
  apiRequest<SubmissionResponse>(`/problems/library/submission/${submissionId}`, {
    skipAuth: true,
  });

/**
 * 将后端返回的样例数据统一归一化为「{ input, output } 对象数组」。
 * 后端可能返回 JSON 字符串（如 '[{"input":"1","output":"2"}]'）或已解析的数组，
 * 也可能为空/非法。字符串若被直接交给 v-for 会按字符遍历，导致渲染出大量空样例。
 */
export function normalizeSamples(raw: unknown): Array<{ input: string; output: string }> {
  if (!raw) return [];
  let arr: unknown = raw;
  if (typeof raw === 'string') {
    try {
      arr = JSON.parse(raw);
    } catch {
      return [];
    }
  }
  if (!Array.isArray(arr)) return [];
  return arr.map((s: any) => ({
    input: typeof s?.input === 'string' ? s.input : '',
    output: typeof s?.output === 'string' ? s.output : '',
  }));
}

export const createContestProblem = (contestId: number, data: {
  problem_index: string;
  title: string;
  description: string;
  input_desc?: string;
  output_desc?: string;
  correct_answer: string;
  time_limit?: number;
  memory_limit?: number;
  difficulty?: string;
}) =>
  apiRequest<ContestProblemData>(`/admin/contests/?contest_id=${contestId}`, {
    method: 'POST',
    body: JSON.stringify(data),
  });

export const updateContestProblem = (id: number, data: Partial<{
  problem_index: string;
  title: string;
  description: string;
  input_desc: string;
  output_desc: string;
  correct_answer: string;
  time_limit: number;
  memory_limit: number;
  difficulty: string;
}>) =>
  apiRequest<ContestProblemData>(`/admin/contests/${id}`, {
    method: 'PUT',
    body: JSON.stringify(data),
  });

export const deleteContestProblem = (id: number) =>
  apiRequest<{ success: boolean }>(`/admin/contests/${id}`, { method: 'DELETE' });

export const regenerateTestcases = (problemId: number) =>
  apiRequest<{ success: boolean; count: number }>(`/admin/contests/${problemId}/regenerate-testcases`, {
    method: 'POST',
  });

// ---------- 学习资源收藏 ----------

export interface LearnFavoriteItem {
  resource_id: string;
  favorited_at: string | null;
}

export const listLearnFavorites = () =>
  apiRequest<{ data: LearnFavoriteItem[]; total: number }>('/learn-favorites');

export const addLearnFavorite = (resourceId: string) =>
  apiRequest<{ success: boolean; favorited: boolean }>(`/learn-favorites/${encodeURIComponent(resourceId)}`, {
    method: 'POST',
  });

export const removeLearnFavorite = (resourceId: string) =>
  apiRequest<{ success: boolean; favorited: boolean }>(`/learn-favorites/${encodeURIComponent(resourceId)}`, {
    method: 'DELETE',
  });

export const getLearnFavoriteStatus = (resourceId: string) =>
  apiRequest<{ favorited: boolean }>(`/learn-favorites/${encodeURIComponent(resourceId)}/status`);

// ---------- 学习资源浏览记录 ----------

export interface LearnHistoryItem {
  resource_id: string;
  browsed_at: string | null;
}

export const listLearnHistory = () =>
  apiRequest<{ data: LearnHistoryItem[]; total: number }>('/learn-history');

export const recordLearnHistory = (resourceId: string) =>
  apiRequest<{ success: boolean }>('/learn-history', {
    method: 'POST',
    body: JSON.stringify({ resource_id: resourceId }),
  });
