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
 
 
idle_image = load_scaled_image("assets/idle.png", PLAYER_DISPLAY_SIZE)
walk_images = [
    load_scaled_image("assets/walk1.png", PLAYER_DISPLAY_SIZE),
    load_scaled_image("assets/walk2.png", PLAYER_DISPLAY_SIZE),
]
 
# 몬스터는 아직 그림 파일이 없다고 가정하고, 빨간 원으로 표현합니다.
# 나중에 몬스터 그림이 생기면 player처럼 load_scaled_image()로 불러와서
# draw_monster() 함수 안의 pygame.draw.circle(...) 부분만 screen.blit(...)로 바꾸면 됩니다.
MONSTER_SIZE = 32  # 지름(px). 캐릭터(40px)보다 살짝 작게 설정
 
 
# ── 3. 캐릭터(플레이어) 정보 ──────────────────────────
player_x = SCREEN_WIDTH // 2
player_y = SCREEN_HEIGHT // 2
player_speed = 4
 
is_moving = False
anim_frame = 0
anim_timer = 0
ANIM_SPEED = 8
 
MAX_HP = 100
player_hp = MAX_HP  # 체력. 0이 되면 게임 오버
 
# 공격 관련 변수
ATTACK_RANGE = 70       # 공격이 닿는 반경(px)
ATTACK_COOLDOWN = 20    # 공격 후 다시 공격 가능해지기까지 걸리는 프레임 수
attack_cooldown_timer = 0
attack_flash_timer = 0  # 공격 이펙트(원)를 잠깐 보여주기 위한 타이머
 
 
def get_player_center():
    """플레이어 사각형의 정중앙 좌표를 계산해서 반환. 거리 계산에 사용."""
    return (player_x + PLAYER_DISPLAY_SIZE[0] / 2,
            player_y + PLAYER_DISPLAY_SIZE[1] / 2)
 
 
def draw_player(x, y, moving, frame):
    current_image = walk_images[frame] if moving else idle_image
    screen.blit(current_image, (x, y))
 
 
# ── 4. 몬스터 정보 ────────────────────────────────────
# 몬스터 하나하나를 딕셔너리로 표현하고, 여러 마리를 리스트에 담아서 관리합니다.
# 예: {"x": 100, "y": 200} 처럼 위치 정보를 가짐
 
MONSTER_COUNT = 6      # 스테이지에 등장할 몬스터 수 (적게 유지)
MONSTER_SPEED = 1.3    # 몬스터가 플레이어를 향해 다가오는 속도
MONSTER_MAX_HP = 100   # 몬스터 최대 체력
ATTACK_DAMAGE = 34     # 한 번 공격할 때 몬스터에게 주는 데미지 (100/34 -> 약 3번 맞으면 처치)
 
 
def spawn_monsters(count):
    """몬스터를 화면 안 랜덤한 위치에 배치하되, 플레이어 시작 위치와는 멀리 떨어뜨려서 생성."""
    monsters = []
    px, py = get_player_center()
 
    while len(monsters) < count:
        mx = random.randint(0, SCREEN_WIDTH - MONSTER_SIZE)
        my = random.randint(0, SCREEN_HEIGHT - MONSTER_SIZE)
 
        # 플레이어와 너무 가까운 곳에 스폰되지 않도록 거리 체크
        distance = math.hypot(mx - px, my - py)
        if distance > 150:
            # "hp" 키에 몬스터의 현재 체력을 저장. 공격을 맞을 때마다 이 값이 줄어듦
            monsters.append({"x": mx, "y": my, "hp": MONSTER_MAX_HP})
 
    return monsters
 
 
