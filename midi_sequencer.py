"""
Client for running a sequencer on the "sampling computer".

Receives the state from the remote sequencer user interface. 
Syncs with Live via Ableton Link and triggers the MIDI notes.
"""

import paho.mqtt.client as mqcl
import json
import pygame.midi
import time
import numpy as np
from collections import namedtuple
from LinkToPie import LinkInterface
from functools import partial
import threading
from ui_widgets import LatencyNudgeWidget
import multiprocessing
from multiprocessing import Process, Pipe
import sys

# named tuple for midi notes
MidiNote = namedtuple('MidiNote', ['channel', 'note'])

class Sequencer:
    def __init__(self, nsteps=8, ntracks=4):
        self.nsteps = nsteps
        self.ntracks = ntracks
        self.steps_per_beat = 4

        self.step_state = [[0] * self.nsteps] * 4
        self.midi_notes = [MidiNote(channel=10, note=36),
                           MidiNote(channel=10, note=38), 
                           MidiNote(channel=10, note=42), 
                           MidiNote(channel=10, note=51)]

        # midi stuff
        try:
            self.latency_correction = np.loadtxt("latency_config.dat")
        except OSError:  # if load fails
            self.latency_correction = 75e3  # microseconds
        print(f"Connecting to MIDI out \"{pygame.midi.get_device_info(3)[1].decode()}\"")
        self.midi_output = pygame.midi.Output(3)

        

        # link stuff
        self.beat = -1
        self.step = -1
        self.last_state = {'beat': 0., 'time': int(time.time() * 1e6), 'bpm': 120.}
        self.last_when = 0.

        self.link = LinkInterface()  # make sure that carabiner is running before calling this
        self.link.callbacks['status'] = self.update_link_state_callback
        self.link.callbacks['phase-at-time'] = self.phase_at_time_callback
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

        self.step_thread = threading.Thread(target=self.step_if_its_time, daemon=True)
        self.step_thread.start()

    def midi_notes_on(self, notes: list):
        t = pygame.midi.time()
        midi_messages = [[[0x90 + note.channel, note.note, 64], t] for note in notes]
        self.midi_output.write(midi_messages)

    def step_if_its_time(self):
        while True:
            t_live = int(time.time() * 1e6) + self.latency_correction
            # if t_live > self.last_state['time']:
            current_beat = self.last_state['beat'] + (t_live - self.last_state['time']) * self.last_state['bpm'] / 60e6
            current_step = int(self.steps_per_beat * current_beat)

            if current_step > self.beat:
                red_step = current_step % len(self.step_state[0])
                self.beat = current_step
                self.step = red_step
                notes_on_list = []
                for track_id in range(self.ntracks):
                    if self.step_state[track_id][self.step]:
                        notes_on_list.append(self.midi_notes[track_id])
                self.midi_notes_on(notes_on_list)

                self.mqtt_client.publish("sequencer/step", json.dumps({'sender_id': self.name, 'step': self.step}), qos=0, retain=False)
            time.sleep(0.01)

    def step(self, new_beat):
        print(new_beat)
        self.beat = new_beat
        notes_on_list = []
        for track_id in range(self.ntracks):
            if self.step_state[track_id][self.beat]:
                notes_on_list.append(self.midi_notes[track_id])
        self.midi_notes_on(notes_on_list)

        self.mqtt_client.publish("sequencer/step", json.dumps({'sender_id': self.name, 'step': self.beat}), qos=0, retain=False)

    def update_link_state(self):
        while True:
            self.link.status()
            # self.link.phase_at_time(int(time.time() * 1e6 + self.latency_correction), quantum=8.)
            time.sleep(0.1)

    def update_link_state_callback(self, msg):
        self.last_state['bpm'] = msg['bpm']
        self.last_state['beat'] = msg['beat']
        self.last_state['time'] = int(time.time() * 1e6)

    def phase_at_time_callback(self, msg):
        int_beat = int(msg['phase'])
        if int_beat != self.beat and msg['when'] > self.last_when:
            self.step(int_beat)
            self.last_when = msg['when']


    def on_mqtt_message(self, client, userdata, msg):
        msg_dict = json.loads(msg.payload)
        self.step_state = msg_dict['state']

def pygame_function(pipe):
    import pygame

    pygame.init()
    
    screen = pygame.display.set_mode((400, 400))

    latency_widget = LatencyNudgeWidget(50, 100, 300, 200)

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.MOUSEBUTTONDOWN:
                clicked_button = latency_widget.button_clicked(pygame.mouse.get_pos())
                if clicked_button == 'left':
                    pipe.send(-5e3)
                elif clicked_button == 'right':
                    pipe.send(5e3)

            if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_q):
                running = False

        latency_widget.draw(screen)
        pygame.display.flip()
    pygame.quit()

if __name__ == "__main__":
    pygame.midi.init()
    sequencer = Sequencer()

    nudge = False
    if len(sys.argv) > 1:
        if sys.argv[1] == "nudge":
            nudge = True

    if nudge:
        multiprocessing.set_start_method('spawn')
        parent_conn, child_conn = Pipe()
        pygame_process = Process(target=pygame_function, args=(child_conn,))
        pygame_process.start()

    try:
        while True:
            if nudge:
                if parent_conn.poll():
                    nudge_value = parent_conn.recv()
                    sequencer.latency_correction += nudge_value
                    print(f"Latency correction: {sequencer.latency_correction} µs")

            time.sleep(1000)
    except KeyboardInterrupt:
        pass

    # sequencer.midi_output.close()
    # np.savetxt("latency_config.dat", np.array([sequencer.latency_correction]))