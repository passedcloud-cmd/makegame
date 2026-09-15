"""
ui.py — 화면에 표시되는 글자/체력바 담당
====================================================
player.py와 monster.py가 둘 다 이 파일의 draw_hp_bar()를 가져다 쓰기 때문에,
체력바 디자인을 한 군데(여기)만 고치면 플레이어/몬스터 체력바가 동시에 바뀝니다.
"""

import pygame
import math
import config


def draw_hp_bar(screen, center_x, top_y, current_hp, max_hp, bar_width=40, bar_height=6):
    """캐릭터 머리 위에 체력바를 그리는 공용 함수."""
    ratio = max(0, current_hp / max_hp)

    bar_x = int(center_x - bar_width / 2)
    bar_y = int(top_y)

    pygame.draw.rect(screen, (180, 180, 180), (bar_x, bar_y, bar_width, bar_height))

    if ratio > 0.5:
        bar_color = config.GREEN
    elif ratio > 0.2:
        bar_color = (230, 180, 30)
    else:
        bar_color = config.RED

    pygame.draw.rect(screen, bar_color, (bar_x, bar_y, int(bar_width * ratio), bar_height))
    pygame.draw.rect(screen, config.BLACK, (bar_x, bar_y, bar_width, bar_height), 1)


def _find_korean_font():
    """
    시스템에 설치된 한글 지원 폰트를 이름으로 찾아서 파일 경로를 반환.
    pygame.font.SysFont(None, ...)은 한글을 지원하지 않는 기본 폰트로 대체될 수 있어서,
    Windows/Mac/Linux에 흔히 깔려있는 한글 폰트 이름들을 순서대로 시도함.
    하나도 못 찾으면 None을 반환 (이 경우 한글이 깨질 수 있음).
    """
    candidates = [
        "malgungothic",       # Windows 기본 한글 폰트
        "applesdgothicneo",   # macOS 기본 한글 폰트
        "applegothic",
        "notosanscjkkr",      # Linux에 흔히 설치된 구글 폰트
        "notosanskr",
        "nanumgothic",
        "gulim",
        "batang",
    ]
    for name in candidates:
        path = pygame.font.match_font(name)
        if path:
            return path
    return None


def create_fonts():
    """HUD/대화창에서 쓸 폰트들을 만들어서 반환. main.py에서 한 번만 호출."""
    pygame.font.init()
    font_path = _find_korean_font()

    if font_path:
        return {
            "small": pygame.font.Font(font_path, 22),
            "normal": pygame.font.Font(font_path, 32),
            "big": pygame.font.Font(font_path, 64),
        }
    else:
        # 한글 지원 폰트를 못 찾은 경우 - 영어 텍스트는 정상 표시되지만 한글은 깨질 수 있음
        return {
            "small": pygame.font.SysFont(None, 22),
            "normal": pygame.font.SysFont(None, 32),
            "big": pygame.font.SysFont(None, 64),
        }


def draw_hud(screen, fonts, current_stage, waves_spawned, total_waves, player, monster_count):
    """화면 상단에 스테이지, 웨이브 진행, 레벨/경험치, 체력, 남은 몬스터 수를 표시."""
    font = fonts["normal"]
    hits_left = math.ceil(player["hp"] / config.DAMAGE_PER_HIT) if player["hp"] > 0 else 0

    stage_text = font.render(
        f"스테이지: {current_stage}  (웨이브 {min(waves_spawned, total_waves)}/{total_waves})", True, config.BLACK)
    level_text = font.render(
        f"레벨 {player['level']}  (EXP {int(player['xp'])}/{player['xp_to_next']})", True, config.BLACK)
    hp_text = font.render(
        f"HP: {int(player['hp'])}/{int(player['max_hp'])}  (남은 목숨 {hits_left}번)", True, config.BLACK)
    monster_text = font.render(f"남은 몬스터: {monster_count}", True, config.BLACK)

    screen.blit(stage_text, (10, 10))
    screen.blit(level_text, (10, 40))
    screen.blit(hp_text, (10, 70))
    screen.blit(monster_text, (10, 100))


def draw_end_message(screen, fonts, text, color):
    """STAGE CLEAR! / GAME OVER 같은 큰 안내 문구를 화면 중앙에 표시."""
    msg = fonts["big"].render(text, True, color)
    screen.blit(msg, (config.SCREEN_WIDTH // 2 - msg.get_width() // 2,
                       config.SCREEN_HEIGHT // 2 - 30))


def get_restart_button_rect(fonts=None, label="Restart"):
    """
    Restart/재시작 버튼의 위치와 크기를 계산해서 반환 (그리기 + 클릭 판정 둘 다에 사용).
    fonts를 넘기면 label 글자 길이에 맞춰 버튼 폭을 자동으로 넓혀서, 긴 한글 문구도 안 잘리게 함.
    클릭 판정 쪽에서도 실제로 그려진 버튼과 같은 크기를 쓰려면 반드시 같은 label을 넘겨야 함.
    """
    height = 50
    if fonts:
        text_width = fonts["normal"].size(label)[0]
        width = max(160, text_width + 48)  # 최소 160px, 글자가 길면 여유 24px씩 더 확보
    else:
        width = 160

    x = config.SCREEN_WIDTH // 2 - width // 2
    y = config.SCREEN_HEIGHT // 2 + 90
    return pygame.Rect(x, y, width, height)


def draw_restart_button(screen, fonts, label="Restart"):
    """게임 오버/엔딩 화면에 버튼을 그림. 클릭 판정에 쓸 Rect를 반환.
    label을 바꾸면 같은 버튼 모양을 다른 문구로 재사용할 수 있음 (예: '처음부터 다시')."""
    rect = get_restart_button_rect(fonts, label)
    pygame.draw.rect(screen, config.GREEN, rect, border_radius=8)
    pygame.draw.rect(screen, config.BLACK, rect, 2, border_radius=8)

    text_surface = fonts["normal"].render(label, True, config.WHITE)
    text_rect = text_surface.get_rect(center=rect.center)
    screen.blit(text_surface, text_rect)

    return rect


def get_menu_button_rect(fonts, label, center_x, center_y, width=None, height=50):
    """
    메인 화면/일시정지/환경설정처럼 버튼 여러 개가 특정 좌표에 나열되는 화면에서 쓰는 범용 버튼 Rect 계산.
    width를 지정하지 않으면 label 글자 길이에 맞춰 자동으로 넓힘 (get_restart_button_rect와 같은 방식).
    그리기(draw_menu_button)와 클릭 판정 양쪽에서 반드시 같은 인자로 호출해야 같은 위치/크기를 보장함.
    """
    if width is None:
        text_width = fonts["normal"].size(label)[0]
        width = max(160, text_width + 48)

    rect = pygame.Rect(0, 0, width, height)
    rect.center = (center_x, center_y)
    return rect


def draw_menu_button(screen, fonts, label, rect, bg_color=None):
    """get_menu_button_rect()로 계산한 Rect 위치에 버튼을 그림."""
    bg_color = bg_color if bg_color is not None else config.GREEN
    pygame.draw.rect(screen, bg_color, rect, border_radius=8)
    pygame.draw.rect(screen, config.BLACK, rect, 2, border_radius=8)

    text_surface = fonts["normal"].render(label, True, config.WHITE)
    screen.blit(text_surface, text_surface.get_rect(center=rect.center))
