from os import walk
from types import NoneType
import pygame
from pygame.math import Vector2
from code.player import Player
from code.settings import *
from code.sprite import *
from code.entity import *

# pyright: reportGeneralTypeIssues=false

class Enemy(Entity):
    def __init__(self, animations, pos, level_group, groups, enemy_group):
        super().__init__(animations, pos, level_group, groups, enemy_group)
        ## Animation
        self.animation_speed = ENEMY_ANIMATION_SPEED
        ## Bullet Logic
        self.bullet_speed = ENEMY_BULLET_SPEED
        self.bullet_shoot_delay = ENEMY_BULLET_DELAY
        self.bullet_x = 64
        self.bullet_y = -13
        self.bullet_direction_x = 1
        self.bullet_list = []
        ## Game Logic
        self.health = ENEMY_MAX_HEALTH
        self.blink_period = ENEMY_BLINK_TIME
        self.blink_timer = 0
        self.blinking = False
        ## AI
        self.player = self.enemy_group.sprites()[0] # type: ignore
        self.player: Player
        self.attacking = False
        self.random_turn_delay_min = ENEMY_TURN_DELAY_MIN
        self.random_turn_delay_max = ENEMY_TURN_DELAY_MAX
        self.random_turn_delay = randrange(ENEMY_TURN_DELAY_MIN, ENEMY_TURN_DELAY_MAX)
        self.random_turn_timer = 0
        ## Sounds
        self.sounds['shoot'] = pygame.mixer.Sound("audio/bullet.wav")
        self.sounds['hit'] = pygame.mixer.Sound("audio/hit.wav")
        for sound in self.sounds.values():
            sound: pygame.mixer.Sound
            sound.set_volume(SOUND_VOLUME)
        ## Adjust Position
        for sprite in level_group.sprites():
            if sprite.rect.collidepoint(self.rect.midbottom):
                self.rect.bottom = sprite.rect.top
        self.originalposition = Vector2(self.rect.center)
        pass
    
    def animation_states(self):
        pass
    
    def face_player(self):
        if self.player.pos.x - self.pos.x < 0:
            self.status[0] = 'left'
            self.bullet_direction_x = -1
        else:
            self.status[0] = 'right'
            self.bullet_direction_x = 1
        self.bullet_offset = Vector2(self.rect.center) + Vector2(self.bullet_x * self.bullet_direction_x, 
                                                                self.bullet_y)
    
    def check_player_in_sight(self):
        right = True
        if self.status[0] == 'left':
            right = False
        if self.player.pos.y < self.rect.bottom + 50 and self.player.pos.y > self.rect.top - 50 and not self.player.dead:
            if (right and self.player.pos.x >= self.pos.x) \
                or (not right and self.player.pos.x <= self.pos.x):
                return True
        return False
        
    
    def logic(self, dt):
        ## Player Death Check
        if self.player.dead:
            self.attacking = False
        ## Bullet Timer
        if not self.bullet_ready:
            if self.bullet_shoot_timer > self.bullet_shoot_delay:
                self.bullet_ready = True
            self.bullet_shoot_timer += dt * 1000
        ## Blink Timer
        if self.blinking:
            if self.blink_timer > self.blink_period:
                self.blinking = False
            self.blink_timer += dt * 1000
            self.blink()
        ## Idle Logic
        if not self.attacking:
            ## Random Turn Timer
            if self.random_turn_timer < self.random_turn_delay:
                self.random_turn_timer += dt * 1000
            else:
                self.random_turn_timer = 0
                self.random_turn_delay = randrange(ENEMY_TURN_DELAY_MIN, ENEMY_TURN_DELAY_MAX)
                if self.status[0] == 'left': self.status[0] = 'right'
                else: self.status[0] = 'left'
                self.bullet_direction_x *= -1
                self.bullet_offset = Vector2(self.rect.center) + Vector2(self.bullet_x * self.bullet_direction_x, 
                                                                self.bullet_y)
        ## Sight Logic
        if self.pos.distance_to(self.player.pos) <= ENEMY_AGGRO_DISTANCE and self.check_player_in_sight():
            self.attacking = True
            
        ## Attacking Logic
        if self.attacking and not self.player.dead:
            if self.pos.distance_to(self.player.pos) > ENEMY_AGGRO_DISTANCE:
                self.attacking = False
            self.face_player()
            self.frame_index = 2
            self.last_frame_index = -1
            if self.bullet_ready:
                self.fire_bullet()
            
        pass
    
    def damage(self):
        self.sounds['hit'].play()
        if not self.dead:
            self.health -= 1
            self.blinking = True
            self.blink_timer = 0
        if self.health <= 0:
            self.blinking = False
            self.die()
        pass
    
    def die(self, pitfall = False):
        super().die()
        self.status[1] = '_dead'
        self.animation_speed *= 1.5
        self.frame_index = 0
        self.last_frame_index = -1
        self.health = 0
        self.blinking = False
    
    def respawn(self):
        super().respawn()
        self.status[1] = ''
        self.animation_speed = ENEMY_ANIMATION_SPEED
        self.frame_index = 0
        self.last_frame_index = -1
        for blood in self.blood_list:
            blood.kill()
            self.blood_list = []
        self.health = ENEMY_MAX_HEALTH
        pass

    def update(self, dt):
        self.animate(dt)
        if not self.dead:
            self.logic(dt)
        pass