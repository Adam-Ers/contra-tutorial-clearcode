from math import sin
from os import walk
from types import NoneType
import pygame
from pygame.math import Vector2
from code.settings import *
from code.sprite import *

class Entity(pygame.sprite.Sprite):
    def __init__(self, animations, pos, level_group, groups, enemy_group = None):
        super().__init__(groups)
        ## Image
        self.animations = animations
        self.status = ['right', '']
        self.image = self.animations[''.join(self.status)][0]
        self.rect = self.image.get_rect(midtop = pos)
        self.z = LAYERS['main']
        self.frame_index = 0
        self.last_frame_index = 0
        self.last_status = ''.join(self.status)
        self.animation_speed = PLAYER_ANIMATION_SPEED
        self.reverse_animation = False
        ## Movement
        self.pos = Vector2(self.rect.center)
        self.originalposition = Vector2(pos)
        self.direction = Vector2()
        ## Bullet Logic
        self.enemy_group = enemy_group
        self.fire_images = [pygame.image.load(f"{PATHS['fire']}/0.png"),
                            pygame.image.load(f"{PATHS['fire']}/1.png")]
        self.bullet_image = pygame.image.load(PATHS['bullet']).convert_alpha()
        self.bullet_speed = 0
        self.bullet_shoot_timer = 0
        self.bullet_shoot_delay = 0
        self.bullet_ready = True
        self.bullet_x = 58
        self.bullet_y = -16
        self.bullet_direction_x = 1
        self.bullet_scale = 1
        self.bullet_offset = Vector2(self.rect.center) + Vector2(self.bullet_x * self.bullet_direction_x, 
                                                                self.bullet_y)
        self.bullet_list = []
        ## Game Logic
        self.dt = 0
        self.bloodsurface = pygame.image.load("graphics/blood.png").convert_alpha()
        self.dead = False
        self.health = 1
        self.blood_list = []
        self.blood_color = None
        self.vulnerable = True
        self.max_blood = 2
        ## Collision
        self.level_group = level_group
        ## Sounds
        self.sounds = {}
        self.sounds['gib'] = pygame.mixer.Sound("audio/bodysplat.wav")
        self.sounds['shoot'] = pygame.mixer.Sound("audio/bullet.wav")
        for sound in self.sounds.values():
            sound: pygame.mixer.Sound
            sound.set_volume(SOUND_VOLUME)
            
    def fire_bullet(self):
        self.bullet_ready = False
        self.bullet_shoot_timer = 0
        self.sounds['shoot'].play()
        FireAnimation(self, self.fire_images, self.bullet_direction_x, self.groups()[0])
        self.bullet_list.append(Bullet(self.bullet_image, self.bullet_offset, Vector2(self.bullet_direction_x, 0), self.bullet_speed, self.groups()[0], self.level_group, self.enemy_group, self.bullet_scale))
        if len(self.bullet_list) > 10:
            self.bullet_list[0].kill()
            self.bullet_list.pop(0)
        pass
    
    def animation_states(self):
        pass
    
    def damage(self):
        pass
    
    def blink(self):
        self.last_frame_index = -1
        dt = pygame.time.get_ticks() / 25
        mask = pygame.mask.from_surface(self.image) # type: ignore
        white_surf = mask.to_surface(setcolor=(150, 150, 150))
        white_surf.set_colorkey((0, 0, 0))
        if (sin(dt) >= 0):
            self.image = white_surf
        else:
            white_surf.fill((100, 100, 100))
            new_image = self.image.copy()
            new_image.blit(white_surf, (0, 0), special_flags = pygame.BLEND_RGBA_MULT)
            self.image = new_image


    
    def die(self):
        for i in range(2):
            self.blood_list.append(BloodSplat(self.bloodsurface, self.rect.center, self.groups()[0], self.blood_color))
            if len(self.blood_list) > self.max_blood:
                self.blood_list[0].kill()
                del(self.blood_list[0])
        self.dead = True
    
    def respawn(self):
        self.pos = Vector2(self.originalposition)
        self.rect.center = (round(self.pos.x), round(self.pos.y))
        self.dead = False
        for sound in self.sounds.values():
            sound.stop()
        pass
    
    def animate(self, dt: float):
        self.frame_index += self.animation_speed * dt
        self.animation_states()
        # Reverse animation by subtracing the frame change twice, to revert and then reverse
        if self.reverse_animation:
            self.frame_index -= self.animation_speed * dt * 2
        # Regular animation loop
        if self.frame_index >= len(self.animations[''.join(self.status)]):
            if self.dead:
                self.frame_index = len(self.animations[''.join(self.status)]) - 1
                self.last_frame_index = self.frame_index - 1
            else:
                self.frame_index = 0
                self.last_frame_index = -1
        # Reverse frame loop
        if self.frame_index < 0:
            self.frame_index = len(self.animations[''.join(self.status)]) - 0.01
            self.last_frame_index = -1
        # Only change image if we're actually on the next frame
        if (int(self.frame_index) != int(self.last_frame_index) or ''.join(self.status) != self.last_status):
            self.image = self.animations[''.join(self.status)][int(self.frame_index)]
            self.last_frame_index = int(self.frame_index)
            self.last_status = ''.join(self.status)
        pass