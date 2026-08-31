"""
main.py — 게임 진입점. 이 파일을 실행하면 게임이 시작됩니다.
====================================================
python main.py

이제 게임은 3가지 상태(state) 중 하나로 존재합니다.
- "PLAYING"    : 평소 게임플레이 (이동, 공격, 몬스터)
- "STORY"      : 스테이지 클리어 후 대화 장면
- "GAME_OVER"  : 체력이 0이 되어 Restart 버튼을 보여주는 상태

game_state 변수 하나로 "지금 어떤 화면인지"를 관리하고,
게임 루프 안에서 game_state 값에 따라 다른 코드를 실행합니다.
"""

import pygame

import config
import player as player_module
import monster as monster_module
import companion as companion_module
import camera as camera_module
import story as story_module
import ui

# ── 초기화 ──
pygame.init()
screen = pygame.display.set_mode((config.SCREEN_WIDTH, config.SCREEN_HEIGHT))
pygame.display.set_caption("WASD 이동 + 몬스터 배치 & 충돌 처리")
clock = pygame.time.Clock()

# 이미지는 화면(screen)이 만들어진 뒤에만 불러올 수 있으므로 여기서 로드
player_images = player_module.load_images()
background_image = camera_module.load_background("assets/backgrounds/stage1_bg.png")
portrait_image = story_module.load_portrait("assets/portraits/character.png")
fonts = ui.create_fonts()


# ── 스테이지 시작/재시작 공용 함수 ──
def start_stage(stage):
    """플레이어, 동료, 몬스터를 전부 초기화하고 첫 웨이브를 등장시킴.
    새 스테이지 진입, 그리고 Restart 버튼 클릭(재시작) 둘 다 이 함수 하나로 처리."""
    new_player = player_module.create_player()
    new_companion = companion_module.create_companion(new_player)
    new_monsters = monster_module.spawn_wave(config.WAVE_SIZE, new_player, stage)
    return new_player, new_companion, new_monsters


# ── 게임 상태 ──
game_state = "PLAYING"
current_stage = 1
player, companion, monsters = start_stage(current_stage)
stage_frame_count = 0
waves_spawned = 1
story_state = None      # STORY 상태일 때만 값이 채워짐
game_over_reason = ""   # GAME_OVER 상태일 때 "누가 쓰러졌는지" 문구


# ── 화면 그리기 (PLAYING과 GAME_OVER가 함께 사용) ──
def draw_playing_scene():
    px, py = player_module.get_center(player)
    camera_x, camera_y = camera_module.compute_camera(px, py)

    camera_module.draw_background(screen, background_image, camera_x, camera_y)
    for m in monsters:
        monster_module.draw(screen, m, camera_x, camera_y)
    companion_module.draw(screen, companion, camera_x, camera_y)
    player_module.draw(screen, player, player_images, camera_x, camera_y)
    player_module.draw_attack_effect(screen, player, camera_x, camera_y)
    ui.draw_hud(screen, fonts, current_stage, waves_spawned, config.TOTAL_WAVES, player, len(monsters))


