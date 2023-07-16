from os import walk
import pygame, sys, pytmx
from pygame import Vector2
from pytmx.util_pygame import load_pygame
from code.enemy import Enemy
from code.player import Player
from code.settings import * 
from code.sprite import *
from code.tile import *

# pyright: reportGeneralTypeIssues=false

def object_position(object):
    return (object.x, object.y)

def import_assets(path):
    animations = {}
    for index, folder in enumerate(walk(f'{path}')):
        if index == 0:
            for name in folder[1]:
                animations[name] = []
        else:
            for image in sorted(folder[2], key = lambda string: int(string.split('.')[0])):
                # Replace \s with /s
                fixed_folder = folder[0].replace('\\','/')
                # Create path to image
                path = f"{fixed_folder}/{image}"
                surf = pygame.image.load(path).convert_alpha();
                # Find name of folder by taking only what comes after '\'
                print(fixed_folder)
                key = fixed_folder.split('/').pop()
                # Append image to the animations dictionary, using folder name as key
                animations[key].append(surf)
    return animations

class AllSprites(pygame.sprite.Group):
	def __init__(self, width, height):
		super().__init__()
		self.offset = Vector2()
		bg_path = PATHS['bg']
		fg_path = PATHS['fg']
		self.bg = pygame.image.load(bg_path).convert_alpha()
		self.fg = pygame.image.load(fg_path).convert_alpha()
		self.map_width = width
		self.map_height = height
		self.sky_num = self.map_width // self.bg.get_width() + 1
		self.layers = len(LAYERS)
		pass
    
	def customize_draw(self, display_surface, player):
		## Adjust offset based on player position
		self.offset.x = player.rect.centerx - WINDOW_WIDTH / 2
		self.offset.y = player.rect.centery - WINDOW_HEIGHT / 2
		# Left/Top bounds
		if (self.offset.x < 0): self.offset.x = 0
		if (self.offset.y < 0): self.offset.y = 0
		# Right/Bottom bounds
		if (self.offset.x + WINDOW_WIDTH > self.map_width): self.offset.x = self.map_width - WINDOW_WIDTH
		if (self.offset.y + WINDOW_HEIGHT > self.map_height): self.offset.y = self.map_height - WINDOW_HEIGHT
		# Draw layered scrolling background
		for x in range(self.sky_num):
			bg_pos_x = (-WINDOW_WIDTH / 2) + (x * self.bg.get_width())
			display_surface.blit(self.bg, (bg_pos_x - self.offset.x / 2.5, 850 - self.offset.y / 2.5))
			display_surface.blit(self.fg, (bg_pos_x - self.offset.x / 2, 850 - self.offset.y / 2))
		# Draw Sprites via layers
		for layer in range(0, self.layers):
			for sprite in [x for x in self.sprites() if x.z == layer]:
				offset_rect = sprite.image.get_rect(center = sprite.rect.center)
				offset_rect.center -= self.offset
				display_surface.blit(sprite.image, offset_rect)
			pass
		pass
        # Bottom Cloud Cover
		for x in range(0, (self.map_width // self.fg.get_width()) + 1):
			display_surface.blit(self.fg, Vector2(x * self.fg.get_width() - self.offset.x, self.map_height - 500 - self.offset.y))
	pass

class Main:
	def __init__(self):
		pygame.init()
		self.display_surface = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SCALED)
		pygame.display.set_caption('Contra')
		self.clock = pygame.time.Clock()
		## Music
		pygame.mixer.music.load("audio/music.ogg")
		pygame.mixer.music.set_volume(MUSIC_VOLUME)
		pygame.mixer.music.play(-1)	
		## HUD
		self.health_offset = (16, 16)
		self.health_image = pygame.image.load("graphics/health.png").convert()
		## Framerate Stuff
		self.framerate_show = False
		self.font = pygame.font.Font(None, 24)
		self.win_font = pygame.font.Font(None, 64)
		self.framerate_list = []
		self.framerate_average = 0
		## Tiled Load
		tmx_data = load_pygame(f"{PATHS['map']}")
		self.player = None
		## Groups
		self.all_sprites = AllSprites(tmx_data.width * tmx_data.tilewidth, tmx_data.height * tmx_data.tileheight)
		self.player_group = pygame.sprite.Group()
		self.enemy_group = pygame.sprite.Group()
		self.level_group = pygame.sprite.Group()
		self.platforms = pygame.sprite.Group()
		self.platform_border_rects = []
		## Animations
		player_animations = import_assets(PATHS['player'])
		enemy_animations = import_assets(PATHS['enemy'])
  		## Tiles
		for x, y, surf in tmx_data.get_layer_by_name('Level').tiles():
			Tile((x * surf.get_width(), y * surf.get_height()), surf, LAYERS['main'], (self.all_sprites, self.level_group))
		for layer in ['BG', 'BG Detail', 'FG Detail Bottom', 'FG Detail Top']:
			for x, y, surf in tmx_data.get_layer_by_name(layer).tiles():
				Tile((x * surf.get_width(), y * surf.get_height()), surf, LAYERS[layer.lower()], (self.all_sprites))
		## Platforms
		for obj in tmx_data.get_layer_by_name('Platforms'):
			if obj.name == 'Platform':
				MovingPlatform(object_position(obj), obj.image, LAYERS['main'], (self.all_sprites, self.level_group, self.platforms), self.platform_border_rects, self.player_group)
			else: ## Border
				border_rect = pygame.Rect(obj.x, obj.y, obj.width, obj.height)
				self.platform_border_rects.append(border_rect)
				## Entities
		for obj in tmx_data.get_layer_by_name('Entities'):
			## Player
			if obj.name == 'Player':
				self.player = Player(animations = player_animations,
                         pos = object_position(obj),
                         level_group = self.level_group,
                         death_y = self.all_sprites.map_height,
                         groups = (self.all_sprites, self.player_group),
                         enemy_group = self.enemy_group)
			## Enemies
			if obj.name == 'Enemy':
				Enemy(animations = enemy_animations,
                         pos = object_position(obj),
                         level_group = self.level_group,
                         groups = (self.all_sprites, self.enemy_group),
                         enemy_group = self.player_group)
		pass

	def run(self):
		while True:
			for event in pygame.event.get():
				if event.type == pygame.QUIT:
					pygame.quit()
					sys.exit()
				if event.type == pygame.KEYDOWN:
					if event.key == PLAYER_FULLSCREEN_KEY:
						pygame.display.toggle_fullscreen()
					if event.key == PLAYER_FRAMERATE_KEY:
						self.framerate_show = not self.framerate_show

			dt = self.clock.tick(FRAMERATE) / 1000
   
			## Framerate Calculation
			self.framerate_list.append(round(self.clock.get_fps()))
			if (len(self.framerate_list) > FRAMERATE):
				self.framerate_average = sum(self.framerate_list) / len(self.framerate_list)  
				self.framerate_list = []
   
			self.display_surface.fill((249,131,103))
   
			self.all_sprites.customize_draw(self.display_surface, self.player)
			self.all_sprites.update(dt)
   
			## Show Health
			for x in range(0, self.player.health):
				self.display_surface.blit(self.health_image, Vector2(self.health_offset) + Vector2(x * self.health_offset[0], 0))
   
			## Show FPS
			if (self.framerate_show):
				fpstext = self.font.render(F"{round(self.framerate_average)} FPS", True, 'white')
				self.display_surface.blit(fpstext, fpstext.get_rect(topright = (WINDOW_WIDTH - 10, 10)))
    
			## Win Screen
			deaths = 0
			for enemy in self.enemy_group.sprites():
				deaths += not enemy.dead
			if not deaths:
				wintext = self.win_font.render("U R DA CONTRA", True, 'white')
				wintext2 = self.win_font.render("U WIN", True, 'white')
				self.display_surface.blit(wintext, wintext.get_rect(center = (WINDOW_WIDTH / 2, WINDOW_HEIGHT / 2 - 32)))
				self.display_surface.blit(wintext2, wintext2.get_rect(center = (WINDOW_WIDTH / 2, WINDOW_HEIGHT / 2 + 32)))

			pygame.display.update()

if __name__ == '__main__':
	main = Main()
	main.run()
