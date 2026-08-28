"""
config.py — 게임 전체에서 쓰는 설정값(상수)을 모아둔 파일
====================================================
다른 파일들은 전부 이 파일을 "import config"로 불러와서
config.SCREEN_WIDTH 처럼 값을 꺼내 씁니다.

이 파일은 pygame.display.set_mode()보다 먼저 import 되어도 안전하도록
'숫자 값'만 담고, 이미지 로딩처럼 화면이 필요한 코드는 넣지 않습니다.
난이도나 화면 크기를 바꾸고 싶을 때는 이 파일의 숫자만 고치면 됩니다.
"""

# ── 화면 & 맵 ──
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
MAP_WIDTH = 1200   # 화면(800)보다 넓어서 카메라가 스크롤됨
MAP_HEIGHT = 900
FPS = 60

# ── 색상 (R, G, B) ──
WHITE = (255, 255, 255)
RED = (200, 40, 40)
DARK_RED = (140, 20, 20)
BLACK = (20, 20, 20)
GREEN = (40, 180, 80)

# ── 캐릭터 크기 ──
PLAYER_DISPLAY_SIZE = (40, 40)
MONSTER_SIZE = 32

# ── 플레이어 체력 ──
MAX_HP = 100
HITS_TO_DIE = 10
DAMAGE_PER_HIT = MAX_HP / HITS_TO_DIE       # 100 / 10 = 10
PLAYER_INVINCIBLE_DURATION = 30              # 피격 후 무적 프레임 수

# ── 공격 ──
ATTACK_RANGE = 70
ATTACK_COOLDOWN = 20
ATTACK_ANIM_TOTAL = 12                       # 공격 모션 재생 프레임 수

# ── 몬스터 이동 & 넉백 ──
MONSTER_SPEED = 1.3
KNOCKBACK_SPEED = 6
KNOCKBACK_DURATION = 10

# ── 플레이어 피격 시 경직(진동) ── 몬스터 넉백과 다르게, 거의 안 밀리고 짧게 떨리기만 함
PLAYER_STAGGER_DURATION = 10   # 경직 지속 프레임 수 (이 동안 조작 불가)
PLAYER_STAGGER_AMPLITUDE = 3   # 진동 폭(px). 작을수록 미세하게 떨림

# ── 몬스터 체력 & 스테이지 난이도 ──
BASE_MONSTER_HP = 100
MONSTER_HP_PER_STAGE = 50
ATTACK_DAMAGE = 40

# ── 웨이브 스폰 (5마리씩 3번, 5초 간격) ──
WAVE_SIZE = 5
TOTAL_WAVES = 3
WAVE_INTERVAL_SECONDS = 5
WAVE_INTERVAL_FRAMES = WAVE_INTERVAL_SECONDS * FPS