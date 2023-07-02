import pygame
from pygame import mixer
import random
import csv
import constants
from character import Character
from weapon import Weapon
from items import Item
from world import World
from button import Button

# TODO: Make code modular (like setting HP and damage of things in classes), use inheritance
# items that buffs player
# Rapid fire, RPM buff, Hit scan bow, guided arrow, AOE bow, body punchthrough arrow, freeze/slow enemy arrow
# Different HP/Speed for each character

pygame.init()
mixer.init()

screen = pygame.display.set_mode((constants.SCREEN_WIDTH, constants.SCREEN_HEIGHT))
game_name = "Dungeon"
pygame.display.set_caption(game_name)

# Create clock for maintaining frame rate
clock = pygame.time.Clock()

# Select game map
level = 3
start_game = False
pause_game = False
start_intro = False

# The camera should follow the player
# But the camera is not always centered to the player
# The maximum space between the player and the edge of screen is constants.SCROLL_THRESH
screen_scroll = [0, 0]

# Define player movement variables
moving_left = False
moving_right = False
moving_up = False
moving_down = False

# Define font
FONT_SIZE = 20
font = pygame.font.Font("assets/fonts/AtariClassic.ttf", FONT_SIZE)


# Scale the image by the given constant
def scale_img(image, scale):
    w = image.get_width()
    h = image.get_height()
    return pygame.transform.scale(image, (w * scale, h * scale))


# Load music and sounds
pygame.mixer.music.load("assets/audio/music.wav")
pygame.mixer.music.set_volume(0.3)  # Set volume
# pygame.mixer.music.play(-1, 0.0, 5000)  # -1: run as loop, 0.0: start point of audio, 5000 ms fade in effect

shot_fx = pygame.mixer.Sound("assets/audio/arrow_shot.mp3")
shot_fx.set_volume(0.5)
hit_fx = pygame.mixer.Sound("assets/audio/arrow_hit.wav")
hit_fx.set_volume(0.5)
coin_fx = pygame.mixer.Sound("assets/audio/coin.wav")
coin_fx.set_volume(0.5)
heal_fx = pygame.mixer.Sound("assets/audio/heal.wav")
heal_fx.set_volume(0.5)

# Load button images
start_img = scale_img(pygame.image.load(f"assets/images/buttons/button_start.png").convert_alpha(), constants.BUTTON_SCALE)
restart_img = scale_img(pygame.image.load(f"assets/images/buttons/button_restart.png").convert_alpha(), constants.BUTTON_SCALE)
exit_img = scale_img(pygame.image.load(f"assets/images/buttons/button_exit.png").convert_alpha(), constants.BUTTON_SCALE)
resume_img = scale_img(pygame.image.load(f"assets/images/buttons/button_resume.png").convert_alpha(), constants.BUTTON_SCALE)

# Load heart images
heart_empty = scale_img(pygame.image.load(f"assets/images/items/heart_empty.png").convert_alpha(), constants.ITEM_SCALE)
heart_half = scale_img(pygame.image.load(f"assets/images/items/heart_half.png").convert_alpha(),
                       constants.ITEM_SCALE)
heart_full = scale_img(pygame.image.load(f"assets/images/items/heart_full.png").convert_alpha(),
                       constants.ITEM_SCALE)

# Load coin images
coin_images = []
for x in range(4):
    img = scale_img(pygame.image.load(f"assets/images/items/coin_f{x}.png").convert_alpha(), constants.ITEM_SCALE)
    coin_images.append(img)

# Load potion image
red_potion = scale_img(pygame.image.load(f"assets/images/items/potion_red.png").convert_alpha(), constants.POTION_SCALE)

item_images = []
item_images.append(coin_images)
item_images.append(red_potion)

# Load weapon images and scale it
bow_image = scale_img(pygame.image.load(f"assets/images/weapons/bow.png").convert_alpha(), constants.WEAPON_SCALE)
arrow_image = scale_img(pygame.image.load(f"assets/images/weapons/arrow.png").convert_alpha(), constants.WEAPON_SCALE)
fireball_image = scale_img(pygame.image.load(f"assets/images/weapons/fireball.png").convert_alpha(),
                           constants.FIREBALL_SCALE)

# Load tile map images
tile_list = []
for x in range(constants.TILE_TYPES):
    tile_image = pygame.image.load(f"assets/images/tiles/{x}.png").convert_alpha()
    tile_image = pygame.transform.scale(tile_image, (constants.TILE_SIZE, constants.TILE_SIZE))
    tile_list.append(tile_image)

