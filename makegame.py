"""
WASD 이동 + 애니메이션 + 몬스터 배치 & 충돌 처리
====================================================
이전 코드에서 추가된 부분만 정리하면:

1. 몬스터 여러 마리를 "리스트"로 관리 (딕셔너리를 담은 리스트)
2. 몬스터가 매 프레임마다 플레이어 쪽으로 조금씩 다가옴
3. 스페이스바를 누르면 플레이어 주변 일정 범위의 몬스터가 사라짐 (공격)
4. 몬스터가 플레이어에게 닿아있으면 체력(HP)이 서서히 줄어듦 (피격)
5. 몬스터를 모두 처치하면 "스테이지 클리어" 문구 표시

화면에 그림을 그리는 방식(이미지 불러오기, blit)은 지난 코드와 동일합니다.
"""

import pygame
import random
import math

# ── 1. 기본 설정 ─────────────────────────────────────
pygame.init()

SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("WASD 이동 + 몬스터 배치 & 충돌 처리")

# 맵(월드) 전체 크기. 화면(SCREEN_WIDTH x SCREEN_HEIGHT)보다 훨씬 커서
# 플레이어가 이동하면 화면에 안 보이던 부분이 새로 보이게 됨.
MAP_WIDTH = 2400
MAP_HEIGHT = 1800

clock = pygame.time.Clock()
FPS = 60

WHITE = (255, 255, 255)
RED = (200, 40, 40)
DARK_RED = (140, 20, 20)
BLACK = (20, 20, 20)
GREEN = (40, 180, 80)


# ── 2. 이미지 불러오기 ────────────────────────────────
PLAYER_DISPLAY_SIZE = (40, 40)


def load_scaled_image(path, size):
    """이미지 파일을 불러온 뒤, 지정한 크기로 고정해서 반환하는 함수."""
    image = pygame.image.load(path).convert_alpha()
    return pygame.transform.scale(image, size)


def load_facing_pair(path, size):
    """
    이미지를 불러와서 (오른쪽을 보는 원본, 왼쪽을 보는 반전본) 한 쌍으로 반환.
    캐릭터 그림은 보통 '오른쪽을 보는 모습'으로 그렸다고 가정하고,
    왼쪽 이미지는 pygame.transform.flip()으로 좌우를 거울처럼 뒤집어서
    별도 그림 파일 없이 만들어냅니다. (첫 번째 True = 좌우 반전, 두 번째 False = 상하 반전 안 함)
    """
    right_image = load_scaled_image(path, size)
    left_image = pygame.transform.flip(right_image, True, False)
    return right_image, left_image


idle_right, idle_left = load_facing_pair("assets/idle.png", PLAYER_DISPLAY_SIZE)

walk_right_images = [
    load_scaled_image("assets/walk1.png", PLAYER_DISPLAY_SIZE),
    load_scaled_image("assets/walk2.png", PLAYER_DISPLAY_SIZE),
]
walk_left_images = [pygame.transform.flip(img, True, False) for img in walk_right_images]

# 공격 모션용 이미지 2장 (예: 팔을 뻗기 시작 -> 최대로 뻗은 자세)
# 아직 직접 그린 공격 그림이 없다면, 테스트용 색깔 이미지가 assets 폴더에 들어있습니다.
# 나중에 실제로 그린 attack1.png, attack2.png로 같은 이름으로 교체하면 코드 수정 없이 바로 적용됩니다.
attack_right_images = [
    load_scaled_image("assets/attack1.png", PLAYER_DISPLAY_SIZE),
    load_scaled_image("assets/attack2.png", PLAYER_DISPLAY_SIZE),
]
attack_left_images = [pygame.transform.flip(img, True, False) for img in attack_right_images]

# 몬스터는 아직 그림 파일이 없다고 가정하고, 빨간 원 + 방향을 나타내는 작은 삼각형으로 표현합니다.
# 나중에 몬스터 그림이 생기면 player처럼 load_facing_pair()로 불러와서
# draw_monster() 함수 안의 pygame.draw.circle(...) 부분만 screen.blit(...)로 바꾸면 됩니다.
# 배경 이미지는 맵 전체 크기(MAP_WIDTH x MAP_HEIGHT)로 만들어져 있다고 가정.
# 화면 크기로 늘리거나 줄이지 않고, 원본 크기 그대로 불러와서 카메라가 필요한 부분만 잘라서 보여줌.
background_image = pygame.image.load("assets/backgrounds/stage1_bg.png").convert()

