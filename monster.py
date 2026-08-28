"""
monster.py — 몬스터 관련 기능 모음
====================================================
몬스터 하나하나는 딕셔너리로 표현하고, 여러 마리를 리스트에 담아 관리합니다.
(player.py의 플레이어와 똑같은 "딕셔너리로 상태 관리" 패턴)
"""

import random
import math
import config
import ui


def get_current_monster_max_hp(stage):
    """스테이지 번호에 따라 몬스터가 가져야 할 최대 체력을 계산."""
    return config.BASE_MONSTER_HP + (stage - 1) * config.MONSTER_HP_PER_STAGE


def spawn_wave(count, player, stage):
    """
    몬스터를 맵 안 랜덤한 위치에 count마리 배치.
    플레이어와 너무 가까운 곳에는 스폰되지 않도록 거리 체크.
    """
    monsters = []
    px = player["x"] + config.PLAYER_DISPLAY_SIZE[0] / 2
    py = player["y"] + config.PLAYER_DISPLAY_SIZE[1] / 2
    monster_max_hp = get_current_monster_max_hp(stage)

    while len(monsters) < count:
        mx = random.randint(0, config.MAP_WIDTH - config.MONSTER_SIZE)
        my = random.randint(0, config.MAP_HEIGHT - config.MONSTER_SIZE)

        if math.hypot(mx - px, my - py) > 150:
            monsters.append({
                "x": mx, "y": my,
                "hp": monster_max_hp,
                "max_hp": monster_max_hp,
                "facing_right": True,
                "knockback_timer": 0,
                "knockback_dx": 0,
                "knockback_dy": 0,
            })

    return monsters


def move_toward_player(m, player):
    """몬스터를 이동시킴. 넉백 중이면 넉백을, 아니면 평소처럼 플레이어를 추격."""
    if m["knockback_timer"] > 0:
        m["x"] += m["knockback_dx"] * config.KNOCKBACK_SPEED
        m["y"] += m["knockback_dy"] * config.KNOCKBACK_SPEED
        m["knockback_timer"] -= 1
    else:
        px = player["x"] + config.PLAYER_DISPLAY_SIZE[0] / 2
        py = player["y"] + config.PLAYER_DISPLAY_SIZE[1] / 2
        mx_center = m["x"] + config.MONSTER_SIZE / 2
        my_center = m["y"] + config.MONSTER_SIZE / 2

        dx = px - mx_center
        dy = py - my_center
        distance = math.hypot(dx, dy)

        if dx > 0.5:
            m["facing_right"] = True
        elif dx < -0.5:
            m["facing_right"] = False

        if distance > 1:
            dx, dy = dx / distance, dy / distance
            m["x"] += dx * config.MONSTER_SPEED
            m["y"] += dy * config.MONSTER_SPEED

    # 넉백으로 맵 밖까지 밀려나지 않도록 위치 제한
    m["x"] = max(0, min(m["x"], config.MAP_WIDTH - config.MONSTER_SIZE))
    m["y"] = max(0, min(m["y"], config.MAP_HEIGHT - config.MONSTER_SIZE))


def draw(screen, m, camera_x, camera_y):
    """몬스터 한 마리와 방향 표시, 체력바를 화면에 그림 (카메라 오프셋 반영)."""
    import pygame

    center = (int(m["x"] + config.MONSTER_SIZE / 2 - camera_x),
              int(m["y"] + config.MONSTER_SIZE / 2 - camera_y))

    pygame.draw.circle(screen, config.RED, center, config.MONSTER_SIZE // 2)
    pygame.draw.circle(screen, config.DARK_RED, center, config.MONSTER_SIZE // 2, 2)

    nose_dir = 1 if m["facing_right"] else -1
    radius = config.MONSTER_SIZE // 2
    tip = (center[0] + nose_dir * (radius + 6), center[1])
    base_top = (center[0] + nose_dir * (radius - 4), center[1] - 5)
    base_bottom = (center[0] + nose_dir * (radius - 4), center[1] + 5)
    pygame.draw.polygon(screen, config.DARK_RED, [tip, base_top, base_bottom])

    ui.draw_hp_bar(screen, center[0], center[1] - config.MONSTER_SIZE / 2 - 12,
                    m["hp"], m["max_hp"], bar_width=32, bar_height=5)
