import pygame
import math

pygame.init()

# Screen setup
screen_width, screen_height = 1000, 600
screen = pygame.display.set_mode((screen_width, screen_height))
pygame.display.set_caption("Two-Player Arena Duel")

# Font setup for health and bullet display
font = pygame.font.Font(None, 36)

# Player properties
player1 = {
    'pos': [100, 300],
    'health': 100,
    'bullets': 10,
    'angle': 0,
    'projectiles': [],
    'can_shoot': True
}
player2 = {
    'pos': [700, 300],
    'health': 100,
    'bullets': 10,
    'angle': 0,
    'projectiles': [],
    'can_shoot': True
}
projectile_speed = 2  # Speed of the projectiles
rotation_speed = 0.2  # Rotation speed for players' arrows
move_speed = 0.2  # Movement speed in the facing direction
player_radius = 30  # Radius of the player circle
damage = 5  # Damage per hit

# Function to check if a projectile hits a player
def check_collision(projectile_pos, player_pos, player_radius):
    dist = math.sqrt((projectile_pos[0] - player_pos[0]) ** 2 + (projectile_pos[1] - player_pos[1]) ** 2)
    return dist <= player_radius

# Game loop
running = True
while running:
    screen.fill((0, 0, 0))  # Clear screen

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYUP:  # Reset shoot flag on key release
            if event.key == pygame.K_e:
                player1['can_shoot'] = True
            if event.key == pygame.K_SLASH:
                player2['can_shoot'] = True

    # Get keys pressed
    keys = pygame.key.get_pressed()
    
    # Player 1 movement and shooting (W/S for movement, A/D for rotation, E for shooting)
    if keys[pygame.K_a]:  # Rotate counterclockwise
        player1['angle'] -= rotation_speed
    if keys[pygame.K_d]:  # Rotate clockwise
        player1['angle'] += rotation_speed
    if keys[pygame.K_w]:  # Move forward in facing direction
        angle_rad = math.radians(player1['angle'])
        new_x = player1['pos'][0] + math.cos(angle_rad) * move_speed
        new_y = player1['pos'][1] + math.sin(angle_rad) * move_speed
        # Boundary check
        if player_radius <= new_x <= screen_width - player_radius:
            player1['pos'][0] = new_x
        if player_radius <= new_y <= screen_height - player_radius:
            player1['pos'][1] = new_y
    if keys[pygame.K_s]:  # Move backward in facing direction
        angle_rad = math.radians(player1['angle'])
        new_x = player1['pos'][0] - math.cos(angle_rad) * move_speed
        new_y = player1['pos'][1] - math.sin(angle_rad) * move_speed
        # Boundary check
        if player_radius <= new_x <= screen_width - player_radius:
            player1['pos'][0] = new_x
        if player_radius <= new_y <= screen_height - player_radius:
            player1['pos'][1] = new_y
    if keys[pygame.K_e] and player1['can_shoot'] and player1['bullets'] > 0:  # Shoot projectile if able and has bullets
        angle_rad = math.radians(player1['angle'])
        dx = math.cos(angle_rad) * projectile_speed
        dy = math.sin(angle_rad) * projectile_speed
        player1['projectiles'].append({'pos': player1['pos'][:], 'dir': [dx, dy]})
        player1['can_shoot'] = False  # Disable further shooting until key is released
        player1['bullets'] -= 1  # Decrease bullet count

    # Player 2 movement and shooting (Arrow keys for movement, / for shooting)
    if keys[pygame.K_LEFT]:  # Rotate counterclockwise
        player2['angle'] -= rotation_speed
    if keys[pygame.K_RIGHT]:  # Rotate clockwise
        player2['angle'] += rotation_speed
    if keys[pygame.K_UP]:  # Move forward in facing direction
        angle_rad = math.radians(player2['angle'])
        new_x = player2['pos'][0] + math.cos(angle_rad) * move_speed
        new_y = player2['pos'][1] + math.sin(angle_rad) * move_speed
        # Boundary check
        if player_radius <= new_x <= screen_width - player_radius:
            player2['pos'][0] = new_x
        if player_radius <= new_y <= screen_height - player_radius:
            player2['pos'][1] = new_y
    if keys[pygame.K_DOWN]:  # Move backward in facing direction
        angle_rad = math.radians(player2['angle'])
        new_x = player2['pos'][0] - math.cos(angle_rad) * move_speed
        new_y = player2['pos'][1] - math.sin(angle_rad) * move_speed
        # Boundary check
        if player_radius <= new_x <= screen_width - player_radius:
            player2['pos'][0] = new_x
        if player_radius <= new_y <= screen_height - player_radius:
            player2['pos'][1] = new_y
    if keys[pygame.K_SLASH] and player2['can_shoot'] and player2['bullets'] > 0:  # Shoot projectile if able and has bullets
        angle_rad = math.radians(player2['angle'])
        dx = math.cos(angle_rad) * projectile_speed
        dy = math.sin(angle_rad) * projectile_speed
        player2['projectiles'].append({'pos': player2['pos'][:], 'dir': [dx, dy]})
        player2['can_shoot'] = False  # Disable further shooting until key is released
        player2['bullets'] -= 1  # Decrease bullet count

    # Draw players
    pygame.draw.circle(screen, (255, 0, 0), (int(player1['pos'][0]), int(player1['pos'][1])), player_radius)
    pygame.draw.circle(screen, (0, 0, 255), (int(player2['pos'][0]), int(player2['pos'][1])), player_radius)

    # Draw arrows for each player to indicate direction
    arrow_length = 30
    player1_arrow_x = player1['pos'][0] + math.cos(math.radians(player1['angle'])) * arrow_length
    player1_arrow_y = player1['pos'][1] + math.sin(math.radians(player1['angle'])) * arrow_length
    pygame.draw.line(screen, (255, 255, 255), player1['pos'], (player1_arrow_x, player1_arrow_y), 3)

    player2_arrow_x = player2['pos'][0] + math.cos(math.radians(player2['angle'])) * arrow_length
    player2_arrow_y = player2['pos'][1] + math.sin(math.radians(player2['angle'])) * arrow_length
    pygame.draw.line(screen, (255, 255, 255), player2['pos'], (player2_arrow_x, player2_arrow_y), 3)

    # Update and draw projectiles (bullets) and check for collision
    new_projectiles_player1 = []
    for projectile in player1['projectiles']:
        projectile['pos'][0] += projectile['dir'][0]
        projectile['pos'][1] += projectile['dir'][1]
        # Check for collision with player2
        if check_collision(projectile['pos'], player2['pos'], player_radius):
            player2['health'] -= damage  # Reduce health on hit
        else:
            new_projectiles_player1.append(projectile)  # Keep projectile if no collision
        pygame.draw.circle(screen, (255, 0, 0), (int(projectile['pos'][0]), int(projectile['pos'][1])), 5)
    player1['projectiles'] = new_projectiles_player1  # Update projectiles list

    new_projectiles_player2 = []
    for projectile in player2['projectiles']:
        projectile['pos'][0] += projectile['dir'][0]
        projectile['pos'][1] += projectile['dir'][1]
        # Check for collision with player1
        if check_collision(projectile['pos'], player1['pos'], player_radius):
            player1['health'] -= damage  # Reduce health on hit
        else:
            new_projectiles_player2.append(projectile)  # Keep projectile if no collision
        pygame.draw.circle(screen, (0, 0, 255), (int(projectile['pos'][0]), int(projectile['pos'][1])), 5)
    player2['projectiles'] = new_projectiles_player2  # Update projectiles list

    # Display health and bullets for each player
    health_text_player1 = font.render(f"Player 1 Health: {player1['health']} Bullets: {player1['bullets']}", True, (255, 255, 255))
    health_text_player2 = font.render(f"Player 2 Health: {player2['health']} Bullets: {player2['bullets']}", True, (255, 255, 255))
    screen.blit(health_text_player1, (10, 10))
    screen.blit(health_text_player2, (screen_width - 400, 10))

    # Update display
    pygame.display.flip()

pygame.quit()
