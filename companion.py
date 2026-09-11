"""
companion.py — 보호 대상(동료) 캐릭터 담당
====================================================
플레이어를 졸졸 따라다니는 캐릭터입니다. player.py와 똑같이 딕셔너리로
상태를 관리하고, 몬스터에게 닿으면 체력이 깎이고 잠깐 넉백당합니다.
이 캐릭터의 체력이 0이 되면 "보호 실패"로 게임 오버가 됩니다.

아직 전용 그림이 없어서 사각형 도형 + 방향 삼각형으로 표시합니다.
나중에 그림이 생기면 player.py의 load_facing_pair() 패턴을 그대로 적용하면 됩니다.
"""

import pygame
import math
import config
import ui


def create_companion(player):
    """플레이어 바로 옆에서 시작하는 동료 캐릭터 상태를 생성."""
    return {
        "x": player["x"] - 50,
        "y": player["y"],
        "hp": config.COMPANION_MAX_HP,

        "facing_right": True,
        "is_moving": False,

        "invincible_timer": 0,
        "knockback_timer": 0,
        "knockback_dx": 0,
        "knockback_dy": 0,

        # 자가 힐 패시브 스킬 관련
        "heal_timer": 0,        # 다음 회복까지 몇 프레임 지났는지 (COMPANION_HEAL_INTERVAL_FRAMES에 도달하면 회복)
        "heal_flash_timer": 0,  # 회복 이펙트("+8" 표시)를 잠깐 보여주기 위한 타이머
    }


def get_center(companion):
    return (companion["x"] + config.COMPANION_SIZE / 2,
            companion["y"] + config.COMPANION_SIZE / 2)


def update_follow(companion, player):
    """넉백 중이 아니면, 플레이어 뒤쪽의 목표 지점을 향해 따라 이동."""
    if companion["knockback_timer"] > 0:
        companion["x"] += companion["knockback_dx"] * config.KNOCKBACK_SPEED
        companion["y"] += companion["knockback_dy"] * config.KNOCKBACK_SPEED
        companion["knockback_timer"] -= 1
        companion["is_moving"] = False
    else:
        # 목표 지점: 플레이어가 "바라보는 반대 방향"으로 일정 거리 떨어진 곳
        # -> 플레이어가 어느 방향을 향하든 항상 그 뒤쪽에서 따라오는 느낌을 줌
        target_x = player["x"] - player["facing_dx"] * config.COMPANION_FOLLOW_DISTANCE
        target_y = player["y"] - player["facing_dy"] * config.COMPANION_FOLLOW_DISTANCE

        dx = target_x - companion["x"]
        dy = target_y - companion["y"]
        distance = math.hypot(dx, dy)

        if distance > config.COMPANION_FOLLOW_DEAD_ZONE:
            dx, dy = dx / distance, dy / distance
            companion["x"] += dx * config.COMPANION_FOLLOW_SPEED
            companion["y"] += dy * config.COMPANION_FOLLOW_SPEED
            companion["is_moving"] = True

            if dx > 0.1:
                companion["facing_right"] = True
            elif dx < -0.1:
                companion["facing_right"] = False
        else:
            # 목표 지점에 거의 도착했으면 멈춤 (계속 미세 조정하면 캐릭터가 부들부들 떪)
            companion["is_moving"] = False

    companion["x"] = max(0, min(companion["x"], config.MAP_WIDTH - config.COMPANION_SIZE))
    companion["y"] = max(0, min(companion["y"], config.MAP_HEIGHT - config.COMPANION_SIZE))


def update_passive_heal(companion):
    """
    자가 힐 패시브 스킬: COMPANION_HEAL_INTERVAL_FRAMES(5초)마다
    체력을 COMPANION_HEAL_AMOUNT만큼 자동으로 회복시킴 (최대 체력을 넘지 않음).
    """
    companion["heal_timer"] += 1
    if companion["heal_timer"] >= config.COMPANION_HEAL_INTERVAL_FRAMES:
        companion["heal_timer"] = 0
        before_hp = companion["hp"]
        companion["hp"] = min(config.COMPANION_MAX_HP, companion["hp"] + config.COMPANION_HEAL_AMOUNT)
        if companion["hp"] > before_hp:
            companion["heal_flash_timer"] = 30  # 회복 이펙트를 0.5초 동안 표시

    if companion["heal_flash_timer"] > 0:
        companion["heal_flash_timer"] -= 1


