"""
Client for running a sequencer on the "sampling computer".

Receives the state from the remote sequencer user interface. 
Syncs with Live via Ableton Link and triggers the MIDI notes.
"""
import paho.mqtt.client as mqcl
import json
import pygame.midi
import time
from collections import namedtuple
from LinkToPy import LinkToPy
from functools import partial
import threading

# named tuple for midi notes
MidiNote = namedtuple('MidiNote', ['channel', 'note'])


class Sequencer:
	def __init__(self, nsteps=8, ntracks=4, link=None):
		self.nsteps = nsteps
		self.ntracks = ntracks

		self.step_state = [[0] * self.nsteps] * 4
		self.midi_notes = [MidiNote(channel=10, note=36),  # check, if channel should be 11 due to 1-based count
						   MidiNote(channel=10, note=38), 
						   MidiNote(channel=10, note=42), 
						   MidiNote(channel=10, note=51)]

		# midi stuff
		self.latency_correction = 75e3  # this should be in mus, not tied to the tempo!
		print(f"Connecting to MIDI out \"{pygame.midi.get_device_info(3)[1].decode()}\"")
		self.midi_output = pygame.midi.Output(3)

		self.beat = -1

		self.last_state = (0., time.monotonic() * 1e6, 120.)
		self.link = link
		self.update_thread = threading.Thread(target=self.update_link_state, daemon=True)
		self.update_thread.start()

	def midi_notes_on(self, notes: list):
		t = pygame.midi.time()
		midi_messages = [[[0x90 + note.channel, note.note, 64], t] for note in notes]
		self.midi_output.write(midi_messages)

	def step_if_its_time(self):
		t_live = int(time.time() * 1e6) + self.latency_correction
		current_beat = self.last_state[0] + (t_live - self.last_state[1]) * self.last_state[2] / 60e6
		red_beat = (int(current_beat) % 4) + 1
		if red_beat != self.beat:
			self.beat = red_beat
			self.midi_notes_on([self.midi_notes[0], self.midi_notes[1]])

	def update_link_state(self):
		while True:
			self.link.status()
			time.sleep(0.1)

	def on_mqtt_message(self, client, userdata, msg):
		state_dict = json.loads(msg.payload)
		print(state_dict)


pygame.midi.init()

link = LinkToPy.LinkInterface("carabiner\\Carabiner.exe")

def print_phase(msg, seq):
	# print(msg['phase'])
	# print(msg)
	seq.last_state = (msg['beat'], int(time.time() * 1e6), msg['bpm'])

	# phase_beat = (int(msg['beat']) % 4) + 1
	# if phase_beat != seq.beat:
	# 	seq.beat = phase_beat
	# 	seq.midi_notes_on([seq.midi_notes[0], seq.midi_notes[1]])
	# 	print(phase_beat)	

sequencer = Sequencer(link=link)

link.callbacks['status'] = partial(print_phase, seq=sequencer)

# networking stuff
my_name = "live_sequencer"
mqtt_broker_ip = "localhost"
mqtt_client = mqcl.Client(client_id=my_name, clean_session=True)
mqtt_client.on_message = on_mqtt_message

mqtt_client.connect(mqtt_broker_ip, 1883, 60)
mqtt_client.subscribe("sampling", qos=1)
mqtt_client.loop_start()

try:
	
	while True:
		
		sequencer.step_if_its_time()
		time.sleep(0.01)
except KeyboardInterrupt:
	sequencer.midi_output.close()
	del link
	exit()