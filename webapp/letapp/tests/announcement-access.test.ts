import assert from 'node:assert/strict';
import test from 'node:test';

import {
  announcementToForm,
  resolveManagerRoute,
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
