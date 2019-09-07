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

# named tuple for midi notes
MidiNote = namedtuple('MidiNote', ['channel', 'note'])

def on_mqtt_message(client, userdata, msg):
	state_dict = json.loads(msg.payload)
	print(state_dict)

class Sequencer:
	def __init__(self, nsteps=8, ntracks=4):
		self.nsteps = nsteps
		self.ntracks = ntracks

		self.step_state = [[0] * self.nsteps] * 4
		self.midi_notes = [MidiNote(channel=10, note=36),  # check, if channel should be 11 due to 1-based count
						   MidiNote(channel=10, note=38), 
						   MidiNote(channel=10, note=42), 
						   MidiNote(channel=10, note=51)]

		# midi stuff
		self.latency_correction = 0  # this should be in ms, not tied to the tempo!
		print(f"Connecting to MIDI out \"{pygame.midi.get_device_info(3)[1].decode()}\"")
		self.midi_output = pygame.midi.Output(3)

	def midi_notes_on(self, notes: list):
		t = pygame.midi.time()
		midi_messages = [[[0x90 + note.channel, note.note, 64], t] for note in notes]
		self.midi_output.write(midi_messages)

pygame.midi.init()

sequencer = Sequencer()

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
		time.sleep(0.1)
except KeyboardInterrupt:
	sequencer.midi_output.close()
	exit()