MONSTER_SIZE = 32  # 지름(px). 캐릭터(40px)보다 살짝 작게 설정


# ── 3. 캐릭터(플레이어) 정보 ──────────────────────────
# player_x, player_y는 이제 "화면 좌표"가 아니라 "맵(월드) 전체 기준 좌표"입니다.
# 화면에 그릴 때는 카메라 위치만큼 빼서 계산합니다 (아래 게임 루프의 camera_x, camera_y 참고).
player_x = MAP_WIDTH // 2
player_y = MAP_HEIGHT // 2
player_speed = 4

is_moving = False
anim_frame = 0
anim_timer = 0
ANIM_SPEED = 8

MAX_HP = 100
player_hp = MAX_HP  # 체력. 0이 되면 게임 오버

# ── 난이도 설계: "몇 번 맞으면 죽는지"로 체력을 정함 ──
HITS_TO_DIE = 10                        # 플레이어는 몬스터에게 10번 닿으면 사망
DAMAGE_PER_HIT = MAX_HP / HITS_TO_DIE   # 한 번 맞을 때 깎이는 체력 (100/10 = 10)

# 몬스터에 닿아있는 "매 프레임"마다 맞은 것으로 치면 순식간에 죽어버리므로,
# 한 번 맞으면 짧은 시간 동안 다시 맞지 않는 "무적 시간"을 둡니다.
PLAYER_INVINCIBLE_DURATION = 30  # 무적 시간 (프레임 수). 60FPS 기준 약 0.5초
player_invincible_timer = 0

# 공격 관련 변수
ATTACK_RANGE = 70       # 공격이 닿는 반경(px)
ATTACK_COOLDOWN = 20    # 공격 후 다시 공격 가능해지기까지 걸리는 프레임 수
attack_cooldown_timer = 0
attack_flash_timer = 0  # 공격 이펙트(부채꼴)를 잠깐 보여주기 위한 타이머

# 플레이어가 "바라보는 방향"을 저장하는 벡터. (0, 1)은 아래쪽을 의미.
# 이동 키를 누를 때마다 이 값을 갱신해서, 마지막으로 움직인 방향을 계속 기억하게 함.
# (이 값은 공격 부채꼴 방향 계산에 쓰임 - 위/아래/대각선 등 모든 방향 포함)
facing_dx, facing_dy = 0, 1

# 반면 facing_right는 "좌우 이미지 반전"만을 위한 값으로, True/False 둘 중 하나만 가짐.
# 위/아래로만 움직일 때는 바뀌지 않고, 마지막으로 좌우로 움직인 방향을 계속 유지합니다.
facing_right = True

# 공격 모션(애니메이션) 상태 관리용 변수
ATTACK_ANIM_TOTAL = 12   # 공격 모션이 총 몇 프레임 동안 재생되는지
is_attacking = False     # 지금 공격 모션을 재생 중인지
attack_anim_timer = 0    # 공격 모션이 시작된 뒤 몇 프레임이 지났는지


def get_player_center():
    """플레이어 사각형의 정중앙 좌표를 계산해서 반환. 거리 계산에 사용."""
    return (player_x + PLAYER_DISPLAY_SIZE[0] / 2,
            player_y + PLAYER_DISPLAY_SIZE[1] / 2)


def draw_player(x, y, moving, frame, facing_right, attacking, attack_frame):
    """
    캐릭터를 화면에 그리는 함수.
    상태 우선순위: 공격 중 > 이동 중 > 가만히 있음
    같은 상태라도 facing_right 값에 따라 오른쪽/왼쪽 이미지 중 하나를 고름.
    """
    if attacking:
        images = attack_right_images if facing_right else attack_left_images
        current_image = images[attack_frame]
    elif moving:
        images = walk_right_images if facing_right else walk_left_images
        current_image = images[frame]
    else:
        current_image = idle_right if facing_right else idle_left

    screen.blit(current_image, (x, y))


# ── 4. 몬스터 정보 ────────────────────────────────────
# 몬스터 하나하나를 딕셔너리로 표현하고, 여러 마리를 리스트에 담아서 관리합니다.
# 예: {"x": 100, "y": 200} 처럼 위치 정보를 가짐

MONSTER_COUNT = 6      # 스테이지에 등장할 몬스터 수 (적게 유지)
MONSTER_SPEED = 1.3    # 몬스터가 플레이어를 향해 다가오는 속도

