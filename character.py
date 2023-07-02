import pygame
import constants
import math
import weapon


class Character():
    def __init__(self, x, y, health, mob_animations, char_type, boss, size):
        self.char_type = char_type
        self.boss = boss
        self.score = 0
        self.flip = False
        self.animation_list = mob_animations[char_type]
        self.frame_index = 0
        self.action = 0  # 0: idle, 1: running
        self.running = False
        self.health = health
        self.alive = True
        self.update_time = pygame.time.get_ticks()
        # If player gets hit, cooldown to avoid very fast hits
        self.hit = False
        self.last_hit = pygame.time.get_ticks()
        self.last_attack = pygame.time.get_ticks()
        self.stunned = False

        self.image = self.animation_list[self.action][self.frame_index]  # 0 is the idle animation list
        # Using tile size as rect dimensions makes all characters the same size in game
        # x, y, width, height of rectangle. Size allows us to make the rectangle bigger for bosses etc.
        # Subtracted -1 because the tile set is too narrow for the player to move easily
        self.rect = pygame.Rect(0, 0, constants.TILE_SIZE * size - 1, constants.TILE_SIZE * size - 1)
        self.rect.center = (x, y)

    def move(self, dx, dy, obstacle_tiles, exit_tile=None):
        screen_scroll = [0, 0]
        level_complete = False
        self.running = False
        # If player is moving, set running to true to animate running images
        if dx != 0 or dy != 0:
            self.running = True

        # If moving left, flip player image to left, otherwise don't flip
        if dx < 0:
            self.flip = True
        if dx > 0:
            self.flip = False

        # Control diagonal speed (Pythagoras)
        # If player is moving diagonally, avoid moving very fast
        if dx != 0 and dy != 0:
            dx = dx * (math.sqrt(2) / 2)
            dy = dy * (math.sqrt(2) / 2)

        # Check for collision with map in x direction
        self.rect.x += dx
        for obstacle in obstacle_tiles:
            # 1. index is the rectangle of obstacle
            # Check the rect collisions
            if obstacle[1].colliderect(self.rect):
                # Check which side the collision is from
                if dx > 0:
                    self.rect.right = obstacle[1].left
                if dx < 0:
                    self.rect.left = obstacle[1].right
        # Check for collision with map in y direction
        self.rect.y += dy
        for obstacle in obstacle_tiles:
            # 1. index is the rectangle of obstacle
            # Check the rect collisions
            if obstacle[1].colliderect(self.rect):
                # Check which side the collision is from
                if dy> 0:
                    self.rect.bottom = obstacle[1].top
                if dy < 0:
                    self.rect.top = obstacle[1].bottom

        # Move screen depending on player position
        if self.char_type == 0:
            # Check collision with exit ladder
            if exit_tile[1].colliderect(self.rect):
                # Check if player is close to the center of exit ladder
                exit_dist = math.sqrt(((self.rect.centerx - exit_tile[1].centerx) ** 2) + ((self.rect.centery - exit_tile[1].centery) ** 2))
                if exit_dist < 25:
                    level_complete = True
                    print("Exit")

            # Move camera left-right
            if self.rect.right > (constants.SCREEN_WIDTH - constants.SCROLL_THRESH):
                screen_scroll[0] = (constants.SCREEN_WIDTH - constants.SCROLL_THRESH) - self.rect.right
                # Player freezes at position
                self.rect.right = constants.SCREEN_WIDTH - constants.SCROLL_THRESH
            if self.rect.left < constants.SCROLL_THRESH:
                screen_scroll[0] = constants.SCROLL_THRESH - self.rect.left
                self.rect.left = constants.SCROLL_THRESH

            # Move camera up-down
            if self.rect.bottom > (constants.SCREEN_HEIGHT - constants.SCROLL_THRESH):
                screen_scroll[1] = (constants.SCREEN_HEIGHT - constants.SCROLL_THRESH) - self.rect.bottom
                # Player freezes at position
                self.rect.bottom = constants.SCREEN_HEIGHT - constants.SCROLL_THRESH
            if self.rect.top < constants.SCROLL_THRESH:
                screen_scroll[1] = constants.SCROLL_THRESH - self.rect.top
                self.rect.top = constants.SCROLL_THRESH

        return screen_scroll, level_complete

    def ai(self, player, obstacle_tiles, screen_scroll, fireball_image):
        clipped_line = ()
        stun_cooldown = 150
        ai_dx = 0
        ai_dy = 0
        fireball = None

        # Reposition mobs based on screen scroll
        self.rect.x += screen_scroll[0]
        self.rect.y += screen_scroll[1]

        # Create line of sight from enemy to player
        line_of_sight = ((self.rect.centerx, self.rect.centery), (player.rect.centerx, player.rect.centery))
        # pygame.draw.line(surface, constants.RED, line_of_sight[0], line_of_sight[1])
        # Check if line of sight passes through an obstacle tile
        for obstacle in obstacle_tiles:
            # First index is its rectangle
            if obstacle[1].clipline(line_of_sight):
                # Returns the actual line and not true or false
                # If there is a direct line of sight, it returns ()
                clipped_line = obstacle[1].clipline(line_of_sight)

        # Check distance to player with pythagoras
        dist = math.sqrt(((self.rect.centerx - player.rect.centerx) ** 2) + ((self.rect.centery - player.rect.centery) ** 2))
        # If enemy has clear line of sight and is within the allowed range to the player
        if not clipped_line and dist > constants.ENEMY_RANGE_TO_PLAYER:
            if self.rect.centerx > player.rect.centerx:
                ai_dx = -constants.ENEMY_SPEED
            if self.rect.centerx < player.rect.centerx:
                ai_dx = constants.ENEMY_SPEED
            if self.rect.centery > player.rect.centery:
                ai_dy = -constants.ENEMY_SPEED
            if self.rect.centery < player.rect.centery:
                ai_dy = constants.ENEMY_SPEED

        if self.alive:
            # Move towards player if not stunned
            if not self.stunned:
                self.move(ai_dx, ai_dy, obstacle_tiles)
                # Enemy attacks player if in range
                if dist < constants.ATTACK_RANGE and not player.hit:
                    player.health -= 10
                    player.hit = True
                    player.last_hit = pygame.time.get_ticks()
                # Boss enemies shoot fireballs
                fireball_cooldown = 700
                if self.boss:
                    if dist < 500:
                        if pygame.time.get_ticks() - self.last_attack >= fireball_cooldown:
                            fireball = weapon.Fireball(fireball_image, self.rect.centerx, self.rect.centery,
                                                       player.rect.centerx, player.rect.centery)
                            self.last_attack = pygame.time.get_ticks()

            # Check if hit
            if self.hit:
                self.hit = False
                self.last_hit = pygame.time.get_ticks()
                self.stunned = True
                self.running = False
                self.update_action(0)

            # Reset stun after stun cooldown
            if pygame.time.get_ticks() - self.last_hit > stun_cooldown:
                self.stunned = False

        return fireball

    # Update the animation of the character (Switch between images)
    def update(self):
        # Check if character died
        if self.health <= 0:
            self.health = 0
            self.alive = False

        # Timer to reset player taking a hit
        hit_cooldown = 1000
        if self.char_type == 0:
            if self.hit and (pygame.time.get_ticks() - self.last_hit > hit_cooldown):
                self.hit = False

        # Check what action player is performing
        if self.running:
            self.update_action(1)  # 1: run
        else:
            self.update_action(0)  # 0: idle

        # Speed of the animation
        animation_cooldown = 70
        # Handle and update image
        self.image = self.animation_list[self.action][self.frame_index]
        # Check if enough time has passed since the last update
        # If yes, animate the next frame
        if pygame.time.get_ticks() - self.update_time > animation_cooldown:
            self.frame_index += 1
            self.frame_index %= len(self.animation_list[self.action])
            self.update_time = pygame.time.get_ticks()

    # Update the animation state (between idle and running)
    def update_action(self, new_action):
        # Check if the new action is different from the previous one
        if new_action != self.action:
            self.action = new_action
            # Update animation settings, start cycling the images from beginning
            self.frame_index = 0
            self.update_time = pygame.time.get_ticks()

    # Draw player on the surface (which is the game screen) on the rectangle.
    # Rectangle is used for collisions
    def draw(self, surface):
        # Flip image in x-axis with self.flip
        flipped_image = pygame.transform.flip(self.image, self.flip, False)
        # The elf image has a blank space at top, fix it by offsetting image.
        # Because we are scaling the images, also scale the offset
        if self.char_type == 0:
            surface.blit(flipped_image, (self.rect.x, self.rect.y - constants.OFFSET * constants.SCALE))
        else:
            # If an enemy dies, flip the enemy image vertically and rotate
            if not self.alive:
                flipped_image = pygame.transform.rotate(self.image, 30)
                flipped_image = pygame.transform.flip(flipped_image, False, True)
            surface.blit(flipped_image, self.rect)
        # Draw collision rectangle of characters
        pygame.draw.rect(surface, constants.RED, self.rect, 1)
