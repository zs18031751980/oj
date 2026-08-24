import type { AnnouncementData, AnnouncementForm } from '../services/api';


export type ManagerRouteDecision = 'allow' | 'login' | 'forbidden';

// 允许进入管理后台的角色（仅 manager；公告编辑与比赛管理均仅限管理员）
const ADMIN_PANEL_ROLES = new Set(['manager']);

export const resolveManagerRoute = (
  isAuthenticated: boolean,
  role?: string,
): ManagerRouteDecision => {
  if (!isAuthenticated) return 'login';
  return ADMIN_PANEL_ROLES.has(role ?? '') ? 'allow' : 'forbidden';
};

export const announcementToForm = (
  item: AnnouncementData,
): AnnouncementForm => ({
  id: item.id,
  title: item.title,
  content: item.content,
  permission: item.permission || 'member',
  is_published: item.is_published,
});

export const canSaveAnnouncement = (form: AnnouncementForm) =>
  Boolean(form.title.trim() && form.content.trim());

export const parseAnnouncementId = (raw: unknown): number | null => {
  const value = Array.isArray(raw) ? raw[0] : raw;
  const parsed = Number(value);
  return Number.isInteger(parsed) && parsed > 0 ? parsed : null;
};

export const sortAnnouncementsNewestFirst = (items: AnnouncementData[]) =>
  [...items].sort((left, right) => {
    const leftTime = Date.parse(
      left.updated_at || left.published_at || left.created_at || '',
    );
    const rightTime = Date.parse(
      right.updated_at || right.published_at || right.created_at || '',
    );
    return rightTime - leftTime;
  });
