"""
sound.py — 배경음악(BGM)과 효과음(SFX) 재생 담당
====================================================
pygame.mixer를 사용합니다. init_mixer()는 pygame.init() 직후,
load_sounds()/play_background_music()은 화면이 만들어진 뒤 main.py에서
각각 한 번만 호출하면 됩니다.

사운드 장치가 없는 환경(예: headless 테스트)에서도 게임 자체는 죽지 않도록,
믹서 초기화나 로딩이 실패하면 조용히 무시하고 "소리 없이" 동작합니다.
"""

import pygame


def init_mixer():
    """사운드 재생을 위한 pygame 믹서를 초기화. 실패해도(사운드 장치 없음 등) 게임은 계속 진행."""
    try:
        pygame.mixer.init()
    except pygame.error:
        pass


def load_sounds():
    """효과음들을 불러와서 딕셔너리로 반환. 믹서가 없거나 로딩에 실패하면 빈 딕셔너리를 반환."""
    if not pygame.mixer.get_init():
        return {}

    try:
        return {
            "attack_hit": pygame.mixer.Sound("assets/sounds/attack_hit.wav"),
            "item_pickup": pygame.mixer.Sound("assets/sounds/item_pickup.wav"),
            "level_up": pygame.mixer.Sound("assets/sounds/level_up.wav"),
        }
    except pygame.error:
        return {}


def play_background_music(path="assets/sounds/bgm.wav", volume=0.4):
    """배경음악을 무한 반복 재생. 실패해도 조용히 무시."""
    if not pygame.mixer.get_init():
        return
    try:
        pygame.mixer.music.load(path)
        pygame.mixer.music.set_volume(volume)
        pygame.mixer.music.play(loops=-1)
    except pygame.error:
        pass


def play_sound(sounds, name, volume=0.6):
    """효과음 하나를 재생 (이름이 없거나 로딩 실패한 사운드면 아무 일도 하지 않음)."""
    sound = sounds.get(name)
    if sound:
        sound.set_volume(volume)
        sound.play()


def set_music_volume(volume):
    """환경설정 화면에서 배경음악 음량을 실시간으로 바꿀 때 사용."""
    if pygame.mixer.get_init():
        try:
            pygame.mixer.music.set_volume(volume)
        except pygame.error:
            pass


def pause_music():
    """일시정지(ESC) 시 배경음악을 함께 멈춤."""
    if pygame.mixer.get_init():
        pygame.mixer.music.pause()


def resume_music():
    """일시정지 해제 시 배경음악을 이어서 재생."""
    if pygame.mixer.get_init():
        pygame.mixer.music.unpause()
