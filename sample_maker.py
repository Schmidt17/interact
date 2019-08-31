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
        self.row_spacing = 100

        # source buttons
        self.source_button_width = int(0.8 * w / 4.)
        self.source_button_height = 40
        self.source_button_spacing = w // 4
        self.source_button_rects = [pygame.Rect(x + (self.source_button_spacing - self.source_button_width)//2 + i*self.source_button_spacing, y, self.source_button_width, self.source_button_height)
                                for i in range(4)]
        self.source_labels = ["Baum", "Harfe", "Gedengel", "Mic"]

        # sync buttons
        self.sync_button_width = int(0.85 * w / 3.)
        self.sync_button_height = 40
        self.sync_button_spacing = w // 3
        self.sync_button_rects = [pygame.Rect(x + (self.sync_button_spacing - self.sync_button_width)//2 + i*self.sync_button_spacing, y + self.row_spacing, self.sync_button_width, self.sync_button_height)
                                for i in range(3)]
        self.sync_labels = ["None", "1 beat", "1 bar"]

        # rec/stop button
        self.button_width = 100
        self.icon_width = int(self.button_width * 0.5)
        self.rec_stop_rect = pygame.Rect(x + w//2 - self.button_width//2, y + 2 * self.row_spacing, self.button_width, self.button_width)
        self.rec_stop_icon_rect = pygame.Rect(x + w//2 - self.icon_width//2, self.rec_stop_rect.centery - self.icon_width//2, self.icon_width, self.icon_width)

        # interaction stuff
        self.rec_state = 'stopped'
        self.sync_state = 2
        self.source_state = 0

    def handle_click(self, mousepos):
        if self.rec_stop_rect.collidepoint(mousepos):
            if self.rec_state == 'stopped':
                self.rec_state = 'recording'
            else:
                self.rec_state = 'stopped'
        for i, button_rect in enumerate(self.sync_button_rects):
            if button_rect.collidepoint(mousepos):
                self.sync_state = i
        for i, button_rect in enumerate(self.source_button_rects):
            if button_rect.collidepoint(mousepos):
                self.source_state = i

    def draw_labels(self, screen):
        """ Draw the labels of the sync switch buttons on the screen """
        font = pygame.font.SysFont('Arial', 20)

        for i, label in enumerate(self.source_labels):
            if self.source_state == i:
                bgcol = (0, 0, 255)
            else:
                bgcol = (0, 0, 0)
            text_surface = font.render(label, True, (255, 255, 255, 255), bgcol)
            textrect = text_surface.get_rect()
            textrect.centerx = self.source_button_rects[i].x + self.source_button_width/2
            textrect.centery = self.source_button_rects[i].y + self.source_button_height/2

            screen.blit(text_surface, textrect)

        for i, label in enumerate(self.sync_labels):
            if self.sync_state == i:
                bgcol = (0, 255, 0)
            else:
                bgcol = (0, 0, 0)
            text_surface = font.render(label, True, (255, 255, 255, 255), bgcol)
            textrect = text_surface.get_rect()
            textrect.centerx = self.sync_button_rects[i].x + self.sync_button_width/2
            textrect.centery = self.sync_button_rects[i].y + self.sync_button_height/2

            screen.blit(text_surface, textrect)

    def draw(self, screen):
        screen.fill((0, 0, 0), self.bounding_rect)

        for i, button_rect in enumerate(self.source_button_rects):
            if self.source_state == i:
                fill_color = (0, 0, 255)
            else:
                fill_color = (0, 0, 0)
            pygame.draw.rect(screen, fill_color, button_rect)
            pygame.draw.rect(screen, (255, 255, 255), button_rect, 2)

        for i, button_rect in enumerate(self.sync_button_rects):
            if self.sync_state == i:
                fill_color = (0, 255, 0)
            else:
                fill_color = (0, 0, 0)
            pygame.draw.rect(screen, fill_color, button_rect)
            pygame.draw.rect(screen, (255, 255, 255), button_rect, 2)

        self.draw_labels(screen)

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
pygame.display.set_caption("The Sample Maker")

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
