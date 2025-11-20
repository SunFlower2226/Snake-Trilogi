import pygame
import random
import os
import sys

pygame.init()

WIDTH, HEIGHT = 800, 600
CELL = 40
GRID_W, GRID_H = WIDTH // CELL, HEIGHT // CELL

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Snake Trilogy")
clock = pygame.time.Clock()

font_big = pygame.font.Font(None, 80)
font_med = pygame.font.Font(None, 48)
font_small = pygame.font.Font(None, 36)

# === СКИНЫ (обновлённая система разблокировки) ===
colors = [
    (0, 255, 0),     # 0 — Зелёный (сразу)
    (255, 50, 50),   # 1 — Красный
    (50, 150, 255),  # 2 — Синий
    (200, 0, 255),   # 3 — Фиолетовый
    (0, 180, 0),     # 4 — Тёмно-зелёный (новый!)
    (255, 215, 0)    # 5 — Золотой
]
color_names = ["Зелёный", "Красный", "Синий", "Фиолетовый", "Тёмно-зелёный", "Золотой"]

# Пороги разблокировки
unlock_scores = [0, 100, 200, 400, 750, 1000]  # соответствует индексу скина

# Рекорд
try:
    with open("highscore.txt", "r", encoding="utf-8") as f:
        high_score = int(f.read().strip())
except:
    high_score = 0

# Фон и музыка
has_bg = False
try:
    bg = pygame.image.load("assets/background.jpg")
    bg = pygame.transform.scale(bg, (WIDTH, HEIGHT))
    has_bg = True
except: pass

music_ok = False
try:
    pygame.mixer.music.load("assets/1-13_-wet-hands.mp3")
    pygame.mixer.music.set_volume(0.35)
    pygame.mixer.music.play(-1)
    music_ok = True
except: pass

# Бонусы
FOOD_TYPES = {
    "golden": {"color": (255,215,0), "points": 30, "effect": "double", "duration": 12000, "icon": "star",      "lifetime": 10000},
    "speed":  {"color": (50,200,255), "points": 15, "effect": "speed",  "duration": 10000, "icon": "lightning", "lifetime": 10000},
    "ghost":  {"color": (180,180,255),"points": 20, "effect": "ghost",  "duration": 10000, "icon": "ghost",     "lifetime": 10000},
    "bomb":   {"color": (150,0,0),    "points": -40,"effect": "bomb",                 "icon": "bomb",      "lifetime": 5000}
}

# Игровые переменные
snake = []
direction = (1, 0)
apple = (0, 0)
bonuses = []
score = 0
power_timer = 0
power_active = None
speed_mode = ghost_mode = double_mode = False
current_skin = 0
bonus_spawn_timer = 0
move_timer = 0
game_state = "menu"
selected_skin_in_menu = 0

def spawn_pos():
    while True:
        pos = (random.randint(0, GRID_W-1), random.randint(0, GRID_H-1))
        if pos not in snake and pos != apple and all(pos != b["pos"] for b in bonuses):
            return pos

