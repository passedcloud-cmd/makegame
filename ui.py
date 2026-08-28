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


def create_fonts():
    """HUD에서 쓸 폰트들을 만들어서 반환. main.py에서 한 번만 호출."""
    pygame.font.init()
    return {
        "normal": pygame.font.SysFont(None, 32),
        "big": pygame.font.SysFont(None, 64),
    }


def draw_hud(screen, fonts, current_stage, waves_spawned, total_waves, player, monster_count):
    """화면 상단에 스테이지, 웨이브 진행, 체력, 남은 몬스터 수를 표시."""
    font = fonts["normal"]
    hits_left = math.ceil(player["hp"] / config.DAMAGE_PER_HIT) if player["hp"] > 0 else 0

    stage_text = font.render(
        f"스테이지: {current_stage}  (웨이브 {min(waves_spawned, total_waves)}/{total_waves})", True, config.BLACK)
    hp_text = font.render(f"HP: {int(player['hp'])}  (남은 목숨 {hits_left}번)", True, config.BLACK)
    monster_text = font.render(f"남은 몬스터: {monster_count}", True, config.BLACK)

    screen.blit(stage_text, (10, 10))
    screen.blit(hp_text, (10, 40))
    screen.blit(monster_text, (10, 70))


def draw_end_message(screen, fonts, text, color):
    """STAGE CLEAR! / GAME OVER 같은 큰 안내 문구를 화면 중앙에 표시."""
    msg = fonts["big"].render(text, True, color)
    screen.blit(msg, (config.SCREEN_WIDTH // 2 - msg.get_width() // 2,
                       config.SCREEN_HEIGHT // 2 - 30))
