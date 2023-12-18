from pyglet.window import key
from webbrowser    import open as open_url
from minilogger    import Console
from threading     import Thread
from random        import random, randint, choice
from time          import time, sleep
from json          import load, dump
from math          import sin
from os            import listdir

import pyglet

class Empty: ...

# Initializing the window
screen = pyglet.canvas.get_display().get_screens()
window = pyglet.window.Window(fullscreen=True, screen=screen[0])
window.set_mouse_visible(False)

# Loading localization strings
with open('resources/localization.json', 'r', encoding = 'utf-8') as file: locales = load(file)
# Loading user settings
with open('data/settings.json', 'r') as file: settings = load(file)

# Loading images
bubble_img                  = pyglet.image.load('resources/sprites/bubble.png')
weighted_companion_cube_img = pyglet.image.load('resources/sprites/weighted_companion_cube.png')
cursor_img                  = pyglet.image.load('resources/sprites/cursor.png')
github_img                  = pyglet.image.load('resources/sprites/github.png')
settings_img                = pyglet.image.load('resources/sprites/settings.png')
shuffle_img                 = pyglet.image.load('resources/sprites/shuffle.png')
play_pause_img              = pyglet.image.load('resources/sprites/play_pause.png')
show_img                    = pyglet.image.load('resources/sprites/show.png')
hide_img                    = pyglet.image.load('resources/sprites/hide.png')
cross_img                   = pyglet.image.load('resources/sprites/cross.png')
disabled_img                = pyglet.image.load('resources/sprites/disabled.png')
enabled_img                 = pyglet.image.load('resources/sprites/enabled.png')
globe_img                   = pyglet.image.load('resources/sprites/globe.png')
pulse_img                   = pyglet.image.load('resources/sprites/pulse.png')
level0_img                  = pyglet.image.load('resources/sprites/level_off.png')
level1_img                  = pyglet.image.load('resources/sprites/level_low.png')
level2_img                  = pyglet.image.load('resources/sprites/level_medium.png')
level3_img                  = pyglet.image.load('resources/sprites/level_high.png')

weighted_companion_cube_img.anchor_x = weighted_companion_cube_img.width // 2
weighted_companion_cube_img.anchor_y = weighted_companion_cube_img.height // 2

# Creating sprites from images
cursor = pyglet.sprite.Sprite(cursor_img)

# Creating drawing batches
settings_batch = pyglet.graphics.Batch()
ui_batch = pyglet.graphics.Batch()

# Loading music
with open('resources/music_meta.json', 'r') as file: music_meta = load(file)
music = []
for fname in listdir('resources/music/'):
	if fname not in music_meta:
		Console.log(f'"resources/music/{fname}" has no accompanying entry in music_meta; skipping', 'ResourceLoader', 'W')
		continue
	music.append({
		'media': pyglet.resource.media(f'resources/music/{fname}'),
		'name': music_meta[fname]['name']
	})

# Looped playlist generator
shuffle_playlist = settings['shuffle']
selected_track = 0
def media_player_controller():
	global selected_track

	while True:
		if shuffle_playlist:
			next_track = randint(0, len(music) - 1)
			while next_track == selected_track:
				next_track = randint(0, len(music) - 1)
			selected_track = next_track
		else:
			selected_track += 1
			if selected_track == len(music):
				selected_track = 0
		yield music[selected_track]['media']

# Initializing the media player
media_player = pyglet.media.Player()
media_player.queue(media_player_controller())

locales_list = list(locales.keys())
locale = settings['locale']
def change_language():
	global locale
	locale += 1
	if locale == len(locales_list):
		locale = 0

	song_name.text = f'{locales[locales_list[locale]]["song"]}: {music[0]["name"]}'
	song_hint.text = locales[locales_list[locale]]['to_skip'].format('+'.join(['Ctrl', 'N']))
	locale_label.text = f'{locales[locales_list[locale]]["self_name"]} ({locales[locales_list[locale]]["en_name"]})'
	restore_ui_hint.text = locales[locales_list[locale]]['restore_ui_hint'].format('+'.join(['F1']))

