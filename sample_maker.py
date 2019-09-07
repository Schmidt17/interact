"""
Client for launching recording of a sample. This runs on the "performer computer" (tablet or similar).

This sends a command to the "audio computer" to record something on a specified channel
and send it to the "sequencing computer" for playing.
"""

import pygame
from ui_widgets import TransportWidget

# fetch ip of mqtt broker
mqtt_broker_ip = input("Type in IP or hostname of MQTT broker or press Enter to use localhost:")
if mqtt_broker_ip == "":
    mqtt_broker_ip = "localhost"

pygame.init()
screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
pygame.display.set_caption("The Sample Maker")
width, height = screen.get_width(), screen.get_height()

# create the UI widget objects
transport_widget = TransportWidget(100, 100, width-200, height-200, mqtt_broker_ip=mqtt_broker_ip)

# collect the event handlers
# call those on clicking the mouse, passing the mouse coordinates as a tuple
on_mouse_click_functions = [transport_widget.handle_click]

# do initial draw
screen.fill((0, 0, 0))
transport_widget.draw(screen)
pygame.display.flip()  # update screen

running = True
while running:
    # handle events
    for event in pygame.event.get():
        if event.type == pygame.MOUSEBUTTONDOWN:
            for click_handler in on_mouse_click_functions:
                click_handler(pygame.mouse.get_pos())
        if (event.type == pygame.QUIT 
            or (event.type == pygame.KEYDOWN and event.key == pygame.K_q)):
            running = False

    # draw stuff
    transport_widget.draw(screen)

    # update screen
    pygame.display.flip()

pygame.quit()
