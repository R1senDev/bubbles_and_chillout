from lib.plato import show_popup
from traceback import format_exc

try:

	from pyglet.graphics import Batch
	from pyglet.resource import media
	from pyglet.display  import get_display
	from pyglet.window   import key, Window
	from pyglet.sprite   import Sprite
	from pyglet.image    import load as pgl_load_image, AbstractImage
	from pyglet.clock    import schedule_interval
	from pyglet.event    import EVENT_HANDLED
	from pyglet.media    import Player
	from pyglet.text     import Label
	from pyglet.app      import event_loop, run

	from lib.settingsmgr import settings, save_settings
	from lib.pligamepad  import GamepadListener
	from lib.minilogger  import Console

	from webbrowser import open as open_url
	from threading  import Thread
	from random     import random, randint, choice
	from time       import time, sleep
	from json       import load
	from math       import sin
	from os         import listdir


	def load_image(path: str) -> AbstractImage:
		Console.log(f'loading image asset: {path}', 'Loader')
		return pgl_load_image(path)


	# Initializing the window
	try:
		screen = get_display().get_screens()
		window = Window(
			fullscreen = True,
			screen     = screen[0],
			caption    = 'Bubbles and Chillout'
		)
	except:

		with open('traceback.txt', 'w') as exception_file:
			exception_file.write(format_exc())

		show_popup(
			'Bubbles and Chillout',
			'An exception occurred during window initialization. Traceback was dumped to a file traceback.txt.'
		)

		exit(-1)

	window.set_mouse_visible(False)


	##############
	##  ASSETS  ##
	##############


	# Loading localization strings
	with open('resources/data/localization.json', 'r', encoding = 'utf-8') as file: locales = load(file)

	# Loading images
	bubble_img                  = load_image('resources/sprites/bubble.png')
	weighted_companion_cube_img = load_image('resources/sprites/weighted_companion_cube.png')

	cursor_img     = load_image('resources/ui/cursor.png')
	github_img     = load_image('resources/ui/github.png')
	settings_img   = load_image('resources/ui/settings.png')
	shuffle_img    = load_image('resources/ui/shuffle.png')
	play_pause_img = load_image('resources/ui/play_pause.png')
	show_img       = load_image('resources/ui/show.png')
	hide_img       = load_image('resources/ui/hide.png')
	minimize_img   = load_image('resources/ui/minimize.png')
	cross_img      = load_image('resources/ui/cross.png')
	disabled_img   = load_image('resources/ui/disabled.png')
	enabled_img    = load_image('resources/ui/enabled.png')
	globe_img      = load_image('resources/ui/globe.png')
	pulse_img      = load_image('resources/ui/pulse.png')
	level0_img     = load_image('resources/ui/level_off.png')
	level1_img     = load_image('resources/ui/level_low.png')
	level2_img     = load_image('resources/ui/level_medium.png')
	level3_img     = load_image('resources/ui/level_high.png')

	# Settings up anchors
	weighted_companion_cube_img.anchor_x = weighted_companion_cube_img.width // 2
	weighted_companion_cube_img.anchor_y = weighted_companion_cube_img.height // 2

	# Creating sprites from images
	cursor = Sprite(cursor_img)

	# Creating drawing batches
	settings_batch      = Batch()
	ui_batch            = Batch()
	gamepad_ctrls_batch = Batch()

	# Loading music
	with open('resources/data/music_meta.json', 'r') as file: music_meta = load(file)
	music = []
	for fname in listdir('resources/music/'):
		if fname not in music_meta:
			Console.log(f'"resources/music/{fname}" has no accompanying entry in music_meta; skipping', 'ResourceLoader', 'W')
			continue
		music.append({
			'media': media(f'resources/music/{fname}'),
			'name': music_meta[fname]['name']
		})


	###############
	##  CLASSES  ##
	###############


	class Hotkeys:
		class Keyboard:
			TOGGLE_UI  = 'F1'
			SKIP_TRACK = 'Ctrl+N'
		class Gamepad:
			TOGGLE_UI  = 'X'
			SKIP_TRACK = 'RB'


	class IntPoint:
		def __init__(self, x: int, y: int) -> None:
			self.x = x
			self.y = y


	class Effector:
		'''
		Generates screen effects.
		'''

		render_offset = IntPoint(0, 0)

		@classmethod
		def shake_fx(cls, x_offset: int, y_offset: int, end_time: float):
			if not event_loop.is_running:
				Console.log('waiting until event_loop runs', 'Effector.shake', 'I')
				while not event_loop.is_running:
					sleep(0.2)
				Console.log('met event_loop', 'Effector.shake', 'I')
			Console.log('started', 'Effector.shake', 'D')
			while time() < end_time:
				xs = list([i for i in range(-x_offset, x_offset + 1)])
				ys = list([i for i in range(-y_offset, y_offset + 1)])
				xs.remove(cls.render_offset.x)
				ys.remove(cls.render_offset.y)
				if not (xs or ys):
					Console.log('effect cannot be played: all of offsets == 0', 'Effector.shake', 'I')
					return None
				if xs:
					cls.render_offset.x = choice(xs)
				if ys:
					cls.render_offset.y = choice(ys)
				if not event_loop.is_running:
					Console.log('event_loop is inactive; ending', 'Effector.shake', 'I')
					return None
				sleep(0.01)
			Console.log('ended', 'Effector.shake', 'D')
			cls.render_offset.x = 0
			cls.render_offset.y = 0

		@classmethod
		def shake_widget_fx(cls, x_offset: int, y_offset: int, end_time: float):
			if not event_loop.is_running:
				Console.log('waiting until event_loop runs', 'Effector.shake_widget', 'I')
				while not event_loop.is_running:
					sleep(0.2)
				Console.log('met event_loop', 'Effector.shake_widget', 'I')
			Console.log('started', 'Effector.shake_widget', 'D')
			sx = shake_level_widget.sprites[0].x
			sy = shake_level_widget.sprites[0].y
			while time() < end_time:
				xs = list([i + sx for i in range(-x_offset, x_offset + 1)])
				ys = list([i + sy for i in range(-y_offset, y_offset + 1)])
				try:
					xs.remove(shake_level_widget.sprites[0].x)
					ys.remove(shake_level_widget.sprites[0].y)
				except: ...
				if not (xs or ys):
					Console.log('effect cannot be played: all of offsets == 0', 'Effector.shake_widget', 'I')
					return None
				if xs:
					for sprite in shake_level_widget.sprites:
						sprite.x = choice(xs)
				if ys:
					for sprite in shake_level_widget.sprites:
						sprite.y = choice(ys)
				if not event_loop.is_running:
					Console.log('event_loop is inactive; ending', 'Effector.shake_widget', 'I')
					return None
				sleep(0.01)
			Console.log('ended', 'Effector.shake_widget', 'D')
			for sprite in shake_level_widget.sprites:
				sprite.x = sx
				sprite.y = sy

		@classmethod
		def shake(cls, x_offset: int = 3, y_offset: int = 3, fx_time: float = 1):
			thr = Thread(
				target = cls.shake_fx,
				args   = (x_offset, y_offset, time() + fx_time),
				name   = 'ShakeFXThread'
			)
			thr.start()

		@classmethod
		def shake_widget(cls, x_offset: int = 3, y_offset: int = 3, fx_time: float = 1):
			thr = Thread(
				target = cls.shake_widget_fx,
				args   = (x_offset, y_offset, time() + fx_time),
				name   = 'WidgetShakeFXThread'
			)
			thr.start()


	class LevelWidget:
		def __init__(self, x: int, y: int, level_sprites: list):
			self.sprites = []
			for img in level_sprites:
				self.sprites.append(Sprite(img, x, y))
			self.level = settings['shake_level']

		def draw(self):
			self.sprites[self.level].draw()


	class Button:
		def __init__(self, position: IntPoint, size: IntPoint, texture: AbstractImage, on_click = lambda: ..., has_two_states: bool = False, classes: list[str] = []) -> None:
			self.pos = position
			self.size = size
			self.sprite = Sprite(
				img   = texture,
				batch = settings_batch if 'settings' in classes else ui_batch,
				x     = position.x,
				y     = position.y
			)
			self.on_click = on_click
			self.has_two_states = has_two_states
			self.classes = classes
			if self.has_two_states:
				self.state = True
				self.cross = Sprite(
					img   = disabled_img,
					x     = self.pos.x + self.size.x - 15,
					y     = -15,
					batch = ui_batch
				)
				self.tick = Sprite(
					img   = enabled_img,
					x     = self.pos.x + self.size.x - 15,
					y     = self.pos.y,
					batch = ui_batch
				)

		def set_y(self, y: int):
			self.pos.y = y
			self.sprite.y = y
			if not self.has_two_states:
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
			if x > self.pos.x and x < self.pos.x + self.size.x and y > self.pos.y and y < self.pos.y + self.size.y and ui_shown:
				self.on_click()
				if self.has_two_states:
					self.state = not self.state
					if self.state:
						self.cross.y = -15
						self.tick.y = self.pos.y
					else:
						self.cross.y = self.pos.y
						self.tick.y = -15
				return True
			return False
		

	class Bubble:
		raw_y = 0
		size = bubble_img.width
		tried_to_update = False
		common = True
		popped = False
		sprite = Sprite(bubble_img)

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
					self.sprite = Sprite(weighted_companion_cube_img)
					self.common = False
				self.tried_to_update = True
			if not self.common:
				self.sprite.rotation += 0.1
			self.raw_y = (time() - self.start_time) * self.speed - bubble_img.width

		def pop(self):
			self.popped = True
			Effector.shake(2 * settings['shake_level'], 2 * settings['shake_level'], 0.1)

		def draw(self):
			self.sprite.x = self.x + Effector.render_offset.x
			self.sprite.y = self.y + Effector.render_offset.y
			self.sprite.draw()

		
	###############
	##  GLOBALS  ##
	###############


	hotkey_provider = Hotkeys.Keyboard
	cursor_pos = IntPoint(0, 0)
	selected_track = 0
	media_player = Player()
	locales_list = list(locales.keys())
	show_song_info_until = time()
	settings_shown = False
	restore_ui_hint_shown = False
	restore_ui_hint_already_shown = False
	ui_shown = True
	bubbles: list['Bubble'] = []
	a_old = b_old = x_old = rb_old = False
	gamepad = GamepadListener()


	#################
	##  FUNCTIONS  ##
	#################


	def media_player_controller():
		'''
		Looped playlist generator.
		'''
		global selected_track

		while True:
			if settings['shuffle']:
				next_track = randint(0, len(music) - 1)
				while next_track == selected_track:
					next_track = randint(0, len(music) - 1)
				selected_track = next_track
			else:
				selected_track += 1
				if selected_track == len(music):
					selected_track = 0
			yield music[selected_track]['media']

	media_player.queue(media_player_controller())


	def change_language(just_refresh: bool = False):
		'''
		Changes the GUI locale.
		'''
		settings['locale'] += 1 - just_refresh
		if settings['locale'] == len(locales_list):
			settings['locale'] = 0

		song_hint.text = locales[locales_list[settings["locale"]]]['to_skip'].format(hotkey_provider.SKIP_TRACK)
		locale_label.text = f'{locales[locales_list[settings["locale"]]]["self_name"]} ({locales[locales_list[settings["locale"]]]["en_name"]})'
		restore_ui_hint.text = locales[locales_list[settings['locale']]]['restore_ui_hint'].format('+'.join([hotkey_provider.TOGGLE_UI]))

	
	def open_github():
		'''
		Opens the project page on GitHub in the browser.
		'''
		open_url('https://github.com/R1senDev/bubbles_and_chillout')

	
	def toggle_settings():
		'''
		Shows/Hides the settings section.
		'''
		global settings_shown
		settings_shown = not settings_shown

		for btn in buttons:
			if 'main_row' in btn.classes:
				btn.set_y(130 if settings_shown else 10)


	def toggle_playback():
		'''
		Plays/Pauses the music playback.
		'''
		if media_player.playing:
			media_player.pause()
		else:
			media_player.play()

		
	def restore_ui_hint_controller():
		'''
		Controls the HowToBringTheUIBackAfterHidingIt hint label.
		'''
		global restore_ui_hint_shown
		restore_ui_hint_shown = True
		end_time = time() + 10
		while time() < end_time and not ui_shown:
			sleep(0.02)
		restore_ui_hint_shown = False


	def toggle_ui():
		'''
		Shows/Hides the UI.
		'''
		global ui_shown, restore_ui_hint_already_shown
		ui_shown = not ui_shown
		if settings_shown:
			toggle_settings()
		if not restore_ui_hint_already_shown:
			restore_ui_hint_already_shown = True
			thr = Thread(
				target = restore_ui_hint_controller,
				args   = (),
				name   = 'RestoreUIControllerThread'
			)
			thr.start()


	def toggle_shuffle():
		'''
		Toggles tracks playback order.
		'''
		settings['shuffle'] = not settings['shuffle']


	def change_shake_level():
		settings['shake_level'] += 1
		if settings['shake_level'] > 3:
			settings['shake_level'] = 0
		shake_level_widget.level = settings['shake_level']
		Effector.shake_widget(3 * settings['shake_level'], 3 * settings['shake_level'], 0.25)


	def close_app():
		on_close()
		window.close()


	####################
	##  GUI ELEMENTS  ##
	####################


	song_name = Label(
		text      = f'{locales[locales_list[settings["locale"]]]["song"]}: {music[0]["name"]}',
		font_name = 'Arial',
		font_size = 50,
		weight    = 'bold',
		italic    = True,
		color     = (255, 255, 255, 125),
		x         = window.width - 10,
		y         = 55,
		anchor_x  = 'right'
	)
	song_hint = Label(
		text      = locales[locales_list[settings['locale']]]['to_skip'].format('+'.join(['Ctrl', 'N'])),
		font_name = 'Arial',
		font_size = 17,
		italic    = True,
		color     = (255, 255, 255, 75),
		x         = window.width - 10,
		y         = 20,
		anchor_x  = 'right'
	)

	locale_label = Label(
		text      = f'{locales[locales_list[settings["locale"]]]["self_name"]} ({locales[locales_list[settings["locale"]]]["en_name"]})',
		font_name = 'Arial',
		font_size = 20,
		color     = (255, 255, 255, 100),
		x         = 70,
		y         = 95,
		anchor_y  = 'center',
		batch     = settings_batch
	)

	restore_ui_hint = Label(
		text      = locales[locales_list[settings['locale']]]['restore_ui_hint'].format('+'.join(['F1'])),
		font_name = 'Arial',
		font_size = 20,
		italic    = True,
		color     = (255, 255, 255, 75),
		x         = 10,
		y         = window.height - 10,
		anchor_y  = 'top',
	)


	buttons = [
		Button(IntPoint( 10, 10), IntPoint( 50, 50), github_img,     open_github,        False, ['main_row']),
		Button(IntPoint( 70, 10), IntPoint( 50, 50), settings_img,   toggle_settings,    False, ['main_row']),
		Button(IntPoint(130, 10), IntPoint( 50, 50), shuffle_img,    toggle_shuffle,     True,  ['main_row']),
		Button(IntPoint(190, 10), IntPoint( 50, 50), play_pause_img, toggle_playback,    False, ['main_row']),

		Button(IntPoint( 10, 70), IntPoint( 50, 50), globe_img,      change_language,    False, ['settings']),
		Button(IntPoint( 10, 10), IntPoint(110, 50), pulse_img,      change_shake_level, False, ['settings']),

		Button(IntPoint(10, window.height - 60), IntPoint(50, 50), hide_img, toggle_ui, False, []),

		Button(IntPoint(window.width - 90, window.height - 40), IntPoint(30, 30), minimize_img, window.minimize, False, ['window_controls']),
		Button(IntPoint(window.width - 40, window.height - 40), IntPoint(30, 30), cross_img, close_app, False, ['window_controls']),
	]


	if not settings['shuffle']:
		buttons[2].state = False
		buttons[2].cross.y = buttons[2].pos.y
		buttons[2].tick.y = -15


	def update(*args) -> None:
		...


	#######################
	##  EVENTS HANDLERS  ##
	#######################


	def emulated_mouse_press(x, y, button, modifiers) -> None:
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
				

	def gamepad_handler(*args) -> None:
		global hotkey_provider, a_old, b_old, x_old, rb_old

		if gamepad.registered and hotkey_provider != Hotkeys.Gamepad:
			hotkey_provider = Hotkeys.Gamepad
			change_language(just_refresh = True)

		window.set_mouse_position(
			int(cursor_pos.x + gamepad.stick.left.x * settings['gamepad']['mouse_sensitivity']),
			int(cursor_pos.y + 1 - gamepad.stick.left.y * settings['gamepad']['mouse_sensitivity'])
		)

		if (gamepad.key.a or gamepad.trigger.right.value > 0.5) and not a_old: emulated_mouse_press(cursor_pos.x, cursor_pos.y, -1, -1)
		if gamepad.key.b and not b_old: toggle_playback()
		if gamepad.key.x and not x_old: toggle_ui()
		if gamepad.bumper.right and not rb_old: media_player.next_source()

		a_old  = bool(gamepad.key.a) or gamepad.trigger.right.value > 0.5
		b_old  = bool(gamepad.key.b)
		x_old  = bool(gamepad.key.x)
		rb_old = bool(gamepad.bumper.right)


	@media_player.event
	def on_player_next_source():
		global show_song_info_until
		song_name.text = f'{locales[locales_list[settings["locale"]]]["song"]}: {music[selected_track]["name"]}'
		show_song_info_until = time() + 5

	shake_level_widget = LevelWidget(70, 20, [
		level0_img,
		level1_img,
		level2_img,
		level3_img
	])


	@window.event
	def on_draw():
		global bubbles

		window.clear()

		new_bubbles: list[Bubble] = []
		for bubble in reversed(bubbles):
			bubble.update_y()
			if bubble.y < window.height + bubble.size and not bubble.popped:
				bubble.draw()
				new_bubbles.insert(0, bubble)
		bubbles = new_bubbles

		if restore_ui_hint_shown:
			restore_ui_hint.draw()

		# Draw the UI if it is not hidden
		if ui_shown:
			ui_batch.draw()

		# Draw gamepad hints if required
		# TODO: freaking hints
		if gamepad.registered:
			gamepad_ctrls_batch.draw()

		# Draw the settings if they are not hidden
		if settings_shown:
			settings_batch.draw()
			shake_level_widget.draw()

		# Draw song info if it should be displayed at the moment
		if show_song_info_until >= time():
			song_name.draw()
			song_hint.draw()

		# Draw the cursor
		cursor.draw()


	@window.event
	def on_mouse_press(x, y, button, modifiers):
		emulated_mouse_press(x, y, button, modifiers)


	@window.event
	def on_mouse_motion(x, y, dx, dy):
		cursor_pos.x = x
		cursor_pos.y = y
		cursor.x = x
		cursor.y = y - 20


	@window.event
	def on_mouse_drag(x, y, dx, dy, buttons, modifiers):
		on_mouse_motion(x, y, dx, dy)


	@window.event
	def on_key_press(symbol, modifiers):
		match symbol:

			case key.ESCAPE:
				if settings_shown:
					toggle_settings()
				return EVENT_HANDLED

			case key.F1:
				toggle_ui()
				return EVENT_HANDLED

			case key.S:
				if modifiers & key.MOD_CTRL:
					buttons[2].click(buttons[2].pos.x + 1, buttons[2].pos.y + 1)

			case key.N:
				if modifiers & key.MOD_CTRL:
					media_player.next_source()
					return EVENT_HANDLED

			case key.SPACE:
				toggle_playback()
				return EVENT_HANDLED


	@window.event
	def on_close():
		Console.log('got window closing intent', 'IntentHandler', 'I')
		Console.log('saving settings', 'IntentHandler', 'I')
		save_settings()
		Console.log('stopping gamepad listener', 'IntentHandler', 'I')
		gamepad.stop()
		Console.log('exitting', 'IntentHandler', 'I')


	def spawner():
		'''
		Creates random bubbles with a random delay.
		
		*Blocking.*
		'''
		if not event_loop.is_running:
			while not event_loop.is_running:
				Console.log('waiting until event_loop runs', 'Spawner', 'I')
				sleep(0.2)
		Console.log('met event_loop', 'Spawner', 'I')

		while event_loop.is_running:
			delay = randint(1, 3)
			sleep(delay)
			bubbles.insert(0, Bubble(
				x_origin  = randint(0, window.width - bubble_img.width),
				speed     = randint(30, 60),
				frequency = randint(15, 25) / 1000,
				x_shift   = int(random() * 2 - 1)
			))
			
		Console.log('event_loop is inactive; ending', 'Spawner', 'I')


	# Creating threads
	spawner_thread = Thread(
		target = spawner,
		args   = (),
		name   = 'SpawnerThread'
	)

	# Starting everything 
	gamepad.start()

	schedule_interval(gamepad_handler, 0.01)
	schedule_interval(update, 1/60)

	spawner_thread.start()

	media_player.play()
	on_player_next_source()

	run()

	# Waiting for event_loop to stop, then cleanup
	while event_loop.is_running:
		sleep(1)
	gamepad.stop()
	media_player.pause()
	media_player.delete()

except:

	with open('traceback.txt', 'w') as exception_file:
			exception_file.write(format_exc())

	show_popup(
		'Bubbles and Chillout',
		'An exception occurred. Traceback was dumped to a file traceback.txt.'
	)

	exit(-1)