def reset_game():
    global snake, direction, apple, bonuses, score, power_timer, power_active
    global speed_mode, ghost_mode, double_mode, bonus_spawn_timer, move_timer
    snake = [(GRID_W//2, GRID_H//2)]
    direction = (1, 0)
    apple = spawn_pos()
    bonuses = []
    score = 0
    power_timer = 0
    power_active = None
    speed_mode = ghost_mode = double_mode = False
    bonus_spawn_timer = pygame.time.get_ticks() + random.randint(8000, 15000)
    move_timer = pygame.time.get_ticks()

reset_game()

# === Основной цикл ===
running = True
while running:
    now = pygame.time.get_ticks()
    clock.tick(60)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if event.type == pygame.KEYDOWN:
            if game_state == "menu":
                if event.key == pygame.K_SPACE:
                    current_skin = selected_skin_in_menu
                    reset_game()
                    game_state = "playing"

                if event.key == pygame.K_UP:
                    selected_skin_in_menu = (selected_skin_in_menu - 1) % len(colors)
                if event.key == pygame.K_DOWN:
                    selected_skin_in_menu = (selected_skin_in_menu + 1) % len(colors)

            elif game_state == "playing":
                if event.key == pygame.K_ESCAPE:
                    game_state = "menu"
                    selected_skin_in_menu = current_skin
                if music_ok and event.key == pygame.K_m:
                    pygame.mixer.music.set_paused(not pygame.mixer.music.get_busy())

                if event.key in (pygame.K_w, pygame.K_UP)    and direction != (0, 1):  direction = (0, -1)
                if event.key in (pygame.K_s, pygame.K_DOWN)  and direction != (0, -1): direction = (0, 1)
                if event.key in (pygame.K_a, pygame.K_LEFT)  and direction != (1, 0):  direction = (-1, 0)
                if event.key in (pygame.K_d, pygame.K_RIGHT) and direction != (-1, 0): direction = (1, 0)

            elif game_state == "gameover":
                if event.key == pygame.K_SPACE:
                    game_state = "menu"

    # === Логика игры ===
    if game_state == "playing":
        if power_timer and now > power_timer:
            speed_mode = ghost_mode = double_mode = False
            power_timer = 0
            power_active = None

        delay = 90 if speed_mode else 140
        if now - move_timer >= delay:
            move_timer = now
            nx = (snake[0][0] + direction[0]) % GRID_W
            ny = (snake[0][1] + direction[1]) % GRID_H
            new_head = (nx, ny)

            if new_head in snake[1:] and not ghost_mode:
                game_state = "gameover"
            else:
                snake.insert(0, new_head)

                if new_head == apple:
                    score += 20 if double_mode else 10
                    apple = spawn_pos()
                else:
                    eaten = None
                    for b in bonuses[:]:
                        if new_head == b["pos"]:
                            eaten = b
                            bonuses.remove(b)
                            break
                    if eaten:
                        data = FOOD_TYPES[eaten["type"]]
                        if eaten["type"] == "bomb":
                            game_state = "gameover"
                        else:
                            pts = data["points"] * (2 if double_mode else 1)
                            score += pts
                            if "effect" in data:
                                if data["effect"] == "double":
                                    double_mode = True; power_active = "x2"
                                elif data["effect"] == "speed":
                                    speed_mode = True; power_active = "Скорость"
                                elif data["effect"] == "ghost":
                                    ghost_mode = True; power_active = "Призрак"
                                power_timer = now + data["duration"]
                    else:
                        snake.pop()

        if now > bonus_spawn_timer and len(bonuses) < 3:
            chosen = random.choices(["golden","speed","ghost","bomb"], weights=[30,30,30,10], k=1)[0]
            bonuses.append({
                "type": chosen,
                "pos": spawn_pos(),
                "spawn_time": now,
                "lifetime": FOOD_TYPES[chosen]["lifetime"]
            })
            bonus_spawn_timer = now + random.randint(10000, 18000)

        bonuses = [b for b in bonuses if now - b["spawn_time"] < b["lifetime"]]

        # === Рисование игры ===
        screen.blit(bg, (0,0)) if has_bg else screen.fill((15,15,35))

        for i, pos in enumerate(snake):
            r = pygame.Rect(pos[0]*CELL, pos[1]*CELL, CELL, CELL)
            c = colors[current_skin]
            if i == 0:
                pygame.draw.rect(screen, c, r.inflate(-8,-8))
                pygame.draw.rect(screen, (255,255,255), r.inflate(-8,-8), 3)
            else:
                pygame.draw.rect(screen, c, r.inflate(-6,-6))
                pygame.draw.rect(screen, (255,255,255), r.inflate(-6,-6), 2)

        # Яблоко
        ar = pygame.Rect(apple[0]*CELL, apple[1]*CELL, CELL, CELL)
        pygame.draw.circle(screen, (220,20,20), ar.center, CELL//2-4)
        pygame.draw.circle(screen, (255,100,100), (ar.centerx-10, ar.centery-10), 8)
        pygame.draw.line(screen, (139,69,19), (ar.centerx, ar.centery-18), (ar.centerx, ar.centery-28), 4)
        leaf = pygame.Surface((20,12), pygame.SRCALPHA)
        pygame.draw.ellipse(leaf, (0,200,0), (0,0,20,12))
        screen.blit(leaf, (ar.centerx+6, ar.centery-32))

        # Бонусы
        for b in bonuses:
            br = pygame.Rect(b["pos"][0]*CELL, b["pos"][1]*CELL, CELL, CELL)
            data = FOOD_TYPES[b["type"]]
            pygame.draw.circle(screen, data["color"], br.center, CELL//2-4)
            icon = font_med.render(data["icon"], True, (255,255,255))
            screen.blit(icon, icon.get_rect(center=br.center))

        # UI
        score_surf = font_med.render(f"Очки: {score}", True, (255,255,200))
        screen.blit(score_surf, (15,10))
        if power_timer:
            t = max(0, (power_timer - now)//1000 + 1)
            power_surf = font_small.render(f"{power_active} {t}с", True, (255,255,0))
            screen.blit(power_surf, (WIDTH - power_surf.get_width() - 15, 10))
        hint = font_small.render("ESC — меню | M — музыка", True, (180,180,180))
        screen.blit(hint, (15, HEIGHT-40))

    # === МЕНЮ ===
    elif game_state == "menu":
        screen.blit(bg, (0,0)) if has_bg else screen.fill((10,10,30))

        title = font_big.render("SNAKE TRILOGY", True, (255,255,100))
        screen.blit(title, title.get_rect(center=(WIDTH//2, 100)))

        rec = font_med.render(f"Рекорд: {high_score}", True, (255,255,255))
        screen.blit(rec, rec.get_rect(center=(WIDTH//2, 170)))

        for i in range(len(colors)):
            unlocked = high_score >= unlock_scores[i]
            col = colors[i] if unlocked else (100,100,100)
            lock_text = "" if unlocked else f" (нужно {unlock_scores[i]} очков)"
            name_text = font_med.render(f"{color_names[i]}{lock_text}", True, col)

            y = 240 + i * 50
            screen.blit(name_text, name_text.get_rect(center=(WIDTH//2 + 30, y)))

            if i == selected_skin_in_menu and unlocked:
                check = font_big.render("Checkmark", True, (0, 255, 0))
                screen.blit(check, (WIDTH//2 - 150, y - 35))

        hint1 = font_small.render("Up/Down — выбрать скин", True, (200,200,200))
        hint2 = font_small.render("SPACE — играть", True, (255,255,255))
        screen.blit(hint1, hint1.get_rect(center=(WIDTH//2, 520)))
        screen.blit(hint2, hint2.get_rect(center=(WIDTH//2, 550)))

    # === GAME OVER ===
    elif game_state == "gameover":
        screen.blit(bg, (0,0)) if has_bg else screen.fill((30,0,0))
        go = font_big.render("GAME OVER", True, (255,50,50))
        screen.blit(go, go.get_rect(center=(WIDTH//2,200)))
        final = font_med.render(f"Очки: {score}", True, (255,255,255))
        screen.blit(final, final.get_rect(center=(WIDTH//2,300)))
        if score > high_score:
            high_score = score
            with open("highscore.txt", "w", encoding="utf-8") as f:
                f.write(str(high_score))
            nr = font_med.render("НОВЫЙ РЕКОРД!", True, (255,215,0))
            screen.blit(nr, nr.get_rect(center=(WIDTH//2,360)))
        restart = font_small.render("Пробел — в меню", True, (200,200,200))
        screen.blit(restart, restart.get_rect(center=(WIDTH//2,480)))

    pygame.display.flip()

if music_ok:
    pygame.mixer.music.stop()
pygame.quit()
sys.exit()