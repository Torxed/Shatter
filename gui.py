import pyglet, pickle
from pyglet.gl import *
from threading import *
from os.path import isfile, abspath
from collections import OrderedDict as OD
from time import time
from json import loads, dumps

## The audio transport:
from record import *
# REQUIRES: AVBin
pyglet.options['audio'] = ('alsa', 'openal', 'silent')
key = pyglet.window.key

if isfile('./cache.pick'):
	with open('./cache.pick', 'rb') as fh:
		try:
			cache = pickle.load(fh)
		except EOFError as err:
			cache = {}
else:
	cache = {}

net = network()
net.connect('109.124.175.121')#('192.168.227.128')
sound = microphone(net)

def decompress(data):
	try:
		return zlib.decompress(data)
	except:
		return b'{"Error" : "Decompressing string"}'

def deserialize(data):
	return b64decode(data)

def depickle(data):
	return pickle.loads(data)

def convertData(obfuscated_audio_frame):
	return depickle(deserialize(obfuscated_audio_frame))

def mainThread():
	for t in enumerate():
		if t.name == 'MainThread':
			return t
	return None

class Spr(pyglet.sprite.Sprite):
	def __init__(self, texture=None, width=None, height=None, color="#C2C2C2", x=None, y=None, anchor=None):
		if not texture or not isfile(texture):
			## If no texture was supplied, we will create one
			if not width:
				width = 220
			if not height:
				height = 450
			self.texture = self.gen_solid_img(width, height, color)
		else:
			self.texture = pyglet.image.load(texture)
		super(Spr, self).__init__(self.texture)
		scale = 1.0
		if width and width < self.texture.width:
			scale = (1.0/max(width, self.texture.width))*min(width, self.texture.width)
		elif height and height < self.texture.height:
			scale = (1.0/max(height, self.texture.height))*min(height, self.texture.height)
		self.scale = scale

		self.anchor = anchor
		if anchor == 'center':
			self.image.anchor_x = self.image.width / 2
			self.image.anchor_y = self.image.height / 2
		if x:
			self.x = x
		if y:
			self.y = y

	def swap_image(self, image, filePath=True, width=None):
		if filePath:
			self.texture = pyglet.image.load(abspath(image))
		else:
			self.texture = image
		self.image = self.texture
		if width and width < self.texture.width:
			scale = (1.0/max(width, self.texture.width))*min(width, self.texture.width)
			self.scale = scale

	def gen_solid_img(self, width, height, c):
		if '#' in c:
			c = c.lstrip("#")
			c = max(6-len(c),0)*"0" + c
			r = int(c[:2], 16)
			g = int(c[2:4], 16)
			b = int(c[4:], 16)
			c = (r,g,b,255)#int(0.2*255))
		return pyglet.image.SolidColorImagePattern(c).create_image(width,height)

	def draw_line(self, xy, dxy, color=(0.2, 0.2, 0.2, 1)):
		glColor4f(color[0], color[1], color[2], color[3])
		glBegin(GL_LINES)
		glVertex2f(xy[0], xy[1])
		glVertex2f(dxy[0], dxy[1])
		glEnd()

	def draw_border(self, color=(0.2, 0.2, 0.2, 0.5)):
		self.draw_line((self.x, self.y), (self.x, self.y+self.height+1), color)
		self.draw_line((self.x, self.y+self.height+1), (self.x+self.width+1, self.y+self.height+1), color)
		self.draw_line((self.x+self.width+1, self.y+self.height+1), (self.x+self.width+1, self.y), color)
		self.draw_line((self.x+self.width+1, self.y), (self.x, self.y), color)

	def pixels_to_vertexlist(self, pixels):
		# Outdated pixel conversion code
		vertex_pixels = []
		vertex_colors = []

		for pixel in pixels:
			vertex = list(pixel)
			vertex_pixels += vertex[:-1]
			vertex_colors += list(vertex[-1])

		# Old pyglet versions (including 1.1.4, not including 1.2
		# alpha1) throw an exception if vertex_list() is called with
		# zero vertices. Therefore the length must be checked before
		# calling vertex_list().
		#
		# TODO: Remove support for pyglet 1.1.4 in favor of pyglet 1.2.
		if len(pixels):
			return pyglet.graphics.vertex_list(
				len(pixels),
				('v2i', tuple(vertex_pixels)),
				('c4B', tuple(vertex_colors)))
		else:
			return None

	def clean_vertexes(self, *args):
		clean_list = []
		for pair in args:
			clean_list.append((int(pair[0]), int(pair[1])))
		return clean_list

	def draw_square(self, bottom_left, top_left, top_right, bottom_right, color=(0.2, 0.2, 0.2, 0.5)):
		#glColor4f(0.2, 0.2, 0.2, 1)
		#glBegin(GL_LINES)

		bottom_left, top_left, top_right, bottom_right = self.clean_vertexes(bottom_left, top_left, top_right, bottom_right)

		c = (255, 255, 255, 128)

		window_corners = [
			(bottom_left[0],bottom_left[1],c),	# bottom left
			(top_left[0],top_left[1],c),	# top left
			(top_right[0],top_right[1],c),	# top right
			(bottom_right[0],bottom_right[1],c)		# bottom right
		]

		box_vl = self.pixels_to_vertexlist(window_corners)
		box_vl.draw(pyglet.gl.GL_QUADS)
		#glEnd()

	def draw_header(self):
		"""size = 15
			glPointSize(size)
			glColor4f(0.2, 0.2, 0.2, 0.5)
			glEnable(GL_BLEND)
			glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
			glBegin(GL_POINTS)
	
			for x in range(self.x, self.x+self.width+size, size):
				for y in range(self.y, self.y+self.height, size):
					glVertex2f(x, y)
			glEnd()"""
		self.draw_square((self.x, self.y), (self.x, self.y+self.height), (self.x+self.width, self.y+self.height), (self.x+self.width, self.y))

	def rotate(self, deg):
		self.image.anchor_x = self.image.width / 2
		self.image.anchor_y = self.image.height / 2
		self.rotation = self.rotation+deg
		if self.anchor != 'center':
			self.image.anchor_x = 0
			self.image.anchor_y = 0
		return True

	def fade_in(self):
		self.opacity += 10
		if self.opacity > 255:
			self.opacity = 255

	def fade_out(self):
		self.opacity -= 2.5
		if self.opacity < 0:
			self.opacity = 0

	def click_check(self, x, y):
		"""
		When called, returns self (the object)
		to the calling-origin as a verification
		that we pressed inside this object, and
		by sending back self (the object) the caller
		can interact with this object
		"""
		if x > self.x and x < (self.x + self.width):
			if y > self.y and y < (self.y + self.height):
				return self

	def click(self, x, y, merge):
		"""
		Usually click_check() is called followed up
		with a call to this function.
		Basically what this is, is that a click
		should occur within the object.
		Normally a class who inherits Spr() will create
		their own click() function but if none exists
		a default must be present.
		"""
		return True

	def right_click(self, x, y, merge):
		"""
		See click(), same basic concept
		"""
		return True

	def hover(self, x, y):
		"""
		See click(), same basic concept
		"""
		return True

	def hover_out(self, x, y):
		"""
		See click(), same basic concept
		"""
		return True

	def type(self, what):
		"""
		Type() is called from main() whenever a key-press
		has occured that is type-able.
		Meaning whenever a keystroke is made and it was
		of a character eg. A-Z it will be passed as a str()
		representation to type() that will handle the character
		in a given manner.
		This function doesn't process anything but will need
		to be here in case a class that inherits Spr() doesn't
		have their own function for it (which, they should...) 
		"""
		return True

	def gettext(self):
		return ''

	def move(self, x, y):
		self.x += x
		self.y += y

	def _draw(self):
		"""
		Normally we call _draw() instead of .draw() on sprites
		because _draw() will contains so much more than simply
		drawing the object, it might check for interactions or
		update inline data (and most likely positioning objects).
		"""
		self.draw()

