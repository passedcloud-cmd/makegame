"""
main.py — 게임 진입점. 이 파일을 실행하면 게임이 시작됩니다.
====================================================
python main.py

다른 모든 로직(플레이어, 몬스터, 카메라, 화면 표시)은 각자 파일로 분리되어 있고,
이 파일은 그것들을 "불러와서 순서대로 실행"하는 역할만 합니다.
"""

import pygame

import config
import player as player_module
import monster as monster_module
import camera as camera_module
import ui

# ── 초기화 ──
pygame.init()
screen = pygame.display.set_mode((config.SCREEN_WIDTH, config.SCREEN_HEIGHT))
pygame.display.set_caption("WASD 이동 + 몬스터 배치 & 충돌 처리")
clock = pygame.time.Clock()

# 이미지는 화면(screen)이 만들어진 뒤에만 불러올 수 있으므로 여기서 로드
player_images = player_module.load_images()
background_image = camera_module.load_background("assets/backgrounds/stage1_bg.png")
fonts = ui.create_fonts()

# ── 게임 상태 ──
player = player_module.create_player()
current_stage = 1
monsters = monster_module.spawn_wave(config.WAVE_SIZE, player, current_stage)  # 1웨이브 즉시 등장
stage_frame_count = 0
waves_spawned = 1


# ── 게임 루프 ──
running = True
while running:

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    keys = pygame.key.get_pressed()

    game_over = player["hp"] <= 0
    stage_clear = len(monsters) == 0 and waves_spawned >= config.TOTAL_WAVES

    if not game_over:
        # 웨이브 스폰 타이머
        stage_frame_count += 1
        if waves_spawned < config.TOTAL_WAVES and stage_frame_count >= waves_spawned * config.WAVE_INTERVAL_FRAMES:
            monsters += monster_module.spawn_wave(config.WAVE_SIZE, player, current_stage)
            waves_spawned += 1

        # 플레이어 이동
        player_module.handle_movement(player, keys)

        # 공격 입력
        player_module.update_timers(player)
        if keys[pygame.K_SPACE]:
            started = player_module.start_attack(player)
            if started:
                monsters = player_module.resolve_attack(player, monsters)

    # 몬스터 이동 (넉백/추격)
    for m in monsters:
        monster_module.move_toward_player(m, player)

    # 플레이어 피격 판정
    if not game_over:
        player_module.take_contact_damage(player, monsters)

    # ── 카메라 계산 ──
    px, py = player_module.get_center(player)
    camera_x, camera_y = camera_module.compute_camera(px, py)

    # ── 화면 그리기 ──
    camera_module.draw_background(screen, background_image, camera_x, camera_y)

    for m in monsters:
        monster_module.draw(screen, m, camera_x, camera_y)

    player_module.draw(screen, player, player_images, camera_x, camera_y)
    player_module.draw_attack_effect(screen, player, camera_x, camera_y)

    ui.draw_hud(screen, fonts, current_stage, waves_spawned, config.TOTAL_WAVES, player, len(monsters))

    if stage_clear:
        ui.draw_end_message(screen, fonts, "STAGE CLEAR!", config.GREEN)
    elif game_over:
        ui.draw_end_message(screen, fonts, "GAME OVER", config.RED)

    pygame.display.flip()
    clock.tick(config.FPS)

pygame.quit()