# Pop-up with the track name
song_name = pyglet.text.Label(
	text      = f'{locales[locales_list[locale]]["song"]}: {music[0]["name"]}',
	font_name = 'Arial',
	font_size = 50,
	bold      = True,
	italic    = True,
	color     = (255, 255, 255, 125),
	x         = window.width - 10,
	y         = 55,
	anchor_x  = 'right'
)
song_hint = pyglet.text.Label(
	text      = locales[locales_list[locale]]['to_skip'].format('+'.join(['Ctrl', 'N'])),
	font_name = 'Arial',
	font_size = 17,
	italic    = True,
	color     = (255, 255, 255, 75),
	x         = window.width - 10,
	y         = 20,
	anchor_x  = 'right'
)

locale_label = pyglet.text.Label(
	text      = f'{locales[locales_list[locale]]["self_name"]} ({locales[locales_list[locale]]["en_name"]})',
	font_name = 'Arial',
	font_size = 20,
	color     = (255, 255, 255, 100),
	x         = 70,
	y         = 95,
	anchor_y  = 'center',
	batch     = settings_batch
)

restore_ui_hint = pyglet.text.Label(
	text      = locales[locales_list[locale]]['restore_ui_hint'].format('+'.join(['F1'])),
	font_name = 'Arial',
	font_size = 20,
	italic    = True,
	color     = (255, 255, 255, 75),
	x         = 10,
	y         = window.height - 10,
	anchor_y  = 'top',
)

# A function that makes the track name visible for 5 seconds. Blocking (requires a dedicated thread for OpenGL to work).
showing_song_info = False
def show_song_info():
	global showing_song_info
	showing_song_info = True
	sleep(5)
	showing_song_info = False

# Media player on_player_next_source event handler
@media_player.event
def on_player_next_source():
	song_name.text = f'{locales[locales_list[locale]]["song"]}: {music[selected_track]["name"]}'
	thr = Thread(target=show_song_info, args=())
	thr.start()

# Opens the project page on GitHub in the browser
def open_github():
	open_url('https://github.com/R1senDev/bubbles_and_chillout')

# Shows/Hides the settings section
settings_shown = False
def toggle_settings():
	global settings_shown
	settings_shown = not settings_shown

	for btn in buttons:
		if 'main_row' in btn.classes:
			btn.set_y(130 if settings_shown else 10)

def toggle_playback():
	if media_player.playing:
		media_player.pause()
	else:
		media_player.play()

restore_ui_hint_shown = False
restore_ui_hint_already_shown = False
def restore_ui_hint_controller():
	global restore_ui_hint_shown
	restore_ui_hint_shown = True
	end_time = time() + 10
	while time() < end_time and not ui_shown:
		sleep(0.02)
	restore_ui_hint_shown = False

# Shows/Hides the UI
ui_shown = True
def toggle_ui():
	global ui_shown
	global restore_ui_hint_already_shown
	ui_shown = not ui_shown
	if settings_shown:
		toggle_settings()
	if not restore_ui_hint_already_shown:
		restore_ui_hint_already_shown = True
		thr = Thread(target = restore_ui_hint_controller, args = ())
		thr.start()

# Enables/Disables playlist shuffling
def toggle_shuffle():
	global shuffle_playlist
	shuffle_playlist = not shuffle_playlist

shake_level = settings['shake_level']
def change_shake_level():
	global shake_level
	shake_level += 1
	if shake_level > 3:
		shake_level = 0
	shake_level_widget.level = shake_level
	Effector.shake_widget(3 * shake_level, 3 * shake_level, 0.25)

def close_app():
	on_close()
	window.close()

bubbles = []

# Render offset (required for shaking animation)
render_offset = Empty()
render_offset.x = 0
render_offset.y = 0