def colorConverter(r,g,b,a=255):
	r = (1.0/255)*r
	g = (1.0/255)*g
	b = (1.0/255)*b
	a = (1.0/255)*a
	return r,g,b,a

class profilePicture(Spr):
	def __init__(self, pic, width=72, height=72, x=0, y=0, border=False):
		super(profilePicture, self).__init__(pic, width, height)
		self.x = x
		self.y = y
		self.border = border

	def _draw(self):
		if self.border:
			self.draw_border(colorConverter(0, 191, 226))
		self.draw()

class searchBox(Spr):
	def __init__(self):
		super(searchBox, self).__init__(width=315-2, height=4, color=(0,0,0,0))
		self.x = 1
		self.y = 498
		self.showButton = True
		self.searchTxt = pyglet.text.Label("SEARCH", font_size=6, font_name=('Verdana', 'Calibri', 'Arial'), x=self.x+self.width/2-17, y=self.y-7)

	def _draw(self):
		self.draw_line((self.x, self.y), (self.x+self.width, self.y), colorConverter(71, 71, 71))
		self.draw_line((self.x, self.y+1), (self.x+self.width, self.y+1), colorConverter(71, 71, 71))
		self.draw_line((self.x, self.y+2), (self.x+self.width, self.y+2), colorConverter(71, 71, 71))
		self.draw_line((self.x, self.y+3), (self.x+self.width, self.y+3), colorConverter(71, 71, 71))

		if self.showButton:
			BUTTONWIDTH = 41
			startx = self.x+self.width/2 - BUTTONWIDTH/2
			starty = self.y-9
			self.draw_line((startx+3, starty), (startx+BUTTONWIDTH-3, starty), colorConverter(71, 71, 71))
			self.draw_line((startx+2, starty+1), (startx+BUTTONWIDTH-2, starty+1), colorConverter(71, 71, 71))
			self.draw_line((startx+1, starty+2), (startx+BUTTONWIDTH-1, starty+2), colorConverter(71, 71, 71))
			self.draw_line((startx, starty+3), (startx+BUTTONWIDTH, starty+3), colorConverter(71, 71, 71))
			for ypos in range(4,10):
				self.draw_line((startx, starty+ypos), (startx+BUTTONWIDTH, starty+ypos), colorConverter(71, 71, 71))
		self.searchTxt.draw()
		self.draw()

