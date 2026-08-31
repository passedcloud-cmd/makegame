"""
monster.py — 몬스터 관련 기능 모음
====================================================
몬스터 하나하나는 딕셔너리로 표현하고, 여러 마리를 리스트에 담아 관리합니다.
(player.py의 플레이어와 똑같은 "딕셔너리로 상태 관리" 패턴)

일반 몬스터와 보스 몬스터는 "크기(size)"와 "공격력(damage)"이 서로 다르므로,
이제 이 값들을 전역 상수가 아니라 몬스터 딕셔너리 안에 각자 저장합니다.
"""

import random
import math
import pygame
import config
import ui


def get_current_monster_max_hp(stage):
    """스테이지 번호에 따라 일반 몬스터가 가져야 할 최대 체력을 계산."""
    return config.BASE_MONSTER_HP + (stage - 1) * config.MONSTER_HP_PER_STAGE


def _random_spawn_position(size, player):
    """플레이어와 너무 가깝지 않은 랜덤 위치를 찾아서 반환. size가 클수록(보스) 그만큼 맵 안쪽에서만 뽑힘."""
    px = player["x"] + config.PLAYER_DISPLAY_SIZE[0] / 2
    py = player["y"] + config.PLAYER_DISPLAY_SIZE[1] / 2

    while True:
        mx = random.randint(0, config.MAP_WIDTH - size)
        my = random.randint(0, config.MAP_HEIGHT - size)
        if math.hypot(mx - px, my - py) > 150:
            return mx, my


def spawn_wave(count, player, stage):
    """일반 몬스터를 맵 안 랜덤한 위치에 count마리 배치."""
    monsters = []
    monster_max_hp = get_current_monster_max_hp(stage)

    for _ in range(count):
        mx, my = _random_spawn_position(config.MONSTER_SIZE, player)
        monsters.append({
            "x": mx, "y": my,
            "size": config.MONSTER_SIZE,
            "hp": monster_max_hp,
            "max_hp": monster_max_hp,
            "damage": config.DAMAGE_PER_HIT,
            "is_boss": False,
            "facing_right": True,
            "knockback_timer": 0,
            "knockback_dx": 0,
            "knockback_dy": 0,
        })

    return monsters


def spawn_boss(player, stage):
    """
    보스 몬스터 1마리를 생성.
    일반 몬스터 대비 크기 2배, 체력 3배, 공격력 3배 (config.BOSS_* 배율 참고).
    """
    size = config.MONSTER_SIZE * config.BOSS_SIZE_MULTIPLIER
    boss_hp = get_current_monster_max_hp(stage) * config.BOSS_HP_MULTIPLIER
    boss_damage = config.DAMAGE_PER_HIT * config.BOSS_DAMAGE_MULTIPLIER

    mx, my = _random_spawn_position(size, player)

    boss = {
        "x": mx, "y": my,
        "size": size,
        "hp": boss_hp,
        "max_hp": boss_hp,
        "damage": boss_damage,
        "is_boss": True,
        "facing_right": True,
        "knockback_timer": 0,
        "knockback_dx": 0,
        "knockback_dy": 0,
    }
    return [boss]  # 다른 웨이브 함수들과 형태를 맞추기 위해 리스트로 감싸서 반환


def distance_to(m, target_x, target_y):
    """몬스터 중심에서 특정 좌표까지의 거리를 계산. 타겟 선택(더 가까운 쪽 쫓기)에 사용."""
    mx_center = m["x"] + m["size"] / 2
    my_center = m["y"] + m["size"] / 2
    return math.hypot(target_x - mx_center, target_y - my_center)


def move_toward_target(m, target_center_x, target_center_y):
    """몬스터를 이동시킴. 넉백 중이면 넉백을, 아니면 target_center_x/y 위치를 향해 추격."""
    if m["knockback_timer"] > 0:
        m["x"] += m["knockback_dx"] * config.KNOCKBACK_SPEED
        m["y"] += m["knockback_dy"] * config.KNOCKBACK_SPEED
        m["knockback_timer"] -= 1
    else:
        mx_center = m["x"] + m["size"] / 2
        my_center = m["y"] + m["size"] / 2

        dx = target_center_x - mx_center
        dy = target_center_y - my_center
        distance = math.hypot(dx, dy)

        if dx > 0.5:
            m["facing_right"] = True
        elif dx < -0.5:
            m["facing_right"] = False

        if distance > 1:
            dx, dy = dx / distance, dy / distance
            m["x"] += dx * config.MONSTER_SPEED
            m["y"] += dy * config.MONSTER_SPEED

    # 넉백으로 맵 밖까지 밀려나지 않도록 위치 제한 (몬스터 자신의 크기 기준)
    m["x"] = max(0, min(m["x"], config.MAP_WIDTH - m["size"]))
    m["y"] = max(0, min(m["y"], config.MAP_HEIGHT - m["size"]))


def draw(screen, m, camera_x, camera_y):
    """몬스터(또는 보스) 한 마리와 방향 표시, 체력바를 화면에 그림."""
    size = m["size"]
    is_boss = m["is_boss"]

    center = (int(m["x"] + size / 2 - camera_x), int(m["y"] + size / 2 - camera_y))
    body_color = config.BOSS_COLOR if is_boss else config.RED
    outline_color = config.BOSS_OUTLINE_COLOR if is_boss else config.DARK_RED
    outline_width = 3 if is_boss else 2

    pygame.draw.circle(screen, body_color, center, size // 2)
    pygame.draw.circle(screen, outline_color, center, size // 2, outline_width)

    # 바라보는 방향 표시용 작은 삼각형("코")
    nose_dir = 1 if m["facing_right"] else -1
    radius = size // 2
    tip = (center[0] + nose_dir * (radius + 6), center[1])
    base_top = (center[0] + nose_dir * (radius - 4), center[1] - 5)
    base_bottom = (center[0] + nose_dir * (radius - 4), center[1] + 5)
    pygame.draw.polygon(screen, outline_color, [tip, base_top, base_bottom])

    bar_width = 70 if is_boss else 32
    ui.draw_hp_bar(screen, center[0], center[1] - size / 2 - 12,
                    m["hp"], m["max_hp"], bar_width=bar_width, bar_height=5)

    if is_boss:
        font = pygame.font.SysFont(None, 22)
        label = font.render("BOSS", True, config.BOSS_OUTLINE_COLOR)
        screen.blit(label, (center[0] - label.get_width() / 2, center[1] - size / 2 - 30))
