"""比赛发布后不可变性和可见性的领域回归测试。"""

import unittest

from services.contest_lifecycle import (
    can_delete_contest,
    can_edit_contest_assets,
    can_view_rankings,
)


class ContestLifecyclePolicyTests(unittest.TestCase):
    def test_published_contest_assets_are_immutable(self):
        self.assertTrue(can_edit_contest_assets('DRAFT'))
        self.assertTrue(can_edit_contest_assets('READY'))
        self.assertFalse(can_edit_contest_assets('SCHEDULED'))
        self.assertFalse(can_edit_contest_assets('FINALIZED'))

    def test_only_unpublished_contests_can_be_deleted(self):
        self.assertTrue(can_delete_contest('DRAFT'))
        self.assertFalse(can_delete_contest('SCHEDULED'))
        self.assertFalse(can_delete_contest('FINALIZED'))

    def test_unpublished_or_private_rankings_require_manager(self):
        self.assertFalse(can_view_rankings('DRAFT', is_public=True, is_manager=False))
        self.assertFalse(can_view_rankings('SCHEDULED', is_public=False, is_manager=False))
        self.assertTrue(can_view_rankings('SCHEDULED', is_public=True, is_manager=False))
        self.assertTrue(can_view_rankings('DRAFT', is_public=False, is_manager=True))


if __name__ == '__main__':
    unittest.main()
