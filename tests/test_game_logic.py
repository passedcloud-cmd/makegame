"""화면 렌더링 없이 검증 가능한 순수 로직에 대한 단위 테스트."""

import unittest

import camera
import config
import monster
import story


class ComputeCameraTests(unittest.TestCase):
    def test_centers_on_player_within_bounds(self):
        # 맵 중앙 근처에서는 카메라가 플레이어를 정중앙에 둘 수 있어야 함
        player_center_x, player_center_y = config.MAP_WIDTH / 2, config.MAP_HEIGHT / 2
        camera_x, camera_y = camera.compute_camera(player_center_x, player_center_y)

        self.assertAlmostEqual(camera_x, player_center_x - config.SCREEN_WIDTH / 2)
        self.assertAlmostEqual(camera_y, player_center_y - config.SCREEN_HEIGHT / 2)

    def test_clamped_to_top_left_map_edge(self):
        camera_x, camera_y = camera.compute_camera(0, 0)
        self.assertEqual(camera_x, 0)
        self.assertEqual(camera_y, 0)

    def test_clamped_to_bottom_right_map_edge(self):
        camera_x, camera_y = camera.compute_camera(config.MAP_WIDTH, config.MAP_HEIGHT)
        self.assertEqual(camera_x, config.MAP_WIDTH - config.SCREEN_WIDTH)
        self.assertEqual(camera_y, config.MAP_HEIGHT - config.SCREEN_HEIGHT)


class StoryProgressionTests(unittest.TestCase):
    def test_defined_stage_uses_its_own_dialogue(self):
        lines = story.get_dialogue_for_stage(1)
        self.assertEqual(lines, story.STAGE_DIALOGUES[1])

    def test_undefined_stage_falls_back_to_default_dialogue(self):
        # STAGE_DIALOGUES에는 3번 스테이지가 정의되어 있지 않음
        self.assertNotIn(3, story.STAGE_DIALOGUES)
        self.assertEqual(story.get_dialogue_for_stage(3), story.DEFAULT_DIALOGUE)

    def test_advance_returns_false_until_last_line(self):
        state = story.create_story_state(1)
        total_lines = len(state["lines"])

        for _ in range(total_lines - 1):
            self.assertFalse(story.advance(state))

        self.assertTrue(story.advance(state))
        self.assertEqual(state["line_index"], total_lines)


class MonsterStatsTests(unittest.TestCase):
    def test_max_hp_scales_with_stage(self):
        self.assertEqual(monster.get_current_monster_max_hp(1), config.BASE_MONSTER_HP)
        self.assertEqual(
            monster.get_current_monster_max_hp(3),
            config.BASE_MONSTER_HP + 2 * config.MONSTER_HP_PER_STAGE,
        )

    def test_distance_to_measures_from_monster_center(self):
        m = {"x": 0, "y": 0, "size": 10}
        # 몬스터 중심은 (5, 5) -> 목표가 (5, 15)면 정확히 10만큼 떨어짐
        self.assertAlmostEqual(monster.distance_to(m, 5, 15), 10)


if __name__ == "__main__":
    unittest.main()
