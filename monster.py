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


_XP_REWARDS = {
    "normal": config.XP_REWARD_NORMAL,
    "fast": config.XP_REWARD_FAST,
    "tank": config.XP_REWARD_TANK,
    "ranged": config.XP_REWARD_RANGED,
    "boss": config.XP_REWARD_BOSS,
}


def get_xp_reward(m):
    """몬스터를 처치했을 때 플레이어가 얻는 경험치를 종류에 따라 반환."""
    return _XP_REWARDS[m["type"]]


def _random_spawn_position(size, player):
    """플레이어와 너무 가깝지 않은 랜덤 위치를 찾아서 반환. size가 클수록(보스) 그만큼 맵 안쪽에서만 뽑힘."""
    px = player["x"] + config.PLAYER_DISPLAY_SIZE[0] / 2
    py = player["y"] + config.PLAYER_DISPLAY_SIZE[1] / 2

    while True:
        mx = random.randint(0, config.MAP_WIDTH - size)
        my = random.randint(0, config.MAP_HEIGHT - size)
        if math.hypot(mx - px, my - py) > 150:
            return mx, my


def _get_type_weights(stage):
    """스테이지가 오를수록 더 다양한 몬스터 종류가 섞여서 등장하도록 가중치를 조절.
    'normal'(추격형)은 항상 존재하고, 스테이지가 오를수록 fast -> tank -> ranged 순으로 합류함."""
    if stage <= 1:
        return {"normal": 70, "fast": 30}
    elif stage == 2:
        return {"normal": 45, "fast": 25, "tank": 30}
    else:
        return {"normal": 30, "fast": 20, "tank": 20, "ranged": 30}


def _pick_type(stage):
    weights = _get_type_weights(stage)
    return random.choices(list(weights.keys()), weights=list(weights.values()), k=1)[0]


def _create_monster(monster_type, stage, player):
    """종류(type)에 따라 크기/체력/속도/공격력이 다른 몬스터 하나를 만들어서 반환.
    모든 배율은 그 스테이지의 일반 몬스터 체력(base_hp)을 기준으로 계산."""
    base_hp = get_current_monster_max_hp(stage)

    if monster_type == "fast":
        size = round(config.MONSTER_SIZE * config.FAST_MONSTER_SIZE_MULTIPLIER)
        hp = base_hp * config.FAST_MONSTER_HP_MULTIPLIER
        speed = config.MONSTER_SPEED * config.FAST_MONSTER_SPEED_MULTIPLIER
        damage = config.DAMAGE_PER_HIT
    elif monster_type == "tank":
        size = round(config.MONSTER_SIZE * config.TANK_MONSTER_SIZE_MULTIPLIER)
        hp = base_hp * config.TANK_MONSTER_HP_MULTIPLIER
        speed = config.MONSTER_SPEED * config.TANK_MONSTER_SPEED_MULTIPLIER
        damage = config.DAMAGE_PER_HIT * config.TANK_MONSTER_DAMAGE_MULTIPLIER
    elif monster_type == "ranged":
        size = round(config.MONSTER_SIZE * config.RANGED_MONSTER_SIZE_MULTIPLIER)
        hp = base_hp * config.RANGED_MONSTER_HP_MULTIPLIER
        speed = config.MONSTER_SPEED * config.RANGED_MONSTER_SPEED_MULTIPLIER
        damage = config.DAMAGE_PER_HIT  # 근접 접촉 시 데미지 (투사체 데미지는 별도 계산)
    else:  # "normal"
        size = config.MONSTER_SIZE
        hp = base_hp
        speed = config.MONSTER_SPEED
        damage = config.DAMAGE_PER_HIT

    mx, my = _random_spawn_position(size, player)

    return {
        "x": mx, "y": my,
        "size": size,
        "hp": hp,
        "max_hp": hp,
        "damage": damage,
        "speed": speed,
        "type": monster_type,
        "is_boss": False,
        "facing_right": True,
        "knockback_timer": 0,
        "knockback_dx": 0,
        "knockback_dy": 0,
        "wiggle_timer": random.uniform(0, 6.28),           # fast 타입 지그재그 위상 (마리마다 다르게 시작)
        "attack_cooldown": random.randint(0, config.RANGED_ATTACK_COOLDOWN_FRAMES),  # ranged 타입 전용
    }