def call(who):
	if who in sound.calls:
		net.send(bytes(dumps({'command' : 'hangup::'+who}), 'UTF-8'))
		del sound.calls[who]
		sound.mute()
		sound.silence()
	else:
		net.send(bytes(dumps({'command' : 'call::'+who}), 'UTF-8'))
		sound.calls[who] = {'muted' : False, 'micmute' : False}
		sound.unmute()
		sound.unsilence()

class Button(Spr):
	def __init__(self, pic, x, y, func, params=[]):
		self.pics = pic
		self.pic = 0
		super(Button, self).__init__(self.pics[self.pic], x=x, y=y)
		self.func = func
		self.params = params

	def click(self, x, y, merge):
		if self.func:
			self.pic += 1%(len(self.pics))
			self.image = pyglet.image.load(self.pics[self.pic])
			self.func(*self.params)

class chatwindow(pyglet.window.Window):
	def __init__ (self, friends_name, friend_id):
		super(chatwindow, self).__init__(315, 400, fullscreen = False, caption=friends_name)
		self.bg = Spr(width=315, height=400, color=(228,228,228,255))

		self.picture = profilePicture('./data/'+friends_name.lower().replace(' ', '_')+'.png', x=1, y=400-73, border=True)
		self.friends_name = friends_name
		self.friend_id = friend_id

		self.buttons = OD()
		self.buttons['call'] = Button(['./data/call.png', './data/hangup.png'], x=315-48-10, y=400-48-10, func=call, params=[friend_id,])

		self.drag = False
		self.active = None, None
		self.alive = 1
		self.multiselect = False

		self.modifiers = {'shift' : False}

		self.input = pyglet.text.Label("", font_size=8, font_name=('Verdana', 'Calibri', 'Arial'), x=4, y=30, multiline=False, width=380, height=40, color=(100, 100, 100, 255))

	def clean_vertexes(self, *args):
		clean_list = []
		for pair in args:
			clean_list.append((int(pair[0]), int(pair[1])))
		return clean_list

	def pixels_to_vertexlist(self, pixels):
		# Outdated pixel conversion code
		vertex_pixels = []
		vertex_colors = []

		for pixel in pixels:
			vertex = list(pixel)
			vertex_pixels += vertex[:-1]
			vertex_colors += list(vertex[-1])

		# Old pyglet versions (including 1.1.4, not including 1.2
		# alpha1) throw an exception if vertex_list() is called with
		# zero vertices. Therefore the length must be checked before
		# calling vertex_list().
		#
		# TODO: Remove support for pyglet 1.1.4 in favor of pyglet 1.2.
		if len(pixels):
			return pyglet.graphics.vertex_list(
				len(pixels),
				('v2i', tuple(vertex_pixels)),
				('c4B', tuple(vertex_colors)))
		else:
			return None

	def draw_square(self, bottom_left, top_left, top_right, bottom_right, color=(0.2, 0.2, 0.2, 0.5)):
		#glColor4f(0.2, 0.2, 0.2, 1)
		#glBegin(GL_LINES)

		bottom_left, top_left, top_right, bottom_right = self.clean_vertexes(bottom_left, top_left, top_right, bottom_right)

		c = (255, 255, 255, 128)

		window_corners = [
			(bottom_left[0],bottom_left[1],c),	# bottom left
			(top_left[0],top_left[1],c),	# top left
			(top_right[0],top_right[1],c),	# top right
			(bottom_right[0],bottom_right[1],c)		# bottom right
		]

		box_vl = self.pixels_to_vertexlist(window_corners)
		box_vl.draw(pyglet.gl.GL_QUADS)
		#glEnd()

	def on_draw(self):
		self.render()

	def on_close(self):
		print('closing')
		self.has_exit = True
		self.set_visible(False)
		self.close()

	def on_mouse_motion(self, x, y, dx, dy):
		pass

	def on_mouse_release(self, x, y, button, modifiers):
		for button in self.buttons:
			if self.buttons[button].click_check(x,y):
				self.buttons[button].click(x,y, None)
	
	def on_mouse_press(self, x, y, button, modifiers):
		pass

	def on_mouse_drag(self, x, y, dx, dy, button, modifiers):
		pass

	def on_key_release(self, symbol, modifiers):
		print(symbol)
		if symbol == key.LSHIFT:
			self.modifiers['shift'] = False
		print(self.modifiers)

	def on_key_press(self, symbol, modifiers):
		if symbol == 65307: # [ESC]
			self.has_exit = True
			self.set_visible(False)
			self.close()
		elif symbol == key.LSHIFT:
			self.modifiers['shift'] = True

		elif symbol == key.SPACE:
			self.input.text += ' '
		elif symbol == key.BACKSPACE:
			self.input.text = self.input.text[:-1]
		elif symbol == key.F11:
			pass #window.set_fullscreen(not window.fullscreen)
		elif symbol == key.ENTER:
			print('Sending',self.input.text)
		else:
			try:
				if self.modifiers['shift']:
					self.input.text += chr(symbol).upper()
				else:
					self.input.text += chr(symbol)
			except:
				pass

	def render(self):
		try:
			self.clear()
			self.bg.draw()
			self.picture._draw()

			self.draw_square((1,1), (1,40), (399,40), (399,1))
			self.input.draw()

			for button in self.buttons:
				self.buttons[button]._draw()

			self.flip()
			event = self.dispatch_events()
			return True
		except AttributeError:
			return None


