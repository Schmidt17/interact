"""
Client for launching recording of a sample. This runs on the "performer computer" (tablet or similar).

This sends a command to the "audio computer" to record something on a specified channel
and send it to the "sequencing computer" for playing.
"""

import pygame
import pygame.gfxdraw

class TransportWidget:
	"""
	Widget containing the controls for selecting channels
	and starting/stopping the recording.
	"""
	def __init__(self, x, y, w, h):
		# graphics stuff
		self.bounding_rect = pygame.Rect(x, y, w, h)

		# sync buttons
		self.sync_button_width = int(0.8 * w / 3.)
		self.sync_button_height = 40
		self.sync_button_spacing = w // 3
		self.sync_button_rects = [pygame.Rect(x + (self.sync_button_spacing - self.sync_button_width)//2 + i*self.sync_button_spacing, y + h//3, self.sync_button_width, self.sync_button_height)
								for i in range(3)]

		# rec/stop button
		self.button_width = 100
		self.icon_width = int(self.button_width * 0.5)
		self.rec_stop_rect = pygame.Rect(x + w//2 - self.button_width//2, y + h*3//4 - self.button_width//2, self.button_width, self.button_width)
		self.rec_stop_icon_rect = pygame.Rect(x + w//2 - self.icon_width//2, y + h*3//4 - self.icon_width//2, self.icon_width, self.icon_width)

		# interaction stuff
		self.rec_state = 'stopped'
		self.sync_state = 0

	def handle_click(self, mousepos):
		if self.rec_stop_rect.collidepoint(mousepos):
			if self.rec_state == 'stopped':
				self.rec_state = 'recording'
			else:
				self.rec_state = 'stopped'
		for i, button_rect in enumerate(self.sync_button_rects):
			if button_rect.collidepoint(mousepos):
				self.sync_state = i

	def draw(self, screen):
		screen.fill((0, 0, 0), self.bounding_rect)

		for i, button_rect in enumerate(self.sync_button_rects):
			if self.sync_state == i:
				fill_color = (0, 255, 0)
			else:
				fill_color = (0, 0, 0)
			pygame.draw.rect(screen, fill_color, button_rect)
			pygame.draw.rect(screen, (255, 255, 255), button_rect, 2)

		if self.rec_state == 'stopped':
			pygame.draw.rect(screen, (255, 255, 255), self.rec_stop_rect, 2)
			pygame.gfxdraw.filled_circle(screen, self.rec_stop_icon_rect.centerx, self.rec_stop_icon_rect.centery, self.icon_width//2, (255, 0, 0))
			pygame.gfxdraw.aacircle(screen, self.rec_stop_icon_rect.centerx, self.rec_stop_icon_rect.centery, self.icon_width//2, (255, 0, 0))
		else:
			pygame.draw.rect(screen, (255, 0, 0), self.rec_stop_rect)
			pygame.draw.rect(screen, (255, 255, 255), self.rec_stop_rect, 2)
			pygame.draw.rect(screen, (255, 255, 255), self.rec_stop_icon_rect)

class SyncSwitchWidget:
	def __init__(self, x, y, w, h):
		# graphics stuff
		self.bounding_rect = pygame.Rect(x, y, w, h)

		self.button_width = int(0.8 * w / 3.)
		self.button_height = 40
		self.button_spacing = w // 3
		self.button_rects = [pygame.Rect(x + (self.button_spacing - self.button_width)//2 + i*self.button_spacing, y, self.button_width, self.button_height)
								for i in range(3)]

	def draw(self, screen):
		screen.fill((0, 0, 0), self.bounding_rect)
		
		for button_rect in self.button_rects:
			pygame.draw.rect(screen, (0, 0, 0), button_rect)
			pygame.draw.rect(screen, (255, 255, 255), button_rect, 2)


pygame.init()
screen = pygame.display.set_mode((600, 400))

screen.fill((0, 0, 0))

transport_widget = TransportWidget(50, 50, 500, 300)
transport_widget.draw(screen)

pygame.display.flip()

running = True
while running:
	for event in pygame.event.get():
		if event.type == pygame.MOUSEBUTTONDOWN:
			transport_widget.handle_click(pygame.mouse.get_pos())
		if event.type == pygame.QUIT:
			running = False

	transport_widget.draw(screen)

	pygame.display.flip()

pygame.quit()
