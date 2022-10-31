from math import sin
from os import walk
from types import NoneType
import pygame
from pygame.math import Vector2
from code.settings import *
from code.sprite import BloodSplat, Bullet, FireAnimation
from code.entity import *

# pyright: reportGeneralTypeIssues=false

class Player(Entity):
    def __init__(self, animations, pos, level_group, death_y, groups, enemy_group):
        super().__init__(animations, pos, level_group, groups, enemy_group)
        ## Movement
        self.horizontal_speed = 0
        self.vertical_speed = -400
        self.strafing = False
        self.strafing_direction = ''
        self.ducking = False
        self.can_jump = False
        self.jump_grace_period = 250
        self.jump_grace_period_timer = 0
        self.can_wall_jump = False
        self.wall_jump_direction = 0
        self.wall_jump_period = 200
        self.wall_jump_period_timer = 0
        self.wall_slide_speed = PLAYER_WALL_SLIDE_SPEED
        self.movement_disabled = False
        self.dashing = False
        self.dash_speed = PLAYER_DASH_SPEED
        self.dash_invincibility_period = PLAYER_DASH_INVINCIBILITY
        self.dash_period = PLAYER_DASH_TIME
        self.dash_timer = 0
        self.dash_trails = []
        self.dash_trail_create_timer = 0
        self.dash_trail_create_period = 10
        self.max_dash_trails = 4
        ## Input
        self.jump_released = True
        self.dash_released = True
        ## Collision
        self.collision_sprites_dict = self.level_group.spritedict
        self.platform_list = [x for x in self.collision_sprites_dict.keys() if hasattr(x, 'direction')]
        self.hitbox: pygame.rect.Rect
        self.hitbox = self.rect.inflate(-self.rect.width * 0.75, 0)
        self.prev_hitbox = self.hitbox.copy()
        self.wall_jump_hitbox: pygame.rect.Rect
        self.wall_jump_hitbox = self.rect.inflate(-self.rect.width * 0.70, -self.rect.height * 0.75)
        self.moving_floor = None
        ## Bullet Logic
        self.bullet_speed = PLAYER_BULLET_SPEED
        self.bullet_shoot_delay = PLAYER_BULLET_DELAY
        self.bullet_y_duck = 8
        self.bullet_y_jump = -22
        self.bullet_direction_x = 1
        self.bullet_list = []
        self.bullet_scale = 1
        ## Game Logic
        self.health = PLAYER_MAX_HEALTH
        self.death_y = death_y
        self.blood_gib_count = 100
        self.max_blood = self.blood_gib_count * 4
        self.knockback_invulnerability = False
        self.knockback_invulnerability_timer = 0
        self.knockback_invulnerability_period = PLAYER_INVINCIBILITY_TIME
        self.knocked_back = False
        self.knockback_timer = 0
        self.knockback_period = PLAYER_KNOCKBACK_TIME
        ## Sounds
        self.sounds['jump'] = pygame.mixer.Sound("audio/jump.wav")
        self.sounds['dash'] = pygame.mixer.Sound("audio/dash.wav")
        self.sounds['step1'] = pygame.mixer.Sound("audio/step1.wav")
        self.sounds['step2'] = pygame.mixer.Sound("audio/step2.wav")
        self.sounds['land'] = pygame.mixer.Sound("audio/land.wav")
        self.sounds['slide'] = pygame.mixer.Sound("audio/slide_loop.wav")
        self.sounds['pain'] = pygame.mixer.Sound("audio/pain.wav")
        self.sounds['fall_scream'] = pygame.mixer.Sound("audio/scream.wav")
        self.sounds['pitfall_scream'] = pygame.mixer.Sound("audio/long_scream.wav")
        for sound in self.sounds.values():
            sound: pygame.mixer.Sound
            sound.set_volume(SOUND_VOLUME)
        pass
    
    def input(self):
        keys = pygame.key.get_pressed()
        mouse = pygame.mouse.get_pressed()
        if not self.dead:
            self.strafing = keys[PLAYER_STRAFE_KEY]
            if self.strafing and self.strafing_direction == '':
                self.strafing_direction = self.status[0]
            # Horizontal movement
            if not self.movement_disabled:
                if keys[PLAYER_RIGHT_KEY]:
                    if not self.strafing and not self.can_wall_jump:
                        self.status[0] = 'right'
                        self.reverse_animation = False
                    if self.strafing:
                        self.reverse_animation = self.status[0] == 'left'
                    self.direction.x = 1
                elif keys[PLAYER_LEFT_KEY]:
                    if not self.strafing and not self.can_wall_jump:
                        self.status[0] = 'left'
                        self.reverse_animation = False
                    if self.strafing:
                        self.reverse_animation = self.status[0] == 'right'
                    self.direction.x = -1
                else:
                    self.direction.x = 0
                    self.reverse_animation = False
                if keys[PLAYER_DASH_KEY] and self.can_jump and self.dash_released:
                    if self.direction.x == 0:
                        self.direction.x = -1 if self.status[0] == 'left' else 1
                    self.sounds['dash'].play()
                    self.dashing = True
                    self.dash_timer = 0
                    self.dash_released = False
            self.ducking = self.can_jump and not self.movement_disabled and keys[PLAYER_DUCK_KEY]
            if self.ducking: self.status[1] = '_duck'
            if not self.knocked_back:
                if keys[PLAYER_JUMP_KEY] and self.can_jump and self.jump_released:
                    self.can_jump = False
                    self.vertical_speed = -PLAYER_JUMP_SPEED
                    self.dashing = False
                    self.movement_disabled = False
                    self.jump_released = False
                    self.sounds['jump'].play()
                if keys[PLAYER_JUMP_KEY] and self.can_wall_jump and self.jump_released:
                    self.can_wall_jump = False
                    self.direction.x = self.wall_jump_direction
                    self.wall_jump_period_timer = 1
                    self.dashing = False
                    self.movement_disabled = True
                    self.vertical_speed = -PLAYER_WALL_JUMP_SPEED
                    self.jump_released = False
                    self.sounds['jump'].play()
                if keys[PLAYER_SHOOT_KEY] and self.bullet_ready:
                    self.fire_bullet()
            if not keys[PLAYER_JUMP_KEY] and (self.can_jump or self.can_wall_jump):
                self.jump_released = True
            if not keys[PLAYER_DASH_KEY] and not self.dashing:
                self.dash_released = True
            
            if keys[PLAYER_RESTART_KEY]:
                self.die()
            if not self.strafing:
                self.strafing_direction = ''
            pass
    pass

    def respawn_input(self):
        if pygame.key.get_pressed()[PLAYER_JUMP_KEY]:
            self.respawn()
            pass
        pass

    def collision(self, direction):
        self.collision_sprites: pygame.sprite.Group
        collided_direction = False
        collisions = False
        platform_touched = False
        if self.direction.magnitude() > 0:
            collisions = self.rect.collidedictall(self.collision_sprites_dict)  # type: ignore
        if collisions:
            for sprite, rect in collisions: # type: ignore
                sprite: pygame.sprite.Sprite
                if sprite.hitbox:
                    if sprite.hitbox.colliderect(self.hitbox):  # type: ignore
                        if direction == 'horizontal':
                            if self.hitbox.right >= sprite.hitbox.left and self.prev_hitbox.right <= sprite.prev_hitbox.left: # right
                                self.hitbox.right = sprite.hitbox.left
                                #collided_direction = 'right'
                            elif self.hitbox.left <= sprite.hitbox.right and self.prev_hitbox.left >= sprite.prev_hitbox.right: # left
                                self.hitbox.left = sprite.hitbox.right
                                #collided_direction = 'left'
                            pass
                        else:
                            if self.hitbox.bottom >= sprite.hitbox.top and self.prev_hitbox.bottom <= sprite.prev_hitbox.top: # down
                                self.hitbox.bottom = sprite.hitbox.top
                                if self.vertical_speed >= PLAYER_TERMINAL_VELOCITY:
                                    self.die()
                                self.vertical_speed = 0
                                if not self.can_jump and not self.dead:
                                    self.sounds['land'].play()
                                self.can_jump = True
                                self.jump_grace_period_timer = 0
                                #collided_direction = 'down'
                            elif self.hitbox.top <= sprite.hitbox.bottom and self.prev_hitbox.top >= sprite.prev_hitbox.bottom: # up
                                self.hitbox.top = sprite.hitbox.bottom
                                self.vertical_speed = 0
                                #collided_direction = 'up'
                            pass
                        self.rect.center = self.hitbox.center
                        self.wall_jump_hitbox.midtop = Vector2(self.hitbox.center) + Vector2(0, 20) #type: ignore
                        self.pos = Vector2(self.hitbox.center)
                        pass
                    # Check wall collisions for wall jump/slide
                    if sprite.hitbox.colliderect(self.wall_jump_hitbox) and not self.movement_disabled:
                        if direction == 'horizontal':
                            if self.direction.x > 0 and not self.can_jump: # right
                                    self.can_wall_jump = True
                                    self.wall_jump_direction = -1
                                    if self.vertical_speed > self.wall_slide_speed:
                                        self.vertical_speed = self.wall_slide_speed
                                    self.status[0] = 'left'
                                #collided_direction = 'right'
                            elif self.direction.x < 0 and not self.can_jump: # left
                                if sprite.rect.colliderect(self.wall_jump_hitbox):
                                    self.can_wall_jump = True
                                    self.wall_jump_direction = 1
                                    if self.vertical_speed > self.wall_slide_speed:
                                        self.vertical_speed = self.wall_slide_speed
                                    self.status[0] = 'right'
                                #collided_direction = 'left'
                            pass
        pass
    
    def platform_check(self):
        bottom_rect = pygame.rect.Rect(0, 0, self.hitbox.width, 5)
        bottom_rect.midtop = self.rect.midbottom
        # print(len(platform_list))
        collisions = bottom_rect.collidelist(self.platform_list)
        if collisions > -1 and self.direction.y > 0:
            self.moving_floor = self.platform_list[collisions]
            self.can_jump = True
            pass

    def move(self, dt):
        # Stay still if ducking
        if self.ducking: self.direction.x = 0
        # Check speed
        if self.can_jump:
            self.horizontal_speed = PLAYER_SPEED
        if self.dashing:
            self.horizontal_speed = PLAYER_DASH_SPEED
        # Gravity
        self.vertical_speed += PLAYER_GRAVITY * dt
        if self.vertical_speed > PLAYER_TERMINAL_VELOCITY:
            self.vertical_speed = PLAYER_TERMINAL_VELOCITY
            if not pygame.mixer.Sound.get_num_channels(self.sounds['fall_scream']) and not self.dead:
                self.sounds['fall_scream'].play()
        if self.vertical_speed > 0:
            self.direction.y = 1
        elif self.vertical_speed < 0:
            self.direction.y = -1
        else:
            self.direction.y = 0
        # Horizontal Movement
        self.pos.x += self.direction.x * self.horizontal_speed * dt
        self.prev_hitbox.centerx = self.hitbox.centerx
        self.rect.centerx = round(self.pos.x)
        self.hitbox.centerx = round(self.pos.x)
        self.wall_jump_hitbox.centerx = self.hitbox.centerx
        self.collision('horizontal')
        # Vertical Movement
        self.pos.y += self.vertical_speed * dt
        self.platform_check()
        if self.moving_floor and self.moving_floor.direction.y > 0 and self.direction.y > 0:
            self.vertical_speed = 0
            self.rect.bottom = self.moving_floor.rect.top
            self.pos.y = self.rect.centery
            self.can_jump = True
        
        self.rect.centery = round(self.pos.y)
        self.prev_hitbox.centery = self.hitbox.centery
        self.hitbox.centery = round(self.pos.y)
        self.wall_jump_hitbox.top = self.hitbox.centery + 20
        self.collision('vertical')
        self.moving_floor = None
        # Update Bullet Firing Position
        self.bullet_direction_x = -1 if self.status[0] == 'left' else 1
        bullet_y = self.bullet_y if not self.ducking else self.bullet_y_duck
        if not self.can_jump:
            bullet_y = self.bullet_y_jump
        if self.status[1] == "" and int(self.frame_index) in [1, 2, 5, 6]:
            bullet_y += 4
        self.bullet_offset = Vector2(self.rect.center) + Vector2(self.bullet_x * self.bullet_direction_x, 
                                                                bullet_y)
        pass
    
    def animation_states(self):
        # Keep facing the same direction if strafing, except if wall sliding
        if self.strafing and self.strafing_direction != '' and not self.can_wall_jump:
            self.status[0] = self.strafing_direction
        # Idle State
        if self.direction.x.__abs__() == 0:
            self.status[1] = "_idle"
            if not self.bullet_ready:
                self.frame_index = 0
        # Walk State
        else:
            self.status[1] = ""
        # Jump/Dash State
        if not self.can_jump or self.knocked_back or self.dashing:
            self.status[1] = "_jump"
        # Duck State
        if self.ducking:
            self.status[1] = "_duck"
        # Footstep sounds
        if self.status[1] == "":
            if int(self.frame_index) == 1 and not pygame.mixer.Sound.get_num_channels(self.sounds['step1']):
                self.sounds['step1'].play()
            if int(self.frame_index) == 5 and not pygame.mixer.Sound.get_num_channels(self.sounds['step2']):
                self.sounds['step2'].play()

    def create_trails(self, dt_ms):
        # Trail Logic
        if (self.dash_trail_create_timer > self.dash_trail_create_period):
            trail_sprite: pygame.surface.Surface
            trail_sprite = self.image.copy() 
            trail_sprite.set_alpha(125)
            self.dash_trails.append(Sprite(trail_sprite, self.rect.center, self.groups()[0]))
            self.dash_trail_create_timer = 0
            if len(self.dash_trails) > self.max_dash_trails:
                self.dash_trails[0].kill()
                del(self.dash_trails[0])
        self.dash_trail_create_timer += dt_ms

    def clear_trails(self):
        for trail in self.dash_trails:
            trail.kill()
        self.dash_trails = []
    
    def logic(self, dt):
        dt_ms = dt * 1000
        # Always set vulnerable to be true if nothing else changes it
        self.vulnerable = True
        # Wall Sliding Sound
        if self.can_wall_jump:
            if not pygame.mixer.Sound.get_num_channels(self.sounds['slide']):
                self.sounds['slide'].play()
        else:
            self.sounds['slide'].stop()
        # Dash Logic:
        if self.dashing:
            self.movement_disabled = True
            # End Dash Timer
            if self.dash_timer > self.dash_period:
                self.dashing = False
                self.movement_disabled = False
            # End Dash Invincibility Period
            if self.dash_timer <= self.dash_invincibility_period:
                self.vulnerable = False
            self.dash_timer += dt_ms 
        # Create trails if at dash speed
        if self.horizontal_speed == self.dash_speed:
            self.create_trails(dt_ms)
        # Delete all trails otherwise
        elif len(self.dash_trails) > 0: self.clear_trails()
        # Wall Jump Logic
        self.can_wall_jump = False
        if (self.wall_jump_period_timer >= 1):
            self.movement_disabled = True
            self.wall_jump_period_timer += dt * 1000
            if self.wall_jump_period_timer > self.wall_jump_period:
                self.wall_jump_period_timer = 0
                self.movement_disabled = False
        # Jump Grace Period Logic
        self.jump_grace_period_timer += dt * 1000
        if self.jump_grace_period_timer > self.jump_grace_period:
            self.can_jump = False
        # Bullet Delay Logic
        if not self.bullet_ready:
            self.bullet_shoot_timer += dt * 1000
            if self.bullet_shoot_timer > self.bullet_shoot_delay:
                self.bullet_ready = True
                self.bullet_shoot_timer = 0
        # Invincibility Logic
        if self.knockback_invulnerability:
            self.vulnerable = False
            if self.knockback_invulnerability_timer > self.knockback_invulnerability_period:
                self.knockback_invulnerability = False
            self.knockback_invulnerability_timer += dt * 1000
        if not self.vulnerable:
            self.blink()
        # Knockback Logic
        if self.knocked_back:
            if self.knockback_timer > self.knockback_period:
                self.knocked_back = False
                self.movement_disabled = False
            self.strafing = True
            self.knockback_timer += dt * 1000
        # Die if we fall to our death (duh)
        if self.rect.bottom > self.death_y:
            self.die(True)
        pass
        
    def knockback(self):
        self.knocked_back = True
        self.direction.x = 1 if self.status[0] == 'left' else -1
        self.knockback_timer = 0
        self.movement_disabled = True
        self.dashing = False
        self.horizontal_speed = PLAYER_SPEED
        self.strafing = True
        self.knockback_invulnerability = True
        self.vertical_speed = -PLAYER_KNOCKBACK_SPEED
        
    def damage(self):
        if self.vulnerable and self.health > 0:
            self.health -= 1
            self.vulnerable = False
            self.knockback_invulnerability_timer = 0
            self.knockback()
            if self.health <= 0:
                self.die()
            else:
                self.sounds['pain'].play()
            
    
    def die(self, pitfall = False):
        super().die()
        self.image = self.image.copy()
        self.image.set_alpha(0)
        self.sounds['fall_scream'].stop()
        self.sounds['gib'].play() if not pitfall else self.sounds['pitfall_scream'].play()
        self.can_wall_jump = False
        self.can_jump = False
        self.health = 0
        self.clear_trails()
    
    def respawn(self):
        super().respawn()
        self.hitbox.center = self.rect.center
        self.wall_jump_hitbox.midtop = self.hitbox.center
        # self.vertical_speed = -400
        # self.can_jump = False
        # self.direction.y = -1
        # self.health = PLAYER_MAX_HEALTH
        # self.vulnerable = True
        # self.movement_disabled = False
        # self.knocked_back = False
        # self.dashing = False
        # self.knockback_invulnerability = False
        for enemy in self.enemy_group.sprites():
            enemy.respawn()
        old_blood_list = self.blood_list.copy()
        self.__init__(self.animations, self.pos, self.level_group, self.death_y, self.groups(), self.enemy_group)
        self.blood_list = old_blood_list
        self.vertical_speed = -400
        self.direction.y = -1
        pass

    def update(self, dt):
        self.dt = dt
        if not self.dead:
            self.animate(dt)
            self.input()
            self.logic(dt)
            self.move(dt)
        else:
            self.respawn_input()
        pass