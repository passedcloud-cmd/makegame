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
DAMAGE_PER_HIT = MAX_HP / HITS_TO_DIE       # 100 / 10 = 10 (몬스터의 기본 공격력)
PLAYER_INVINCIBLE_DURATION = 30              # 피격 후 무적 프레임 수

# ── 플레이어 스탯 특성: 높은 방어력 ──
# 몬스터의 기본 공격력(DAMAGE_PER_HIT)에 이 배율을 곱해서 실제 데미지를 계산.
# 0.4면 원래 데미지의 40%만 받는다는 뜻 (방어력이 높아 훨씬 적게 닳음)
PLAYER_DEFENSE_MULTIPLIER = 0.4

PLAYER_BASE_SPEED = 4.0   # 레벨/아이템으로 이동속도가 늘어나기 전 기본 이동속도

# ── 성장 요소: 경험치 & 레벨업 ──
# 몬스터를 처치하면 경험치를 얻고, 다 채우면 레벨업 하면서 스탯이 영구적으로 강해짐.
XP_TO_LEVEL_BASE = 50        # 1 -> 2레벨에 필요한 경험치
XP_TO_LEVEL_GROWTH = 25      # 레벨이 오를 때마다 다음 레벨에 필요한 경험치가 이만큼씩 늘어남
LEVEL_UP_HP_BONUS = 8        # 레벨업 시 늘어나는 최대 체력 (동시에 체력 전부 회복)
LEVEL_UP_DAMAGE_BONUS = 4    # 레벨업 시 늘어나는 공격력
LEVEL_UP_SPEED_BONUS = 0.15  # 레벨업 시 늘어나는 이동속도
LEVEL_UP_FLASH_DURATION = 45 # "LEVEL UP!" 문구가 보이는 프레임 수

# ── 공격 ──
# 답답하지 않고 시원시원하게 느껴지도록 넓은 범위 + 짧은 쿨다운으로 설정
ATTACK_RANGE = 115
ATTACK_COOLDOWN = 15
ATTACK_ANIM_TOTAL = 12                       # 공격 모션 재생 프레임 수
ATTACK_FLASH_DURATION = 14                   # 공격 이펙트(부채꼴)가 화면에 보이는 프레임 수

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

# ── 보스 몬스터 ──
BOSS_STAGES = {4, 5}           # 보스가 등장하는 스테이지 번호들 (마지막 웨이브에 등장)
FINAL_STAGE = 5                # 이 스테이지를 클리어하면 엔딩
BOSS_SIZE_MULTIPLIER = 2      # 일반 몬스터 대비 크기 배율
BOSS_HP_MULTIPLIER = 3        # 일반 몬스터 대비 체력 배율
BOSS_DAMAGE_MULTIPLIER = 3    # 일반 몬스터 대비 공격력(접촉 데미지) 배율
BOSS_COLOR = (140, 30, 140)       # 보스 몸 색 (일반 몬스터=빨강과 구분되는 보라색)
BOSS_OUTLINE_COLOR = (80, 10, 80)  # 보스 테두리 색

# ── 동료(보호 대상) 캐릭터 ──
# 아직 전용 그림이 없어서 도형으로 표시 (몬스터와 같은 방식)
COMPANION_SIZE = 34
COMPANION_MAX_HP = 100          # 플레이어와 동일하게 10번 맞으면 사망
COMPANION_COLOR = (230, 200, 60)  # 노란색 계열 (플레이어=파랑, 몬스터=빨강과 구분)

# ── 몬스터 종류(일반 외 3종) ──
# 일반 몬스터(빨강)는 그대로 두고, 서로 다른 움직임 패턴을 가진 몬스터들을 추가.
# 모든 배율은 "그 스테이지의 일반 몬스터" 기준(monster.get_current_monster_max_hp)으로 계산됨.

# "fast": 작고 약하지만 훨씬 빠르며, 좌우로 흔들리며 접근해 맞추기 까다로움
FAST_MONSTER_SIZE_MULTIPLIER = 0.75
FAST_MONSTER_SPEED_MULTIPLIER = 2.1
FAST_MONSTER_HP_MULTIPLIER = 0.5
FAST_MONSTER_COLOR = (250, 150, 40)
FAST_MONSTER_OUTLINE_COLOR = (180, 90, 10)
FAST_WIGGLE_AMOUNT = 0.7    # 진행 방향에 수직으로 흔들리는 정도 (0~1)
FAST_WIGGLE_SPEED = 0.25    # 흔들림(지그재그)이 진동하는 속도