# Creates effects (shaking)
class Effector:

	def shake_fx(x_offset: int, y_offset: int, end_time: float):
		global render_offset
		if not pyglet.app.event_loop.is_running:
			Console.log('waiting until event_loop runs', 'Effector.shake', 'I')
			while not pyglet.app.event_loop.is_running:
				sleep(0.2)
			Console.log('met event_loop', 'Effector.shake', 'I')
		Console.log('started', 'Effector.shake', 'D')
		while time() < end_time:
			xs = list([i for i in range(-x_offset, x_offset + 1)])
			ys = list([i for i in range(-y_offset, y_offset + 1)])
			xs.remove(render_offset.x)
			ys.remove(render_offset.y)
			if not (xs or ys):
				Console.log('effect cannot be played: all of offsets == 0', 'Effector.shake', 'I')
				return None
			if xs:
				render_offset.x = choice(xs)
			if ys:
				render_offset.y = choice(ys)
			if not pyglet.app.event_loop.is_running:
				Console.log('event_loop is inactive; ending', 'Effector.shake', 'I')
				return None
			sleep(0.01)
		Console.log('ended', 'Effector.shake', 'D')
		render_offset.x = 0
		render_offset.y = 0
	
	def shake_widget_fx(x_offset: int, y_offset: int, end_time: float):
		if not pyglet.app.event_loop.is_running:
			Console.log('waiting until event_loop runs', 'Effector.shake_widget', 'I')
			while not pyglet.app.event_loop.is_running:
				sleep(0.2)
			Console.log('met event_loop', 'Effector.shake_widget', 'I')
		Console.log('started', 'Effector.shake_widget', 'D')
		sx = shake_level_widget.sprites[0].x
		sy = shake_level_widget.sprites[0].y
		while time() < end_time:
			xs = list([i + sx for i in range(-x_offset, x_offset + 1)])
			ys = list([i + sy for i in range(-y_offset, y_offset + 1)])
			xs.remove(shake_level_widget.sprites[0].x)
			ys.remove(shake_level_widget.sprites[0].y)
			if not (xs or ys):
				Console.log('effect cannot be played: all of offsets == 0', 'Effector.shake_widget', 'I')
				return None
			if xs:
				for sprite in shake_level_widget.sprites:
					sprite.x = choice(xs)
			if ys:
				for sprite in shake_level_widget.sprites:
					sprite.y = choice(ys)
			if not pyglet.app.event_loop.is_running:
				Console.log('event_loop is inactive; ending', 'Effector.shake_widget', 'I')
				return None
			sleep(0.01)
		Console.log('ended', 'Effector.shake_widget', 'D')
		for sprite in shake_level_widget.sprites:
			sprite.x = sx
			sprite.y = sy

	@classmethod
	def shake(self, x_offset: int = 3, y_offset: int = 3, fx_time: float = 1):
		thr = Thread(target=self.shake_fx, args=[x_offset, y_offset, time() + fx_time])
		thr.start()
	
	@classmethod
	def shake_widget(self, x_offset: int = 3, y_offset: int = 3, fx_time: float = 1):
		thr = Thread(target=self.shake_widget_fx, args=[x_offset, y_offset, time() + fx_time])
		thr.start()

class LevelWidget:
	def __init__(self, x: int, y: int, level_sprites: list):
		self.sprites = []
		for img in level_sprites:
			self.sprites.append(pyglet.sprite.Sprite(img, x, y))
		self.level = shake_level
	
	def draw(self):
		self.sprites[self.level].draw()

shake_level_widget = LevelWidget(70, 20, [
	level0_img,
	level1_img,
	level2_img,
	level3_img
])

