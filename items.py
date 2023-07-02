import pygame.sprite


class Item(pygame.sprite.Sprite):
    def __init__(self, x, y, item_type, animation_list, dummy_coin=False):
        pygame.sprite.Sprite.__init__(self)
        self.item_type = item_type  # 0: coin, 1: HP potion
        self.animation_list = animation_list
        self.frame_index = 0
        self.update_time = pygame.time.get_ticks()
        self.image = self.animation_list[self.frame_index]
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)
        self.dummy_coin = dummy_coin

    def update(self, screen_scroll, player, coin_fx, heal_fx):
        # Don't move the coin displayed in the score
        if not self.dummy_coin:
            # Reposition item based on screen scroll
            self.rect.x += screen_scroll[0]
            self.rect.y += screen_scroll[1]

        # Check collision with player
        if self.rect.colliderect(player.rect):
            # Coin collected
            if self.item_type == 0:
                player.score += 1
                coin_fx.play()
                # Destroy item
                self.kill()
            elif self.item_type == 1:
                # Limit health to 100
                if player.health < 100:
                    player.health += 10
                    heal_fx.play()
                    # Destroy item
                    self.kill()

        # Set speed of animation
        animation_cooldown = 150
        self.image = self.animation_list[self.frame_index]
        # Check if enough time passed since last update
        if pygame.time.get_ticks() - self.update_time > animation_cooldown:
            self.frame_index += 1
            self.update_time = pygame.time.get_ticks()
        # Check if animation has finished and cycle it
        if self.frame_index >= len(self.animation_list):
            self.frame_index = 0

    # For sprite groups you can call the draw function of the group,
    # but for individual objects, you create your own draw function
    def draw(self, surface):
        surface.blit(self.image, self.rect)
