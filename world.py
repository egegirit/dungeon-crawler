import constants
from items import Item
from character import Character


class World():
    def __init__(self):
        self.map_tiles = []
        self.obstacle_tiles = []
        self.exit_tile = None
        self.item_list = []
        self.player = None
        self.character_list = []

    def process_data(self, data, tile_list, item_images, mob_animations):
        self.level_length = len(data)
        # Iterate through each value in level data file
        # While iterating through, to also keep record of the index and count it, use enumerate
        for y, row in enumerate(data):
            for x, tile in enumerate(row):
                image = tile_list[tile]
                image_rect = image.get_rect()
                image_x = x * constants.TILE_SIZE
                image_y = y * constants.TILE_SIZE
                # image_rect.x = image_x
                # image_rect.y = image_y
                image_rect.center = (image_x, image_y)
                tile_data = [image, image_rect, image_x, image_y]

                # 7th png is a wall with collision
                if tile == 7:
                    self.obstacle_tiles.append(tile_data)
                # 8th png is a door between levels
                elif tile == 8:
                    self.exit_tile = tile_data
                # Coin placement (Type 0, image index 0)
                elif tile == 9:
                    coin = Item(image_x, image_y, 0, item_images[0])
                    self.item_list.append(coin)
                    # After adding the coin on the map, override the huge coin tile image with empty floor image
                    tile_data[0] = tile_list[0]
                # Potion placement (Type 1, image index 1)
                elif tile == 10:
                    # wrap item image in list bcs parameter accepts anim list
                    potion = Item(image_x, image_y, 1, [item_images[1]])
                    self.item_list.append(potion)
                    # Replace floor tile
                    tile_data[0] = tile_list[0]
                # Character placement
                elif tile == 11:
                    player = Character(image_x, image_y, 100, mob_animations, 0, False, 1)  # 0: elf
                    self.player = player
                    tile_data[0] = tile_list[0]
                # Enemy placements (enemies are in between 12 and 17.png)
                elif 12 <= tile <= 16:
                    enemy = Character(image_x, image_y, 100, mob_animations, tile - 11, False, 1)
                    self.character_list.append(enemy)
                    tile_data[0] = tile_list[0]
                # Boss placement
                elif tile == 17:
                    enemy = Character(image_x, image_y, 400, mob_animations, 6, True, 2)
                    self.character_list.append(enemy)
                    tile_data[0] = tile_list[0]

                # Add image data to main tiles list (-1 means empty tile)
                if tile >= 0:
                    self.map_tiles.append(tile_data)

    def update(self, screen_scroll):
        # Update each map tile
        for tile in self.map_tiles:
            # Shift coordinates
            tile[2] += screen_scroll[0]  # X coordinate
            tile[3] += screen_scroll[1]  # Y coordinate
            tile[1].center = (tile[2], tile[3])  # image_rect of tile_data

    def draw(self, surface):
        for tile in self.map_tiles:
            surface.blit(tile[0], tile[1])