class friend(Spr):
	def __init__(self, name, _id):
		super(friend, self).__init__(width=315-2, height=20, color='#cdcdcd')
		self.x = 1
		self.y = 476
		self.picture = profilePicture('./data/'+_id.lower().replace(' ', '_')+'.png', width=22, height=22, x=self.x, y=self.y-1)
		self.name = pyglet.text.Label(name, font_size=6, font_name=('Verdana', 'Calibri', 'Arial'), x=self.x+30, y=self.y+6, color=(100, 100, 100, 255))
		self.last_click = time()-10
		self.chatwindow = None
		self._id = _id.lower().replace(' ', '_')

	def click(self, x, y, merge):
		if time() - self.last_click < 0.5:
			pass
			if not self.chatwindow:
				self.chatwindow = chatwindow(self.name.text, self._id)
		else:
			print('Single-clicked')
		self.last_click = time()

	def _draw(self):
		self.draw_line((self.x, self.y), (self.x+self.width, self.y), colorConverter(178, 178, 178))
		self.draw_line((self.x, self.y+21), (self.x+self.width, self.y+21), colorConverter(178, 178, 178))
		self.draw()
		self.picture.y = self.y-1
		self.picture._draw()
		self.name.y=self.y+6
		self.name.draw()

		if self.chatwindow:
			if not self.chatwindow.render():
				self.chatwindow = None

