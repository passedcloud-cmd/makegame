"""
main.py — 게임 진입점. 이 파일을 실행하면 게임이 시작됩니다.
====================================================
python main.py

게임은 여러 상태(state) 중 하나로 존재합니다.
- "MENU"        : 대기 화면 (게임 시작 / 환경 설정 / 게임 종료)
- "SETTINGS"    : 환경 설정 화면 (배경음악/효과음 음량 조절)
- "PLAYING"     : 평소 게임플레이 (이동, 공격, 몬스터)
- "PAUSED"      : ESC로 일시정지한 상태 (다시 진행 / 메인 화면으로 돌아가기)
- "STAGE_CLEAR" : 웨이브를 모두 클리어한 직후 잠깐 보여주는 전환 화면
- "STORY"       : 스테이지 클리어 후 대화 장면
- "GAME_OVER"   : 체력이 0이 되어 Restart 버튼을 보여주는 상태
- "ENDING"      : 마지막 스테이지 클리어 후 엔딩 화면

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
import items as items_module
import ui
import sound as sound_module

# ── 초기화 ──
pygame.init()
sound_module.init_mixer()
screen = pygame.display.set_mode((config.SCREEN_WIDTH, config.SCREEN_HEIGHT))
pygame.display.set_caption("몬스터 퇴치")
clock = pygame.time.Clock()

# 이미지는 화면(screen)이 만들어진 뒤에만 불러올 수 있으므로 여기서 로드
player_images = player_module.load_images()
background_image = camera_module.load_background("assets/backgrounds/stage1_bg.png")
portrait_image = story_module.load_portrait("assets/portraits/character.png")
fonts = ui.create_fonts()
sounds = sound_module.load_sounds()

# 대기 화면(MENU)/환경설정 화면 배경: 기존 스테이지 배경을 화면 크기로 축소해서 재사용
menu_background = pygame.transform.smoothscale(background_image, (config.SCREEN_WIDTH, config.SCREEN_HEIGHT))

bgm_volume = config.DEFAULT_BGM_VOLUME
sfx_volume = config.DEFAULT_SFX_VOLUME
sound_module.play_background_music(volume=bgm_volume)


# ── 스테이지 시작/재시작 공용 함수 ──
def start_stage(stage):
    """플레이어, 동료, 몬스터, 투사체, 아이템을 전부 초기화하고 첫 웨이브를 등장시킴.
    새 스테이지 진입, 그리고 Restart 버튼 클릭(재시작) 둘 다 이 함수 하나로 처리."""
    new_player = player_module.create_player()
    new_companion = companion_module.create_companion(new_player)
    new_monsters = monster_module.spawn_wave(config.WAVE_SIZE, new_player, stage)
    return new_player, new_companion, new_monsters, [], [], []


# ── 화면별 버튼 위치 ──
# 클릭 판정(이벤트 처리)과 그리기가 항상 같은 위치/크기를 쓰도록 함수 하나로 묶어서 양쪽에서 재사용.
def menu_button_rects():
    cx = config.SCREEN_WIDTH // 2
    return {
        "start": ui.get_menu_button_rect(fonts, "게임 시작", cx, 320, width=240),
        "settings": ui.get_menu_button_rect(fonts, "환경 설정", cx, 390, width=240),
        "quit": ui.get_menu_button_rect(fonts, "게임 종료", cx, 460, width=240),
    }


def settings_button_rects():
    cx = config.SCREEN_WIDTH // 2
    return {
        "bgm_minus": ui.get_menu_button_rect(fonts, "-", cx - 130, 250, width=50, height=44),
        "bgm_plus": ui.get_menu_button_rect(fonts, "+", cx + 130, 250, width=50, height=44),
        "sfx_minus": ui.get_menu_button_rect(fonts, "-", cx - 130, 330, width=50, height=44),
        "sfx_plus": ui.get_menu_button_rect(fonts, "+", cx + 130, 330, width=50, height=44),
        "back": ui.get_menu_button_rect(fonts, "뒤로가기", cx, 440, width=200),
    }


def pause_button_rects():
    cx = config.SCREEN_WIDTH // 2
    return {
        "resume": ui.get_menu_button_rect(fonts, "다시 진행", cx, config.SCREEN_HEIGHT // 2 + 60, width=220),
        "to_menu": ui.get_menu_button_rect(fonts, "메인 화면으로 돌아가기", cx, config.SCREEN_HEIGHT // 2 + 130, width=320),
    }


# ── 게임 상태 ──
game_state = "MENU"
current_stage = 1
player, companion, monsters, projectiles, items, pickup_effects = start_stage(current_stage)
stage_frame_count = 0
waves_spawned = 1
stage_clear_timer = 0   # STAGE_CLEAR 상태일 때만 값이 채워짐 (0이 되면 STORY로 전환)
story_state = None      # STORY 상태일 때만 값이 채워짐
game_over_reason = ""   # GAME_OVER 상태일 때 "누가 쓰러졌는지" 문구


# ── 화면 그리기 (PLAYING, PAUSED, STAGE_CLEAR, GAME_OVER가 함께 사용) ──
def draw_playing_scene():
    px, py = player_module.get_center(player)
    camera_x, camera_y = camera_module.compute_camera(px, py)

    camera_module.draw_background(screen, background_image, camera_x, camera_y)
    items_module.draw(screen, items, camera_x, camera_y)
    for m in monsters:
        monster_module.draw(screen, m, camera_x, camera_y)
    monster_module.draw_projectiles(screen, projectiles, camera_x, camera_y)
    companion_module.draw(screen, companion, camera_x, camera_y)
    player_module.draw(screen, player, player_images, camera_x, camera_y)
    player_module.draw_attack_effect(screen, player, camera_x, camera_y)
    items_module.draw_pickup_effects(screen, pickup_effects, fonts, camera_x, camera_y)
    ui.draw_hud(screen, fonts, current_stage, waves_spawned, config.TOTAL_WAVES, player, len(monsters))


def draw_dim_overlay(alpha=140):
    """어두운 반투명 오버레이를 화면 전체에 덮어서, 그 위의 글자/버튼이 잘 보이게 함."""
    overlay = pygame.Surface((config.SCREEN_WIDTH, config.SCREEN_HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, alpha))
    screen.blit(overlay, (0, 0))


# ── 게임 루프 ──
running = True
while running:

    # ── 이벤트 처리 ──
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        # ESC: PLAYING <-> PAUSED 토글 (다른 상태에서는 무시)
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            if game_state == "PLAYING":
                game_state = "PAUSED"
                sound_module.pause_music()
            elif game_state == "PAUSED":
                game_state = "PLAYING"
                sound_module.resume_music()

        # MENU 상태: 버튼 클릭
        if game_state == "MENU" and event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            rects = menu_button_rects()
            if rects["start"].collidepoint(event.pos):
                current_stage = 1
                player, companion, monsters, projectiles, items, pickup_effects = start_stage(current_stage)
                stage_frame_count = 0
                waves_spawned = 1
                game_state = "PLAYING"
            elif rects["settings"].collidepoint(event.pos):
                game_state = "SETTINGS"
            elif rects["quit"].collidepoint(event.pos):
                running = False

        # SETTINGS 상태: 음량 조절 / 뒤로가기
        if game_state == "SETTINGS" and event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            rects = settings_button_rects()
            if rects["bgm_minus"].collidepoint(event.pos):
                bgm_volume = max(0.0, round(bgm_volume - config.VOLUME_STEP, 2))
                sound_module.set_music_volume(bgm_volume)
            elif rects["bgm_plus"].collidepoint(event.pos):
                bgm_volume = min(1.0, round(bgm_volume + config.VOLUME_STEP, 2))
                sound_module.set_music_volume(bgm_volume)
            elif rects["sfx_minus"].collidepoint(event.pos):
                sfx_volume = max(0.0, round(sfx_volume - config.VOLUME_STEP, 2))
                sound_module.play_sound(sounds, "item_pickup", sfx_volume)  # 바뀐 음량을 바로 들려줌
            elif rects["sfx_plus"].collidepoint(event.pos):
                sfx_volume = min(1.0, round(sfx_volume + config.VOLUME_STEP, 2))
                sound_module.play_sound(sounds, "item_pickup", sfx_volume)
            elif rects["back"].collidepoint(event.pos):
                game_state = "MENU"

        # PAUSED 상태: 버튼 클릭
        if game_state == "PAUSED" and event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            rects = pause_button_rects()
            if rects["resume"].collidepoint(event.pos):
                game_state = "PLAYING"
                sound_module.resume_music()
            elif rects["to_menu"].collidepoint(event.pos):
                current_stage = 1
                player, companion, monsters, projectiles, items, pickup_effects = start_stage(current_stage)
                stage_frame_count = 0
                waves_spawned = 1
                game_state = "MENU"
                sound_module.resume_music()

        # STORY 상태: 스페이스/엔터로 다음 대사 진행
        if game_state == "STORY" and event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_SPACE, pygame.K_RETURN):
                story_finished = story_module.advance(story_state)
                if story_finished:
                    if current_stage == config.FINAL_STAGE:
                        game_state = "ENDING"  # 마지막 스테이지 클리어 -> 다음 스테이지 없이 엔딩으로
                    else:
                        current_stage += 1
                        player, companion, monsters, projectiles, items, pickup_effects = start_stage(current_stage)
                        stage_frame_count = 0
                        waves_spawned = 1
                        game_state = "PLAYING"

        # GAME_OVER 상태: Restart 버튼 클릭 감지
        if game_state == "GAME_OVER" and event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # 마우스 왼쪽 버튼
                button_rect = ui.get_restart_button_rect(fonts, "Restart")
                if button_rect.collidepoint(event.pos):
                    player, companion, monsters, projectiles, items, pickup_effects = start_stage(current_stage)  # 같은 스테이지로 재시작
                    stage_frame_count = 0
                    waves_spawned = 1
                    game_state = "PLAYING"

        # ENDING 상태: "처음부터 다시" 버튼 클릭 감지
        if game_state == "ENDING" and event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                button_rect = ui.get_restart_button_rect(fonts, "처음부터 다시")
                if button_rect.collidepoint(event.pos):
                    current_stage = 1  # 엔딩 이후 재시작은 항상 1스테이지부터
                    player, companion, monsters, projectiles, items, pickup_effects = start_stage(current_stage)
                    stage_frame_count = 0
                    waves_spawned = 1
                    game_state = "PLAYING"

    keys = pygame.key.get_pressed()

    # ══════════════════════════════════════════
    # 상태별 갱신(update) + 그리기(draw)
    # ══════════════════════════════════════════

    if game_state == "MENU":
        screen.blit(menu_background, (0, 0))
        draw_dim_overlay(130)

        title_surface = fonts["big"].render("몬스터 퇴치", True, config.WHITE)
        screen.blit(title_surface, (config.SCREEN_WIDTH // 2 - title_surface.get_width() // 2, 130))

        rects = menu_button_rects()
        ui.draw_menu_button(screen, fonts, "게임 시작", rects["start"], bg_color=config.GREEN)
        ui.draw_menu_button(screen, fonts, "환경 설정", rects["settings"], bg_color=config.MENU_SECONDARY_COLOR)
        ui.draw_menu_button(screen, fonts, "게임 종료", rects["quit"], bg_color=config.RED)

    elif game_state == "SETTINGS":
        screen.blit(menu_background, (0, 0))
        draw_dim_overlay(160)

        title_surface = fonts["big"].render("환경 설정", True, config.WHITE)
        screen.blit(title_surface, (config.SCREEN_WIDTH // 2 - title_surface.get_width() // 2, 110))

        rects = settings_button_rects()

        bgm_label = fonts["normal"].render(f"배경음악 음량  {int(round(bgm_volume * 100))}%", True, config.WHITE)
        screen.blit(bgm_label, (config.SCREEN_WIDTH // 2 - bgm_label.get_width() // 2, 225))
        ui.draw_menu_button(screen, fonts, "-", rects["bgm_minus"], bg_color=config.MENU_SECONDARY_COLOR)
        ui.draw_menu_button(screen, fonts, "+", rects["bgm_plus"], bg_color=config.MENU_SECONDARY_COLOR)

        sfx_label = fonts["normal"].render(f"효과음 음량  {int(round(sfx_volume * 100))}%", True, config.WHITE)
        screen.blit(sfx_label, (config.SCREEN_WIDTH // 2 - sfx_label.get_width() // 2, 305))
        ui.draw_menu_button(screen, fonts, "-", rects["sfx_minus"], bg_color=config.MENU_SECONDARY_COLOR)
        ui.draw_menu_button(screen, fonts, "+", rects["sfx_plus"], bg_color=config.MENU_SECONDARY_COLOR)

        ui.draw_menu_button(screen, fonts, "뒤로가기", rects["back"], bg_color=config.MENU_SECONDARY_COLOR)

    elif game_state == "PLAYING":
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
                monsters, hit_something, killed_monsters = player_module.resolve_attack(player, monsters)
                if hit_something:
                    sound_module.play_sound(sounds, "attack_hit", sfx_volume)

                # 처치한 몬스터마다 경험치 지급 + 확률적으로 아이템 드랍 (보스는 항상 드랍)
                for dead in killed_monsters:
                    leveled_up = player_module.add_xp(player, monster_module.get_xp_reward(dead))
                    if leveled_up:
                        sound_module.play_sound(sounds, "level_up", sfx_volume)

                    dead_center_x = dead["x"] + dead["size"] / 2
                    dead_center_y = dead["y"] + dead["size"] / 2
                    new_item = items_module.maybe_drop_item(dead_center_x, dead_center_y, dead["is_boss"])
                    if new_item:
                        items.append(new_item)

        # 동료(보호 대상) 이동 - 플레이어를 따라감 (몬스터가 쫓아갈 최신 위치를 먼저 계산)
        companion_module.update_follow(companion, player)
        companion_module.update_passive_heal(companion)  # 자가 힐 패시브 스킬

        # 몬스터 이동 - 플레이어와 동료 중 "지금 더 가까운 쪽"을 골라서 추격
        # (거리가 같으면 플레이어를 우선하도록 <= 사용)
        # ranged 타입은 이동하면서 발사하기도 하는데, 그 투사체를 여기서 모아둠
        player_center_x, player_center_y = player_module.get_center(player)
        companion_center_x, companion_center_y = companion_module.get_center(companion)
        for m in monsters:
            dist_to_player = monster_module.distance_to(m, player_center_x, player_center_y)
            dist_to_companion = monster_module.distance_to(m, companion_center_x, companion_center_y)

            if dist_to_player <= dist_to_companion:
                new_projectile = monster_module.move_toward_target(m, player_center_x, player_center_y)
            else:
                new_projectile = monster_module.move_toward_target(m, companion_center_x, companion_center_y)

            if new_projectile:
                projectiles.append(new_projectile)

        projectiles = monster_module.update_projectiles(projectiles)

        # 아이템: 바닥에 놓인 아이템 애니메이션 갱신 + 플레이어가 밟으면 즉시 습득/적용
        items_module.update(items)
        items, picked_types = items_module.check_pickup(
            items, pickup_effects, player_center_x, player_center_y, config.PLAYER_DISPLAY_SIZE[0] / 2)
        for item_type in picked_types:
            sound_module.play_sound(sounds, "item_pickup", sfx_volume)
            if item_type == "heal":
                player["hp"] = min(player["max_hp"], player["hp"] + config.ITEM_HEAL_AMOUNT)
            elif item_type == "power":
                player["bonus_damage"] += config.ITEM_POWER_BONUS
            elif item_type == "speed":
                player["bonus_speed"] += config.ITEM_SPEED_BONUS
        pickup_effects = items_module.update_pickup_effects(pickup_effects)

        # 플레이어 & 동료 피격 판정 (몬스터가 둘 중 누구에게 닿아도 데미지)
        player_module.take_contact_damage(player, monsters)
        companion_module.take_contact_damage(companion, monsters)

        # 투사체 피격 판정 (무적 시간 중이면 맞지 않음 - 위 접촉 피격 판정과 같은 타이머 공유)
        if player["invincible_timer"] == 0:
            projectiles, player_projectile_damage = monster_module.resolve_projectile_hits(
                projectiles, player_center_x, player_center_y, config.PLAYER_DISPLAY_SIZE[0] / 2)
            if player_projectile_damage > 0:
                player["hp"] = max(0, player["hp"] - player_projectile_damage * config.PLAYER_DEFENSE_MULTIPLIER)
                player["invincible_timer"] = config.PLAYER_INVINCIBLE_DURATION

        if companion["invincible_timer"] == 0:
            projectiles, companion_projectile_damage = monster_module.resolve_projectile_hits(
                projectiles, companion_center_x, companion_center_y, config.COMPANION_SIZE / 2)
            if companion_projectile_damage > 0:
                companion["hp"] = max(0, companion["hp"] - companion_projectile_damage)
                companion["invincible_timer"] = config.PLAYER_INVINCIBLE_DURATION

        # ── 상태 전환 판정 ──
        if player["hp"] <= 0:
            game_state = "GAME_OVER"
            game_over_reason = "플레이어가 쓰러졌습니다"
        elif companion["hp"] <= 0:
            game_state = "GAME_OVER"
            game_over_reason = "보호 대상이 쓰러졌습니다 (보호 실패)"
        elif len(monsters) == 0 and waves_spawned >= config.TOTAL_WAVES:
            stage_clear_timer = config.STAGE_CLEAR_DURATION
            game_state = "STAGE_CLEAR"

        draw_playing_scene()

    elif game_state == "STAGE_CLEAR":
        draw_playing_scene()  # 클리어 순간의 화면을 배경처럼 그대로 보여줌 (움직이지는 않음)
        draw_dim_overlay(120)
        ui.draw_end_message(screen, fonts, "STAGE CLEAR!", config.GREEN)

        stage_clear_timer -= 1
        if stage_clear_timer <= 0:
            story_state = story_module.create_story_state(current_stage)
            game_state = "STORY"

    elif game_state == "PAUSED":
        draw_playing_scene()  # 멈춘 화면을 그대로 배경처럼 보여줌 (아무것도 갱신하지 않음)
        draw_dim_overlay(150)

        ui.draw_end_message(screen, fonts, "PAUSED", config.WHITE)

        rects = pause_button_rects()
        ui.draw_menu_button(screen, fonts, "다시 진행", rects["resume"], bg_color=config.GREEN)
        ui.draw_menu_button(screen, fonts, "메인 화면으로 돌아가기", rects["to_menu"], bg_color=config.RED)

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