monsters = spawn_monsters(MONSTER_COUNT)
 
 
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
 
 
def draw_monster(m):
    """몬스터 한 마리와 그 위의 체력바를 화면에 그리는 함수. 원 중심 좌표 기준으로 그림."""
    center = (int(m["x"] + MONSTER_SIZE / 2), int(m["y"] + MONSTER_SIZE / 2))
    pygame.draw.circle(screen, RED, center, MONSTER_SIZE // 2)
    pygame.draw.circle(screen, DARK_RED, center, MONSTER_SIZE // 2, 2)  # 테두리
 
    # 몬스터 원 바로 위에 체력바 표시
    draw_hp_bar(center[0], center[1] - MONSTER_SIZE / 2 - 12, m["hp"], MONSTER_MAX_HP, bar_width=32, bar_height=5)
 
 
def move_monster_toward_player(m):
    """몬스터를 플레이어 방향으로 한 프레임만큼 이동시키는 함수."""
    px, py = get_player_center()
    mx_center = m["x"] + MONSTER_SIZE / 2
    my_center = m["y"] + MONSTER_SIZE / 2
 
    # 플레이어 방향 벡터 (얼마나 오른쪽/아래로 가야 하는지)
    dx = px - mx_center
    dy = py - my_center
    distance = math.hypot(dx, dy)
 
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
    """화면 상단에 남은 몬스터 수와 체력을 표시."""
    hp_text = font.render(f"HP: {int(player_hp)}", True, BLACK)
    monster_text = font.render(f"남은 몬스터: {len(monsters)}", True, BLACK)
    screen.blit(hp_text, (10, 10))
    screen.blit(monster_text, (10, 40))
 
 
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
        if keys[pygame.K_w]:
            player_y -= player_speed
            is_moving = True
        if keys[pygame.K_s]:
            player_y += player_speed
            is_moving = True
        if keys[pygame.K_a]:
            player_x -= player_speed
            is_moving = True
        if keys[pygame.K_d]:
            player_x += player_speed
            is_moving = True
 
    player_x = max(0, min(player_x, SCREEN_WIDTH - PLAYER_DISPLAY_SIZE[0]))
    player_y = max(0, min(player_y, SCREEN_HEIGHT - PLAYER_DISPLAY_SIZE[1]))
 
    if is_moving:
        anim_timer += 1
        if anim_timer >= ANIM_SPEED:
            anim_frame = (anim_frame + 1) % len(walk_images)
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
 
        px, py = get_player_center()
        survivors = []  # 이번 공격 이후에도 살아남은(hp가 남은) 몬스터만 다시 담을 리스트
 
        for m in monsters:
            mx_center = m["x"] + MONSTER_SIZE / 2
            my_center = m["y"] + MONSTER_SIZE / 2
            # 지난번에 설명드린 "두 점 사이 거리" 공식: 루트((x차이)^2 + (y차이)^2)
            distance = math.hypot(px - mx_center, py - my_center)
 
            if distance <= ATTACK_RANGE:
                m["hp"] -= ATTACK_DAMAGE  # 사정거리 안에 있으면 데미지를 입힘 (즉사 아님)
 
            if m["hp"] > 0:
                survivors.append(m)  # 체력이 남아있으면 생존
            # 체력이 0 이하면 survivors에 안 담기므로 자동으로 제거됨(=처치)
 
        monsters = survivors
 
    # ── 몬스터 이동 & 플레이어 피격 판정 ──
    if not stage_clear and not game_over:
        px, py = get_player_center()
        for m in monsters:
            move_monster_toward_player(m)
 
            mx_center = m["x"] + MONSTER_SIZE / 2
            my_center = m["y"] + MONSTER_SIZE / 2
            distance = math.hypot(px - mx_center, py - my_center)
 
            # 몬스터 반지름 + 플레이어 반지름보다 가까우면 "닿았다"고 판정
            touching_distance = (MONSTER_SIZE / 2) + (PLAYER_DISPLAY_SIZE[0] / 2)
            if distance < touching_distance:
                player_hp -= 0.5  # 닿아있는 동안 서서히 체력 감소
                player_hp = max(0, player_hp)
 
    # ── 화면 그리기 ──
    screen.fill(WHITE)
 
    for m in monsters:
        draw_monster(m)
 
    draw_player(player_x, player_y, is_moving, anim_frame)
 
    # 플레이어 머리 위에도 몬스터와 똑같은 draw_hp_bar() 함수로 체력바 표시
    player_center_x, player_top_y = get_player_center()[0], player_y
    draw_hp_bar(player_center_x, player_top_y - 14, player_hp, MAX_HP, bar_width=40, bar_height=6)
 
    # 공격 범위를 잠깐 원으로 표시 (시각적 피드백)
    if attack_flash_timer > 0:
        px, py = get_player_center()
        pygame.draw.circle(screen, GREEN, (int(px), int(py)), ATTACK_RANGE, 3)
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
 