# Button class
class Button:
	def __init__(self, x: int, y: int, w: int, h: int, texture, on_click = lambda: ..., two_states: bool = False, classes: list[str] = []) -> None:
		self.x = x
		self.y = y
		self.w = w
		self.h = h
		self.sprite = pyglet.sprite.Sprite(texture, batch = settings_batch if 'settings' in classes else ui_batch, x = x, y = y)
		self.on_click = on_click
		self.two_states = two_states
		self.classes = classes
		if self.two_states:
			self.state = True
			self.cross = pyglet.sprite.Sprite(disabled_img, x = self.x + self.w - 15, y = -15, batch = ui_batch)
			self.tick = pyglet.sprite.Sprite(enabled_img, x = self.x + self.w - 15, y = self.y, batch = ui_batch)
	
	def set_y(self, y: int):
		self.y = y
		self.sprite.y = y
		if not self.two_states:
			return None
		if self.state:
			self.cross.y = -15
			self.tick.y = y
		else:
			self.cross.y = y
			self.tick.y = -15

	def click(self, x: int, y: int) -> bool:
		if 'settings' in self.classes and not settings_shown:
			return False
		if x > self.x and x < self.x + self.w and y > self.y and y < self.y + self.h and ui_shown:
			self.on_click()
			if self.two_states:
				self.state = not self.state
				if self.state:
					self.cross.y = -15
					self.tick.y = self.y
				else:
					self.cross.y = self.y
					self.tick.y = -15
			return True
		return False

# Creating UI buttons (settings, GitHub)
buttons = [
	Button(10, 10, 50, 50, github_img, open_github, False, ['main_row']),
	Button(70, 10, 50, 50, settings_img, toggle_settings, False, ['main_row']),
	Button(130, 10, 50, 50, shuffle_img, toggle_shuffle, True, ['main_row']),
	Button(190, 10, 50, 50, play_pause_img, toggle_playback, False, ['main_row']),

	Button(10, 70, 50, 50, globe_img, change_language, False, ['settings']),
	Button(10, 10, 110, 50, pulse_img, change_shake_level, False, ['settings']),

	Button(10, window.height - 60, 50, 50, hide_img, toggle_ui, False, []),

	Button(window.width - 40, window.height - 40, 30, 30, cross_img, close_app, False, ['window_controls']),
]

if not shuffle_playlist:
	buttons[2].state = False
	buttons[2].cross.y = buttons[2].y
	buttons[2].tick.y = -15

# Bubble class
class Bubble:
	raw_y = 0
	size = bubble_img.width
	tried_to_update = False
	common = True
	sprite = pyglet.sprite.Sprite(bubble_img)

	def __init__(self, x_origin: int, amplitude: float = 150, frequency: float = 0.025, x_shift: int = 0, speed: float = 40, function = sin) -> None:
		self.start_time = time()
		self.x_origin = x_origin
		self.amplitude = amplitude
		self.frequency = frequency
		self.x_shift = x_shift
		self.speed = speed
		self.func = function

	@property
	def y(self) -> int:
		return int(self.raw_y)
	
	@property
	def x(self) -> int:
		return int(self.func(self.y * self.frequency) * self.amplitude) + (self.x_shift * self.y) + self.x_origin
	
	def update_y(self) -> None:
		if not self.tried_to_update:
			if random() <= 0.001:
				self.sprite = pyglet.sprite.Sprite(weighted_companion_cube_img)
				self.common = False
			self.tried_to_update = True
		if not self.common:
			self.sprite.rotation += 0.1
		self.raw_y = (time() - self.start_time) * self.speed - bubble_img.width
	
	def pop(self):
		self.sprite.y = window.height + self.size
		Effector.shake(2 * shake_level, 2 * shake_level, 0.1)
	
	def draw(self):
		self.sprite.x = self.x + render_offset.x
		self.sprite.y = self.y + render_offset.y
		self.sprite.draw()

# Draw the window's content
@window.event
def on_draw():
	global bubbles

	window.clear()

	# Updating bubbles' position and draw that are in the visible area
	for i in range(len(bubbles) - 1, -1, -1):
		bubbles[i].update_y()
		if bubbles[i].y < window.height + bubbles[i].size:
			bubbles[i].draw()
			#pyglet.shapes.Line(0, 0, bubbles[i].x, bubbles[i].y, 2, (255, 0, 0)).draw()
	
	if restore_ui_hint_shown:
		restore_ui_hint.draw()

	# Draw the UI if it is not hidden
	if ui_shown:
		ui_batch.draw()
	
	# Draw the settings if they are not hidden
	if settings_shown:
		settings_batch.draw()
		shake_level_widget.draw()

	# Draw song info if it should be displayed at the moment
	if showing_song_info:
		song_name.draw()
		song_hint.draw()
	
	# Draw the cursor
	cursor.draw()

