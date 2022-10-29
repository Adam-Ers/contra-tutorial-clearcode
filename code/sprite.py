from random import randrange, uniform
import pygame
from pygame.math import Vector2
from code.settings import *

def changeColor(image, color):
    colouredImage = pygame.Surface(image.get_size())
    colouredImage.fill(color)
    
    finalImage = image.copy()
    finalImage.blit(colouredImage, (0, 0), special_flags = pygame.BLEND_MULT)
    return finalImage

class Sprite(pygame.sprite.Sprite):
    def __init__(self, surface, pos, groups, z = 1):
        super().__init__(groups)
        self.image = surface
        self.rect = self.image.get_rect(center = pos)
        self.hitbox = self.rect.inflate(0, -self.rect.height * 0.6)
        self.hitbox.top = self.rect.centery
        self.offset_pos = Vector2()
        self.z = 1
        pass
    pass

class BloodSplat(pygame.sprite.Sprite):
    def __init__(self, surface: pygame.surface.Surface, pos, groups, color = None):
        super().__init__(groups)
        random_size = uniform(2.0, 4.0)
        self.angle = randrange(0, 360)
        self.image = pygame.transform.scale(surface, (surface.get_width() * random_size, surface.get_height() * random_size))
        self.image = pygame.transform.rotate(self.image, self.angle)
        self.rect = self.image.get_rect(center = pos)
        self.offset_pos = Vector2()
        self.z = 1
        if color is not None:
            self.image = changeColor(self.image, color)
        pass
    pass

class Bullet(pygame.sprite.Sprite):
    def __init__(self, surface, pos, direction, speed, groups, collision_group, enemy_group = None, mask_scale = 1):
        super().__init__(groups)
        self.image = surface
        if direction.x == -1: self.image = pygame.transform.flip(self.image, True, False)
        self.rect = self.image.get_rect(center = pos)
        #self.rect.inflate_ip(self.rect.width * mask_scale, self.rect.height * mask_scale)
        #self.mask = pygame.mask.from_surface(self.image)
        #self.mask.scale((self.image.get_width() * mask_scale, self.image.get_height() * mask_scale))
        #self.image = self.mask.to_surface()
        self.hitbox = self.rect.inflate(0, 0)
        self.offset_pos = Vector2()
        self.enemy_group = enemy_group
        self.collision_group = collision_group
        self.z = 1
        
        ## Movement
        self.pos = Vector2(pos)
        self.direction = Vector2(direction)
        self.speed = speed
        
        ## Time
        self.timer = 0
        pass
    
    def collision(self):
        collision = pygame.sprite.spritecollideany(self, self.enemy_group) if self.enemy_group else None # type: ignore
        if collision:
                if pygame.sprite.collide_mask(self, collision):
                    try:
                        if not collision.dead and collision.vulnerable: # type: ignore
                            collision.damage() # type: ignore
                            self.kill()
                    except:
                        self.kill()
                        pass
        level_collision = pygame.sprite.spritecollideany(self, self.collision_group)
        if level_collision and pygame.sprite.collide_mask(self, level_collision):
            self.kill()
        pass
    
    def update(self, dt):
        self.collision()
        self.pos += self.direction * self.speed * dt
        self.rect.center = (round(self.pos.x), round(self.pos.y))
        self.timer += dt * 1000
        if self.timer > BULLET_FADE_TIME:
            self.kill()
        pass
    pass

class FireAnimation(Sprite):
    def __init__(self, entity, surf_list, direction_x, groups):
        super().__init__(surf_list[0], entity.bullet_offset, groups)
        self.entity = entity
        self.surf_list = surf_list
        self.frame_index = 0
        self.last_frame_index = 0
        self.direction_x = direction_x
        self.z = 1
        
    def update(self, dt):
        self.frame_index += FIRE_ANIMATION_SPEED * dt
        self.rect.center = self.entity.bullet_offset
        
        if self.frame_index >= len(self.surf_list):
            self.kill()
            return
        
        if int(self.frame_index) != int(self.last_frame_index):
            self.image = self.surf_list[int(self.frame_index)] if self.direction_x > 0 else pygame.transform.flip(self.surf_list[int(self.frame_index)], True, False)