class friendslist(Spr):
	def __init__(self):
		super(friendslist, self).__init__(width=315-2, height=20, color=(0,0,0,0))
		self.x = 1
		self.y = 476
		self.friends = OD()
		net.send(bytes(dumps({'command' : 'friendslist::get'}), 'UTF-8'))
		result = net.recv()
		result = loads(decompress(result[0]).decode('utf-8'))
		result = result['result']
		for friendObj in result:
			_id, name, status = friendObj
			self.friends[_id] = friend(name, _id)
			self.friends[_id].status = status

	def click_check(self, x, y):
		least_x = 1
		max_x = self.x+self.width
		least_y = self.y-(22*len(self.friends))
		max_y = self.y+self.height

		if x > least_x and x < max_x:
			if y > least_y and y < max_y:
				for friend in self.friends:
					if x > self.friends[friend].x and x < self.friends[friend].x+self.friends[friend].width:
						if y > self.friends[friend].y and y < self.friends[friend].y+self.friends[friend].height:
							return self.friends[friend]
				return self

	def _draw(self):
		self.draw()
		starty = self.y
		for friend in self.friends:
			self.friends[friend].y = starty
			self.friends[friend]._draw()
			starty -= 22

class inputfield(Spr):
	def __init__(self, x, y):
		super(inputfield, self).__init__(width=220, height=25, color=(200,200,200,128))
		self.x = x
		self.y = y
		self.text = pyglet.text.Label('', font_size=10, font_name=('Verdana', 'Calibri', 'Arial'), x=self.x+5, y=self.y+5)

	def input(self, c):
		if c == '\b':
			self.text.text = self.text.text[:-1]
		else:
			self.text.text += c

	def gettext(self):
		return self.text.text

	def _draw(self):
		self.draw_border(color=(0.2, 0.2, 0.2, 0.5))
		self.draw()
		self.text.draw()

class loginForm(Spr):
	def __init__(self, x=50, y=270, pic=None):
		super(loginForm, self).__init__(width=220, height=50, color=(0,0,0,0))
		self.username = inputfield(x, y+30)
		self.password = inputfield(x, y)
		if pic is None or pic=='./data/shatter.png':
			pic = './data/shatter.png'
			width = 113
			border=False
		else:
			width = 113
			border = True
		self.profilePic = profilePicture(pic, x=x+((self.width/2)-55), y=y+70, width=width, height=None, border=border)
		self.active = None

	def input(self, c):
		if self.active:
			self.active.input(c)
			if self.active == self.username:
				if isfile('./data/'+self.active.gettext()+'.png'):
					cache['loginpic'] = './data/' + self.active.gettext() + '.png'
					self.profilePic.swap_image(cache['loginpic'], width=113)
					#self.profilePic = profilePicture(cache['loginpic'], x=x+((self.width/2)-55), y=y+70, width=113, border=True)

	def next(self):
		if self.active == self.username:
			self.active = self.password
		else:
			self.active = self.username

	def gettext(self):
		return self.username.gettext(), self.password.gettext()

	def click_check(self, x, y):
		if self.username.click_check(x,y):
			self.active = self.username
		elif self.password.click_check(x,y):
			self.active = self.password
		return self

	def _draw(self):
		self.username._draw()
		self.password._draw()
		self.profilePic._draw()