# Handler for the mouse button press event
@window.event
def on_mouse_press(x, y, button, modifiers):
	global bubbles

	for btn in buttons:
		if btn.click(x, y):
			return None

	for i, obj in enumerate(bubbles):
		if obj.common:
			if x > obj.x and x < obj.x + obj.size and y > obj.y and y < obj.y + obj.size:
				obj.pop()
				bubbles.pop(i)
				return None
		else:
			if x > obj.x - (weighted_companion_cube_img.width // 2) and x < obj.x - (weighted_companion_cube_img.width // 2) + obj.size and y > obj.y - (weighted_companion_cube_img.width // 2) and y < obj.y - (weighted_companion_cube_img.width // 2) + obj.size:
				obj.pop()
				bubbles.pop(i)
				return None

# Handler for the mouse button motion event
@window.event
def on_mouse_motion(x, y, dx, dy):
	cursor.x = x
	cursor.y = y - 20

# Handler for the mouse button drag event
@window.event
def on_mouse_drag(x, y, dx, dy, buttons, modifiers):
	on_mouse_motion(x, y, dx, dy)

# Handler for the keyboard press event
@window.event
def on_key_press(symbol, modifiers):
	match symbol:

		case key.ESCAPE:
			if settings_shown:
				toggle_settings()
			return pyglet.event.EVENT_HANDLED
		
		case key.F1:
			toggle_ui()
			return pyglet.event.EVENT_HANDLED
		
		case key.S:
			if modifiers & key.MOD_CTRL:
				buttons[2].click(buttons[2].x + 1, buttons[2].y + 1)

		case key.N:
			if modifiers & key.MOD_CTRL:
				media_player.next_source()
				return pyglet.event.EVENT_HANDLED
			
		case key.SPACE:
			toggle_playback()
			return pyglet.event.EVENT_HANDLED

@window.event
def on_close():
	Console.log('window was closed', 'IntentHandler', 'I')
	Console.log('collecting app data to settings', 'IntentHandler', 'I')
	settings['locale'] = locale
	settings['shuffle'] = shuffle_playlist
	settings['shake_level'] = shake_level
	Console.log('dumping settings -> data/settings.json', 'IntentHandler', 'I')
	with open('data/settings.json', 'w') as file: dump(settings, file, indent = 4)
	Console.log('exitting', 'IntentHandler', 'I')

# A function that creates random bubbles with a random delay. Blocking.
def spawner():
	Console.log('hello', 'Spawner', 'I')
	if not pyglet.app.event_loop.is_running:
		while not pyglet.app.event_loop.is_running:
			Console.log('waiting until event_loop runs', 'Spawner', 'I')
			sleep(0.2)
	Console.log('met event_loop', 'Spawner', 'I')
	while pyglet.app.event_loop.is_running:
		delay = randint(1, 3)
		sleep(delay)
		bubbles.reverse()
		bubbles.append(Bubble(
			x_origin  = randint(0, window.width - bubble_img.width),
			speed     = randint(30, 60),
			frequency = randint(15, 25) / 1000,
			x_shift   = random() * 2 - 1
		))
		bubbles.reverse()
	Console.log('event_loop is inactive; ending', 'Spawner', 'I')

# Starting the spawner thread
thr = Thread(target=spawner, args=())
thr.start()

# Starting the music
media_player.play()
on_player_next_source()

# Starting the Pyglet app
pyglet.app.run()

# Waiting for event_loop to stop, then delete media_player
while pyglet.app.event_loop.is_running:
	sleep(1)
media_player.pause()
media_player.delete()
