import assert from 'node:assert/strict';
import test from 'node:test';

import {
  announcementToForm,
  parseAnnouncementId,
  resolveManagerRoute,
  sortAnnouncementsNewestFirst,
} from '../src/utils/announcement-access.ts';


test('manager route requires authentication and manager role', () => {
  assert.equal(resolveManagerRoute(false, undefined), 'login');
  assert.equal(resolveManagerRoute(true, 'member'), 'forbidden');
  assert.equal(resolveManagerRoute(true, 'manager'), 'allow');
});

test('announcement form preserves the edited announcement id', () => {
  assert.deepEqual(
    announcementToForm({
      id: 17,
      title: '通知',
      content: '# 正文',
      is_published: true,
    }),
    {
      id: 17,
      title: '通知',
      content: '# 正文',
      permission: 'member',
      is_published: true,
    },
  );
});

test('published announcements sort newest first', () => {
  const sorted = sortAnnouncementsNewestFirst([
    {
      id: 1,
      title: '旧公告',
      content: '',
      is_published: true,
      updated_at: '2026-01-01',
    },
    {
      id: 2,
      title: '新公告',
      content: '',
      is_published: true,
      updated_at: '2026-02-01',
    },
  ]);

  assert.deepEqual(sorted.map((item) => item.id), [2, 1]);
});

test('announcement id parser rejects invalid values', () => {
  assert.equal(parseAnnouncementId('17'), 17);
  assert.equal(parseAnnouncementId(['18', '19']), 18);
  assert.equal(parseAnnouncementId('abc'), null);
  assert.equal(parseAnnouncementId('-1'), null);
  assert.equal(parseAnnouncementId(undefined), null);
});
