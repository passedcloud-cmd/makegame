"""
items.py — 몬스터 처치 시 드랍되는 아이템(회복/공격력/이동속도) 담당
====================================================
아이템 하나는 바닥에 놓인 딕셔너리로 표현하고, 여러 개를 리스트에 담아 관리합니다
(monster.py의 몬스터, player.py의 플레이어와 같은 "딕셔너리로 상태 관리" 패턴).
플레이어가 위로 걸어가면 자동으로 줍고, 그 즉시 효과가 적용됩니다(효과 적용 자체는 main.py 몫).
"""

import random
import math
import pygame
import config

_TYPE_WEIGHTS = {"heal": 45, "power": 30, "speed": 25}

_TYPE_INFO = {
    "heal": {"color": config.ITEM_HEAL_COLOR, "label": f"+{config.ITEM_HEAL_AMOUNT} HP"},
    "power": {"color": config.ITEM_POWER_COLOR, "label": f"+{config.ITEM_POWER_BONUS} 공격력"},
    "speed": {"color": config.ITEM_SPEED_COLOR, "label": "+이동속도"},
}


def maybe_drop_item(center_x, center_y, is_boss):
    """몬스터가 죽은 자리에 확률적으로 아이템을 하나 떨어뜨림 (보스는 항상 드랍). 없으면 None."""
    if not is_boss and random.random() > config.ITEM_DROP_CHANCE:
        return None

    item_type = random.choices(list(_TYPE_WEIGHTS.keys()), weights=list(_TYPE_WEIGHTS.values()), k=1)[0]
    return {
        "x": center_x - config.ITEM_SIZE / 2,
        "y": center_y - config.ITEM_SIZE / 2,
        "type": item_type,
        "bob_timer": random.uniform(0, 6.28),   # 아이템마다 위아래로 떠 있는 위상을 다르게 시작
    }


def update(items):
    """바닥에 놓인 아이템들의 위아래로 살짝 떠 있는 애니메이션 타이머를 갱신."""
    for item in items:
        item["bob_timer"] += config.ITEM_BOB_SPEED


def check_pickup(items, pickup_effects, player_x, player_y, player_radius):
    """플레이어 위치와 겹치는 아이템을 줍고, 화면에 뜰 문구 효과를 pickup_effects에 추가.
    (남은 아이템 리스트, 이번에 주운 아이템들의 type 리스트)를 반환.
    실제로 스탯에 어떤 효과를 줄지 적용하는 건 main.py 몫 (아이템 종류만 알려줌)."""
    survivors = []
    picked_types = []
    pickup_radius = config.ITEM_SIZE / 2 + player_radius

    for item in items:
        center_x = item["x"] + config.ITEM_SIZE / 2
        center_y = item["y"] + config.ITEM_SIZE / 2
        distance = math.hypot(player_x - center_x, player_y - center_y)

        if distance < pickup_radius:
            picked_types.append(item["type"])
            info = _TYPE_INFO[item["type"]]
            pickup_effects.append({
                "x": center_x, "y": center_y,
                "text": info["label"], "color": info["color"],
                "timer": config.ITEM_PICKUP_FLASH_DURATION,
            })
        else:
            survivors.append(item)

    return survivors, picked_types


def update_pickup_effects(pickup_effects):
    """습득 문구 효과들의 타이머를 갱신하고, 다 끝난 것을 제거한 새 리스트를 반환."""
    survivors = []
    for effect in pickup_effects:
        effect["timer"] -= 1
        if effect["timer"] > 0:
            survivors.append(effect)
    return survivors


def draw(screen, items, camera_x, camera_y):
    """바닥에 놓인 아이템들을 위아래로 살짝 떠 있는 사각형으로 그림."""
    for item in items:
        bob_offset = math.sin(item["bob_timer"]) * config.ITEM_BOB_AMOUNT
        screen_x = item["x"] - camera_x
        screen_y = item["y"] - camera_y + bob_offset

        color = _TYPE_INFO[item["type"]]["color"]
        rect = pygame.Rect(int(screen_x), int(screen_y), config.ITEM_SIZE, config.ITEM_SIZE)
        pygame.draw.rect(screen, color, rect, border_radius=4)
        pygame.draw.rect(screen, config.BLACK, rect, 2, border_radius=4)


def draw_pickup_effects(screen, pickup_effects, fonts, camera_x, camera_y):
    """아이템을 주웠을 때 위로 떠오르며 사라지는 문구 효과를 그림.
    문구에 한글이 섞여 있어서(예: '공격력') 반드시 한글 지원 폰트(fonts["small"])를 받아서 사용."""
    font = fonts["small"]
    for effect in pickup_effects:
        progress = 1 - (effect["timer"] / config.ITEM_PICKUP_FLASH_DURATION)
        rise_offset = progress * 26
        text_surface = font.render(effect["text"], True, effect["color"])
        screen_x = effect["x"] - camera_x - text_surface.get_width() / 2
        screen_y = effect["y"] - camera_y - 20 - rise_offset
        screen.blit(text_surface, (screen_x, screen_y))
