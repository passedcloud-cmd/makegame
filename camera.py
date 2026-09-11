"""
camera.py — 카메라(뷰포트) 계산과 배경 스크롤 담당
====================================================
"카메라"는 실제로 움직이는 물체가 아니라, 그냥 숫자 두 개(camera_x, camera_y)예요.
"화면 왼쪽 위 모서리가 맵의 어느 좌표를 보고 있는지"를 나타냅니다.
"""

import pygame
import config


def load_background(path):
    """배경 이미지를 맵 크기 그대로 불러옴 (화면 크기로 늘리거나 줄이지 않음)."""
    return pygame.image.load(path).convert()


def compute_camera(player_center_x, player_center_y):
    """플레이어가 항상 화면 정중앙에 오도록 카메라 위치를 계산하고, 맵 경계 안으로 제한."""
    camera_x = player_center_x - config.SCREEN_WIDTH / 2
    camera_y = player_center_y - config.SCREEN_HEIGHT / 2

    camera_x = max(0, min(camera_x, config.MAP_WIDTH - config.SCREEN_WIDTH))
    camera_y = max(0, min(camera_y, config.MAP_HEIGHT - config.SCREEN_HEIGHT))

    return camera_x, camera_y


def draw_background(screen, background_image, camera_x, camera_y):
    """배경 이미지에서 카메라가 보고 있는 부분(화면 크기만큼)만 잘라서 그림."""
    visible_area = pygame.Rect(camera_x, camera_y, config.SCREEN_WIDTH, config.SCREEN_HEIGHT)
    screen.blit(background_image, (0, 0), area=visible_area)
