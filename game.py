import pygame
import asyncio

# Initialize Pygame
pygame.init()

# Set up the display
WINDOW_SIZE = (800, 600)
screen = pygame.display.set_mode(WINDOW_SIZE)
pygame.display.set_caption("My Pygame Game")

# Colors
WHITE = (255, 255, 255)
RED = (255, 0, 0)

# Player properties
player_pos = [400, 300]
player_size = 40
player_speed = 5

async def main():
    clock = pygame.time.Clock()
    running = True
    
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                
        # Handle player movement
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT]:
            player_pos[0] -= player_speed
        if keys[pygame.K_RIGHT]:
            player_pos[0] += player_speed
        if keys[pygame.K_UP]:
            player_pos[1] -= player_speed
        if keys[pygame.K_DOWN]:
            player_pos[1] += player_speed
            
        # Keep player in bounds
        player_pos[0] = max(player_size/2, min(WINDOW_SIZE[0]-player_size/2, player_pos[0]))
        player_pos[1] = max(player_size/2, min(WINDOW_SIZE[1]-player_size/2, player_pos[1]))
        
        # Clear screen
        screen.fill(WHITE)
        
        # Draw player
        pygame.draw.circle(screen, RED, [int(player_pos[0]), int(player_pos[1])], player_size//2)
        
        # Update display
        pygame.display.flip()
        
        # Control game speed
        clock.tick(60)
        await asyncio.sleep(0)  # Required for browser compatibility

asyncio.run(main())