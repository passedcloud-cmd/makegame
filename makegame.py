"""
WASD 이동 + 걷는 애니메이션 예제
=================================
이 코드는 실제 그림 파일(이미지) 없이도 애니메이션 원리를 이해할 수 있도록
사각형 캐릭터에 '다리 움직임'을 직접 그려서 걷는 것처럼 보이게 만든 예제입니다.
 
나중에 실제 캐릭터 그림(walk1.png, walk2.png 같은 파일)이 생기면,
draw_player() 함수 안의 도형 그리기 코드를,
screen.blit(이미지, (x, y)) 로 교체하면 됩니다.
"""
 
import pygame
 
# ── 1. 기본 설정 ─────────────────────────────────────
pygame.init()
 
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("WASD 이동")
 
clock = pygame.time.Clock()  # 게임 속도(초당 프레임 수)를 조절해주는 시계
FPS = 60  # 1초에 화면을 60번 그림 (숫자가 클수록 부드럽게 움직임)
 
# 색깔은 (빨강, 초록, 파랑) 숫자 조합으로 표현합니다 (0~255)
WHITE = (255, 255, 255)
BLUE = (60, 120, 220)
DARK_BLUE = (40, 90, 170)
BLACK = (30, 30, 30)

# ── 2. 이미지 미리 불러오기 (게임 시작할 때 딱 한 번만) ──
# pygame.image.load()는 파일을 읽어서 화면에 그릴 수 있는 형태로 바꿔줍니다.
# 매 프레임마다 새로 불러오면 느려지기 때문에, 게임 시작 전에 한 번만 불러와서
# 변수에 저장해두고 계속 재사용하는 것이 중요합니다.

# 캐릭터 이미지를 화면에 표시할 때 몇 픽셀 크기로 고정할지 정합니다.
# 원본 그림 파일의 실제 크기(예: 512x512)는 신경 쓰지 않아도 됩니다.
# 여기 숫자만 바꾸면 캐릭터가 크게/작게 보입니다.
PLAYER_DISPLAY_SIZE = (40, 40)  # (가로, 세로) 픽셀

def load_player_image(path):
    """이미지 파일을 불러온 뒤, 지정한 크기로 고정해서 반환하는 함수."""
    image = pygame.image.load(path).convert_alpha()
    # transform.scale(이미지, (가로, 세로)) -> 원본 크기와 상관없이 강제로 크기 조절
    return pygame.transform.scale(image, PLAYER_DISPLAY_SIZE)
 
idle_image = load_player_image("assets/idle.png")
 
# 걷기 애니메이션용 이미지들은 리스트로 묶어서 관리하면
# anim_frame 숫자로 walk_images[anim_frame] 처럼 바로 꺼내 쓸 수 있어 편합니다.
walk_images = [
    load_player_image("assets/walk1.png"),
    load_player_image("assets/walk2.png"),
]
# convert_alpha()는 이미지의 투명 배경을 제대로 표시하고,
# 그림을 화면에 그리는 속도를 더 빠르게 만들어주는 처리입니다. (관용적으로 항상 붙여줍니다)


 
 
# ── 3. 캐릭터(플레이어) 정보 ──────────────────────────
player_x = SCREEN_WIDTH // 2   # 캐릭터의 x 좌표 (화면 가로 중앙에서 시작)
player_y = SCREEN_HEIGHT // 2  # 캐릭터의 y 좌표 (화면 세로 중앙에서 시작)
# player_size = 40               # 캐릭터 몸통(사각형) 크기
player_speed = 4               # 한 프레임에 몇 픽셀씩 움직일지 (이동 속도)
 
# 애니메이션 관련 변수들
is_moving = False       # 지금 캐릭터가 움직이고 있는 중인지
anim_frame = 0          # 지금 몇 번째 걷기 자세인지 (0 또는 1)
anim_timer = 0          # 다음 자세로 바꾸기까지 남은 시간(프레임 수) 카운트
ANIM_SPEED = 8          # 숫자가 작을수록 다리가 더 빨리 움직임 (8프레임마다 자세 전환)
 
 
# def draw_player(x, y, moving, frame):
#     """
#     캐릭터를 화면에 그리는 함수.
#     지금은 사각형 몸통 + 다리 두 개로 '걷는 느낌'을 표현합니다.
#     """
#     # 몸통 (파란 사각형)
#     body_rect = pygame.Rect(x, y, player_size, player_size)
#     pygame.draw.rect(screen, BLUE, body_rect)
 
