"""
Simple interface for editing the step-sequencer state remotely.
Receives the beat info via MQTT from the midi_sequencer on the sampling computer,
sends state updates via MQTT.
"""
import paho.mqtt.client as mqcl
import json

import pygame
import pygame.midi
from functools import partial

class SequencerTrack:
    def __init__(self, x, y, w, h, nsteps=8, margin=30, shrink_pad=0.9):
        self.nsteps = nsteps
        
        # graphics stuff
        self.bounding_rect = pygame.Rect(int(x), int(y), int(w), int(h))
        self.step_width = min(h, int((w - 2*margin)/self.nsteps))
        effective_step_width = int((w - 2*margin - self.step_width)/(self.nsteps-1))
        self.step_rects = [pygame.Rect(x + margin + i*effective_step_width,
                                       y + (h - self.step_width)//2,
                                       shrink_pad * self.step_width,
                                       shrink_pad * self.step_width) for i in range(nsteps)]

        # music stuff
        self.step = -1
        self.state = [0] * self.nsteps
        
    def draw(self, screen):
        """ Draw the step pads in their current state on the screen """
        screen.fill((0, 0, 0), self.bounding_rect)
        for i in range(self.nsteps):
            if self.state[i]:
                pygame.draw.rect(screen, (0, 255, 0), self.step_rects[i])
            if i == self.step:
                pygame.draw.rect(screen, (0, 0, 255), self.step_rects[i])
                
            pygame.draw.rect(screen, (255, 255, 255), self.step_rects[i], 1)

    def check_step_click(self, click_pos):
        """ Based on the click_pos coordinates, return which step button was clicked. If none was clicked, return -1. """
        clicked_step = None   # return -1 if no step was clicked
        for i, step_rect in enumerate(self.step_rects):  # self.step_rects holds the rects of the individual step buttons
            if step_rect.collidepoint(click_pos):
                clicked_step = i
        return clicked_step

class Sequencer:
    def __init__(self, x, y, w, h, ntracks=4, nsteps=8, mqtt_broker_ip="192.168.2.107"):
        self.ntracks = ntracks
        self.nsteps = nsteps
        self.state = [[0] * self.nsteps] * self.ntracks

        # networking stuff
        self.name = "sequencer_ui"
        self.discard_own_messages = True
        self.mqtt_client = mqcl.Client(client_id=self.name, clean_session=True)
        self.mqtt_client.on_message = self.on_mqtt_message
        self.mqtt_client.on_connect = self.on_mqtt_connect

        self.mqtt_client.connect(mqtt_broker_ip, 1883, 60)
        self.mqtt_client.subscribe("sequencer/step", qos=1)
        self.mqtt_client.subscribe("sequencer/state", qos=1)
        self.mqtt_client.loop_start()

        self.tracks = [SequencerTrack(0, i*h//self.ntracks, w, h//self.ntracks, nsteps=self.nsteps) for i in range(self.ntracks)]

    def send_state(self):
        payload = json.dumps({'sender_id': self.name, 
                                'state': self.state})
        self.mqtt_client.publish("sequencer/state", payload, qos=1, retain=True)

    def on_mqtt_connect(self, client, userdata, flags, rc):
        self.discard_own_messages = False

    def on_mqtt_message(self, client, userdata, msg):
        msg_dict = json.loads(msg.payload)
        if 'step' in msg_dict:
            self.update_step(msg_dict['step'])
        elif 'state' in msg_dict:
            if not (self.discard_own_messages and msg_dict['sender_id'] == self.name):
                if msg_dict['sender_id'] == self.name:
                    self.discard_own_messages = True
                self.update_state(msg_dict['state'])

    def update_step(self, new_step):
        self.step = new_step
        for track in self.tracks:
            track.step = new_step

    def update_state(self, new_state):
        self.state = new_state
        for track_id, track in enumerate(self.tracks):
            track.state = new_state[track_id]

    def handle_click(self, click_pos):
        for track_id, track in enumerate(self.tracks):
            clicked_step = track.check_step_click(click_pos)
            if not clicked_step is None:
                if track.state[clicked_step] == 0:
                    track.state[clicked_step] = 1
                else:
                    track.state[clicked_step] = 0
                self.state[track_id] = track.state
                self.send_state()

    def draw(self, screen):
        for track in self.tracks:
            track.draw(screen)


pygame.init()
pygame.midi.init()

screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
width = screen.get_width()
height = screen.get_height()

screen.fill((0, 0, 0))

sequencer = Sequencer(0, 0, width, height)
sequencer.draw(screen)

### The main loop
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_q:
                running = False
        if event.type == pygame.MOUSEBUTTONDOWN:
            mousepos = pygame.mouse.get_pos()
            sequencer.handle_click(mousepos)
        if event.type == pygame.QUIT:
            running = False

    sequencer.draw(screen)
            
    pygame.display.flip()

pygame.quit()
