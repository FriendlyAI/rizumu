from struct import unpack
from time import time

import pygame
from pygame.font import Font
from pygame.time import Clock

from layer import Layer


class Game:
    def __init__(self, audio_player, track, enabled_layers_keys, preview_length, prune_unused_layers):
        pygame.init()

        self.audio_player = audio_player
        self.track = track
        self.layers = {}
        self.enabled_layers = enabled_layers_keys.keys()
        self.prune_unused_layers = prune_unused_layers
        for layer in ('A', 'B', 'C', 'D', 'E', 'F'):
            self.layers[layer] = Layer(layer, enabled_layers_keys.get(layer, None))

        self.total_num_beats = 0
        self.read_in_beats(self.track.track_filepath)

        self.num_layers = max(len(self.layers.keys()), 1)

        self.track_height = 600
        self.bottom_offset = 200
        self.preview_length = preview_length  # seconds

        size = self.width, self.height = 500, self.track_height + self.bottom_offset

        self.pixels_per_second = self.track_height / self.preview_length  # 400 pixels = 1 sec
        self.lenience = 0.07  # seconds +/- per beat

        # pygame.display.set_icon(pygame.image.load('img/icon.png'))
        self.screen = pygame.display.set_mode(size)
        self.generic_font = Font('font/good times.ttf', 24)
        self.large_font = Font('font/good times.ttf', 36)
        self.small_font = Font('font/good times.ttf', 18)

        self.beat_width = self.track_height / 3 / self.num_layers
        self.beat_height = self.pixels_per_second / 25

        self.layer_separation = (self.width - self.num_layers * self.beat_width) / (self.num_layers + 1)
        self.layer_centers = [self.layer_separation * (i + 1) + (self.beat_width * (2 * i + 1) / 2)
                              for i in range(0, self.num_layers)]

        for layer, center in zip(sorted(self.layers.keys()), self.layer_centers):
            self.layers[layer].generate_layer_label(self.generic_font, center, self.track_height)

        self.clock = Clock()

        self.latency = audio_player.device.get_output_latency() * 0
        self.average_time_difference = 0

        self.score = 0
        self.num_perfect = self.num_great = self.num_ok = self.num_missed = 0
        self.perfect_color = (128, 255, 255)
        self.great_color = (128, 255, 128)
        self.ok_color = (255, 255, 128)
        self.missed_color = (255, 128, 128)

        self.num_perfect_text = self.small_font.render(f'{self.num_perfect}', True, self.perfect_color)
        self.num_great_text = self.small_font.render(f'{self.num_great}', True, self.great_color)
        self.num_ok_text = self.small_font.render(f'{self.num_ok}', True, self.ok_color)
        self.num_missed_text = self.small_font.render(f'{self.num_missed}', True, self.missed_color)
        self.score_text = self.small_font.render(f'{self.score}', True, (255, 255, 255))
        self.accuracy_text = self.small_font.render(f'{0:.1f}%', True, (255, 255, 255))

        self.combo = 0
        self.combo_multiplier = 1 + 0.2 * (min(30, self.combo) // 10)

        self.hit_text_frames = 0
        self.hit_text_max_frames = 30

        self.hit_text = None
        self.hit_text_box = None

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

                if beat_layer in self.enabled_layers:
                    self.layers[beat_layer].insert_beat(beat_time)

        for layer in ('A', 'B', 'C', 'D', 'E', 'F'):
            layer_object = self.layers[layer]
            layer_object.count_beats()
            if self.prune_unused_layers and (layer_object.num_beats == 0 or layer not in self.enabled_layers):
                del self.layers[layer]
            else:
                print(f'{layer}: {layer_object.num_beats} beats')

        self.total_num_beats = sum([self.layers[layer].num_beats for layer in self.enabled_layers])
        print(f'Total: {self.total_num_beats}')

    def score_beat(self, time_difference):
        if time_difference < self.lenience * .5:
            self.score += int(30 * self.combo_multiplier)
            self.num_perfect += 1
            self.combo += 3
            return 'perfect!', self.perfect_color
        elif time_difference <= self.lenience * .8:
            self.score += int(20 * self.combo_multiplier)
            self.num_great += 1
            self.combo += 2
            return 'great!', self.great_color
        else:
            self.score += int(10 * self.combo_multiplier)
            self.num_ok += 1
            self.combo += 1
            return 'ok!', self.ok_color

    def draw_playing_screen(self):
        if not self.audio_player.stream_open.is_set():
            self.playing_screen = False
            self.score_screen = True
            return

        if not self.paused:
            # Calculate time
            audio_player_time = self.audio_player.get_time()
            current_song_time = time() - self.start_time

            if audio_player_time != 0:
                self.average_time_difference += (current_song_time - audio_player_time - self.average_time_difference) / 60
                self.start_time += self.average_time_difference * .05

            current_song_time -= self.latency

            # Reset screen
            self.screen.fill((0, 0, 0))

            # Draw 1/3 and 2/3 reference lines
            pygame.draw.line(self.screen, (128, 128, 128), (0, self.track_height / 3),
                             (self.width, self.track_height / 3), 1)
            pygame.draw.line(self.screen, (128, 128, 128), (0, 2 * self.track_height / 3),
                             (self.width, 2 * self.track_height / 3), 1)

            # Draw baseline
            pygame.draw.line(self.screen, (255, 255, 255), (0, self.track_height), (self.width, self.track_height), 9)

            # Draw combo progress bar
            if self.combo >= 75:
                combo_color = self.perfect_color
                self.combo_multiplier = 2.0
            elif self.combo >= 50:
                combo_color = self.great_color
                self.combo_multiplier = 1.5
            elif self.combo >= 25:
                combo_color = self.ok_color
                self.combo_multiplier = 1.2
            else:
                combo_color = (255, 255, 255)
                self.combo_multiplier = 1.0

            pygame.draw.line(self.screen, combo_color, (0, self.track_height + 7), (self.width * min(75, self.combo) / 75, self.track_height + 7), 5)

            # Draw layer key labels
            for layer in self.enabled_layers:
                layer_object = self.layers.get(layer, None)
                if layer_object:
                    self.screen.blit(layer_object.key_label_text, layer_object.key_label_text_box)

            # Draw progress bar
            pygame.draw.line(self.screen, (255, 255, 255), (0, self.height - 3), (self.width * max(0, int(current_song_time)) / self.track.duration, self.height - 3), 5)

            # Draw realtime score labels
            self.num_perfect_text = self.small_font.render(f'{self.num_perfect}', True, self.perfect_color)
            self.screen.blit(self.num_perfect_text, (20, self.height - 40))

            self.num_great_text = self.small_font.render(f'{self.num_great}', True, self.great_color)
            self.screen.blit(self.num_great_text, (100, self.height - 40))

            self.num_ok_text = self.small_font.render(f'{self.num_ok}', True, self.ok_color)
            self.screen.blit(self.num_ok_text, (180, self.height - 40))

            self.num_missed_text = self.small_font.render(f'{self.num_missed}', True, self.missed_color)
            self.screen.blit(self.num_missed_text, (260, self.height - 40))

            self.score_text = self.small_font.render(f'{self.score} x {self.combo_multiplier:.1f}', True, (255, 255, 255))
            self.screen.blit(self.score_text, (20, self.height - 70))

            num_hit = self.num_perfect + self.num_great + self.num_ok
            self.accuracy_text = self.small_font.render(f'{(num_hit / max(1, self.num_missed + num_hit) * 100):.2f}%', True, (255, 255, 255))
            self.screen.blit(self.accuracy_text, (200, self.height - 70))

            # Draw track and beats
            missed = False
            for layer, center in zip(sorted(self.layers.keys()), self.layer_centers):
                layer_object = self.layers[layer]

                # Draw layer track
                pygame.draw.line(self.screen, layer_object.color, (center, 0), (center, self.track_height), layer_object.line_thickness)

                # Draw beats
                for i in range(layer_object.count_remaining_beats() - 1, -1, -1):
                    beat = layer_object.get_beat(i)
                    if current_song_time - self.lenience - .1 <= beat.time:
                        if abs(current_song_time - beat.time) <= self.lenience:
                            beat.set_color(self.great_color)
                        elif current_song_time - beat.time > self.lenience:  # missed, convert to shadow
                            beat.set_color(self.missed_color)
                            layer_object.insert_shadow(beat)
                            layer_object.remove_last_beat()

                            self.num_missed += 1
                            missed = True

                        pygame.draw.rect(self.screen, beat.color,
                                         (center - self.beat_width / 2,
                                          self.pixels_per_second * (self.preview_length - beat.time + current_song_time) - self.beat_height / 2,
                                          self.beat_width,
                                          self.beat_height))

                    elif beat.time > current_song_time + self.preview_length:
                        break

                # Draw shadows
                if layer_object.count_shadows() > 0:
                    for i in range(layer_object.count_shadows() - 1, -1, -1):
                        shadow = layer_object.get_shadow(i)
                        pygame.draw.rect(self.screen, shadow.color,
                                         (center - self.beat_width / 2,
                                          self.pixels_per_second * (self.preview_length - shadow.time + current_song_time) - self.beat_height / 2,
                                          self.beat_width,
                                          self.beat_height))

                    if current_song_time - self.bottom_offset / self.pixels_per_second > layer_object.get_shadow(-1).time:
                        layer_object.remove_last_shadow()

            # Check events
            for event in pygame.event.get():
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE and current_song_time > 0:
                        self.paused = True
                        self.audio_player.pause()
                        self.pause_time = time()
                    else:
                        for layer in self.enabled_layers:
                            layer_object = self.layers[layer]
                            if event.key == ord(layer_object.key):
                                layer_object.set_line_thickness(7)
                                if layer_object.count_remaining_beats() > 0:
                                    time_difference = abs(layer_object.get_beat(-1).time - current_song_time)
                                    if time_difference <= self.lenience:
                                        beat_accuracy, color = self.score_beat(time_difference)
                                        layer_object.remove_last_beat()

                                        self.hit_text = self.small_font.render(beat_accuracy, True, color)
                                        self.hit_text_box = self.hit_text.get_rect()
                                        self.hit_text_frames = 0
                                break

                elif event.type == pygame.KEYUP:
                    for layer in self.enabled_layers:
                        layer_object = self.layers[layer]
                        if event.key == ord(layer_object.key):
                            layer_object.set_line_thickness(5)
                            break

                elif event.type == pygame.QUIT:
                    self.audio_player.stream_open.clear()
                    self.playing_screen = False
                    self.score_screen = True
                    return

            if missed:
                self.hit_text = self.small_font.render('miss!', True, self.missed_color)
                self.hit_text_box = self.hit_text.get_rect()
                self.hit_text_frames = 0

                self.combo = 0

            # Draw hit text
            if self.hit_text:
                self.hit_text_box.center = self.width / 2, self.height - 100 - self.hit_text_frames / 2
                self.screen.blit(self.hit_text, self.hit_text_box)
                self.hit_text_frames += 1
                if self.hit_text_frames > self.hit_text_max_frames:
                    self.hit_text_frames = 0
                    self.hit_text = None

            # Update display
            pygame.display.flip()

            # Update title with FPS and time
            display_time = current_song_time if current_song_time > 0 else 0
            pygame.display.set_caption(f'{self.clock.get_fps():.1f} | {int(display_time // 60)}:{display_time % 60:04.1f}')

        else:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.audio_player.unpaused.set()
                    self.audio_player.stream_open.clear()
                    self.playing_screen = False
                    self.score_screen = True
                    return

                elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    self.paused = False
                    self.audio_player.unpause()
                    self.start_time += time() - self.pause_time

        self.clock.tick(60)

    def draw_score_screen(self):
        if self.final_score_text is None:
            self.screen.fill((0, 0, 0))

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

            self.final_score_missed_text = self.large_font.render(f'missed: {self.num_missed}', True, self.missed_color)
            self.final_score_missed_text_box = self.final_score_missed_text.get_rect()
            self.final_score_missed_text_box.center = self.width / 2, self.height / 2 - 100
            self.screen.blit(self.final_score_missed_text, self.final_score_missed_text_box)

            num_hit = self.num_perfect + self.num_great + self.num_ok
            self.final_score_accuracy_text = self.large_font.render(f'accuracy: {(num_hit / max(1, self.num_missed + num_hit) * 100):.2f}%', True, (255, 255, 255))
            self.final_score_accuracy_text_box = self.final_score_accuracy_text.get_rect()
            self.final_score_accuracy_text_box.center = self.width / 2, self.height / 2 + 20
            self.screen.blit(self.final_score_accuracy_text, self.final_score_accuracy_text_box)

            self.final_score_text = self.large_font.render(f'score: {self.score}', True, (255, 255, 255))
            self.final_score_text_box = self.final_score_text.get_rect()
            self.final_score_text_box.center = self.width / 2, self.height / 2 + 140
            self.screen.blit(self.final_score_text, self.final_score_text_box)

            pygame.display.flip()

            pygame.display.set_caption(f'Score: {self.score}')

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
        pass
