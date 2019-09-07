import winsound
import multiprocessing

def beep(fname, queue):
    while True:
        start = queue.get()
        winsound.PlaySound(fname, winsound.SND_FILENAME)

if __name__ == "__main__":
    import pygame
    import pygame.midi
    from functools import partial
    class SequencerTrack:
        def __init__(self, x, y, w, h, sample_filename="", midi_note=12, nsteps=4, margin=30, shrink_pad=0.9):
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
            self.sample_filename = sample_filename
            self.midi_note = midi_note
            self.running = True
            self.start_time = 0.
            self.tempo = 240.   # BPM of steps
            self.step_duration_ms = 1000. * 60./self.tempo  # ms; duration of an individual step
            self.step = -1

            # signaling stuff
            self.events = [[[], []] for i in range(self.nsteps)]
            self.beep_queue = multiprocessing.Queue()
            self.beep_process = multiprocessing.Process(target=beep, args=(self.sample_filename, self.beep_queue), daemon=True)
            self.beep_process.start()
            
        def draw(self, screen):
            """ Draw the step pads in their current state on the screen """
            screen.fill((0, 0, 0), self.bounding_rect)
            for i in range(self.nsteps):
                if self.is_active_step(i):
                    pygame.draw.rect(screen, (0, 255, 0), self.step_rects[i])
                if i == self.step:
                    pygame.draw.rect(screen, (0, 0, 255), self.step_rects[i])
                    
                pygame.draw.rect(screen, (255, 255, 255), self.step_rects[i], 1)

        def step_if_its_time(self, t):
            """ Determine if at time t it is time to advance to the next step. If yes, advance the step. """
            if self.running:
                # Determine which step we should be in at time t
                new_step = int((t - self.start_time) / self.step_duration_ms) % self.nsteps
                if new_step != self.step:  # if this is not where we actually are:
                    # execute step-off events of old step
                    for event in self.events[self.step][1]:
                        event()
                    self.step = new_step    # update step
                    # execute step-on events of new step
                    for event in self.events[self.step][0]:
                        event()

        def check_step_click(self, click_pos):
            """ Based on the click_pos coordinates, return which step button was clicked. If none was clicked, return -1. """
            clicked_step = -1   # return -1 if no step was clicked
            for i, step_rect in enumerate(self.step_rects):  # self.step_rects holds the rects of the individual step buttons
                if step_rect.collidepoint(click_pos):
                    clicked_step = i
            return clicked_step

        def attach_event(self, step, step_on_or_off, event_func):
            """ Attach event_func either to on or off event of step 'step' """
            if step_on_or_off == 'on':
                self.events[step][0].append(event_func)
            elif step_on_or_off == 'off':
                self.events[step][1].append(event_func)

        def clear_step_events(self, step):
            self.events[step] = [[], []]

        def is_active_step(self, step):
            return (len(self.events[step][0]) > 0) or (len(self.events[step][1]) > 0)

        def queue_beep(self):
            self.beep_queue.put(True)



    pygame.init()
    pygame.midi.init()

    screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
    width = screen.get_width()
    height = screen.get_height()

    screen.fill((0, 0, 0))

    sample_fnames = ["kick.wav", "snare.wav", "snare.wav", "snare.wav"]
    seq_tracks = [SequencerTrack(0, i*height//4, width, height//4, nsteps=8, sample_filename=sample_fnames[i])
                  for i in range(4)]
    for track in seq_tracks:
        track.draw(screen)

    def say_hi():
        print("Hi.")

    ### The main loop
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_q:
                    running = False
            if event.type == pygame.MOUSEBUTTONDOWN:
                mousepos = pygame.mouse.get_pos()
                for track in seq_tracks:
                    clicked_step = track.check_step_click(mousepos)
                    if clicked_step > -1:
                        if track.is_active_step(clicked_step):
                            track.clear_step_events(clicked_step)
                        else:
                            track.attach_event(step=clicked_step, step_on_or_off='on', event_func=track.queue_beep)
            if event.type == pygame.QUIT:
                running = False

        for track in seq_tracks:
            track.step_if_its_time(pygame.time.get_ticks())
            track.draw(screen)
                
        pygame.display.flip()

    pygame.quit()