def spawn_wave(count, player, stage):
    """몬스터를 맵 안 랜덤한 위치에 count마리 배치. 스테이지에 따라 여러 종류가 섞여서 등장."""
    return [_create_monster(_pick_type(stage), stage, player) for _ in range(count)]


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
        "speed": config.MONSTER_SPEED,
        "type": "boss",
        "is_boss": True,
        "facing_right": True,
        "knockback_timer": 0,
        "knockback_dx": 0,
        "knockback_dy": 0,
        "wiggle_timer": 0,
        "attack_cooldown": 0,
    }
    return [boss]  # 다른 웨이브 함수들과 형태를 맞추기 위해 리스트로 감싸서 반환


def distance_to(m, target_x, target_y):
    """몬스터 중심에서 특정 좌표까지의 거리를 계산. 타겟 선택(더 가까운 쪽 쫓기)에 사용."""
    mx_center = m["x"] + m["size"] / 2
    my_center = m["y"] + m["size"] / 2
    return math.hypot(target_x - mx_center, target_y - my_center)


def _move_ranged(m, target_x, target_y):
    """ranged 타입 전용 이동: 너무 가까우면 물러나고, 멀면 다가가서 일정 거리를 유지.
    사거리 안이고 쿨타임이 다 됐으면 발사할 투사체 정보를 반환하고, 아니면 None을 반환."""
    mx_center = m["x"] + m["size"] / 2
    my_center = m["y"] + m["size"] / 2
    dx = target_x - mx_center
    dy = target_y - my_center
    distance = math.hypot(dx, dy)

    dir_x, dir_y = (dx / distance, dy / distance) if distance > 0 else (0, -1)

    if dir_x > 0.1:
        m["facing_right"] = True
    elif dir_x < -0.1:
        m["facing_right"] = False

    near_edge = config.RANGED_PREFERRED_DISTANCE - config.RANGED_DISTANCE_MARGIN
    far_edge = config.RANGED_PREFERRED_DISTANCE + config.RANGED_DISTANCE_MARGIN

    if distance > far_edge:
        m["x"] += dir_x * m["speed"]
        m["y"] += dir_y * m["speed"]
    elif distance < near_edge:
        m["x"] -= dir_x * m["speed"]
        m["y"] -= dir_y * m["speed"]
    # near_edge <= distance <= far_edge: 딱 좋은 거리이므로 멈춰서 사격에 집중

    if m["attack_cooldown"] > 0:
        m["attack_cooldown"] -= 1

    if m["attack_cooldown"] == 0 and distance <= config.RANGED_ATTACK_RANGE:
        m["attack_cooldown"] = config.RANGED_ATTACK_COOLDOWN_FRAMES
        return {
            "x": mx_center, "y": my_center,
            "dx": dir_x, "dy": dir_y,
            "damage": config.DAMAGE_PER_HIT * config.RANGED_PROJECTILE_DAMAGE_MULTIPLIER,
        }

    return None


