import pygame.transform
import constants
import math
import random


class Weapon():
    def __init__(self, image, arrow_image):
        self.original_image = image
        # We will be rotating the bow image around the player
        self.angle = 0
        self.image = pygame.transform.rotate(self.original_image, self.angle)
        self.rect = self.image.get_rect()
        self.arrow_image = arrow_image
        self.fired = False  # Holding the mouse 1 won't fire continuously
        self.last_shot = pygame.time.get_ticks()

    def update(self, player):
        shot_cooldown = 100  # Fire cooldown of bow
        arrow = None  # In case the user did not create an arrow, return none

        self.rect.center = player.rect.center
        # Get mouse position on screen
        pos = pygame.mouse.get_pos()
        # pos[0] is the x-axis, pos[1] is y-axis
        x_dist = pos[0] - self.rect.centerx
        y_dist = -(pos[1] - self.rect.centery)  # Y coordinates increase down the screen
        # Calculate angle, convert radians into degrees
        self.angle = math.degrees(math.atan2(y_dist, x_dist))

        # Create arrows from bow
        # Get mouse click, 0 is left click, 1 is middle, 2 is right click
        if pygame.mouse.get_pressed()[0] and self.fired == False and (
                pygame.time.get_ticks() - self.last_shot >= shot_cooldown):
            arrow = Arrow(self.arrow_image, self.rect.centerx, self.rect.centery, self.angle)
            self.fired = True  # Set this to False for rapid fire
            self.last_shot = pygame.time.get_ticks()  # set last shot time
        # Reset mouse click to be able to fire again
        if not pygame.mouse.get_pressed()[0]:
            self.fired = False
        return arrow

    def draw(self, surface):
        self.image = pygame.transform.rotate(self.original_image, self.angle)
        # The bow does not rotate when it is centered to the player rectangle.
        # Adjust it's center by offsetting it
        surface.blit(self.image,
                     ((self.rect.centerx - int(self.image.get_width() / 2)),
                      self.rect.centery - int(self.image.get_height() / 2)))


# Inherit from Sprite for more functionality such as multiple arrows with sprite groups, and kill()
class Arrow(pygame.sprite.Sprite):
    def __init__(self, image, x, y, angle):
        pygame.sprite.Sprite.__init__(self)
        self.original_image = image
        self.angle = angle
        # Subtract 90 bcs original sprite image is rotated
        self.image = pygame.transform.rotate(self.original_image, self.angle - 90)
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)
        # Calculate horizontal and vertical speeds basen on angle
        self.dx = math.cos(math.radians(self.angle)) * constants.ARROW_SPEED
        self.dy = -(math.sin(math.radians(self.angle)) * constants.ARROW_SPEED)  # Negative bcs pygame Y coordinates

    # Update arrow and return the dealt damage if it hit an enemy
    def update(self, screen_scroll, obstacle_tiles, enemy_list):
        # Reset variables
        damage = 0
        damage_pos = None

        # Reposition based on speed
        self.rect.x += screen_scroll[0] + self.dx
        self.rect.y += screen_scroll[1] + self.dy

        # Check for collision between arrow and tile walls
        for obstacle in obstacle_tiles:
            if obstacle[1].colliderect(self.rect):
                self.kill()

        # Check if arrow has gone off-screen to remove arrow from game
        if self.rect.right < 0 or self.rect.left > constants.SCREEN_WIDTH or \
                self.rect.bottom < 0 or self.rect.top > constants.SCREEN_HEIGHT:
            self.kill()

        # Check arrow collision with enemies
        for enemy in enemy_list:
            if enemy.rect.colliderect(self.rect) and enemy.alive:
                damage = 10 + random.randint(-5, 5)  # Random damage
                damage_pos = enemy.rect  # Damage display is positioned at the enemy rectange
                enemy.health -= damage
                enemy.hit = True
                self.kill()  # Destroy arrow after hitting the first enemy
                break

        return damage, damage_pos

    def draw(self, surface):
        surface.blit(self.image,
                     ((self.rect.centerx - int(self.image.get_width() / 2)),
                      self.rect.centery - int(self.image.get_height() / 2)))


class Fireball(pygame.sprite.Sprite):
    def __init__(self, image, x, y, target_x, target_y):
        pygame.sprite.Sprite.__init__(self)
        self.original_image = image
        x_dist = target_x - x
        y_dist = -(target_y - y)
        self.angle = math.degrees(math.atan2(y_dist, x_dist))
        # Subtract 90 bcs original sprite image is rotated
        self.image = pygame.transform.rotate(self.original_image, self.angle - 90)
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)
        # Calculate horizontal and vertical speeds basen on angle
        self.dx = math.cos(math.radians(self.angle)) * constants.FIREBALL_SPEED
        self.dy = -(math.sin(math.radians(self.angle)) * constants.FIREBALL_SPEED)  # Negative bcs pygame Y coordinates

    # Update arrow and return the dealt damage if it hit an enemy
    def update(self, screen_scroll, player):
        # Reposition fireball based on speed
        self.rect.x += screen_scroll[0] + self.dx
        self.rect.y += screen_scroll[1] + self.dy

        # Check if fireball has gone off-screen to remove it from game
        if self.rect.right < 0 or self.rect.left > constants.SCREEN_WIDTH or \
                self.rect.bottom < 0 or self.rect.top > constants.SCREEN_HEIGHT:
            self.kill()

        # Check fireball collision with player
        if player.rect.colliderect(self.rect) and not player.hit:
            player.hit = True
            player.last_hit = pygame.time.get_ticks()
            player.health -= 10
            self.kill()

    def draw(self, surface):
        surface.blit(self.image,
                     ((self.rect.centerx - int(self.image.get_width() / 2)),
                      self.rect.centery - int(self.image.get_height() / 2)))