# Load character images of all mob types and of all animation types
mob_animations = []
mob_types = ["elf", "imp", "skeleton", "goblin", "muddy", "tiny_zombie", "big_demon"]
animation_types = ["idle", "run"]
for mob in mob_types:
    # Load the animations into an animation list
    animation_list = []
    for animation in animation_types:
        # Reset temporary list of images
        temp_list = []
        for i in range(4):
            # Load image, match the game window, alpha is for transparency
            img = pygame.image.load(f"assets/images/characters/{mob}/{animation}/{i}.png").convert_alpha()
            # Scale the player image
            img = scale_img(img, constants.SCALE)
            temp_list.append(img)
        animation_list.append(temp_list)
    mob_animations.append(animation_list)


# Function for displaying game info
def draw_info():
    # Create a layout (Grid and a line) on top of the screen for displaying player info
    pygame.draw.rect(screen, constants.PANEL, (0, 0, constants.SCREEN_WIDTH, 50))
    pygame.draw.line(screen, constants.WHITE, (0, 50), (constants.SCREEN_WIDTH, 50))

    # Draw lives, full HP == 5 times heart, 20 each
    # Avoid displaying multiple half hearts
    half_heart_drawn = False
    for i in range(5):
        if player.health >= ((i + 1) * 20):
            # Each heart is 50px apart, 10 pixels offset, 0 near top of the screen
            screen.blit(heart_full, (10 + i * 50, 0))
        # Calculate remaining half hearts
        elif (player.health % 20 > 0) and not half_heart_drawn:
            screen.blit(heart_half, (10 + i * 50, 0))
            half_heart_drawn = True
        else:
            screen.blit(heart_empty, (10 + i * 50, 0))
    # Show level info
    draw_text("Map: " + str(level), font, constants.WHITE, constants.SCREEN_WIDTH / 2, 15)
    # Show score
    draw_text(f"x: {player.score}", font, constants.WHITE, constants.SCREEN_WIDTH - 100, 15)


# Output text onto screen by converting it to an image
def draw_text(text, font, text_col, x, y):
    image = font.render(text, True, text_col)
    screen.blit(image, (x, y))


# Switch to new level
def reset_level():
    damage_text_group.empty()
    arrow_group.empty()
    item_group.empty()
    fireball_group.empty()

    # Create empty tile list
    data = []
    for row in range(constants.ROWS):
        # -1 means an empty tile
        r = [-1] * constants.COLUMNS
        data.append(r)

    return data


# Create empty tile list with the specified size in constants.py
# So that we can override the empty map with created csv files
world_data = []
for row in range(constants.ROWS):
    # -1 means an empty tile
    r = [-1] * constants.COLUMNS
    world_data.append(r)

# Alternative program to create maps: Tiled

# Load level data and create world
with open(f"levels/level{level}_data.csv", newline="") as csvfile:
    reader = csv.reader(csvfile, delimiter=",")  # Numbers are separated with comma
    # Use enumerate to keep track of index numbers
    for x, row in enumerate(reader):
        for y, tile in enumerate(row):
            world_data[x][y] = int(tile)  # The read value is a string


# Split entire screen into a grid by drawing white lines
def draw_grid():
    for x in range(30):
        pygame.draw.line(screen, constants.WHITE, (x * constants.TILE_SIZE, 0),
                         (x * constants.TILE_SIZE, constants.SCREEN_HEIGHT))
        pygame.draw.line(screen, constants.WHITE, (0, x * constants.TILE_SIZE),
                         (constants.SCREEN_WIDTH, x * constants.TILE_SIZE))


# Damage text class
class DamageTest(pygame.sprite.Sprite):
    def __init__(self, x, y, damage, color, display_time):
        pygame.sprite.Sprite.__init__(self)
        self.image = font.render(damage, True, color)
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)
        self.counter = 0
        self.display_time = display_time

    def update(self):
        # Reposition text based on screen scroll
        self.rect.x += screen_scroll[0]
        self.rect.y += screen_scroll[1]
        # Move damage text up
        self.rect.y -= 2
        # Delete the damage display after counter value is passed
        self.counter += 1
        if self.counter > self.display_time:
            self.kill()


