""" Simple mqtt client """

import paho.mqtt.client as mqcl
import sys
import time
import json

def on_message(client, userdata, msg):
	print(msg.payload)

class FaderWidget:
	def __init__(self, x, y, w, h, mqtt_client=None):
		self.value = 100  # between 0 and 127

		# graphics stuff
		self.bounding_rect = pygame.Rect(x, y, w, h)
		self.knob_rect = pygame.Rect(x, y, w, 20)
		self.knob_rect.y = self.val_to_y(self.value)

		# interaction stuff
		self.dragging = False
		self.drag_start_mouse_y = 0
		self.drag_start_knob_y = 0

		# networking stuff
		self.mqtt_client = mqtt_client
		self.discard_own_messages = True

	def start_drag_if_clicked(self, mousepos):
		if self.knob_rect.collidepoint(mousepos):
			self.dragging = True
			self.drag_start_mouse_y = mousepos[1]
			self.drag_start_knob_y = self.knob_rect.y

	def stop_dragging(self):
		self.dragging = False

	def drag_update_value(self, mousepos):
		new_y = self.drag_start_knob_y + mousepos[1] - self.drag_start_mouse_y
		if new_y < self.bounding_rect.y:
			new_y = self.bounding_rect.y
		elif new_y > self.bounding_rect.y + self.bounding_rect.h - self.knob_rect.h:
			new_y = self.bounding_rect.y + self.bounding_rect.h - self.knob_rect.h
		self.knob_rect.y = new_y
		self.value = self.y_to_val(new_y)

		if not self.mqtt_client is None:
			self.mqtt_client.publish("myChannel", json.dumps({'sender_id': my_name, 'val': self.value}), qos=0, retain=True)

	def on_connect(self,client, userdata, flags, rc):
		self.discard_own_messages = False  # allow to accept one message from myself for getting the retained value

	def update_value_mqtt(self, client, userdata, msg):
		msg_dict = json.loads(msg.payload)
		if not ((msg_dict['sender_id'] == my_name) and self.discard_own_messages):
			if self.discard_own_messages == False:
				self.discard_own_messages = True
			new_value = int(msg_dict['val'])
			if new_value < 0:
				new_value = 0
			elif new_value > 127:
				new_value = 127

			self.value = new_value
			self.knob_rect.y = self.val_to_y(new_value)

	def val_to_y(self, val):
		return int(self.bounding_rect.y + self.bounding_rect.h - self.knob_rect.h - val * (self.bounding_rect.h - self.knob_rect.h) / 127.)

	def y_to_val(self, y):
		val_candidate = - 127./(self.bounding_rect.h-self.knob_rect.h) * (y - self.bounding_rect.y - self.bounding_rect.h + self.knob_rect.h)
		if val_candidate < 0:
			val_candidate = 0
		elif val_candidate > 127:
			val_candidate = 127

		return int(val_candidate)

	def draw(self, screen):
		screen.fill((0, 0, 0), self.bounding_rect)
		pygame.draw.rect(screen, (255, 255, 255), self.bounding_rect, 1)
		pygame.draw.rect(screen, (51, 51, 51), self.knob_rect)

my_name = sys.argv[1]

import pygame
pygame.init()

screen = pygame.display.set_mode((400, 600))
pygame.display.set_caption(my_name)
screen.fill((0, 0, 0))

client = mqcl.Client(client_id=my_name, clean_session=True)

fader = FaderWidget(150, 100, 100, 400, mqtt_client=client)
fader.draw(screen)

client.on_connect = fader.on_connect
client.on_message = fader.update_value_mqtt
client.connect("localhost", 1883, 60)
client.subscribe("myChannel", qos=0)
client.loop_start()

running = True
while running:
	for event in pygame.event.get():
		if event.type == pygame.MOUSEBUTTONDOWN:
			fader.start_drag_if_clicked(pygame.mouse.get_pos())
		if event.type == pygame.MOUSEBUTTONUP:
			fader.stop_dragging()

		if event.type == pygame.QUIT:
			running = False

	if fader.dragging:
		fader.drag_update_value(pygame.mouse.get_pos())
	fader.draw(screen)
	pygame.display.flip()

client.disconnect()
pygame.quit()
