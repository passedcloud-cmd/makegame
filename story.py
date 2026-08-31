"""
story.py — 스테이지 클리어 후 나오는 대화(스토리) 장면 담당
====================================================
비주얼노벨처럼 캐릭터 클로즈샷 + 대화창을 보여주고,
스페이스바/엔터를 누르면 다음 대사로 넘어갑니다.
"""

import pygame
import config

# 스테이지별 대사 목록. 여기 문장만 고치거나 추가하면 스토리가 바뀝니다.
STAGE_DIALOGUES = {
    1: [
        "휴... 겨우 첫 웨이브를 막아냈다.",
        "하지만 이건 시작에 불과해.",
        "더 강한 몬스터들이 몰려온다는 소문이 있어.",
        "각오를 다잡고 다음으로 가자.",
    ],
    2: [
        "두 번째 관문도 통과했다.",
        "몬스터들의 기세가 점점 거세지는 게 느껴진다.",
        "조금만 더 버티면 돼.",
    ],
    4: [
        "저 거대한 몬스터를... 정말로 쓰러뜨렸다.",
        "보스라 불릴 만한 존재였어.",
        "하지만 심상치 않은 기운이 아직 남아있다.",
        "진짜 마지막 싸움이 우리를 기다리고 있는 것 같아.",
    ],
    5: [
        "드디어... 모든 게 끝났다.",
        "가장 강력했던 보스까지 쓰러뜨렸어.",
        "이 모든 여정 동안, 네가 곁에 있어줘서 다행이었어.",
        "이제 우리는 평화로운 일상으로 돌아갈 수 있겠지.",
    ],
}

# 정의되지 않은 스테이지(3 이상)를 클리어했을 때 보여줄 기본 대사
DEFAULT_DIALOGUE = ["스테이지 클리어!", "다음 스테이지로 이동합니다."]


def get_dialogue_for_stage(stage):
    """해당 스테이지의 대사 목록을 반환. 없으면 기본 대사를 사용."""
    return STAGE_DIALOGUES.get(stage, DEFAULT_DIALOGUE)


def create_story_state(stage):
    """대화 진행 상태를 딕셔너리로 생성. line_index는 '지금 몇 번째 대사인지'."""
    return {
        "lines": get_dialogue_for_stage(stage),
        "line_index": 0,
    }


def advance(story_state):
    """다음 대사로 넘어감. 마지막 대사를 이미 보여준 뒤라면 True(스토리 종료)를 반환."""
    story_state["line_index"] += 1
    return story_state["line_index"] >= len(story_state["lines"])


def load_portrait(path):
    """캐릭터 클로즈샷 이미지를 불러옴. main.py에서 화면 생성 후 한 번만 호출."""
    return pygame.image.load(path).convert_alpha()


def _wrap_text(font, text, max_width):
    """긴 대사가 대화창 폭을 넘어가면 자동으로 줄바꿈. 글자 단위로 넓이를 재서 자름."""
    lines = []
    current = ""
    for ch in text:
        test = current + ch
        if font.size(test)[0] > max_width and current:
            lines.append(current)
            current = ch
        else:
            current = test
    if current:
        lines.append(current)
    return lines


def draw(screen, portrait_image, story_state, fonts):
    """캐릭터 클로즈샷(왼쪽) + 대화창(하단)을 그림."""
    screen.fill(config.BLACK)  # 스토리 장면 배경은 어둡게

    # ── 캐릭터 클로즈샷: 화면 왼쪽에 배치 ──
    portrait_x = 60
    portrait_y = config.SCREEN_HEIGHT - portrait_image.get_height() - 170
    screen.blit(portrait_image, (portrait_x, portrait_y))

    # ── 대화창: 화면 하단 ──
    box_height = 140
    box_rect = pygame.Rect(20, config.SCREEN_HEIGHT - box_height - 20,
                            config.SCREEN_WIDTH - 40, box_height)
    pygame.draw.rect(screen, config.WHITE, box_rect, border_radius=10)
    pygame.draw.rect(screen, config.BLACK, box_rect, 3, border_radius=10)

    font = fonts["normal"]
    current_line = story_state["lines"][story_state["line_index"]]
    wrapped_lines = _wrap_text(font, current_line, box_rect.width - 48)

    text_y = box_rect.y + 24
    for line in wrapped_lines:
        text_surface = font.render(line, True, config.BLACK)
        screen.blit(text_surface, (box_rect.x + 24, text_y))
        text_y += 34

    # 진행 안내 (몇 번째 대사인지 + 조작 안내)
    total = len(story_state["lines"])
    progress_text = font.render(
        f"{story_state['line_index'] + 1} / {total}   (Space 또는 Enter로 계속)", True, (130, 130, 130))
    screen.blit(progress_text, (box_rect.x + 24, box_rect.bottom - 36))
