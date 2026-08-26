import pygame
import sys
import random
import math
 
pygame.init()
 
# ===== 화면 설정 =====
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("몬스터 배틀 게임")
clock = pygame.time.Clock()
FPS = 60
 
# ===== 색상 =====
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
BLUE = (50, 150, 255)
RED = (220, 60, 60)
GREEN = (60, 200, 100)
YELLOW = (255, 220, 50)
GRAY = (100, 100, 100)
 
font = pygame.font.SysFont(None, 36)
big_font = pygame.font.SysFont(None, 72)
 
 
class Player:
    def __init__(self):
        self.x = WIDTH // 2
        self.y = HEIGHT // 2
        self.size = 30
        self.speed = 5
        self.hp = 100
        self.max_hp = 100
        self.attack_range = 60          # 공격이 닿는 거리
        self.attack_cooldown = 0        # 공격 후 다시 쓸 수 있을 때까지 남은 시간
        self.attack_cooldown_max = 20   # 약 0.33초마다 공격 가능
        self.attacking_timer = 0        # 공격 이펙트를 보여주는 시간
 
    def move(self, keys):
        dx, dy = 0, 0
        if keys[pygame.K_w]:
            dy -= self.speed
        if keys[pygame.K_s]:
            dy += self.speed
        if keys[pygame.K_a]:
            dx -= self.speed
        if keys[pygame.K_d]:
            dx += self.speed
 
        self.x += dx
        self.y += dy
 
        # 화면 밖으로 나가지 못하게 막기
        self.x = max(self.size, min(WIDTH - self.size, self.x))
        self.y = max(self.size, min(HEIGHT - self.size, self.y))
 
    def update(self):
        if self.attack_cooldown > 0:
            self.attack_cooldown -= 1
        if self.attacking_timer > 0:
            self.attacking_timer -= 1
 
    def try_attack(self, monsters):
        if self.attack_cooldown == 0:
            self.attack_cooldown = self.attack_cooldown_max
            self.attacking_timer = 10
            for m in monsters:
                if m.alive:
                    dist = math.hypot(m.x - self.x, m.y - self.y)
                    if dist <= self.attack_range:
                        m.take_damage(25)
 
    def draw(self, screen):
        pygame.draw.circle(screen, BLUE, (int(self.x), int(self.y)), self.size)
 
        if self.attacking_timer > 0:
            pygame.draw.circle(screen, YELLOW, (int(self.x), int(self.y)), self.attack_range, 3)
 
        # 체력바
        bar_width = 200
        bar_x, bar_y = 10, 10
        pygame.draw.rect(screen, GRAY, (bar_x, bar_y, bar_width, 20))
        hp_width = int(bar_width * (self.hp / self.max_hp))
        pygame.draw.rect(screen, GREEN, (bar_x, bar_y, hp_width, 20))
        hp_text = font.render(f"HP: {self.hp}/{self.max_hp}", True, BLACK)
        screen.blit(hp_text, (bar_x + 5, bar_y - 2))
 
 
class Monster:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.size = 25
        self.speed = 2
        self.hp = 50
        self.max_hp = 50
        self.alive = True
        self.attack_cooldown = 0
 
    def update(self, player):
        if not self.alive:
            return
 
        # 플레이어 쪽으로 한 걸음씩 이동 (추적)
        dx = player.x - self.x
        dy = player.y - self.y
        dist = math.hypot(dx, dy)
        if dist > 1:
            dx, dy = dx / dist, dy / dist
            self.x += dx * self.speed
            self.y += dy * self.speed
 
        # 플레이어에 닿으면 데미지
        if self.attack_cooldown > 0:
            self.attack_cooldown -= 1
        else:
            touch_dist = self.size + player.size
            if dist <= touch_dist:
                player.hp = max(0, player.hp - 10)
                self.attack_cooldown = 30
 
    def take_damage(self, amount):
        self.hp -= amount
        if self.hp <= 0:
            self.alive = False
 
    def draw(self, screen):
        if not self.alive:
            return
        pygame.draw.circle(screen, RED, (int(self.x), int(self.y)), self.size)
 
        bar_width = 40
        bar_x = int(self.x - bar_width / 2)
        bar_y = int(self.y - self.size - 15)
        pygame.draw.rect(screen, GRAY, (bar_x, bar_y, bar_width, 6))
        hp_width = int(bar_width * (self.hp / self.max_hp))
        pygame.draw.rect(screen, GREEN, (bar_x, bar_y, hp_width, 6))
 
 
def spawn_monster():
    edge = random.choice(["top", "bottom", "left", "right"])
    if edge == "top":
        x, y = random.randint(0, WIDTH), -30
    elif edge == "bottom":
        x, y = random.randint(0, WIDTH), HEIGHT + 30
    elif edge == "left":
        x, y = -30, random.randint(0, HEIGHT)
    else:
        x, y = WIDTH + 30, random.randint(0, HEIGHT)
    return Monster(x, y)
 
 
def new_game_state():
    return {
        "player": Player(),
        "monsters": [spawn_monster() for _ in range(3)],
        "score": 0,
        "spawn_timer": 0,
        "game_over": False,
    }
 
 
def main():
    state = new_game_state()
    spawn_interval = 120  # 약 2초마다 몬스터 추가 등장
 
    running = True
    while running:
        clock.tick(FPS)
 
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_z and not state["game_over"]:
                    state["player"].try_attack(state["monsters"])
                if event.key == pygame.K_r and state["game_over"]:
                    state = new_game_state()
 
        if not state["game_over"]:
            player = state["player"]
            monsters = state["monsters"]
 
            keys = pygame.key.get_pressed()
            player.move(keys)
            player.update()
 
            for m in monsters:
                m.update(player)
 
            before = len(monsters)
            still_alive = [m for m in monsters if m.alive]
            state["score"] += (before - len(still_alive)) * 10
            state["monsters"] = still_alive
 
            state["spawn_timer"] += 1
            if state["spawn_timer"] >= spawn_interval:
                state["spawn_timer"] = 0
                state["monsters"].append(spawn_monster())
 
            if player.hp <= 0:
                state["game_over"] = True
 
        # ===== 화면 그리기 =====
        screen.fill(WHITE)
        state["player"].draw(screen)
        for m in state["monsters"]:
            m.draw(screen)
 
        score_text = font.render(f"Score: {state['score']}", True, BLACK)
        screen.blit(score_text, (WIDTH - 150, 10))
 
        info_text = font.render("WASD: 이동 / Z: 공격", True, BLACK)
        screen.blit(info_text, (10, HEIGHT - 30))
 
        if state["game_over"]:
            over_text = big_font.render("GAME OVER", True, RED)
            screen.blit(over_text, (WIDTH // 2 - over_text.get_width() // 2, HEIGHT // 2 - 60))
            restart_text = font.render(
                f"최종 점수: {state['score']}  (R키를 눌러 다시 시작)", True, BLACK
            )
            screen.blit(restart_text, (WIDTH // 2 - restart_text.get_width() // 2, HEIGHT // 2 + 20))
 
        pygame.display.flip()
 
    pygame.quit()
    sys.exit()
 
 
if __name__ == "__main__":
    main()
 