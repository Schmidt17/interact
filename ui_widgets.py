import pygame
import pygame.gfxdraw
import paho.mqtt.client as mqcl
import json

class TransportWidget:
    """
    Widget containing the controls for selecting channels
    and starting/stopping the recording.
    """
    def __init__(self, x, y, w, h, mqtt_broker_ip="192.168.2.107"):
        self.name = "sampling_launcher"

        # graphics stuff
        self.bounding_rect = pygame.Rect(x, y, w, h)
        self.row_spacing = h // 3
        self.font_size = 30

        # source buttons
        self.source_button_width = int(0.8 * w / 4.)
        self.source_button_height = 80
        self.source_button_spacing = w // 4
        self.source_button_rects = [pygame.Rect(x + (self.source_button_spacing - self.source_button_width)//2 + i*self.source_button_spacing, y, self.source_button_width, self.source_button_height)
                                for i in range(4)]
        self.source_labels = ["Baum", "Harfe", "Gedengel", "Mic"]

        # sync buttons
        self.sync_button_width = int(0.85 * w / 3.)
        self.sync_button_height = 80
        self.sync_button_spacing = w // 3
        self.sync_button_rects = [pygame.Rect(x + (self.sync_button_spacing - self.sync_button_width)//2 + i*self.sync_button_spacing, y + self.row_spacing, self.sync_button_width, self.sync_button_height)
                                for i in range(3)]
        self.sync_labels = ["None", "1 beat", "1 bar"]

        # rec/stop button
        self.button_width = 200
        self.icon_width = int(self.button_width * 0.5)
        self.rec_stop_rect = pygame.Rect(x + w//2 - self.button_width//2, y + 2 * self.row_spacing, self.button_width, self.button_width)
        self.rec_stop_icon_rect = pygame.Rect(x + w//2 - self.icon_width//2, self.rec_stop_rect.centery - self.icon_width//2, self.icon_width, self.icon_width)

        # interaction stuff
        self.rec_state = 0  # 0: stopped, 1: record pressed
        self.sync_state = 2
        self.source_state = 0

        # networking stuff
        self.discard_own_messages = True
        self.mqtt_client = mqcl.Client(client_id=self.name, clean_session=True)
        self.mqtt_client.on_message = self.on_mqtt_message
        self.mqtt_client.on_connect = self.on_mqtt_connect

        self.mqtt_client.connect(mqtt_broker_ip, 1883, 60)
        self.mqtt_client.subscribe("timing/beats", qos=0)
        self.mqtt_client.subscribe("sampling", qos=1)
        self.mqtt_client.loop_start()

    def on_mqtt_message(self, client, userdata, msg):
        msg_dict = json.loads(msg.payload)
        if not (self.discard_own_messages and msg_dict['sender_id'] == self.name):
            if msg_dict['sender_id'] == self.name:
                self.discard_own_messages = True
            
            self.source_state = msg_dict['state']['source']
            self.sync_state = msg_dict['state']['sync']
            self.rec_state = msg_dict['state']['record_pressed']

    def on_mqtt_connect(self, client, userdata, flags, rc):
        self.discard_own_messages = False  # enable fetching the last state from the broker
        # will be turned off when the first message is processed

    def send_state(self):
        payload = json.dumps({'sender_id': self.name, 
                            'state': {
                                'source': self.source_state,
                                'sync': self.sync_state,
                                'record_pressed': self.rec_state
                            }})
        self.mqtt_client.publish("sampling", payload, qos=1, retain=True)

    def handle_click(self, mousepos):
        if self.rec_stop_rect.collidepoint(mousepos):
            if self.rec_state == 0:  # if stopped
                self.rec_state = 1  # set record button to pressed
            else:
                self.rec_state = 0
            self.send_state()
        for i, button_rect in enumerate(self.sync_button_rects):
            if button_rect.collidepoint(mousepos):
                self.sync_state = i
                self.send_state()
        for i, button_rect in enumerate(self.source_button_rects):
            if button_rect.collidepoint(mousepos):
                self.source_state = i
                self.send_state()

    def draw_labels(self, screen):
        """ Draw the labels of the sync switch buttons on the screen """
        font = pygame.font.SysFont('Arial', self.font_size)

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

        if self.rec_state == 0:  # "stopped" state
            pygame.draw.rect(screen, (0, 0, 0), self.rec_stop_rect)
            pygame.draw.rect(screen, (255, 255, 255), self.rec_stop_rect, 2)
            pygame.gfxdraw.filled_circle(screen, self.rec_stop_icon_rect.centerx, self.rec_stop_icon_rect.centery, self.icon_width//2, (255, 0, 0))
            pygame.gfxdraw.aacircle(screen, self.rec_stop_icon_rect.centerx, self.rec_stop_icon_rect.centery, self.icon_width//2, (255, 0, 0))
        else:
            pygame.draw.rect(screen, (255, 0, 0), self.rec_stop_rect)
            pygame.draw.rect(screen, (255, 255, 255), self.rec_stop_rect, 2)
            pygame.draw.rect(screen, (255, 255, 255), self.rec_stop_icon_rect)


class LatencyNudgeWidget:
    def __init__(self, x, y, w, h, margin=30):
        # graphics stuff
        self.bounding_rect = pygame.Rect(x, y, w, h)
        self.left_rect = pygame.Rect(x + margin, y + margin, w//2 - 2*margin, h - 2*margin)
        self.right_rect = pygame.Rect(x + w//2 + margin, y + margin, w//2 - 2*margin, h - 2*margin)

    def button_clicked(self, mousepos):
        clicked_button = None
        if self.left_rect.collidepoint(mousepos):
            clicked_button = 'left'
        elif self.right_rect.collidepoint(mousepos):
            clicked_button = 'right'
        return clicked_button

    def draw(self, screen):
        screen.fill((0, 0, 0), self.bounding_rect)

        # blue buttons
        pygame.draw.rect(screen, (0, 0, 255), self.left_rect)
        pygame.draw.rect(screen, (0, 0, 255), self.right_rect)

        # white triangles
        triangle_half_width = 20
        pygame.draw.polygon(screen, (255, 255, 255), [(self.left_rect.centerx - triangle_half_width, self.left_rect.centery),
                                                      (self.left_rect.centerx + triangle_half_width, self.left_rect.centery - triangle_half_width),
                                                      (self.left_rect.centerx + triangle_half_width, self.left_rect.centery + triangle_half_width)])
        pygame.draw.polygon(screen, (255, 255, 255), [(self.right_rect.centerx - triangle_half_width, self.right_rect.centery + triangle_half_width),
                                                      (self.right_rect.centerx - triangle_half_width, self.right_rect.centery - triangle_half_width),
                                                      (self.right_rect.centerx + triangle_half_width, self.right_rect.centery)])