# "tank": 크고 느리지만 체력과 공격력이 훨씬 높은 몬스터
TANK_MONSTER_SIZE_MULTIPLIER = 1.6
TANK_MONSTER_SPEED_MULTIPLIER = 0.55
TANK_MONSTER_HP_MULTIPLIER = 2.4
TANK_MONSTER_DAMAGE_MULTIPLIER = 1.6
TANK_MONSTER_COLOR = (90, 70, 150)
TANK_MONSTER_OUTLINE_COLOR = (50, 35, 90)

# "ranged": 일정 거리를 유지하며 투사체를 쏘는 몬스터 (근접하면 오히려 물러남)
RANGED_MONSTER_SIZE_MULTIPLIER = 0.85
RANGED_MONSTER_SPEED_MULTIPLIER = 0.9
RANGED_MONSTER_HP_MULTIPLIER = 0.7
RANGED_MONSTER_COLOR = (40, 170, 170)
RANGED_MONSTER_OUTLINE_COLOR = (15, 100, 100)
RANGED_PREFERRED_DISTANCE = 220        # 유지하려는 거리(px)
RANGED_DISTANCE_MARGIN = 30            # 이 오차 범위 안이면 멈춰서 사격만 함
RANGED_ATTACK_RANGE = 320              # 이 거리 이내에 있어야 사격 시도
RANGED_ATTACK_COOLDOWN_FRAMES = 90     # 발사 간격 (1.5초)
RANGED_PROJECTILE_SPEED = 5.5
RANGED_PROJECTILE_SIZE = 9
RANGED_PROJECTILE_DAMAGE_MULTIPLIER = 0.75   # DAMAGE_PER_HIT 대비 배율 (플레이어는 방어배율도 추가 적용)
RANGED_PROJECTILE_COLOR = (40, 200, 200)

# ── 몬스터 처치 시 얻는 경험치 (종류별) ──
XP_REWARD_NORMAL = 15
XP_REWARD_FAST = 10
XP_REWARD_TANK = 25
XP_REWARD_RANGED = 20
XP_REWARD_BOSS = 150

# ── 아이템 드랍/획득 ──
ITEM_DROP_CHANCE = 0.25    # 일반 몬스터가 아이템을 떨어뜨릴 확률 (보스는 항상 드랍)
ITEM_SIZE = 18
ITEM_BOB_SPEED = 0.12       # 바닥에 놓인 아이템이 위아래로 떠 있는 애니메이션 속도
ITEM_BOB_AMOUNT = 4         # 떠 있는 폭(px)
ITEM_PICKUP_FLASH_DURATION = 30   # 습득 문구가 떠 있는 프레임 수

ITEM_HEAL_AMOUNT = 30       # "heal" 아이템: 즉시 회복량
ITEM_POWER_BONUS = 3        # "power" 아이템: 영구 공격력 증가량
ITEM_SPEED_BONUS = 0.3      # "speed" 아이템: 영구 이동속도 증가량

ITEM_HEAL_COLOR = (230, 60, 90)
ITEM_POWER_COLOR = (250, 150, 40)
ITEM_SPEED_COLOR = (60, 190, 230)

COMPANION_FOLLOW_DISTANCE = 55   # 플레이어 뒤에서 유지하려는 거리(px)
COMPANION_FOLLOW_SPEED = 3.2     # 따라오는 속도 (플레이어보다 살짝 느리게 해서 자연스럽게 처짐)
COMPANION_FOLLOW_DEAD_ZONE = 6   # 목표 지점과 이 거리 이내면 멈춤 (미세하게 떨리는 것 방지)

# ── 동료 스탯 특성: 자가 힐(회복) 패시브 스킬 ──
COMPANION_HEAL_INTERVAL_SECONDS = 5
COMPANION_HEAL_INTERVAL_FRAMES = COMPANION_HEAL_INTERVAL_SECONDS * FPS
COMPANION_HEAL_AMOUNT = 8   # 5초마다 회복되는 체력량

# ── 화면 흐름: 대기 화면 / 일시정지 / 스테이지 클리어 ──
STAGE_CLEAR_DURATION = 120   # "STAGE CLEAR!" 문구가 보이며 쉬는 시간 (2초), 끝나면 자동으로 STORY로 전환

# ── 사운드 볼륨 (환경설정 화면에서 조절) ──
DEFAULT_BGM_VOLUME = 0.4
DEFAULT_SFX_VOLUME = 0.6
VOLUME_STEP = 0.1

# ── 메뉴류 화면 공용 버튼 색 ──
MENU_SECONDARY_COLOR = (90, 130, 200)   # "환경 설정", "뒤로가기"처럼 강조가 필요 없는 버튼
