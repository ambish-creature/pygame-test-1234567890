import sys
sys.path.append("/opt/homebrew/lib/python3.11/site-packages")
import pygame
import random
import math

# Initialize Pygame
pygame.init()

# Screen and map settings
screen_width, screen_height = 1500, 1500
map_width, map_height = 7500, 7500
screen = pygame.display.set_mode((screen_width, screen_height))
pygame.display.set_caption("2D Shooting Game")

# Player settings
player_color = (255, 182, 193)
player_radius = 20
player_x, player_y = map_width // 2, map_height // 2  # Start at map center
player_speed = 1
player_health = 100
player_max_health = 100
player_regen_delay = 10000  # 10 seconds in milliseconds
player_last_hit = pygame.time.get_ticks()

# Chest settings
chest_color = (139, 69, 19)
chest_size = 30
num_chests = 100
chests = pygame.sprite.Group()  # Create a sprite group for chests

# Weapon settings
ar_damage = 20
ar_fire_rate = 5  # bullets per second
ar_mag_size = 30
ar_reload_time = 2000  # milliseconds
sr_damage = 100
sr_fire_rate = 0.5
sr_mag_size = 3
sr_reload_time = 2000

# Bullet settings
bullet_color = (123, 123, 123)
bullet_radius = 5
bullet_speed = 10
bullet_trail_duration = 1000  # milliseconds
bullets = pygame.sprite.Group()  # Create a sprite group for bullets

# Player inventory
player_inventory = {
    "AR": None,
    "SR": None
}
current_weapon = "AR"  # Start with AR selected

# Barrier settings
barrier_color = (128, 128, 128)
barrier_width = 50
barrier_height = 50
num_barriers = 300
barriers = pygame.sprite.Group()  # Create a sprite group for barriers

# Grid settings
grid_color = (64, 64, 64)
grid_size = 50

# UI settings
font = pygame.font.Font(None, 36)

# Function to generate chests and barriers at the start
def generate_map_elements():
    global chests, barriers

    # Generate chests
    for _ in range(num_chests):
        while True:  # Loop until a valid chest position is found
            chest_x = random.randint(chest_size, map_width - chest_size)
            chest_y = random.randint(chest_size, map_height - chest_size)
            chest_rect = pygame.Rect(chest_x, chest_y, chest_size, chest_size)
            if not pygame.sprite.spritecollideany(chest_rect, barriers.sprites()):
                chest = pygame.sprite.Sprite()
                chest.image = pygame.Surface((chest_size, chest_size))
                chest.image.fill(chest_color)
                chest.rect = chest_rect
                chests.add(chest)
                break

    for _ in range(num_barriers):
        orientation = random.choice(["horizontal", "vertical"])
        if orientation == "horizontal":
            barrier_width = grid_size * 3
            barrier_height = grid_size
        else:
            barrier_width = grid_size
            barrier_height = grid_size * 3

        while True:  # Loop until a valid barrier position is found
            barrier_x = random.randint(0, map_width - barrier_width)
            barrier_y = random.randint(0, map_height - barrier_height)
            barrier_rect = pygame.Rect(barrier_x, barrier_y, barrier_width, barrier_height)
            if not pygame.sprite.spritecollideany(barrier_rect, chests.sprites()):
                barrier = pygame.sprite.Sprite()
                barrier.image = pygame.Surface((barrier_width, barrier_height))
                barrier.image.fill(barrier_color)
                barrier.rect = barrier_rect
                barriers.add(barrier)
                break

# Function to handle chest interaction
f_key_pressed = False  # Global variable to track 'F' key state

def interact_with_chest(player_x, player_y):
    global f_key_pressed  # Access the global variable
    keys = pygame.key.get_pressed()

    closest_chest = None
    closest_distance = float('inf')  # Initialize with a very large distance

    for chest in chests:
        distance = math.sqrt((player_x - chest.rect.centerx) ** 2 + (player_y - chest.rect.centery) ** 2)
        if distance <= closest_distance:
            closest_chest = chest
            closest_distance = distance

    if closest_chest != None and closest_distance <= player_radius + chest_size and f_key_pressed:
        # Give player a random weapon if they don't have it
        weapon_type = random.choice(["AR", "SR"])
        if player_inventory[weapon_type] is None:
            player_inventory[weapon_type] = {
                "ammo": weapon_type == "AR" and ar_mag_size or sr_mag_size,
                "reloading": False,
                "last_shot": 0
            }
        if closest_chest in chest:
            chests.remove(closest_chest)  # Remove the chest after interaction

# Function to handle shooting
def shoot(weapon_type):
    if player_inventory[weapon_type] is not None:
        weapon = player_inventory[weapon_type]
        if weapon["ammo"] > 0 and not weapon["reloading"]:
            # Calculate bullet direction based on mouse position
            mouse_x, mouse_y = pygame.mouse.get_pos()
            angle = math.atan2(mouse_y - player_y, mouse_x - player_x)

            # Create a new bullet
            bullet = pygame.sprite.Sprite()
            bullet.image = pygame.Surface((bullet_radius, bullet_radius))
            bullet.image.fill(bullet_color)
            bullet.rect = bullet.image.get_rect()
            bullet.rect.center = (player_x, player_y)
            bullet.angle = angle
            bullet.speed = bullet_speed
            bullet.trail = []  # Add a trail list to the bullet
            bullets.add(bullet)

            # Update weapon state
            weapon["ammo"] -= 1
            weapon["last_shot"] = pygame.time.get_ticks()

