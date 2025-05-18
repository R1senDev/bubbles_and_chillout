from lib.plato import show_popup
from traceback import format_exc

try:

	from pyglet.media.codecs.base import Source
	from pyglet.graphics          import Batch
	from pyglet.resource          import media, add_font
	from pyglet.display           import get_display
	from pyglet.window            import key, Window
	from pyglet.shapes            import Rectangle, Circle
	from pyglet.sprite            import Sprite
	from pyglet.image             import load as load_image, AbstractImage
	from pyglet.clock             import schedule_interval # type: ignore
	from pyglet.event             import EVENT_HANDLED, EVENT_UNHANDLED
	from pyglet.media             import Player
	from pyglet.text              import Label
	from pyglet.app               import event_loop, run

	from lib.settingsmgr import settings, save_settings
	from lib.commonsense import IntPoint
	from lib.pligamepad  import GamepadListener
	from lib.minilogger  import Console
	from lib.gridgen     import grid

	from webbrowser import open as open_url
	from threading  import Thread
	from string     import ascii_lowercase, digits
	from random     import random, randint, choice
	from typing     import Any, Literal, Union, Callable, Generator
	from types      import SimpleNamespace
	from time       import time, sleep
	from json       import load
	from math       import sin
	from os         import listdir


	Asset = Union[AbstractImage, Source]
	AnchorX = Literal['left', 'center', 'right']
	AnchorY = Literal['top', 'center', 'bottom', 'baseline']
	ContentVAlign = Literal['bottom', 'center', 'top']


	####################
	##  INITIALIZING  ##
	####################


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
	window.set_mouse_position(window.width // 2, window.height // 2)

	media_player = Player()
	gamepad = GamepadListener()


	##############
	##  ASSETS  ##
	##############


	class AssetsManager:

		_consts = SimpleNamespace()
		_consts.allowed_chars = ascii_lowercase + digits + '_'
		_consts.banned_lead   = digits
		_consts.fallback_char = '_'
		_consts.image_exts = ('png', 'jpg', 'jpeg', 'bmp')
		_consts.media_exts = ('wav', 'ogg', 'mp3')
		assets = SimpleNamespace()

		@classmethod
		def _reg_name_by_fname(cls, fname: str) -> str:

			reg_name = ''

			for _char in fname:
				char = _char.lower()
				if char in cls._consts.allowed_chars:
					reg_name += char
				else:
					reg_name += cls._consts.fallback_char

			reg_name = reg_name.lstrip(cls._consts.banned_lead)

			return reg_name
		
		@classmethod
		def _load_asset(cls, path: str) -> Asset | None:
			while '//' in path: path = path.replace('//', '/')
			Console.log(f'loading asset: {path}', 'AssetsLoader', 'I')
			ext = path.rsplit('.')[-1]
			if ext in cls._consts.image_exts: return load_image(path)
			if ext in cls._consts.media_exts: return media(path)
			Console.log(f'failed loading asset: {path}: unable to guess asset category', 'AssetsLoader', 'E')

		@classmethod
		def load_folder(cls, path: str, group_name: str) -> None:

			path += ''
			assets = SimpleNamespace()

			for fname in listdir(path):
				reg_name = fname.rsplit('.')[0].replace('-', '_')
				asset = cls._load_asset(f'{path}/{fname}')
				assets.__setattr__(reg_name, asset)
			
			cls.assets.__setattr__(group_name, assets)

		@classmethod
		def _load_font(cls, path: str) -> None:
			while '//' in path: path = path.replace('//', '/')
			Console.log(f'loading font asset: {path}', 'AssetManager', 'I')
			add_font(path)

		@classmethod
		def load_fonts_folder(cls, path: str) -> None:
			for fname in listdir(path):
				cls._load_font(f'{path}/{fname}')


	class Track:

		def __init__(self, media: Source, artist: str, title: str) -> None:

			self.media = media
			self.artist = artist
			self.title = title


	# Loading localization strings
	with open('resources/data/localization.json', 'r', encoding = 'utf-8') as file: locales = load(file)
	locales_list = list(locales.keys())

	# Loading assets
	AssetsManager.load_folder('resources/sprites/', 'sprites')
	AssetsManager.load_folder('resources/ui/',      'ui')

	# Settings up anchors
	AssetsManager.assets.sprites.weighted_companion_cube.anchor_x = AssetsManager.assets.sprites.weighted_companion_cube.width // 2
	AssetsManager.assets.sprites.weighted_companion_cube.anchor_y = AssetsManager.assets.sprites.weighted_companion_cube.height // 2
	
	# Loading fonts
	AssetsManager.load_fonts_folder('resources/fonts/')
	
	# Creating sprites from images
	cursor = Sprite(AssetsManager.assets.ui.cursor)

	# Creating rendering batches
	settings_batch      = Batch()
	ui_batch            = Batch()
	gamepad_ctrls_batch = Batch()

	# Loading music
	with open('resources/data/music_meta.json', 'r') as file:
		music_meta: dict[str, dict[str, str]] = load(file)
	music: list[Track] = []
	for fname in listdir('resources/music/'):
		if fname not in music_meta:
			Console.log(f'"resources/music/{fname}" has no accompanying entry in music_meta; skipping', 'ResourceLoader', 'W')
			continue
		music.append(Track(
			media(f'resources/music/{fname}'),
			music_meta[fname]['artist'],
			music_meta[fname]['name']
		))


	###############
	##  CLASSES  ##
	###############


	class OldGamepadStates:
		start = False
		mode  = False
		rb    = False
		a     = False
		b     = False
		x     = False


	class Showing:
		song_info_until: float   = 0.0
		settings: bool           = False
		restore_ui_hint: bool    = False
		ui: bool                 = True
		gamepad_ctrls_hint: bool = False
		class Allowed:
			restore_ui_hint: bool = True


	class Controls:
		'''
		This class manages *labels* for GUI controls hints, not influencing on the actual binds.
		'''
		class Keyboard:
			'''
			These strings will be shown only if player uses **keyboard** as the input method.
			'''
			HELP_WINDOW    = 'ctrl_start'
			MOUSE_MOVE     = 'ctrl_left_stk'
			MOUSE_PRESS    = 'ctrl_lmb'
			PAUSE_MUSIC    = 'ctrl_space'
			TOGGLE_UI      = 'ctrl_f1'
			SKIP_TRACK     = 'ctrl_ctrln'
			TOGGLE_SHUFFLE = 'ctrl_ctrls'
			CLOSE_HELP     = 'ctrl_start'
			EXIT_GAME      = 'ctrl_modeb'
		class Gamepad:
			'''
			These strings will be shown only if player uses **gamepad** as the input method.
			'''
			HELP_WINDOW    = 'ctrl_start'
			MOUSE_MOVE     = 'ctrl_left_stk'
			MOUSE_PRESS    = 'ctrl_gmp_a'
			PAUSE_MUSIC    = 'ctrl_gmp_b'
			TOGGLE_UI      = 'ctrl_gmp_x'
			SKIP_TRACK     = 'ctrl_rb'
			TOGGLE_SHUFFLE = 'ctrl_ctrls'
			CLOSE_HELP     = 'ctrl_start'
			EXIT_GAME      = 'ctrl_modeb'
		provider: Keyboard | Gamepad = Keyboard # type: ignore


	class ExtLabel(Label):
		def __init__(
				self,
				text: str = '',
				x: float = 0,
				y: float = 0,
				z: float = 0,
				width: int | None = None,
				height: int | None = None,
				anchor_x: AnchorX = 'left',
				anchor_y: AnchorY = 'baseline',
				rotation: float = 0,
				multiline: bool = False,
				dpi: int | None = None,
				font_name: str | None = None,
				font_size: float | None = None,
				weight: str = 'normal',
				italic: bool | str = False,
				stretch: bool | str = False,
				color: tuple[int, int, int, int] | tuple[int, int, int] = (255, 255, 255, 255),
				align: ContentVAlign = 'bottom',
				batch: Batch | None = None
				) -> None:
			super().__init__(text, x, y, z, width, height, anchor_x, anchor_y, rotation, multiline, dpi, font_name, font_size, weight, italic, stretch, color, align, batch)
			self.default_weight = weight
			self.default_italic = italic

		
	class RoundedRectangle:

		def __init__(
				self,
				pos: IntPoint,
				size: IntPoint,
				radius: int,
				color: tuple[int, int, int] = (255, 255, 255),
				batch: Batch | None = None
				) -> None:
			_color = color + (255,)
			self.drawables: list[Rectangle | Circle] = [
				Rectangle(
					x      = pos.x + radius,
					y      = pos.y,
					width  = size.x - 2 * radius,
					height = size.y,
					color  = _color,
					batch  = batch
				),
				Rectangle(
					x      = pos.x,
					y      = pos.y + radius,
					width  = size.x,
					height = size.y - 2 * radius,
					color  = _color,
					batch  = batch
				),
				Circle(
					x      = pos.x + radius,
					y      = pos.y + radius,
					radius = radius,
					color  = _color,
					batch  = batch
				),
				Circle(
					x      = pos.x + size.x - radius,
					y      = pos.y + radius,
					radius = radius,
					color  = _color,
					batch  = batch
				),
				Circle(
					x      = pos.x + size.x - radius,
					y      = pos.y + size.y - radius,
					radius = radius,
					color  = _color,
					batch  = batch
				),
				Circle(
					x      = pos.x + radius,
					y      = pos.y + size.y - radius,
					radius = radius,
					color  = _color,
					batch  = batch
				)
			]

		def draw(self) -> None:
			for drawable in self.drawables:
				drawable.draw()


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
			thread = Thread(
				target = cls.shake_fx,
				args   = (x_offset, y_offset, time() + fx_time),
				name   = 'ShakeFXThread'
			)
			thread.start()

		@classmethod
		def shake_widget(cls, x_offset: int = 3, y_offset: int = 3, fx_time: float = 1):
			thread = Thread(
				target = cls.shake_widget_fx,
				args   = (x_offset, y_offset, time() + fx_time),
				name   = 'WidgetShakeFXThread'
			)
			thread.start()


	class LevelWidget:
		def __init__(self, x: int, y: int, level_sprites: list[AbstractImage]):
			self.sprites: list[Sprite] = []
			for img in level_sprites:
				self.sprites.append(Sprite(img, x, y))
			self.level: int = settings['shake_level']

		def draw(self):
			self.sprites[self.level].draw()


	class Button:
		def __init__(self, position: IntPoint, size: IntPoint, texture: AbstractImage, on_click: Callable[[], Any] = lambda: ..., has_two_states: bool = False, classes: list[str] = []) -> None:
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
					img   = AssetsManager.assets.ui.disabled,
					x     = self.pos.x + self.size.x - 15,
					y     = -15,
					batch = ui_batch
				)
				self.tick = Sprite(
					img   = AssetsManager.assets.ui.enabled,
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
			if 'settings' in self.classes and not Showing.settings:
				return False
			if x > self.pos.x and x < self.pos.x + self.size.x and y > self.pos.y and y < self.pos.y + self.size.y and Showing.ui:
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
		size = AssetsManager.assets.sprites.bubble.width
		tried_to_update = False
		common = True
		popped = False
		sprite = Sprite(AssetsManager.assets.sprites.bubble)

		def __init__(self, x_origin: int, amplitude: float = 150, frequency: float = 0.025, x_shift: int = 0, speed: float = 40, function: Callable[[float], float] = sin) -> None:
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
					self.sprite = Sprite(AssetsManager.assets.sprites.weighted_companion_cube)
					self.common = False
				self.tried_to_update = True
			if not self.common:
				self.sprite.rotation += 0.1
			self.raw_y = (time() - self.start_time) * self.speed - AssetsManager.assets.sprites.bubble.width

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


	cursor_pos = IntPoint(0, 0)
	selected_track = 0
	bubbles: list['Bubble'] = []


	#################
	##  FUNCTIONS  ##
	#################


	def media_player_controller() -> Generator[Source, None, None]:
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
			media = music[selected_track].media
			yield media

	media_player.queue(media_player_controller())


	def change_language(just_refresh: bool = False):
		'''
		Changes the GUI locale and font.
		'''
		settings['locale'] += 1 - just_refresh
		if settings['locale'] == len(locales_list):
			settings['locale'] = 0

		if not just_refresh:
			labels['reloading_required'] = ExtLabel(
				text = locales[locales_list[settings['locale']]]['reload_is_required'],
				x         = window.width // 2,
				y         = window.height - 10,
				font_size = 25,
				anchor_x  = 'center',
				anchor_y  = 'top',
				batch     = ui_batch
			)

		labels['locale'].text = f'{locales[locales_list[settings["locale"]]]["self_name"]} ({locales[locales_list[settings["locale"]]]["en_name"]})'

		silly_mode: bool = locales[locales_list[settings['locale']]]['_properties']['silly_mode'] # type: ignore

		for label in labels.values():
			label.font_name = locales[locales_list[settings['locale']]]['_properties']['font_name']
			if silly_mode:
				label.weight = 'normal'
				label.italic = False
			else:
				label.weight = label.default_weight
				label.italic = label.default_italic

	
	def open_github():
		'''
		Opens the project page on GitHub in the browser.
		'''
		open_url('https://github.com/R1senDev/bubbles_and_chillout')

	
	def toggle_settings():
		'''
		Shows/Hides the settings section.
		'''
		Showing.settings = not Showing.settings

		for btn in buttons:
			if 'main_row' in btn.classes:
				btn.set_y(130 if Showing.settings else 10)


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
		Showing.restore_ui_hint = True
		end_time = time() + 10
		while time() < end_time and not Showing.ui:
			sleep(0.02)
		Showing.restore_ui_hint = False


	def toggle_ui():
		'''
		Shows/Hides the UI.
		'''
		Showing.ui = not Showing.ui
		if Showing.settings:
			toggle_settings()
		if Showing.Allowed.restore_ui_hint:
			Showing.Allowed.restore_ui_hint = False
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


	HELP_WINDOW_PADDING = 100
	HELP_WINDOW_GRID_STEP = 50
	help_window_grid = grid(IntPoint(0, window.height - round(2 * HELP_WINDOW_PADDING) - 3 * HELP_WINDOW_GRID_STEP), -HELP_WINDOW_GRID_STEP, 'vertical')


	help_window_bg = RoundedRectangle(
		pos    = IntPoint(HELP_WINDOW_PADDING, HELP_WINDOW_PADDING),
		size   = IntPoint(window.width - 2 * HELP_WINDOW_PADDING, window.height - 2 * HELP_WINDOW_PADDING),
		radius = 20,
		color  = (51, 51, 51),
		batch  = gamepad_ctrls_batch
	)


	labels = {
		'song_name': ExtLabel(
			text      = f'...', # type: ignore
			font_size = 50,
			weight    = 'bold',
			italic    = True,
			color     = (255, 255, 255, 125),
			x         = window.width - 30,
			y         = 120,
			anchor_x  = 'right'
		),
		'song_artist': ExtLabel(
			text      = f'от ...', # type: ignore
			font_size = 35,
			italic    = True,
			color     = (255, 255, 255, 125),
			x         = window.width - 30,
			y         = 110,
			anchor_x  = 'right',
			anchor_y  = 'top'
		),
		'song_hint': ExtLabel(
			text      = locales[locales_list[settings['locale']]]['to_skip'].format(locales[locales_list[settings['locale']]][Controls.provider.SKIP_TRACK]), # type: ignore
			font_size = 17,
			italic    = True,
			color     = (255, 255, 255, 75),
			x         = window.width - 30,
			y         = 20,
			anchor_x  = 'right'
		),

		'locale': ExtLabel(
			text      = f'{locales[locales_list[settings["locale"]]]["self_name"]} ({locales[locales_list[settings["locale"]]]["en_name"]})',
			font_size = 20,
			color     = (255, 255, 255, 102),
			x         = 70,
			y         = 95,
			anchor_y  = 'center',
			batch     = settings_batch
		),

		'restore_ui_hint': ExtLabel(
			text      = locales[locales_list[settings['locale']]]['restore_ui_hint'].format(locales[locales_list[settings['locale']]][Controls.provider.TOGGLE_UI]), # type: ignore
			font_size = 20,
			italic    = True,
			color     = (255, 255, 255, 102),
			x         = 10,
			y         = window.height - 10,
			anchor_x  = 'left',
			anchor_y  = 'top'
		),

		'gmp_hint_title': ExtLabel(
			text      = locales[locales_list[settings['locale']]]['gmp_hint_title'],
			font_size = 35,
			weight    = 'bold',
			color     = (255, 255, 255, 255),
			x         = window.width // 2,
			y         = window.height - round(1.5 * HELP_WINDOW_PADDING),
			anchor_x  = 'center',
			anchor_y  = 'top',
			batch     =	gamepad_ctrls_batch
		)
	}

	for data in (
		('gmp_hint_open_this_window',  Controls.Gamepad.HELP_WINDOW),
		('gmp_hint_move_the_mouse',    Controls.Gamepad.MOUSE_MOVE),
		('gmp_hint_lmb',               Controls.Gamepad.MOUSE_PRESS),
		('gmp_hint_pause',             Controls.Gamepad.PAUSE_MUSIC),
		('gmp_hint_hide_ui',           Controls.Gamepad.TOGGLE_UI),
		('gmp_hint_skip_track',        Controls.Gamepad.SKIP_TRACK),
		('gmp_hint_shuffling',         Controls.Gamepad.TOGGLE_SHUFFLE)
	):
		labels[data[0]] = ExtLabel(
			text      = locales[locales_list[settings['locale']]][data[0]].format(locales[locales_list[settings['locale']]][data[1]]),
			font_size = 25,
			color     = (255, 255, 255, 255),
			x         = window.width // 2,
			y         = next(help_window_grid).y,
			anchor_x  = 'center',
			anchor_y  = 'top',
			batch     =	gamepad_ctrls_batch
		)

	labels['gmp_hint_close_this_window'] = ExtLabel(
			text      = locales[locales_list[settings['locale']]]['gmp_hint_close_this_window'].format(locales[locales_list[settings['locale']]][Controls.Gamepad.CLOSE_HELP]),
			font_size = 35,
			weight    = 'bold',
			color     = (255, 255, 255, 255),
			x         = window.width // 2,
			y         = next(help_window_grid).y - 3 * HELP_WINDOW_GRID_STEP,
			anchor_x  = 'center',
			anchor_y  = 'top',
			batch     =	gamepad_ctrls_batch
		)
	
	# Changing the font right away
	change_language(just_refresh = True)


	buttons = [
		Button(IntPoint( 10, 10), IntPoint( 50, 50), AssetsManager.assets.ui.github,     open_github,        False, ['main_row']),
		Button(IntPoint( 70, 10), IntPoint( 50, 50), AssetsManager.assets.ui.settings,   toggle_settings,    False, ['main_row']),
		Button(IntPoint(130, 10), IntPoint( 50, 50), AssetsManager.assets.ui.shuffle,    toggle_shuffle,     True,  ['main_row']),
		Button(IntPoint(190, 10), IntPoint( 50, 50), AssetsManager.assets.ui.play_pause, toggle_playback,    False, ['main_row']),

		Button(IntPoint( 10, 70), IntPoint( 50, 50), AssetsManager.assets.ui.globe,      change_language,    False, ['settings']),
		Button(IntPoint( 10, 10), IntPoint(110, 50), AssetsManager.assets.ui.pulse,      change_shake_level, False, ['settings']),

		Button(IntPoint(10, window.height - 60), IntPoint(50, 50), AssetsManager.assets.ui.hide, toggle_ui, False, []),

		Button(IntPoint(window.width - 90, window.height - 40), IntPoint(30, 30), AssetsManager.assets.ui.minimize, window.minimize, False, ['window_controls']),
		Button(IntPoint(window.width - 40, window.height - 40), IntPoint(30, 30), AssetsManager.assets.ui.cross, close_app, False, ['window_controls']),
	]


	if not settings['shuffle']:
		buttons[2].state = False
		buttons[2].cross.y = buttons[2].pos.y
		buttons[2].tick.y = -15


	#######################
	##  EVENTS HANDLERS  ##
	#######################


	def emulated_mouse_press(x: int, y: int, *args: int) -> None:
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
				if x > obj.x - (AssetsManager.assets.sprites.weighted_companion_cube.width // 2) and x < obj.x - (AssetsManager.assets.sprites.weighted_companion_cube.width // 2) + obj.size and y > obj.y - (AssetsManager.assets.sprites.weighted_companion_cube.width // 2) and y < obj.y - (AssetsManager.assets.sprites.weighted_companion_cube.width // 2) + obj.size:
					obj.pop()
					bubbles.pop(i)
					return None
				

	def gamepad_handler(*args: int) -> None:
		if gamepad.registered and Controls.provider != Controls.Gamepad: # type: ignore
			Controls.provider = Controls.Gamepad # type: ignore
			change_language(just_refresh = True)

		window.set_mouse_position(
			int(cursor_pos.x + gamepad.stick.left.x * settings['gamepad']['mouse_sensitivity']),
			int(cursor_pos.y + 1 - gamepad.stick.left.y * settings['gamepad']['mouse_sensitivity'])
		)

		if gamepad.key.start and gamepad.key.b: window.on_close()
		if gamepad.key.start and not OldGamepadStates.start: Showing.gamepad_ctrls_hint = not Showing.gamepad_ctrls_hint
		if (gamepad.key.a or gamepad.trigger.right.value > 0.5) and not OldGamepadStates.a: emulated_mouse_press(cursor_pos.x, cursor_pos.y, -1, -1)
		if gamepad.key.b and not OldGamepadStates.b: toggle_playback()
		if gamepad.key.x and not OldGamepadStates.x: toggle_ui()
		if gamepad.bumper.right and not OldGamepadStates.rb: media_player.next_source()

		OldGamepadStates.start = bool(gamepad.key.start)
		OldGamepadStates.mode  = bool(gamepad.key.mode)
		OldGamepadStates.rb    = bool(gamepad.bumper.right)
		OldGamepadStates.a     = bool(gamepad.key.a) or gamepad.trigger.right.value > 0.5
		OldGamepadStates.b     = bool(gamepad.key.b)
		OldGamepadStates.x     = bool(gamepad.key.x)


	@media_player.event # type: ignore
	def on_player_next_source():
		labels['song_name'].text = locales[locales_list[settings["locale"]]]["quotes"][0] + music[selected_track].title + locales[locales_list[settings["locale"]]]["quotes"][1]
		labels['song_artist'].text = locales[locales_list[settings["locale"]]]["by_artist"].format(music[selected_track].artist)
		Showing.song_info_until = time() + 5

	shake_level_widget = LevelWidget(70, 20, [
		AssetsManager.assets.ui.level_off,
		AssetsManager.assets.ui.level_low,
		AssetsManager.assets.ui.level_medium,
		AssetsManager.assets.ui.level_high
	])


	@window.event # type: ignore
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

		if Showing.restore_ui_hint:
			labels['restore_ui_hint'].draw()

		# Draw the UI if it is not hidden
		if Showing.ui:
			ui_batch.draw()

		# Draw the settings if they are not hidden
		if Showing.settings:
			settings_batch.draw()
			shake_level_widget.draw()

		# Draw gamepad hints if required
		if Showing.gamepad_ctrls_hint:
			gamepad_ctrls_batch.draw()

		# Draw song info if it should be displayed at the moment
		if Showing.song_info_until >= time():
			labels['song_name'].draw()
			labels['song_artist'].draw()
			labels['song_hint'].draw()

		# Draw the cursor
		cursor.draw()


	@window.event # type: ignore
	def on_mouse_press(x: int, y: int, button: int, modifiers: int):
		emulated_mouse_press(x, y, button, modifiers)


	@window.event # type: ignore
	def on_mouse_motion(x: int, y: int, dx: int, dy: int):
		cursor_pos.x = x
		cursor_pos.y = y
		cursor.x = x
		cursor.y = y - 20


	@window.event # type: ignore
	def on_mouse_drag(x: int, y: int, dx: int, dy: int, buttons: int, modifiers: int):
		on_mouse_motion(x, y, dx, dy)


	@window.event # type: ignore
	def on_key_press(symbol: int, modifiers: int):
		match symbol:

			case key.ESCAPE:
				if Showing.settings:
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
			
			case _:
				return EVENT_UNHANDLED


	@window.event # type: ignore
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
				x_origin  = randint(0, window.width - AssetsManager.assets.sprites.bubble.width),
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