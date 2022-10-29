from math import sin
import pygame
from code.settings import *
from pygame import Vector2

class Tile(pygame.sprite.Sprite):
    def __init__(self, pos, surf, layer, groups):
        super().__init__(groups)
        self.image = surf
        self.rect = self.image.get_rect(topleft = pos)
        self.z = layer
        self.pos = Vector2(pos)
        self.hitbox = self.rect.copy()
        self.prev_hitbox = self.rect.copy()
        
    def update(self, dt):
        # self.pos.y += 1
        # self.rect.topleft = (round(self.pos.x), round(self.pos.y))
        # self.prev_hitbox = self.hitbox.copy()
        # self.hitbox.topleft = self.rect.topleft
        pass
    
class MovingPlatform(Tile):
    def __init__(self, pos, surf, layer, groups, border_list, player_group):
        super().__init__(pos, surf, layer, groups)
        
        self.direction = Vector2(0, -1)
        self.speed = PLATFORM_SPEED
        self.border_list = border_list
        self.player_group: pygame.sprite.Group
        self.player_group = player_group
        # print("I live!")
        pass
    
    def update(self, dt):
        self.pos.y += self.speed * self.direction.y * dt
        self.rect.topleft = (round(self.pos.x), round(self.pos.y))
        self.prev_hitbox = self.hitbox.copy()
        self.hitbox.topleft = self.rect.topleft
        collisions = self.rect.collidelist(self.border_list)
        if collisions > -1:
            if self.direction.y > 0:
                self.rect.bottom = self.border_list[collisions].top
            else:
                self.rect.top = self.border_list[collisions].bottom
            self.direction.y *= -1
            self.pos = Vector2(self.rect.topleft)
        player_collision = self.rect.collidelist(self.player_group.sprites()) # type: ignore
        if player_collision > -1 and self.rect.centery < self.player_group.sprites()[player_collision].rect.centery and self.hitbox.colliderect(self.player_group.sprites()[player_collision].hitbox): #type: ignore
            self.rect.bottom = self.player_group.sprites()[player_collision].rect.top
            self.pos = Vector2(self.rect.topleft)
            self.direction.y *= -1
        self.hitbox.topleft = self.rect.topleft
        pass