class main(pyglet.window.Window):
	def __init__ (self, createStuff=True):
		super(main, self).__init__(315, 575, fullscreen = False, caption='Shatter')
		self.bg = Spr(width=315, height=575, color=(228,228,228,255))

		self.sprites = OD()
		self.lines = OD()
		self.merge_sprites = OD()
		
		self.page = 'login'
		self.show_login()
			
		self.drag = False
		self.active = None, None
		self.alive = 1
		self.multiselect = False

		self.modifiers = {'shift' : False}
		self.profile = None

	def on_draw(self):
		self.render()

	def on_close(self):
		self.alive = 0

	def show_login(self):
		self.sprites = OD()
		if not 'loginpic' in cache:
			cache['loginpic'] = None
		self.sprites['loginform'] = loginForm(pic=cache['loginpic'])

	def show_main(self):
		self.sprites = OD()
		self.sprites['friendslist'] = friendslist()
		self.sprites['profilepic'] = profilePicture(self.profile, x=1, y=502, border=True)
		self.sprites['searchbox'] = searchBox()

		self.lines['left_frame'] = (1, 0), (1, 575), colorConverter(0, 191, 226)
		self.lines['right_frame'] = (315, 0), (315, 575), colorConverter(0, 191, 226)
		self.lines['top'] = (0, 575), (315, 575), colorConverter(0, 191, 226)
		self.lines['bottom'] = (0, 1), (315, 1), colorConverter(0, 191, 226)

	def on_mouse_motion(self, x, y, dx, dy):
		for sprite_name, sprite in self.sprites.items():
			if sprite:
				sprite_obj = sprite.click_check(x, y)
				if sprite_obj:
					sprite_obj.hover(x, y)
				else:
					sprite.hover_out(x, y)

	def link_objects(self, start, end):
		start_obj, end_obj = None, None
		for sprite_name, sprite in self.sprites.items():
			if sprite and sprite_name not in ('2-loading'):
				if sprite.click_check(start[0], start[1]):
					start_obj = sprite_name, sprite
				if sprite.click_check(end[0], end[1]):
					end_obj = sprite_name, sprite

		del(self.lines['link'])
		if start_obj and end_obj and end_obj[0] != start_obj[0]:
			start_obj[1].link(end_obj[1])

	def on_mouse_release(self, x, y, button, modifiers):
		if button == 1:
			if self.active[1] and not self.drag and self.multiselect == False:
				self.active[1].click(x, y, self.merge_sprites)
				if self.active[0] == 'menu':
					del(self.sprites['menu'])
			self.drag = False
			if 'link' in self.lines:
				##   link_objects( lines == ((x, y), (x, y)) )
				self.link_objects(self.lines['link'][0], self.lines['link'][1])
		elif button == 4:
			if not self.active[0]:
				pass #Do something on empty spaces?
			else:
				self.active[1].right_click(x, y, self.merge_sprites)
			#self.sprites['temp_vm'] = virtualMachine(pos=(x-48, y-48))
			#self.requested_input = self.sprites['temp_vm'].draws['1-title']
			#self.sprites['input'] = Input("Enter the name of your virtual machine", pos=(int(self.width/2-128), int(self.height/2-60)), height=120)

		#if type(self.active[1]) != Input:
		#	self.active = None, None
	
	def on_mouse_press(self, x, y, button, modifiers):
		if button == 1 or button == 4:
			for sprite_name, sprite in self.sprites.items():
				if sprite:
					sprite_obj = sprite.click_check(x, y)
					if sprite_obj:
						self.active = sprite_name, sprite_obj
						if button == 1:
							if self.multiselect != False:
								if sprite_name not in self.multiselect:
										self.multiselect.append(sprite_name)

	def on_mouse_drag(self, x, y, dx, dy, button, modifiers):
		self.drag = True
		if self.active[1] and self.multiselect == False and hasattr(self.active[1], 'link'):
			self.lines['link'] = ((self.active[1].x+(self.active[1].width/2), self.active[1].y+(self.active[1].height/2)), (x,y))
		elif self.multiselect:
			for obj in self.multiselect:
				self.sprites[obj].move(dx, dy)

	def on_key_release(self, symbol, modifiers):
		if symbol == key.LCTRL:
			self.multiselect = False

	def on_key_press(self, symbol, modifiers):
		if symbol == 65307: # [ESC]
			self.alive = 0
		
		elif symbol == key.LSHIFT:
			self.modifiers['shift'] = True

		elif self.active[1] and hasattr(self.active[1], 'input') and hasattr(self.active[1], 'gettext'):
			if symbol == key.SPACE:
				if self.active[1]:
					self.active[1].input(' ')
			elif symbol == key.BACKSPACE:
				if self.active[1]:
					self.active[1].input('\b')
			elif symbol == key.TAB:
				if self.active[1] and hasattr(self.active[1], 'next'):
					self.active[1].next()
			elif symbol == key.ENTER:
				if self.active[1]:
					if self.page == 'login':
						username, password = self.active[1].gettext()
						print('Logging in: ', username)
						sound.WhoAmI = username
						net.send(bytes(dumps({'user' : username, 'command' : 'login::' + username + '::' + password}), 'UTF-8'))
						result = net.recv()
						result = loads(decompress(result[0]).decode('utf-8'))
						if result['result'] == 'OK':
							self.profile = './data/' + username.replace(' ', '_').lower() + '.png'
							self.show_main()
				self.active = None, None
			elif symbol == key.F11:
				pass #window.set_fullscreen(not window.fullscreen)
			else:
				if self.active[1]:
					try:
						if self.modifiers['shift']:
							self.active[1].input(chr(symbol).upper())
						else:
							self.active[1].input(chr(symbol))
					except:
						pass

	def draw_line(self, xy, dxy, color=(0.2, 0.2, 0.2, 1)):
		glColor4f(*color)
		glBegin(GL_LINES)
		glVertex2f(xy[0], xy[1])
		glVertex2f(dxy[0], dxy[1])
		glEnd()

	def render(self):
		self.clear()
		self.bg.draw()

		for group_name in self.lines:
			if group_name == 'link':
				xy = self.lines[group_name][0]
				dxy = self.lines[group_name][1]
			elif type(self.lines[group_name]) == tuple:
				try:
					xy, dxy, color = self.lines[group_name]
				except:
					xy, dxy = self.lines[group_name]
					color = colorConverter(255,255,255)
			else:
				xy = self.lines[group_name][0].x+self.lines[group_name][0].width/2, self.lines[group_name][0].y+self.lines[group_name][0].height/2
				dxy = self.lines[group_name][1].x+self.lines[group_name][1].width/2, self.lines[group_name][1].y+self.lines[group_name][1].height/2

			self.draw_line(xy, dxy, color)

		if len(self.merge_sprites) > 0:
			merge_sprite = self.merge_sprites.popitem()
			#if merge_sprite[0] == 'input':
			#	self.requested_input = merge_sprite[1][0]
			#	self.sprites[merge_sprite[0]] = merge_sprite[1][1]
			#else:
			self.sprites[merge_sprite[0]] = merge_sprite[1]


		## Some special code for creating the "header",
		## I'f prefer to put that into a Spr() class with a width and stuff.
		#glPointSize(25)
		#glColor4f(0.2, 0.2, 0.2, 0.5)	
		#glEnable(GL_BLEND)
		#glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
		#glBegin(GL_POINTS)
		#for x in range(0,self.width+25,25):
		#	for y in range(0-64-15,0,25):
		#		glVertex3f(x, self.height+y, 0)
		#glEnd()
		#self.draw_line((0, self.height-64-26), (self.width, self.height-64-26))
		
		for sprite_name, sprite in self.sprites.items():
			if sprite and sprite_name not in ('msgbox', 'input', 'menu'):
				sprite._draw()

		if self.multiselect != False:
			for sprite_name in self.multiselect:
				sprite = self.sprites[sprite_name]
				sprite.draw_border(color=(0.2, 1.0, 0.2, 0.5))

		if 'menu' in self.sprites:
			self.sprites['menu']._draw()

		if 'input' in self.sprites:
			self.sprites['input']._draw()

		#if 'msgbox' in self.sprites:
		#	if self.sprites['msgbox']:
		#		self.sprites['msgbox']._draw()

		#	if self.sprites['msgbox'] and self.sprites['msgbox'].Answer != None:
		#		print('None')

		self.flip()

	def run(self):
		while self.alive == 1:
			self.render()

			# -----------> This is key <----------
			# This is what replaces pyglet.app.run()
			# but is required for the GUI to not freeze
			#
			event = self.dispatch_events()

class sound_output(Thread):
	def __init__(self, network, so):
		Thread.__init__(self)
		self.net = network
		self.sound = so
		self.start()

	def run(self):
		for frame in self.net.recv():
			frame = loads(decompress(frame).decode('utf-8'))
			if 'data' in frame:
				self.sound.play_frame(frame)
			else:
				print(frame)

player = sound_output(net, sound)

x = main()
x.run()

with open('./cache.pick', 'wb') as fh:
	pickle.dump(cache, fh)