# Function to handle reloading
def reload(weapon_type):
    if player_inventory[weapon_type] is not None:
        weapon = player_inventory[weapon_type]
        if weapon["ammo"] < (weapon_type == "AR" and ar_mag_size or sr_mag_size) and not weapon["reloading"]:
            weapon["reloading"] = True
            weapon["reload_start"] = pygame.time.get_ticks()

# Function to update bullets
def update_bullets():
    for bullet in bullets:
        # Move the bullet
        bullet.rect.centerx += bullet.speed * math.cos(bullet.angle)
        bullet.rect.centery += bullet.speed * math.sin(bullet.angle)

        # Add current position to the trail
        bullet.trail.append((bullet.rect.centerx, bullet.rect.centery))

        # Limit trail length
        if len(bullet.trail) > bullet_trail_duration // 10:  # Adjust divisor as needed
            bullet.trail.pop(0)

        # Remove bullets that have gone off-screen
        if (bullet.rect.centerx < 0 or bullet.rect.centerx > map_width or
            bullet.rect.centery < 0 or bullet.rect.centery > map_height):
            bullets.remove(bullet)

def draw_trails(player_x, player_y):
    for bullet in bullets:
        trail = bullet.trail  # Access the trail list
        if len(trail) > 1:  # Need at least two points to draw a line
            pygame.draw.line(screen, bullet_color, False, trail, width=3)  # Draw lines, adjust thickness as needed
            pygame.draw.line(screen, (255, 0, 0), False, [(player_x, player_y), trail[0]], width=3)  # Draw a line from the player to the first point in the trail

# Function to handle player health regeneration
def regenerate_health():
    global player_health
    time_since_hit = pygame.time.get_ticks() - player_last_hit
    if player_health < player_max_health and time_since_hit > player_regen_delay:
        player_health += 1

# Function to draw the UI
def draw_ui():
    weapon_text = font.render(f"Weapon: {current_weapon}", True, (255, 255, 255))
    ammo_text = font.render(f"Ammo: {player_inventory[current_weapon]['ammo'] if player_inventory[current_weapon] else 0}", True, (255, 255, 255))
    health_text = font.render(f"Health: {player_health}", True, (255, 255, 255))
    screen.blit(weapon_text, (10, screen_height - 40))
    screen.blit(ammo_text, (10, screen_height - 80))
    screen.blit(health_text, (10, screen_height - 120))

# Game loop
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_f:
                interact_with_chest(player_x, player_y)
            elif event.key == pygame.K_r:
                reload("AR")
                reload("SR")
            elif event.key == pygame.K_1:
                current_weapon = "AR"
            elif event.key == pygame.K_2:
                current_weapon = "SR"
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # Left click
                shoot("AR")
                draw_trails(player_x, player_y)
            elif event.button == 3:  # Right click
                shoot("SR")
                draw_trails(player_x, player_y)
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_f:
                f_key_pressed = True
        if event.type == pygame.KEYUP:
            if event.key == pygame.K_f:
                f_key_pressed = False
        


    # Handle player movement
    keys = pygame.key.get_pressed()
    if keys[pygame.K_a] or keys[pygame.K_LEFT]:
        player_x -= player_speed
    if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
        player_x += player_speed
    if keys[pygame.K_w] or keys[pygame.K_UP]:
        player_y -= player_speed
    if keys[pygame.K_s] or keys[pygame.K_DOWN]:
        player_y += player_speed
    if keys[pygame.K_f]:
        interact_with_chest(player_x, player_y)

    # Keep player within map bounds
    player_x = max(0, min(player_x, map_width))
    player_y = max(0, min(player_y, map_height))

    
    
    # Update bullets
    update_bullets()

    # Regenerate health
    regenerate_health()

    # Calculate background offset based on player position
    background_offset_x = (map_width // 2) - player_x
    background_offset_y = (map_height // 2) - player_y

    # Clear the screen
    screen.fill((0, 0, 0))

    # Draw grid
    for i in range(0, map_width, grid_size):
        pygame.draw.line(screen, grid_color, (i + background_offset_x, 0), (i + background_offset_x, screen_height))
    for j in range(0, map_height, grid_size):
        pygame.draw.line(screen, grid_color, (0, j + background_offset_y), (screen_width, j + background_offset_y))
        
    # Draw chests
    for chest in chests:
        screen.blit(chest.image, (chest.rect.x + background_offset_x - chest_size // 2,
                                               chest.rect.y + background_offset_y - chest_size // 2))

    # Draw barriers
    for barrier in barriers:
        screen.blit(barrier.image, (barrier.rect.x + background_offset_x,
                                                 barrier.rect.y + background_offset_y))

    # Draw bullets
    for bullet in bullets:
        screen.blit(bullet.image, (bullet.rect.x + background_offset_x - bullet_radius // 2,
                                               bullet.rect.y + background_offset_y - bullet_radius // 2))

    # Draw the player
    pygame.draw.circle(screen, player_color, (screen_width // 2, screen_height // 2), player_radius)

    # Draw UI
    draw_ui()

    # Generate map elements
    generate_map_elements()

    pygame.display.flip()  # Update the display

pygame.quit()