def take_contact_damage(companion, monsters):
    """몬스터와 닿으면 정확히 한 대만큼 피해를 주고, 무적시간 + 넉백을 부여."""
    if companion["invincible_timer"] > 0:
        companion["invincible_timer"] -= 1

    cx, cy = get_center(companion)

    for m in monsters:
        mx_center = m["x"] + m["size"] / 2
        my_center = m["y"] + m["size"] / 2
        distance = math.hypot(cx - mx_center, cy - my_center)
        touching_distance = (m["size"] / 2) + (config.COMPANION_SIZE / 2)

        if distance < touching_distance and companion["invincible_timer"] == 0:
            companion["hp"] -= m["damage"]  # 몬스터별 공격력 (보스는 3배)
            companion["hp"] = max(0, companion["hp"])
            companion["invincible_timer"] = config.PLAYER_INVINCIBLE_DURATION

            # 넉백: 몬스터 -> 동료 방향으로 밀려남 (몬스터와 동일한 세기)
            kb_dx, kb_dy = cx - mx_center, cy - my_center
            if distance > 0:
                companion["knockback_dx"] = kb_dx / distance
                companion["knockback_dy"] = kb_dy / distance
            else:
                companion["knockback_dx"], companion["knockback_dy"] = 0, -1
            companion["knockback_timer"] = config.KNOCKBACK_DURATION


def draw(screen, companion, camera_x, camera_y):
    """동료 캐릭터를 화면에 그림 (도형 + 방향 표시 + 체력바)."""
    screen_x = companion["x"] - camera_x
    screen_y = companion["y"] - camera_y

    rect = pygame.Rect(int(screen_x), int(screen_y), config.COMPANION_SIZE, config.COMPANION_SIZE)
    pygame.draw.rect(screen, config.COMPANION_COLOR, rect, border_radius=6)
    pygame.draw.rect(screen, config.BLACK, rect, 2, border_radius=6)

    # 몬스터의 '코'와 같은 방식으로 바라보는 방향을 작은 삼각형으로 표시
    center_x = int(screen_x + config.COMPANION_SIZE / 2)
    center_y = int(screen_y + config.COMPANION_SIZE / 2)
    nose_dir = 1 if companion["facing_right"] else -1
    half = config.COMPANION_SIZE // 2
    tip = (center_x + nose_dir * (half + 6), center_y)
    base_top = (center_x + nose_dir * (half - 4), center_y - 5)
    base_bottom = (center_x + nose_dir * (half - 4), center_y + 5)
    pygame.draw.polygon(screen, config.BLACK, [tip, base_top, base_bottom])

    ui.draw_hp_bar(screen, screen_x + config.COMPANION_SIZE / 2, screen_y - 14,
                    companion["hp"], config.COMPANION_MAX_HP, bar_width=40, bar_height=6)

    # 회복 직후 잠깐 "+8" 텍스트를 위로 떠오르듯 표시 (패시브 스킬 발동을 눈으로 확인하기 위함)
    if companion["heal_flash_timer"] > 0:
        # 30프레임 동안 위로 살짝 떠오르면서 서서히 사라지는 느낌을 줌
        rise_offset = (30 - companion["heal_flash_timer"]) * 0.6
        font = pygame.font.SysFont(None, 24)
        heal_text = font.render(f"+{config.COMPANION_HEAL_AMOUNT}", True, config.GREEN)
        screen.blit(heal_text, (screen_x + config.COMPANION_SIZE / 2 - heal_text.get_width() / 2,
                                 screen_y - 30 - rise_offset))
