import type { AnnouncementData, AnnouncementForm } from '../services/api';


export type ManagerRouteDecision = 'allow' | 'login' | 'forbidden';

export const resolveManagerRoute = (
  isAuthenticated: boolean,
  role?: string,
): ManagerRouteDecision => {
  if (!isAuthenticated) return 'login';
  return role === 'manager' ? 'allow' : 'forbidden';
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
