from pyglet.window import key
from webbrowser    import open as open_url
from minilogger    import Console
from threading     import Thread
from random        import randint, choice
from time          import time, sleep
from json          import load
from math          import sin
from os            import listdir

import pyglet

class Empty: ...

# Initializing the window
screen = pyglet.canvas.get_display().get_screens()
window = pyglet.window.Window(fullscreen=True, screen=screen[0])
window.set_mouse_visible(False)

# Loading images
bubble_img = pyglet.image.load('resources/sprites/bubble.png')
cursor_img = pyglet.image.load('resources/sprites/cursor.png')
github_img = pyglet.image.load('resources/sprites/github.png')
settings_img = pyglet.image.load('resources/sprites/settings.png')
shuffle_img = pyglet.image.load('resources/sprites/shuffle.png')
cross_img = pyglet.image.load('resources/sprites/cross.png')
disabled_img = pyglet.image.load('resources/sprites/disabled.png')
enabled_img = pyglet.image.load('resources/sprites/enabled.png')

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
shuffle_playlist = True
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

# Pop-up with the track name
song_name = pyglet.text.Label(
	text      = f'Song: {music[0]["name"]}',
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
	text      = '[Ctrl+N] to skip',
	font_name = 'Arial',
	font_size = 17,
	italic    = True,
	color     = (255, 255, 255, 75),
	x         = window.width - 10,
	y         = 20,
	anchor_x  = 'right'
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
	song_name.text = f'Song: {music[selected_track]["name"]}'
	thr = Thread(target=show_song_info, args=())
	thr.start()

# Shows/Hides the settings section. Currently in development.
settings_shown = False
def toggle_settings():
	global settings_shown
	settings_shown = not settings_shown

# Opens the project page on GitHub in the browser
def open_github():
	open_url('https://github.com/R1senDev/bubbles_and_chillout')

# Shows/Hides the UI.
ui_shown = True
def toggle_ui():
	global ui_shown
	ui_shown = not ui_shown

# Enables/Disables playlist shuffling
def toggle_shuffle():
	global shuffle_playlist
	shuffle_playlist = not shuffle_playlist

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
			render_offset.x = choice(xs)
			render_offset.y = choice(ys)
			if not pyglet.app.event_loop.is_running:
				Console.log('event_loop is inactive; ending', 'Effector.shake', 'I')
				return None
			sleep(0.01)
		Console.log('ended', 'Effector.shake', 'D')
		render_offset.x = 0
		render_offset.y = 0

	@classmethod
	def shake(self, x_offset: int = 3, y_offset: int = 3, fx_time: float = 1):
		thr = Thread(target=self.shake_fx, args=[x_offset, y_offset, time() + fx_time])
		thr.start()

# Button class
class Button:
	def __init__(self, x: int, y: int, w: int, h: int, texture, on_click = lambda: ..., two_states: bool = False) -> None:
		self.x = x
		self.y = y
		self.w = w
		self.h = h
		self.sprite = pyglet.sprite.Sprite(texture, batch = ui_batch, x = x, y = y)
		self.on_click = on_click
		self.two_states = two_states
		if self.two_states:
			self.state = True
			self.cross = pyglet.sprite.Sprite(disabled_img, x = self.x + self.w - 15, y = -15, batch = ui_batch)
			self.tick = pyglet.sprite.Sprite(enabled_img, x = self.x + self.w - 15, y = self.y, batch = ui_batch)
	
	def click(self, x: int, y: int) -> bool:
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
	Button(10, 10, 50, 50, github_img, open_github, False),
	#Button(10, 10, 50, 50, settings_img, toggle_settings, False),
	Button(70, 10, 50, 50, shuffle_img, toggle_shuffle, True),
	Button(window.width - 40, window.height - 40, 30, 30, cross_img, pyglet.app.event_loop.exit, False),
]

# Bubble class
class Bubble:
	raw_y = 0
	size = 300
	sprite = pyglet.sprite.Sprite(bubble_img)

	def __init__(self, x_origin: int, amplitude: float = 150, frequency: float = 0.025, speed: float = 40, function = sin) -> None:
		self.start_time = time()
		self.x_origin = x_origin
		self.amplitude = amplitude
		self.frequency = frequency
		self.speed = speed
		self.func = function

	@property
	def y(self) -> int:
		return int(self.raw_y)
	
	@property
	def x(self) -> int:
		return int(self.func(self.y * self.frequency) * self.amplitude) + self.x_origin
	
	def update_y(self) -> None:
		self.raw_y = (time() - self.start_time) * self.speed - 300
	
	def pop(self):
		self.sprite.y = window.height + self.size
	
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
	
	# Draw the UI if it is not hidden
	if ui_shown:
		ui_batch.draw()
	
	# Draw the settings if they are not hidden
	if settings_shown:
		settings_batch.draw()

	# Draw song info if it should be displayed at the moment
	if showing_song_info:
		song_name.draw()
		song_hint.draw()
	
	# Draw the cursor
	cursor.x += render_offset.x
	cursor.y += render_offset.y
	cursor.draw()

# Handler for the mouse button press event
@window.event
def on_mouse_press(x, y, button, modifiers):
	global bubbles

	for btn in buttons:
		if btn.click(x, y):
			return None

	for i, obj in enumerate(bubbles):
		if x > obj.x and x < obj.x + obj.size and y > obj.y and y < obj.y + obj.size:
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
			return pyglet.event.EVENT_HANDLED
		case key.F1:
			toggle_ui()
		case key.N:
			if modifiers & key.MOD_CTRL:
				media_player.next_source()
		case key.SPACE:
			if media_player.playing:
				media_player.pause()
			else:
				media_player.play()

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
			x_origin  = randint(0, window.width - 300),
			speed     = randint(30, 60),
			frequency = randint(15, 25) / 1000
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
