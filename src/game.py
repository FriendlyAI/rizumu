from struct import unpack
from sys import exit, stdout
from time import time

import pygame
from pygame.font import Font
from pygame.time import Clock

from layer import Layer


class Game:
    def __init__(self, audio_player, track, enabled_layers_keys):
        pygame.init()

        self.audio_player = audio_player
        self.track = track
        self.layers = {}
        for i, layer in enumerate(enabled_layers_keys.keys()):
            self.layers[layer] = Layer(layer, enabled_layers_keys[layer])

        self.total_num_beats = 0
        self.read_in_beats(self.track.track_filepath)

        self.num_layers = max(len(self.layers.keys()), 1)

        self.track_height = 650
        self.bottom_offset = 150
        self.preview_length = 1.5  # seconds

        size = self.width, self.height = 500, self.track_height + self.bottom_offset

        self.pixels_per_second = self.track_height / self.preview_length  # 400 pixels = 1 sec
        self.lenience = 0.05 + .005 * self.num_layers  # seconds +/- per beat

        # pygame.display.set_icon(pygame.image.load('img/icon.png'))
        self.screen = pygame.display.set_mode(size)
        self.generic_font = Font('font/good times.ttf', 24)
        self.large_font = Font('font/good times.ttf', 36)

        self.beat_width = self.track_height / 4 / self.num_layers
        self.beat_height = self.pixels_per_second / 25

        self.layer_separation = (self.width - self.num_layers * self.beat_width) / (self.num_layers + 1)
        self.layer_centers = [self.layer_separation * (i + 1) + (self.beat_width * (2 * i + 1) / 2)
                              for i in range(0, self.num_layers)]

        for layer, center in zip(sorted(self.layers.keys()), self.layer_centers):
            self.layers[layer].generate_layer_label(self.generic_font, center, self.track_height)

        self.clock = Clock()

        self.latency = audio_player.device.get_output_latency() * .75
        self.average_time_difference = 0

        self.score = 0
        self.num_perfect = self.num_great = self.num_ok = 0
        self.perfect_color = (70, 175, 255)
        self.great_color = (40, 255, 115)
        self.ok_color = (255, 200, 40)
        self.missed_color = (255, 75, 75)

        self.score_label_frames = 0
        self.score_label_max_frames = 30

        self.score_text = None
        self.score_text_box = None

        self.paused = False
        self.pause_time = 0

        self.start_time = 0
        self.playing_screen = True
        self.score_screen = False

        # Final score screen

        self.final_score_text = None
        self.final_score_text_box = None

        self.final_score_perfect_text = None
        self.final_score_perfect_text_box = None

        self.final_score_great_text = None
        self.final_score_great_text_box = None

        self.final_score_ok_text = None
        self.final_score_ok_text_box = None

        self.final_score_missed_text = None
        self.final_score_missed_text_box = None

        self.final_score_accuracy_text = None
        self.final_score_accuracy_text_box = None

    def read_in_beats(self, track_filepath):
        with open(track_filepath, 'rb') as f:
            while 1:
                beat_layer = f.read(1).decode('ascii')
                if not beat_layer:
                    break
                beat_time = unpack('f', f.read(4))[0]

                if beat_layer in self.layers.keys():
                    self.layers[beat_layer].insert_beat(beat_time)

        for layer in sorted(self.layers.keys()):
            layer_object = self.layers[layer]
            layer_object.count_beats()
            if layer_object.num_beats == 0:
                del self.layers[layer]
            else:
                print(f'{layer}: {layer_object.num_beats} beats')

        self.total_num_beats = sum([layer.num_beats for layer in self.layers.values()])
        print(f'Total: {self.total_num_beats}')

    def score_beat(self, time_difference):
        if time_difference < self.lenience * .5:
            self.score += 3
            self.num_perfect += 1
            return 'perfect!', self.perfect_color
        elif time_difference <= self.lenience * .8:
            self.score += 2
            self.num_great += 1
            return 'great!', self.great_color
        else:
            self.score += 1
            self.num_ok += 1
            return 'ok!', self.ok_color

    def draw_playing_screen(self):
        if not self.audio_player.stream_open.is_set():
            self.playing_screen = False
            self.score_screen = True
            return

        if not self.paused:
            audio_player_time = self.audio_player.get_time()
            current_song_time = time() - self.start_time

            if audio_player_time != 0:
                self.average_time_difference += (current_song_time - audio_player_time - self.average_time_difference) / 30
                self.start_time += self.average_time_difference * .05
                stdout.write(f'\r{self.average_time_difference}')
                stdout.flush()

            current_song_time -= self.latency

            self.screen.fill((0, 0, 0))

            # .5, 1 second lines
            pygame.draw.line(self.screen, (128, 128, 128), (0, self.track_height / 3),
                             (self.width, self.track_height / 3), 1)
            pygame.draw.line(self.screen, (128, 128, 128), (0, 2 * self.track_height / 3),
                             (self.width, 2 * self.track_height / 3), 1)

            # Baseline
            pygame.draw.line(self.screen, (224, 224, 224), (0, self.track_height), (self.width, self.track_height), 9)

            missed = False
            for layer, center in zip(sorted(self.layers.keys()), self.layer_centers):
                layer_object = self.layers[layer]

                # Draw layer track
                pygame.draw.line(self.screen, layer_object.color, (center, 0), (center, self.track_height), 5)

                # Draw beats
                for i in range(layer_object.count_remaining_beats() - 1, -1, -1):
                    beat = layer_object.get_beat(i)
                    if current_song_time - .1 - self.latency <= beat.time <= current_song_time + self.preview_length:
                        y = (self.preview_length - beat.time + current_song_time) * self.pixels_per_second - self.beat_height / 2

                        if abs(y - self.track_height) / self.pixels_per_second <= self.lenience:
                            beat.set_color((50, 200, 50))
                        elif (y - self.track_height) / self.pixels_per_second > self.lenience:  # missed, convert to shadow
                            beat.set_color((255, 150, 150))
                            layer_object.insert_shadow(beat)
                            layer_object.remove_last_beat()
                            missed = True

                        pygame.draw.rect(self.screen, beat.color,
                                         (center - self.beat_width / 2,
                                          self.pixels_per_second * (self.preview_length - beat.time + current_song_time) - self.beat_height / 2,
                                          self.beat_width,
                                          self.beat_height))

                # Draw shadows
                for i in range(layer_object.count_shadows() - 1, -1, -1):
                    shadow = layer_object.get_shadow(i)
                    pygame.draw.rect(self.screen, shadow.color,
                                     (center - self.beat_width / 2,
                                      self.pixels_per_second * (self.preview_length - shadow.time + current_song_time) - self.beat_height / 2,
                                      self.beat_width,
                                      self.beat_height))

                if layer_object.count_shadows() > 0 and current_song_time - self.bottom_offset / self.pixels_per_second - self.latency > layer_object.get_shadow(-1).time:
                    layer_object.remove_last_shadow()

            for layer in self.layers.keys():
                layer_object = self.layers[layer]
                self.screen.blit(layer_object.key_label_text, layer_object.key_label_text_box)

            if missed:
                self.score_text = self.generic_font.render('miss!', True, self.missed_color)
                self.score_text_box = self.score_text.get_rect()
                self.score_label_frames = 0

            for event in pygame.event.get():
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self.audio_player.pause()
                        self.paused = True
                        self.pause_time = time()
                    else:
                        for layer in self.layers.keys():
                            layer_object = self.layers[layer]
                            if event.key == ord(layer_object.key) and layer_object.count_remaining_beats() > 0:
                                time_difference = abs(layer_object.get_beat(-1).time - current_song_time)
                                if time_difference <= self.lenience:
                                    beat_accuracy, color = self.score_beat(time_difference)
                                    layer_object.remove_last_beat()

                                    self.score_text = self.generic_font.render(beat_accuracy, True, color)
                                    self.score_text_box = self.score_text.get_rect()
                                    self.score_label_frames = 0

                elif event.type == pygame.QUIT:
                    self.audio_player.stream_open.clear()
                    self.playing_screen = False
                    self.score_screen = True
                    return

            if self.score_text:
                self.score_text_box.center = self.width / 2, self.height - 40 - self.score_label_frames / 2
                self.screen.blit(self.score_text, self.score_text_box)
                self.score_label_frames += 1
                if self.score_label_frames > self.score_label_max_frames:
                    self.score_label_frames = 0
                    self.score_text = None

            pygame.display.flip()

            display_time = current_song_time if current_song_time > 0 else 0
            pygame.display.set_caption(f'{self.clock.get_fps():.1f} | '
                                       f'{int(display_time // 60)}:{display_time % 60:04.1f} | '
                                       f'{self.score}')

        else:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.audio_player.unpaused.set()
                    self.audio_player.stream_open.clear()
                    self.playing_screen = False
                    self.score_screen = True
                    return

                elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    self.audio_player.unpause()
                    self.paused = False
                    self.start_time += time() - self.pause_time

        self.clock.tick(60)

    def draw_score_screen(self):
        if self.final_score_text is None:
            self.screen.fill((0, 0, 0))

            self.final_score_text = self.large_font.render(f'final score: {self.score}', True, (255, 255, 255))
            self.final_score_text_box = self.final_score_text.get_rect()
            self.final_score_text_box.center = self.width / 2, self.height / 2 + 140
            self.screen.blit(self.final_score_text, self.final_score_text_box)

            self.final_score_perfect_text = self.large_font.render(f'perfect: {self.num_perfect}', True, self.perfect_color)
            self.final_score_perfect_text_box = self.final_score_perfect_text.get_rect()
            self.final_score_perfect_text_box.center = self.width / 2, self.height / 2 - 250
            self.screen.blit(self.final_score_perfect_text, self.final_score_perfect_text_box)

            self.final_score_great_text = self.large_font.render(f'great: {self.num_great}', True, self.great_color)
            self.final_score_great_text_box = self.final_score_great_text.get_rect()
            self.final_score_great_text_box.center = self.width / 2, self.height / 2 - 200
            self.screen.blit(self.final_score_great_text, self.final_score_great_text_box)

            self.final_score_ok_text = self.large_font.render(f'ok: {self.num_ok}', True, self.ok_color)
            self.final_score_ok_text_box = self.final_score_ok_text.get_rect()
            self.final_score_ok_text_box.center = self.width / 2, self.height / 2 - 150
            self.screen.blit(self.final_score_ok_text, self.final_score_ok_text_box)

            num_hit = self.num_perfect + self.num_great + self.num_ok

            self.final_score_missed_text = self.large_font.render(f'missed: {self.total_num_beats - num_hit}', True, self.missed_color)
            self.final_score_missed_text_box = self.final_score_missed_text.get_rect()
            self.final_score_missed_text_box.center = self.width / 2, self.height / 2 - 100
            self.screen.blit(self.final_score_missed_text, self.final_score_missed_text_box)

            self.final_score_accuracy_text = self.large_font.render(f'Accuracy: {(num_hit / max(1, self.total_num_beats) * 100):.1f}%', True, (255, 255, 255))
            self.final_score_accuracy_text_box = self.final_score_accuracy_text.get_rect()
            self.final_score_accuracy_text_box.center = self.width / 2, self.height / 2 + 20
            self.screen.blit(self.final_score_accuracy_text, self.final_score_accuracy_text_box)

            pygame.display.flip()

            pygame.display.set_caption(f'Final Score: {self.score}')

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.score_screen = False
                return

        self.clock.tick(30)

    def display_loop(self):
        while 1:
            if self.playing_screen:
                self.draw_playing_screen()
            elif self.score_screen:
                self.draw_score_screen()
            else:
                break

        self.close_game()

    def start_game(self):
        self.audio_player.open_audio(self.track.audio_filepath)
        self.start_time = time() + self.audio_player.delay_time - self.audio_player.get_fast_forward_time()  # 3 second pre-delay
        self.audio_player.start()
        self.display_loop()

    def close_game(self):
        print(f'\nPerfect: {self.num_perfect}\nGreat: {self.num_great}\nOK: {self.num_ok}')
        print(f'Accuracy: {((self.num_perfect + self.num_great + self.num_ok) / max(1, self.total_num_beats) * 100):.1f}%')
        print(f'Final score: {self.score}')
        pygame.quit()
        exit()