# ── 난이도 설계: 스테이지가 올라갈수록 몬스터가 더 단단해짐 ──
BASE_MONSTER_HP = 100        # 1스테이지 몬스터 체력
MONSTER_HP_PER_STAGE = 50    # 스테이지 하나 올라갈 때마다 몬스터 최대 체력 증가량
ATTACK_DAMAGE = 40           # 플레이어 공격 데미지 (스테이지가 올라도 이 값은 그대로 유지)
# -> 1스테이지: 100 / 40 = 3번 공격이면 처치 (100→60→20→사망)
# -> 2스테이지부터는 몬스터 체력만 늘어나므로 자연스럽게 더 여러 번 때려야 죽게 됨

current_stage = 1  # 지금 몇 번째 스테이지인지


def get_current_monster_max_hp():
    """지금 스테이지 기준으로 몬스터가 가져야 할 최대 체력을 계산."""
    return BASE_MONSTER_HP + (current_stage - 1) * MONSTER_HP_PER_STAGE


def spawn_monsters(count):
    """몬스터를 화면 안 랜덤한 위치에 배치하되, 플레이어 시작 위치와는 멀리 떨어뜨려서 생성."""
    monsters = []
    px, py = get_player_center()

    while len(monsters) < count:
        mx = random.randint(0, MAP_WIDTH - MONSTER_SIZE)
        my = random.randint(0, MAP_HEIGHT - MONSTER_SIZE)

        # 플레이어와 너무 가까운 곳에 스폰되지 않도록 거리 체크
        distance = math.hypot(mx - px, my - py)
        if distance > 150:
            # 지금 스테이지 기준 최대 체력을 계산해서, hp와 max_hp에 함께 저장
            # (max_hp를 따로 저장해두는 이유: 스테이지마다 몬스터 체력이 달라서
            #  체력바를 그릴 때 "이 몬스터의 원래 체력"을 알아야 정확한 비율이 나옴)
            monster_max_hp = get_current_monster_max_hp()
            monsters.append({
                "x": mx, "y": my,
                "hp": monster_max_hp,
                "max_hp": monster_max_hp,
                "facing_right": True,
            })

    return monsters


monsters = spawn_monsters(MONSTER_COUNT)


def get_cone_points(center_x, center_y, radius, dir_x, dir_y, half_angle_deg=90, steps=16):
    """
    플레이어가 바라보는 방향(dir_x, dir_y)을 중심으로,
    좌우로 half_angle_deg만큼씩 펼쳐진 부채꼴의 외곽선 좌표들을 계산해서 반환.
    half_angle_deg=90 이면 좌우 합쳐서 총 180도 범위가 됨.
    이 함수는 '공격 범위를 화면에 그리는 용도'로만 쓰임 (판정은 아래 내적 계산으로 따로 함).
    """
    center_angle = math.atan2(dir_y, dir_x)  # 바라보는 방향을 각도(라디안)로 변환
    half_angle_rad = math.radians(half_angle_deg)
    start_angle = center_angle - half_angle_rad
    end_angle = center_angle + half_angle_rad

    points = [(center_x, center_y)]  # 부채꼴은 중심점에서부터 시작
    for i in range(steps + 1):
        angle = start_angle + (end_angle - start_angle) * (i / steps)
        px = center_x + radius * math.cos(angle)
        py = center_y + radius * math.sin(angle)
        points.append((px, py))

    return points


def draw_hp_bar(center_x, top_y, current_hp, max_hp, bar_width=40, bar_height=6):
    """
    캐릭터 머리 위에 체력바를 그리는 공용 함수.
    center_x, top_y: 체력바를 놓을 기준 위치 (캐릭터의 가로 중앙, 캐릭터보다 살짝 위)
    current_hp / max_hp: 현재 체력 비율을 계산해서 초록 막대 길이를 정함
    """
    ratio = max(0, current_hp / max_hp)  # 0.0 ~ 1.0 사이 비율

    bar_x = int(center_x - bar_width / 2)
    bar_y = int(top_y)

    # 뒷배경(회색) -> 현재 체력만큼 앞쪽(초록~빨강)을 겹쳐 그리는 방식
    pygame.draw.rect(screen, (180, 180, 180), (bar_x, bar_y, bar_width, bar_height))

    # 체력 비율에 따라 색을 초록 -> 빨강으로 바꿔서, 위험할 때 시각적으로 눈에 띄게 함
    if ratio > 0.5:
        bar_color = GREEN
    elif ratio > 0.2:
        bar_color = (230, 180, 30)  # 주황
    else:
        bar_color = RED

    pygame.draw.rect(screen, bar_color, (bar_x, bar_y, int(bar_width * ratio), bar_height))
    pygame.draw.rect(screen, BLACK, (bar_x, bar_y, bar_width, bar_height), 1)  # 테두리