# ── 게임 루프 ──
running = True
while running:

    # ── 이벤트 처리 ──
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        # STORY 상태: 스페이스/엔터로 다음 대사 진행
        if game_state == "STORY" and event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_SPACE, pygame.K_RETURN):
                story_finished = story_module.advance(story_state)
                if story_finished:
                    if current_stage == config.FINAL_STAGE:
                        game_state = "ENDING"  # 마지막 스테이지 클리어 -> 다음 스테이지 없이 엔딩으로
                    else:
                        current_stage += 1
                        player, companion, monsters = start_stage(current_stage)
                        stage_frame_count = 0
                        waves_spawned = 1
                        game_state = "PLAYING"

        # GAME_OVER 상태: Restart 버튼 클릭 감지
        if game_state == "GAME_OVER" and event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # 마우스 왼쪽 버튼
                button_rect = ui.get_restart_button_rect(fonts, "Restart")
                if button_rect.collidepoint(event.pos):
                    player, companion, monsters = start_stage(current_stage)  # 같은 스테이지로 재시작
                    stage_frame_count = 0
                    waves_spawned = 1
                    game_state = "PLAYING"

        # ENDING 상태: "처음부터 다시" 버튼 클릭 감지
        if game_state == "ENDING" and event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                button_rect = ui.get_restart_button_rect(fonts, "처음부터 다시")
                if button_rect.collidepoint(event.pos):
                    current_stage = 1  # 엔딩 이후 재시작은 항상 1스테이지부터
                    player, companion, monsters = start_stage(current_stage)
                    stage_frame_count = 0
                    waves_spawned = 1
                    game_state = "PLAYING"

    keys = pygame.key.get_pressed()

    # ══════════════════════════════════════════
    # 상태별 갱신(update) + 그리기(draw)
    # ══════════════════════════════════════════

    if game_state == "PLAYING":
        # 웨이브 스폰 타이머
        stage_frame_count += 1
        if waves_spawned < config.TOTAL_WAVES and stage_frame_count >= waves_spawned * config.WAVE_INTERVAL_FRAMES:
            is_final_wave = (waves_spawned == config.TOTAL_WAVES - 1)  # 이번에 등장하는 웨이브가 마지막 웨이브인지

            if current_stage in config.BOSS_STAGES and is_final_wave:
                monsters += monster_module.spawn_boss(player, current_stage)  # 마지막 웨이브 = 보스 등장
            else:
                monsters += monster_module.spawn_wave(config.WAVE_SIZE, player, current_stage)

            waves_spawned += 1

        # 플레이어 이동 & 공격
        player_module.handle_movement(player, keys)
        player_module.update_timers(player)
        if keys[pygame.K_SPACE]:
            started = player_module.start_attack(player)
            if started:
                monsters = player_module.resolve_attack(player, monsters)

        # 동료(보호 대상) 이동 - 플레이어를 따라감 (몬스터가 쫓아갈 최신 위치를 먼저 계산)
        companion_module.update_follow(companion, player)
        companion_module.update_passive_heal(companion)  # 자가 힐 패시브 스킬

        # 몬스터 이동 - 플레이어와 동료 중 "지금 더 가까운 쪽"을 골라서 추격
        # (거리가 같으면 플레이어를 우선하도록 <= 사용)
        player_center_x, player_center_y = player_module.get_center(player)
        companion_center_x, companion_center_y = companion_module.get_center(companion)
        for m in monsters:
            dist_to_player = monster_module.distance_to(m, player_center_x, player_center_y)
            dist_to_companion = monster_module.distance_to(m, companion_center_x, companion_center_y)

            if dist_to_player <= dist_to_companion:
                monster_module.move_toward_target(m, player_center_x, player_center_y)
            else:
                monster_module.move_toward_target(m, companion_center_x, companion_center_y)

        # 플레이어 & 동료 피격 판정 (몬스터가 둘 중 누구에게 닿아도 데미지)
        player_module.take_contact_damage(player, monsters)
        companion_module.take_contact_damage(companion, monsters)

        # ── 상태 전환 판정 ──
        if player["hp"] <= 0:
            game_state = "GAME_OVER"
            game_over_reason = "플레이어가 쓰러졌습니다"
        elif companion["hp"] <= 0:
            game_state = "GAME_OVER"
            game_over_reason = "보호 대상이 쓰러졌습니다 (보호 실패)"
        elif len(monsters) == 0 and waves_spawned >= config.TOTAL_WAVES:
            story_state = story_module.create_story_state(current_stage)
            game_state = "STORY"

        draw_playing_scene()

    elif game_state == "STORY":
        story_module.draw(screen, portrait_image, story_state, fonts)

    elif game_state == "GAME_OVER":
        draw_playing_scene()  # 죽기 직전 화면을 그대로 배경처럼 보여줌 (움직이지는 않음)
        ui.draw_end_message(screen, fonts, "GAME OVER", config.RED)

        reason_surface = fonts["normal"].render(game_over_reason, True, config.RED)
        screen.blit(reason_surface, (config.SCREEN_WIDTH // 2 - reason_surface.get_width() // 2,
                                       config.SCREEN_HEIGHT // 2 + 40))

        ui.draw_restart_button(screen, fonts)

    elif game_state == "ENDING":
        screen.fill(config.BLACK)

        title_surface = fonts["big"].render("THE END", True, config.GREEN)
        screen.blit(title_surface, (config.SCREEN_WIDTH // 2 - title_surface.get_width() // 2,
                                      config.SCREEN_HEIGHT // 2 - 90))

        subtitle_surface = fonts["normal"].render("모든 스테이지를 클리어했습니다!", True, config.WHITE)
        screen.blit(subtitle_surface, (config.SCREEN_WIDTH // 2 - subtitle_surface.get_width() // 2,
                                         config.SCREEN_HEIGHT // 2 - 10))

        ui.draw_restart_button(screen, fonts, "처음부터 다시")

    pygame.display.flip()
    clock.tick(config.FPS)

pygame.quit()