def move_toward_target(m, target_center_x, target_center_y):
    """몬스터를 이동시킴. 넉백 중이면 넉백을, 아니면 종류(type)별 패턴으로 target을 향해 움직임.
    ranged 타입이 이번 프레임에 발사했다면 투사체 정보 딕셔너리를, 아니면 None을 반환."""
    projectile = None

    if m["knockback_timer"] > 0:
        m["x"] += m["knockback_dx"] * config.KNOCKBACK_SPEED
        m["y"] += m["knockback_dy"] * config.KNOCKBACK_SPEED
        m["knockback_timer"] -= 1
    elif m["type"] == "ranged":
        projectile = _move_ranged(m, target_center_x, target_center_y)
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

            if m["type"] == "fast":
                # 진행 방향에 수직인 벡터를 사인파로 섞어서 지그재그로 접근하게 만듦
                m["wiggle_timer"] += config.FAST_WIGGLE_SPEED
                wiggle = math.sin(m["wiggle_timer"]) * config.FAST_WIGGLE_AMOUNT
                perp_dx, perp_dy = -dy, dx
                dx += perp_dx * wiggle
                dy += perp_dy * wiggle
                norm = math.hypot(dx, dy)
                if norm > 0:
                    dx, dy = dx / norm, dy / norm

            m["x"] += dx * m["speed"]
            m["y"] += dy * m["speed"]

    # 넉백으로 맵 밖까지 밀려나지 않도록 위치 제한 (몬스터 자신의 크기 기준)
    m["x"] = max(0, min(m["x"], config.MAP_WIDTH - m["size"]))
    m["y"] = max(0, min(m["y"], config.MAP_HEIGHT - m["size"]))

    return projectile


def update_projectiles(projectiles):
    """모든 투사체를 이동시키고, 맵 밖으로 나간 것을 제거한 새 리스트를 반환."""
    survivors = []
    for p in projectiles:
        p["x"] += p["dx"] * config.RANGED_PROJECTILE_SPEED
        p["y"] += p["dy"] * config.RANGED_PROJECTILE_SPEED
        if 0 <= p["x"] <= config.MAP_WIDTH and 0 <= p["y"] <= config.MAP_HEIGHT:
            survivors.append(p)
    return survivors


def resolve_projectile_hits(projectiles, target_x, target_y, target_radius):
    """target(플레이어 또는 동료) 반경 안에 들어온 투사체를 명중 처리.
    (제거되고 남은 투사체 리스트, 이번에 받은 피해 총합)을 튜플로 반환."""
    survivors = []
    damage_taken = 0
    hit_radius = target_radius + config.RANGED_PROJECTILE_SIZE / 2

    for p in projectiles:
        distance = math.hypot(target_x - p["x"], target_y - p["y"])
        if distance < hit_radius:
            damage_taken += p["damage"]
        else:
            survivors.append(p)

    return survivors, damage_taken


def draw_projectiles(screen, projectiles, camera_x, camera_y):
    """모든 투사체를 화면에 그림."""
    radius = config.RANGED_PROJECTILE_SIZE // 2
    for p in projectiles:
        center = (int(p["x"] - camera_x), int(p["y"] - camera_y))
        pygame.draw.circle(screen, config.RANGED_PROJECTILE_COLOR, center, radius)
        pygame.draw.circle(screen, config.RANGED_MONSTER_OUTLINE_COLOR, center, radius, 1)


def draw(screen, m, camera_x, camera_y):
    """몬스터(또는 보스) 한 마리와 방향 표시, 체력바를 화면에 그림."""
    size = m["size"]
    is_boss = m["is_boss"]

    center = (int(m["x"] + size / 2 - camera_x), int(m["y"] + size / 2 - camera_y))

    if is_boss:
        body_color, outline_color, outline_width = config.BOSS_COLOR, config.BOSS_OUTLINE_COLOR, 3
    elif m["type"] == "fast":
        body_color, outline_color, outline_width = config.FAST_MONSTER_COLOR, config.FAST_MONSTER_OUTLINE_COLOR, 2
    elif m["type"] == "tank":
        body_color, outline_color, outline_width = config.TANK_MONSTER_COLOR, config.TANK_MONSTER_OUTLINE_COLOR, 2
    elif m["type"] == "ranged":
        body_color, outline_color, outline_width = config.RANGED_MONSTER_COLOR, config.RANGED_MONSTER_OUTLINE_COLOR, 2
    else:
        body_color, outline_color, outline_width = config.RED, config.DARK_RED, 2

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