#     # 다리는 걷는 중일 때만 좌우로 번갈아 흔들리게 그림
#     leg_offset = 8 if (moving and frame == 0) else -8 if moving else 0
 
#     left_leg_x = x + 8
#     right_leg_x = x + player_size - 12
 
#     # frame이 0이면 왼쪽 다리가 앞으로, frame이 1이면 오른쪽 다리가 앞으로
#     if moving:
#         pygame.draw.rect(screen, DARK_BLUE, (left_leg_x + leg_offset, y + player_size, 6, 14))
#         pygame.draw.rect(screen, DARK_BLUE, (right_leg_x - leg_offset, y + player_size, 6, 14))
#     else:
#         # 가만히 서 있을 때는 다리를 나란히
#         pygame.draw.rect(screen, DARK_BLUE, (left_leg_x, y + player_size, 6, 14))
#         pygame.draw.rect(screen, DARK_BLUE, (right_leg_x, y + player_size, 6, 14))

def draw_player(x, y, moving, frame):
    """
    캐릭터를 화면에 그리는 함수.
    이전 버전과 함수 이름/입력값(x, y, moving, frame)은 완전히 동일합니다.
    바뀐 것은 '함수 안에서 무엇을 그리는지' 뿐입니다.
    """
    if moving:
        # 움직이는 중이면: 걷기 이미지 리스트에서 지금 프레임에 맞는 그림을 꺼내서 그림
        current_image = walk_images[frame]
    else:
        # 멈춰있으면: 가만히 서 있는 이미지를 그림
        current_image = idle_image
 
    # screen.blit(그릴 이미지, (x좌표, y좌표))
    # -> "이 이미지를 화면의 이 위치에 붙여넣어라" 라는 뜻입니다.
    screen.blit(current_image, (x, y))

 
# ── 4. 게임 루프 ─────────────────────────────────────
running = True
while running:
 
    # (1) 입력 확인: 창을 닫으라는 명령이 있었는지 체크
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
 
    # (2) 지금 눌려있는 키들을 전부 확인
    keys = pygame.key.get_pressed()
 
    # 이번 프레임에 움직였는지 여부를 먼저 False로 초기화
    is_moving = False
 
    if keys[pygame.K_w]:  # 위쪽
        player_y -= player_speed
        is_moving = True
    if keys[pygame.K_s]:  # 아래쪽
        player_y += player_speed
        is_moving = True
    if keys[pygame.K_a]:  # 왼쪽
        player_x -= player_speed
        is_moving = True
    if keys[pygame.K_d]:  # 오른쪽
        player_x += player_speed
        is_moving = True
 
    # (3) 화면 밖으로 나가지 않도록 좌표 제한
    # player_x = max(0, min(player_x, SCREEN_WIDTH - player_size))
    # player_y = max(0, min(player_y, SCREEN_HEIGHT - player_size))

    player_x = max(0, min(player_x, SCREEN_WIDTH - idle_image.get_width()))
    player_y = max(0, min(player_y, SCREEN_HEIGHT - idle_image.get_height()))
 
    # (4) 애니메이션 프레임 갱신
    #     움직이고 있을 때만 다리 자세를 주기적으로 바꿔줌
    if is_moving:
        anim_timer += 1
        if anim_timer >= ANIM_SPEED:
            # anim_frame = (anim_frame + 1) % 2  # 0과 1을 번갈아가며 반복
            anim_frame = (anim_frame + 1) % len(walk_images)  # 이미지 개수만큼 자동으로 순환
            anim_timer = 0
    else:
        anim_frame = 0  # 멈추면 기본 자세로
 
    # (5) 화면 그리기
    screen.fill(WHITE)          # 매 프레임마다 화면을 흰색으로 지우고 다시 그림
    draw_player(player_x, player_y, is_moving, anim_frame)
    pygame.display.flip()       # 그린 내용을 실제 화면에 반영
 
    # (6) 속도 유지 (1초에 FPS번만큼만 반복되도록 조절)
    clock.tick(FPS)
 
pygame.quit()
 