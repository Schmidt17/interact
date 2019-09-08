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
	def __init__(self, nsteps=8, ntracks=4):
		self.nsteps = nsteps
		self.ntracks = ntracks

		self.step_state = [[0] * self.nsteps] * 4
		self.midi_notes = [MidiNote(channel=10, note=36),
						   MidiNote(channel=10, note=38), 
						   MidiNote(channel=10, note=42), 
						   MidiNote(channel=10, note=51)]

		# midi stuff
		self.latency_correction = 75e3  # this should be in mus, not tied to the tempo!
		print(f"Connecting to MIDI out \"{pygame.midi.get_device_info(3)[1].decode()}\"")
		self.midi_output = pygame.midi.Output(3)

		# link stuff
		self.beat = -1
		self.last_state = (0., int(time.time() * 1e6), 120.)

		self.link = LinkToPy.LinkInterface("carabiner\\Carabiner.exe")
		self.link.callbacks['status'] = self.update_link_state_callback
		self.update_thread = threading.Thread(target=self.update_link_state, daemon=True)
		self.update_thread.start()

		# networking stuff
		self.name = "live_sequencer"
		mqtt_broker_ip = "localhost"
		self.mqtt_client = mqcl.Client(client_id=self.name, clean_session=True)
		self.mqtt_client.on_message = self.on_mqtt_message

		self.mqtt_client.connect(mqtt_broker_ip, 1883, 60)
		self.mqtt_client.subscribe("sequencer/state", qos=1)
		self.mqtt_client.loop_start()

	def midi_notes_on(self, notes: list):
		t = pygame.midi.time()
		midi_messages = [[[0x90 + note.channel, note.note, 64], t] for note in notes]
		self.midi_output.write(midi_messages)

	def step_if_its_time(self):
		t_live = int(time.time() * 1e6) + self.latency_correction
		current_beat = self.last_state[0] + (t_live - self.last_state[1]) * self.last_state[2] / 60e6
		red_beat = int(current_beat) % len(self.step_state[0])
		if red_beat != self.beat:
			self.beat = red_beat
			notes_on_list = []
			for track_id in range(self.ntracks):
				if self.step_state[track_id][self.beat]:
					notes_on_list.append(self.midi_notes[track_id])
			self.midi_notes_on(notes_on_list)

			self.mqtt_client.publish("sequencer/step", json.dumps({'sender_id': self.name, 'step': self.beat}), qos=0, retain=False)

	def update_link_state(self):
		while True:
			self.link.status()
			time.sleep(0.1)

	def update_link_state_callback(self, msg):
		self.last_state = (msg['beat'], int(time.time() * 1e6), msg['bpm'])

	def on_mqtt_message(self, client, userdata, msg):
		msg_dict = json.loads(msg.payload)
		self.step_state = msg_dict['state']


pygame.midi.init()

sequencer = Sequencer()

try:
	while True:		
		sequencer.step_if_its_time()
		time.sleep(0.01)
except KeyboardInterrupt:
	sequencer.midi_output.close()
	exit()