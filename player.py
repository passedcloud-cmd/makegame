"""
player.py — 플레이어(캐릭터) 관련 기능 모음
====================================================
플레이어는 monster.py의 몬스터처럼 "딕셔너리"로 상태를 관리합니다.
create_player()로 상태를 만들고, 매 프레임 handle_movement() 등을
호출해서 그 딕셔너리 안의 값을 바꿔가는 방식이에요.
"""

import pygame
import math
import config
import ui


def create_player():
    """플레이어의 초기 상태를 딕셔너리로 만들어서 반환."""
    return {
        "x": config.MAP_WIDTH // 2,
        "y": config.MAP_HEIGHT // 2,
        "hp": config.MAX_HP,

        "facing_dx": 0, "facing_dy": 1,   # 공격 부채꼴 방향 계산용 (모든 방향 포함)
        "facing_right": True,             # 좌우 이미지 반전 전용

        "is_moving": False,
        "anim_frame": 0,
        "anim_timer": 0,

        "is_attacking": False,
        "attack_anim_timer": 0,
        "attack_display_frame": 0,
        "attack_cooldown_timer": 0,
        "attack_flash_timer": 0,

        "invincible_timer": 0,

        # 넉백(피격 시 밀려나기) 상태 - 몬스터와 똑같은 패턴
        "knockback_timer": 0,
        "knockback_dx": 0,
        "knockback_dy": 0,
    }


def load_images():
    """
    플레이어 관련 이미지를 전부 불러와서 딕셔너리로 반환.
    반드시 pygame.display.set_mode()를 호출한 '뒤에' main.py에서 한 번만 실행해야 함.
    """
    def load_scaled(path):
        image = pygame.image.load(path).convert_alpha()
        return pygame.transform.scale(image, config.PLAYER_DISPLAY_SIZE)

    idle_right = load_scaled("assets/idle.png")
    idle_left = pygame.transform.flip(idle_right, True, False)

    walk_right = [load_scaled("assets/walk1.png"), load_scaled("assets/walk2.png")]
    walk_left = [pygame.transform.flip(img, True, False) for img in walk_right]

    attack_right = [load_scaled("assets/attack1.png"), load_scaled("assets/attack2.png")]
    attack_left = [pygame.transform.flip(img, True, False) for img in attack_right]

    return {
        "idle_right": idle_right, "idle_left": idle_left,
        "walk_right": walk_right, "walk_left": walk_left,
        "attack_right": attack_right, "attack_left": attack_left,
    }


def get_center(player):
    """플레이어 사각형의 정중앙 월드 좌표를 반환."""
    return (player["x"] + config.PLAYER_DISPLAY_SIZE[0] / 2,
            player["y"] + config.PLAYER_DISPLAY_SIZE[1] / 2)


def handle_movement(player, keys):
    """키 입력을 받아 이동, 방향(facing), 걷기 애니메이션 상태를 갱신."""

    # ── 경직 중이면: 실제로는 거의 안 움직이고, 조작만 잠깐 막음 (흔들림은 draw()에서 시각 효과로 처리) ──
    if player["knockback_timer"] > 0:
        player["knockback_timer"] -= 1
        player["is_moving"] = False
        player["anim_frame"] = 0
        return  # 경직 중엔 WASD 입력을 무시

    move_dx, move_dy = 0, 0
    speed = 4

    if keys[pygame.K_w]:
        player["y"] -= speed
        move_dy -= 1
    if keys[pygame.K_s]:
        player["y"] += speed
        move_dy += 1
    if keys[pygame.K_a]:
        player["x"] -= speed
        move_dx -= 1
    if keys[pygame.K_d]:
        player["x"] += speed
        move_dx += 1

    player["is_moving"] = False
    if move_dx != 0 or move_dy != 0:
        player["is_moving"] = True
        length = math.hypot(move_dx, move_dy)
        player["facing_dx"], player["facing_dy"] = move_dx / length, move_dy / length

    if move_dx > 0:
        player["facing_right"] = True
    elif move_dx < 0:
        player["facing_right"] = False

    # 맵 경계 안으로 위치 제한
    player["x"] = max(0, min(player["x"], config.MAP_WIDTH - config.PLAYER_DISPLAY_SIZE[0]))
    player["y"] = max(0, min(player["y"], config.MAP_HEIGHT - config.PLAYER_DISPLAY_SIZE[1]))

    if player["is_moving"]:
        player["anim_timer"] += 1
        if player["anim_timer"] >= 8:
            player["anim_frame"] = (player["anim_frame"] + 1) % 2
            player["anim_timer"] = 0
    else:
        player["anim_frame"] = 0


def start_attack(player):
    """스페이스바를 눌러 공격을 시작할 때 호출. 쿨다운 중이면 아무 일도 하지 않음."""
    if player["attack_cooldown_timer"] != 0:
        return False

    player["attack_cooldown_timer"] = config.ATTACK_COOLDOWN
    player["attack_flash_timer"] = 10
    player["is_attacking"] = True
    player["attack_anim_timer"] = 0
    return True


def update_timers(player):
    """공격 쿨다운, 공격 애니메이션 진행을 매 프레임 갱신."""
    if player["attack_cooldown_timer"] > 0:
        player["attack_cooldown_timer"] -= 1

    if player["is_attacking"]:
        player["attack_anim_timer"] += 1
        player["attack_display_frame"] = 0 if player["attack_anim_timer"] < config.ATTACK_ANIM_TOTAL / 2 else 1
        if player["attack_anim_timer"] >= config.ATTACK_ANIM_TOTAL:
            player["is_attacking"] = False
            player["attack_anim_timer"] = 0