# Handle screen fade (Transition between levels)
class ScreenFade():
    def __init__(self, direction, color, speed):
        self.direction = direction
        self.color = color
        self.speed = speed
        self.fade_counter = 0

    def fade(self):
        fade_complete = False
        self.fade_counter += self.speed
        # Whole screen fade
        if self.direction == 1:
            pygame.draw.rect(screen, self.color, (0 - self.fade_counter, 0, constants.SCREEN_WIDTH // 2,
                                                  constants.SCREEN_HEIGHT))
            pygame.draw.rect(screen, self.color, (constants.SCREEN_WIDTH // 2 + self.fade_counter, 0,
                                                  constants.SCREEN_WIDTH, constants.SCREEN_HEIGHT))
            pygame.draw.rect(screen, self.color, (0, 0 - self.fade_counter,
                                                  constants.SCREEN_WIDTH, constants.SCREEN_HEIGHT // 2))
            pygame.draw.rect(screen, self.color, (0, constants.SCREEN_HEIGHT // 2 + self.fade_counter,
                                                  constants.SCREEN_WIDTH, constants.SCREEN_HEIGHT))
        # Vertical screen fade down
        elif self.direction == 2:
            pygame.draw.rect(screen, self.color, (0, 0, constants.SCREEN_WIDTH, 9 + self.fade_counter))

        if self.fade_counter >= constants.SCREEN_WIDTH:
            fade_complete = True

        return fade_complete


world = World()
world.process_data(world_data, tile_list, item_images, mob_animations)

# Create player
player = world.player

# Create player's weapon
bow = Weapon(bow_image, arrow_image)

# Extract enemies from world data
enemy_list = world.character_list

# Create sprite groups for multiple arrows etc.
damage_text_group = pygame.sprite.Group()
arrow_group = pygame.sprite.Group()
item_group = pygame.sprite.Group()
fireball_group = pygame.sprite.Group()

# Display the score with a coin image
score_coin = Item(constants.SCREEN_WIDTH - 115, 23, 0, coin_images, True)
item_group.add(score_coin)

# Add items (coin, potion etc.) from level data
for item in world.item_list:
    item_group.add(item)

# coin = Item(400, 400, 0, coin_images)
# item_group.add(coin)

# Create screen fades
intro_fade = ScreenFade(1, constants.BLACK, 4)
death_fade = ScreenFade(2, constants.PINK, 4)

# Create buttons
start_button = Button(constants.SCREEN_WIDTH // 2 - 145, constants.SCREEN_HEIGHT // 2 - 150, start_img)
exit_button = Button(constants.SCREEN_WIDTH // 2 - 110, constants.SCREEN_HEIGHT // 2 + 50, exit_img)
restart_button = Button(constants.SCREEN_WIDTH // 2 - 175, constants.SCREEN_HEIGHT // 2 - 50, restart_img)
resume_button = Button(constants.SCREEN_WIDTH // 2 - 175, constants.SCREEN_HEIGHT // 2 - 150, resume_img)


# Game loop
run_game_loop = True
while run_game_loop:

    # Control frame rate so that pressing a movement key won't move the player superfast
    # The movement will be a constant move
    clock.tick(constants.FPS)

    # Show main menu
    if not start_game:
        screen.fill(constants.MENU_BACKGROUND)
        start_button.draw(screen)
        if start_button.draw(screen):
            start_game = True
            start_intro = True
        if exit_button.draw(screen):
            run_game_loop = False
    # Start the game when start button is pressed
    else:
        # Pause screen with resume and exit buttons
        if pause_game:
            screen.fill(constants.MENU_BACKGROUND)
            if resume_button.draw(screen):
                pause_game = False
            if exit_button.draw(screen):
                run_game_loop = False
        # Resume
        else:
            # Fill the screen background to clear the drawn visuals before
            screen.fill(constants.BACKGROUND)

            # Draw grid lines
            # draw_grid()

            if player.alive:
                # Calculate player movement in pixels (Delta x and y, changes in direction)
                # In pygame the top left corner of the screen is (0,0), moving up means decreasing y value.
                dx = 0
                dy = 0
                if moving_right:
                    dx = constants.SPEED
                if moving_left:
                    dx = -constants.SPEED
                if moving_up:
                    dy = -constants.SPEED
                if moving_down:
                    dy = constants.SPEED

                # Move player
                screen_scroll, level_complete = player.move(dx, dy, world.obstacle_tiles, world.exit_tile)
                # print(screen_scroll)

                # Update all objects
                world.update(screen_scroll)
                # Update enemies
                for enemy in enemy_list:
                    fireball = enemy.ai(player, world.obstacle_tiles, screen_scroll, fireball_image)
                    if fireball:
                        fireball_group.add(fireball)
                    if enemy.alive:
                        enemy.update()
                player.update()
                # If there is an arrow, add to sprite group
                arrow = bow.update(player)
                if arrow:
                    arrow_group.add(arrow)
                    # Play arrow shooting sound
                    shot_fx.play()
                # Update and move arrows, get the damage dealt and the position of damage display
                for arrow in arrow_group:
                    damage, damage_pos = arrow.update(screen_scroll, world.obstacle_tiles, enemy_list)
                    if damage:
                        # Display the damage at the top of enemy, not at the center
                        random_x_axis_offset = random.randint(-10, 10)
                        damage_text = DamageTest(damage_pos.centerx + random_x_axis_offset, damage_pos.y, str(damage),
                                                 constants.RED, 60)
                        damage_text_group.add(damage_text)
                        # Play hit sound
                        hit_fx.play()
                damage_text_group.update()
                fireball_group.update(screen_scroll, player)
                item_group.update(screen_scroll, player, coin_fx, heal_fx)

            # Draw on screen
            world.draw(screen)
            for enemy in enemy_list:
                enemy.draw(screen)
            player.draw(screen)
            bow.draw(screen)
            for arrow in arrow_group:
                arrow.draw(screen)
            for fireball in fireball_group:
                fireball.draw(screen)
            damage_text_group.draw(screen)
            item_group.draw(screen)
            draw_info()
            score_coin.draw(screen)

            # Check level complete
            if level_complete:
                start_intro = True
                level += 1
                world_data = reset_level()
                # Load in level data and create world
                # TODO: pack into function
                with open(f"levels/level{level}_data.csv", newline="") as csvfile:
                    reader = csv.reader(csvfile, delimiter=",")  # Numbers are separated with comma
                    # Use enumerate to keep track of index numbers
                    for x, row in enumerate(reader):
                        for y, tile in enumerate(row):
                            world_data[x][y] = int(tile)  # The read value is a string
                world = World()
                world.process_data(world_data, tile_list, item_images, mob_animations)
                # Save hp and score across levels
                temp_hp = player.health
                temp_score = player.score
                player = world.player
                player.health = temp_hp
                player.score = temp_score

                enemy_list = world.character_list
                score_coin = Item(constants.SCREEN_WIDTH - 115, 23, 0, coin_images, True)
                item_group.add(score_coin)
                # Add items from level data
                for item in world.item_list:
                    item_group.add(item)

            if start_intro:
                if intro_fade.fade():
                    start_intro = False
                    intro_fade.fade_counter = 0

            # Shot death screen
            if not player.alive:
                if death_fade.fade():
                    if restart_button.draw(screen):
                        death_fade.fade_counter = 0
                        start_intro = True
                        # TODO: pack into function
                        world_data = reset_level()
                        # Load in level data and create world
                        with open(f"levels/level{level}_data.csv", newline="") as csvfile:
                            reader = csv.reader(csvfile, delimiter=",")  # Numbers are separated with comma
                            # Use enumerate to keep track of index numbers
                            for x, row in enumerate(reader):
                                for y, tile in enumerate(row):
                                    world_data[x][y] = int(tile)  # The read value is a string
                        world = World()
                        world.process_data(world_data, tile_list, item_images, mob_animations)
                        # HP and score saving is handled different when player dies
                        # temp_hp = player.health
                        # temp_score = player.score
                        player = world.player
                        # player.health = temp_hp
                        # player.score = temp_score
                        enemy_list = world.character_list
                        score_coin = Item(constants.SCREEN_WIDTH - 115, 23, 0, coin_images, True)
                        item_group.add(score_coin)
                        # Add items from level data
                        for item in world.item_list:
                            item_group.add(item)

    # Event handler
    # Iterate through events
    for event in pygame.event.get():
        # Check if the user closes the game window
        if event.type == pygame.QUIT:
            run_game_loop = False
        # Keyboard presses
        # For movement
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_a:
                moving_left = True
            if event.key == pygame.K_d:
                moving_right = True
            if event.key == pygame.K_w:
                moving_up = True
            if event.key == pygame.K_s:
                moving_down = True
            if event.key == pygame.K_ESCAPE:
                pause_game = True
        # Keyboard releases
        # so that the player won't keep moving after pressing a key
        if event.type == pygame.KEYUP:
            if event.key == pygame.K_a:
                moving_left = False
            if event.key == pygame.K_d:
                moving_right = False
            if event.key == pygame.K_w:
                moving_up = False
            if event.key == pygame.K_s:
                moving_down = False

    # Update the drawn things
    pygame.display.update()

pygame.quit()
