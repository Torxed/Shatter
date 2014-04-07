from sys import byteorder, exit, stdout
from array import array
from struct import pack
from json import loads, dumps
from time import sleep
from threading import *
from socket import *
from base64 import b64encode, b64decode
from os import _exit
#from pickle import dumps, loads, HIGHEST_PROTOCOL

import zlib
import pickle
import select
import pyaudio
import wave

CHUNK_SIZE = 1024
FORMAT = pyaudio.paInt16
RATE = 44100

def decompress(data):
	return zlib.decompress(data)

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

class network(Thread):
	def __init__(self):
		Thread.__init__(self)
		self.name = 'Networking'
		self.sockets = {}
		self.watch = {'input' : {}, 'output' : {}}
		self.incomming = socket()
		self.incomming.bind(('',1337))
		self.incomming.listen(4)
		self.sockets['server'] = self.incomming
		self.recieving = False

	def connect(self, target, port=1337):
		self.sockets[target] = socket()
		self.sockets[target].connect((target, port))

	def close(self):
		for s in list(self.sockets.keys()):
			self.sockets[s].close()

	def pick(self, data):
		return pickle.dumps(data, pickle.HIGHEST_PROTOCOL)

	def serialize(self, data):
		return b64encode(data)

	def compress(self, data):
		return zlib.compress(data, 6)

	def encrypt(self, data):
		return data

	def pad(self, data):
		if len(data) >= 4096:
			print('Critical error')
		pads = [b'\x00', b'\x11']
		for i in range(0, len(pads)):
			padWith = pads[i]
			if padWith[0] != data[-1]: break

		return data + padWith*(4096-len(data))

	def send(self, data):
		data = self.encrypt(self.compress(data))
		for s in select.select([], list(sock for key, sock in self.sockets.items()), [], 0.025)[1]:
			if s == self.incomming: continue

			while self.recieving:
				pass

			padded = self.pad(data)
			s.send(padded)

	def remove(self, sock):
		sock.close()
		for socketname in list(self.sockets):
			if self.sockets[socketname] == sock:
				del self.sockets[socketname]

	def recv(self, buffsize=1024):
		frames = []
		for s in select.select(list(sock for key, sock in self.sockets.items()), [], [], 0.025)[0]:
			if s == self.incomming:
				ns, na = s.accept()
				self.sockets[na[0]] = ns
				print(na[0],'connected')
			else:
				self.recieving = True
				try:
					## TODO: Fix this shit, because we need a better way to deal with it.
					## For instance, loop over select.select until it's empty and append
					## data to each socket in a dict instead of a list.
					data = b''
					while len(data) < 4096:
						data += s.recv(4096)
				except ConnectionResetError:
					self.remove(s)
					continue
				if len(data) > 0:
					frames.append(data)
			self.recieving = False
		return frames


class microphone(Thread):
	def __init__(self, _network, WhoAmI='Torxed'):
		Thread.__init__(self)
		self.p = pyaudio.PyAudio()
		self.stream = self.p.open(format=FORMAT, channels=1, rate=RATE,
							input=True, output=True,
							frames_per_buffer=CHUNK_SIZE)
		self.output = None
		self.network = _network
		self.muted = True
		self.silenced = True
		self.WhoAmI = WhoAmI
		self.calls = {}

		self.start()

	def is_silent(self, snd_data, THRESHOLD = 150):
		"Returns 'True' if below the 'silent' threshold"
		return max(snd_data) < THRESHOLD

	def mute(self):
		self.muted = True

	def unmute(self):
		self.muted = False

	def silence(self):
		self.silenced = True

	def unsilence(self):
		self.silenced = False

	def play_frame(self, frame):
		if not self.output:
			self.output = self.p.open(format=self.p.get_format_from_width(frame['sampleWidth']),
							channels=1,
							rate=frame['rate'],
							output=True)
		self.output.write(convertData(frame['data']))

	def run(self):
		r = array('h')

		sample_width = self.p.get_sample_size(FORMAT)
		sending = False
		silence_count = 0

		while mainThread() and mainThread().isAlive():
			audio_frame = self.stream.read(CHUNK_SIZE)
			#audio_frame = array('h', self.stream.read(CHUNK_SIZE))
			silent = self.is_silent(array('h', audio_frame))
			if not silent:
				if not self.muted:
					sending = True
					audio_frame = self.network.serialize(self.network.pick(audio_frame))
					self.network.send(bytes(dumps({'user' : self.WhoAmI, 'rate' : RATE, 'sampleWidth' : sample_width, 'data' : audio_frame.decode('utf-8')}), 'UTF-8'))
			elif sending:
				if not self.muted:
					audio_frame = self.network.serialize(self.network.pick(audio_frame))
					self.network.send(bytes(dumps({'user' : self.WhoAmI, 'rate' : RATE, 'sampleWidth' : sample_width, 'data' : audio_frame.decode('utf-8')}), 'UTF-8'))
					silence_count += 1
					if silence_count > 10:
						silence_count = 0
						sending = False

		if self.output:
			self.output.stop_stream()
			self.output.close()
		self.stream.stop_stream()
		self.stream.close()
		self.p.terminate()

if __name__ == '__main__':
	c = network()
	c.connect('192.168.227.128')
	m = microphone(c)
	while 1:
		for frame in c.recv():
			frame = loads(decompress(frame).decode('utf-8'))
	c.close()