def get_cone_points(center_x, center_y, radius, dir_x, dir_y, half_angle_deg=90, steps=16):
    """바라보는 방향 기준 전방 180도 부채꼴의 외곽선 좌표들을 계산 (그리기 전용)."""
    center_angle = math.atan2(dir_y, dir_x)
    half_angle_rad = math.radians(half_angle_deg)
    start_angle = center_angle - half_angle_rad
    end_angle = center_angle + half_angle_rad

    points = [(center_x, center_y)]
    for i in range(steps + 1):
        angle = start_angle + (end_angle - start_angle) * (i / steps)
        points.append((center_x + radius * math.cos(angle), center_y + radius * math.sin(angle)))
    return points


def resolve_attack(player, monsters):
    """
    공격 사정거리 + 전방 180도 안에 있는 몬스터에게 데미지와 넉백을 주고,
    체력이 남은 몬스터만 담은 새 리스트를 반환 (죽은 몬스터는 자동 제거).
    """
    px, py = get_center(player)
    survivors = []

    for m in monsters:
        mx_center = m["x"] + m["size"] / 2
        my_center = m["y"] + m["size"] / 2
        to_mx, to_my = mx_center - px, my_center - py
        distance = math.hypot(to_mx, to_my)

        in_range = distance <= config.ATTACK_RANGE
        dot = player["facing_dx"] * to_mx + player["facing_dy"] * to_my
        in_front = dot >= 0

        if in_range and in_front:
            m["hp"] -= config.ATTACK_DAMAGE

            if distance > 0:
                m["knockback_dx"] = to_mx / distance
                m["knockback_dy"] = to_my / distance
            else:
                m["knockback_dx"], m["knockback_dy"] = 1, 0
            m["knockback_timer"] = config.KNOCKBACK_DURATION

        if m["hp"] > 0:
            survivors.append(m)

    return survivors


def take_contact_damage(player, monsters):
    """몬스터와 닿아있으면 정확히 한 대만큼 피해를 주고, 무적 시간을 부여."""
    if player["invincible_timer"] > 0:
        player["invincible_timer"] -= 1

    px, py = get_center(player)

    for m in monsters:
        mx_center = m["x"] + m["size"] / 2
        my_center = m["y"] + m["size"] / 2
        distance = math.hypot(px - mx_center, py - my_center)
        touching_distance = (m["size"] / 2) + (config.PLAYER_DISPLAY_SIZE[0] / 2)

        if distance < touching_distance and player["invincible_timer"] == 0:
            # 방어력 특성 적용: 몬스터별 공격력(m["damage"])에 방어 배율을 곱해서 실제 피해량 계산
            actual_damage = m["damage"] * config.PLAYER_DEFENSE_MULTIPLIER
            player["hp"] -= actual_damage
            player["hp"] = max(0, player["hp"])
            player["invincible_timer"] = config.PLAYER_INVINCIBLE_DURATION  # 무적 시간은 기존 그대로

            # ── 경직(진동) 발동: 몬스터 -> 플레이어 방향을 저장해서 draw()에서 그 방향으로 살짝 떨리게 함 ──
            kb_dx, kb_dy = px - mx_center, py - my_center
            if distance > 0:
                player["knockback_dx"] = kb_dx / distance
                player["knockback_dy"] = kb_dy / distance
            else:
                player["knockback_dx"], player["knockback_dy"] = 0, -1  # 완전히 겹친 경우 기본값(위쪽)
            player["knockback_timer"] = config.PLAYER_STAGGER_DURATION


def draw(screen, player, images, camera_x, camera_y):
    """플레이어 스프라이트와 그 위의 체력바를 화면에 그림 (카메라 오프셋 반영)."""
    screen_x = player["x"] - camera_x
    screen_y = player["y"] - camera_y

    # ── 경직(진동) 중이면: 실제 위치는 그대로 두고, 그리는 위치만 아주 살짝 흔들리게 함 ──
    # 프레임이 지날 때마다 부호를 뒤집어서(+, -, +, -...) 짧게 떠는 느낌을 만듦
    if player["knockback_timer"] > 0:
        shake_sign = 1 if player["knockback_timer"] % 2 == 0 else -1
        shake_amount = shake_sign * config.PLAYER_STAGGER_AMPLITUDE
        screen_x += player["knockback_dx"] * shake_amount
        screen_y += player["knockback_dy"] * shake_amount

    if player["is_attacking"]:
        imgs = images["attack_right"] if player["facing_right"] else images["attack_left"]
        current_image = imgs[player["attack_display_frame"]]
    elif player["is_moving"]:
        imgs = images["walk_right"] if player["facing_right"] else images["walk_left"]
        current_image = imgs[player["anim_frame"]]
    else:
        current_image = images["idle_right"] if player["facing_right"] else images["idle_left"]

    screen.blit(current_image, (screen_x, screen_y))

    center_x = screen_x + config.PLAYER_DISPLAY_SIZE[0] / 2
    ui.draw_hp_bar(screen, center_x, screen_y - 14, player["hp"], config.MAX_HP, bar_width=40, bar_height=6)


def draw_attack_effect(screen, player, camera_x, camera_y):
    """공격 시 잠깐 보이는 전방 180도 부채꼴 이펙트를 그림."""
    if player["attack_flash_timer"] > 0:
        px, py = get_center(player)
        screen_x, screen_y = px - camera_x, py - camera_y
        cone_points = get_cone_points(screen_x, screen_y, config.ATTACK_RANGE, player["facing_dx"], player["facing_dy"])
        pygame.draw.lines(screen, config.GREEN, True, cone_points, 3)
        player["attack_flash_timer"] -= 1