def draw_monster(m, camera_x, camera_y):
    """
    몬스터 한 마리와 그 위의 체력바를 화면에 그리는 함수.
    m['x'], m['y']는 월드 좌표이므로, 화면에 그릴 땐 camera_x, camera_y만큼 뺀 위치를 사용.
    """
    center = (int(m["x"] + MONSTER_SIZE / 2 - camera_x), int(m["y"] + MONSTER_SIZE / 2 - camera_y))
    pygame.draw.circle(screen, RED, center, MONSTER_SIZE // 2)
    pygame.draw.circle(screen, DARK_RED, center, MONSTER_SIZE // 2, 2)  # 테두리

    # 아직 몬스터 그림이 없으므로, 바라보는 방향을 작은 삼각형("코")으로 표시.
    # facing_right가 True면 오른쪽, False면 왼쪽으로 삼각형이 튀어나오게 그림.
    # 나중에 실제 몬스터 이미지가 생기면 이 삼각형 코드 대신 좌우 반전된 이미지를 그리면 됩니다.
    nose_dir = 1 if m["facing_right"] else -1
    radius = MONSTER_SIZE // 2
    tip = (center[0] + nose_dir * (radius + 6), center[1])
    base_top = (center[0] + nose_dir * (radius - 4), center[1] - 5)
    base_bottom = (center[0] + nose_dir * (radius - 4), center[1] + 5)
    pygame.draw.polygon(screen, DARK_RED, [tip, base_top, base_bottom])

    # 몬스터 원 바로 위에 체력바 표시 (스테이지마다 다른 max_hp를 정확히 반영)
    draw_hp_bar(center[0], center[1] - MONSTER_SIZE / 2 - 12, m["hp"], m["max_hp"], bar_width=32, bar_height=5)


def move_monster_toward_player(m):
    """몬스터를 플레이어 방향으로 한 프레임만큼 이동시키는 함수."""
    px, py = get_player_center()
    mx_center = m["x"] + MONSTER_SIZE / 2
    my_center = m["y"] + MONSTER_SIZE / 2

    # 플레이어 방향 벡터 (얼마나 오른쪽/아래로 가야 하는지)
    dx = px - mx_center
    dy = py - my_center
    distance = math.hypot(dx, dy)

    # 좌우로 이동하는 쪽으로만 facing_right 갱신 (플레이어와 완전히 같은 x좌표일 땐 유지)
    if dx > 0.5:
        m["facing_right"] = True
    elif dx < -0.5:
        m["facing_right"] = False

    if distance > 1:  # 0으로 나누는 것을 방지
        # 방향을 "길이 1짜리 화살표"로 정규화한 뒤, 속도만큼만 이동
        dx, dy = dx / distance, dy / distance
        m["x"] += dx * MONSTER_SPEED
        m["y"] += dy * MONSTER_SPEED


# ── 5. 텍스트 표시 준비 ───────────────────────────────
pygame.font.init()
font = pygame.font.SysFont(None, 32)
big_font = pygame.font.SysFont(None, 64)


def draw_hud():
    """화면 상단에 스테이지, 남은 몬스터 수, 체력(남은 타격 횟수)을 표시."""
    hits_left = math.ceil(player_hp / DAMAGE_PER_HIT) if player_hp > 0 else 0
    stage_text = font.render(f"스테이지: {current_stage}", True, BLACK)
    hp_text = font.render(f"HP: {int(player_hp)}  (남은 목숨 {hits_left}번)", True, BLACK)
    monster_text = font.render(f"남은 몬스터: {len(monsters)}", True, BLACK)
    screen.blit(stage_text, (10, 10))
    screen.blit(hp_text, (10, 40))
    screen.blit(monster_text, (10, 70))


# ── 6. 게임 루프 ─────────────────────────────────────
running = True
while running:

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    keys = pygame.key.get_pressed()
    is_moving = False

    # 게임 오버나 스테이지 클리어 상태에서는 이동/공격을 막고 싶다면
    # 아래 조건을 활용할 수 있습니다. (지금은 계속 조작 가능하게 둠)
    game_over = player_hp <= 0
    stage_clear = len(monsters) == 0

    if not game_over:
        # 이번 프레임에 눌린 방향키들을 하나의 (move_dx, move_dy) 벡터로 합침
        move_dx, move_dy = 0, 0
        if keys[pygame.K_w]:
            player_y -= player_speed
            move_dy -= 1
        if keys[pygame.K_s]:
            player_y += player_speed
            move_dy += 1
        if keys[pygame.K_a]:
            player_x -= player_speed
            move_dx -= 1
        if keys[pygame.K_d]:
            player_x += player_speed
            move_dx += 1

        if move_dx != 0 or move_dy != 0:
            is_moving = True
            # 대각선 이동(예: W+D)일 때도 방향이 정확히 향하도록 벡터 길이를 1로 정규화
            length = math.hypot(move_dx, move_dy)
            facing_dx, facing_dy = move_dx / length, move_dy / length
            # facing_dx, facing_dy는 "마지막으로 움직인 방향"이라 키를 떼도 값이 유지됨
            # -> 제자리에 멈춰서도 방금 보던 방향을 계속 바라보게 됨

        # 좌우로 움직였을 때만 facing_right 갱신 (W/S만 눌렀을 땐 기존 방향 유지)
        if move_dx > 0:
            facing_right = True
        elif move_dx < 0:
            facing_right = False

    player_x = max(0, min(player_x, MAP_WIDTH - PLAYER_DISPLAY_SIZE[0]))
    player_y = max(0, min(player_y, MAP_HEIGHT - PLAYER_DISPLAY_SIZE[1]))

    if is_moving:
        anim_timer += 1
        if anim_timer >= ANIM_SPEED:
            anim_frame = (anim_frame + 1) % len(walk_right_images)
            anim_timer = 0
    else:
        anim_frame = 0

    # ── 공격 처리 ──
    # 스페이스바를 누르고, 쿨다운이 다 찼을 때만 공격 가능
    if attack_cooldown_timer > 0:
        attack_cooldown_timer -= 1

    if keys[pygame.K_SPACE] and attack_cooldown_timer == 0 and not game_over:
        attack_cooldown_timer = ATTACK_COOLDOWN
        attack_flash_timer = 10  # 공격 범위를 10프레임 동안 화면에 표시

        # 공격 모션 애니메이션 시작 (처음부터 다시 재생)
        is_attacking = True
        attack_anim_timer = 0

        px, py = get_player_center()
        survivors = []  # 이번 공격 이후에도 살아남은(hp가 남은) 몬스터만 다시 담을 리스트

        for m in monsters:
            mx_center = m["x"] + MONSTER_SIZE / 2
            my_center = m["y"] + MONSTER_SIZE / 2

            # 플레이어 -> 몬스터 방향 벡터
            to_mx = mx_center - px
            to_my = my_center - py
            # 지난번에 설명드린 "두 점 사이 거리" 공식: 루트((x차이)^2 + (y차이)^2)
            distance = math.hypot(to_mx, to_my)

            in_range = distance <= ATTACK_RANGE

            # ── 내적(dot product)으로 "앞쪽 180도 안에 있는지" 판정 ──
            # 내적 = facing_dx*to_mx + facing_dy*to_my
            # 두 방향이 같은 쪽을 가리킬수록 내적 값이 크고 양수(+),
            # 정확히 90도로 꺾이면 0, 그보다 더 뒤쪽이면 음수(-)가 됨.
            # 즉 "내적 >= 0" 이라는 조건 하나가 곧 "바라보는 방향 기준 좌우 90도씩,
            # 총 180도 범위 안에 있다"는 뜻과 정확히 같습니다.
            dot = facing_dx * to_mx + facing_dy * to_my
            in_front = dot >= 0

            if in_range and in_front:
                m["hp"] -= ATTACK_DAMAGE  # 사정거리 + 전방 180도 안에 있으면 데미지

            if m["hp"] > 0:
                survivors.append(m)  # 체력이 남아있으면 생존
            # 체력이 0 이하면 survivors에 안 담기므로 자동으로 제거됨(=처치)

        monsters = survivors

    # ── 몬스터 이동 & 플레이어 피격 판정 ──
    if player_invincible_timer > 0:
        player_invincible_timer -= 1

    if not stage_clear and not game_over:
        px, py = get_player_center()
        for m in monsters:
            move_monster_toward_player(m)

            mx_center = m["x"] + MONSTER_SIZE / 2
            my_center = m["y"] + MONSTER_SIZE / 2
            distance = math.hypot(px - mx_center, py - my_center)

            # 몬스터 반지름 + 플레이어 반지름보다 가까우면 "닿았다"고 판정
            touching_distance = (MONSTER_SIZE / 2) + (PLAYER_DISPLAY_SIZE[0] / 2)

            # 닿았고 + 무적 시간이 아닐 때만 "한 대 맞은 것"으로 처리
            if distance < touching_distance and player_invincible_timer == 0:
                player_hp -= DAMAGE_PER_HIT  # 정확히 한 번의 타격만큼만 감소
                player_hp = max(0, player_hp)
                player_invincible_timer = PLAYER_INVINCIBLE_DURATION  # 잠깐 무적

    # ── 공격 애니메이션 진행 갱신 ──
    # 공격이 시작된 뒤 ATTACK_ANIM_TOTAL 프레임이 지나면 원래 자세로 자동 복귀
    attack_display_frame = 0
    if is_attacking:
        attack_anim_timer += 1
        # 앞 절반은 attack_images[0](팔 뻗기 시작), 뒷 절반은 [1](최대로 뻗은 자세)
        attack_display_frame = 0 if attack_anim_timer < ATTACK_ANIM_TOTAL / 2 else 1
        if attack_anim_timer >= ATTACK_ANIM_TOTAL:
            is_attacking = False
            attack_anim_timer = 0

    # ── 카메라 위치 계산 ──
    # 카메라는 항상 플레이어가 화면 정중앙에 오도록 위치를 계산.
    # (카메라_x, 카메라_y) = "화면 왼쪽 위 모서리가 맵의 어느 좌표를 보고 있는지"
    px, py = get_player_center()
    camera_x = px - SCREEN_WIDTH / 2
    camera_y = py - SCREEN_HEIGHT / 2

    # 맵 가장자리에서는 화면 밖(맵 바깥의 검은 여백)이 보이지 않도록 카메라 범위를 제한
    camera_x = max(0, min(camera_x, MAP_WIDTH - SCREEN_WIDTH))
    camera_y = max(0, min(camera_y, MAP_HEIGHT - SCREEN_HEIGHT))

    # ── 화면 그리기 ──
    # 배경 이미지에서 카메라가 보고 있는 부분(화면 크기만큼)만 잘라서 그림
    # area 옵션을 쓰면 큰 이미지 전체를 옮기지 않고 필요한 부분만 빠르게 그릴 수 있음
    visible_area = pygame.Rect(camera_x, camera_y, SCREEN_WIDTH, SCREEN_HEIGHT)
    screen.blit(background_image, (0, 0), area=visible_area)

    for m in monsters:
        draw_monster(m, camera_x, camera_y)

    # 플레이어는 월드 좌표(player_x, player_y)에서 카메라만큼 뺀 화면 좌표에 그림
    draw_player(player_x - camera_x, player_y - camera_y, is_moving, anim_frame, facing_right, is_attacking, attack_display_frame)

    # 플레이어 머리 위 체력바도 화면 좌표(카메라 반영)로 그림
    player_screen_center_x = px - camera_x
    player_screen_top_y = player_y - camera_y
    draw_hp_bar(player_screen_center_x, player_screen_top_y - 14, player_hp, MAX_HP, bar_width=40, bar_height=6)

    # 공격 범위(전방 180도 부채꼴)를 잠깐 표시 (시각적 피드백) - 이것도 화면 좌표 기준
    if attack_flash_timer > 0:
        cone_points = get_cone_points(player_screen_center_x, py - camera_y, ATTACK_RANGE, facing_dx, facing_dy)
        pygame.draw.lines(screen, GREEN, True, cone_points, 3)  # True = 마지막 점과 첫 점을 이어서 닫힌 도형으로 그림
        attack_flash_timer -= 1

    draw_hud()

    if stage_clear:
        msg = big_font.render("STAGE CLEAR!", True, GREEN)
        screen.blit(msg, (SCREEN_WIDTH // 2 - msg.get_width() // 2, SCREEN_HEIGHT // 2 - 30))
    elif game_over:
        msg = big_font.render("GAME OVER", True, RED)
        screen.blit(msg, (SCREEN_WIDTH // 2 - msg.get_width() // 2, SCREEN_HEIGHT // 2 - 30))

    pygame.display.flip()
    clock.tick(FPS)

pygame.quit()