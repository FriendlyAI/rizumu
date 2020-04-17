from struct import unpack
from time import time

import pygame
from pygame.font import Font

from layer import Layer
from util import ALL_LAYERS, seconds_to_readable_time


class Game:
    def __init__(self, screen, width, height, clock, audio_player, track, enabled_layers_keys, preview_length, prune_unused_layers, latency):
        self.audio_player = audio_player
        self.track = track
        self.layers = {}
        self.enabled_layers_keys = enabled_layers_keys
        self.enabled_layers = set(enabled_layers_keys.keys())
        self.prune_unused_layers = prune_unused_layers
        for layer in ALL_LAYERS:
            self.layers[layer] = Layer(layer, enabled_layers_keys.get(layer, None))

        self.total_num_beats = 0
        self.read_in_beats(self.track.map_filepath)

        self.num_layers = max(len(self.layers.keys()), 1)

        self.width = width
        self.track_width = int(self.width * .6)
        self.height = height
        self.track_height = self.height - 150
        self.bottom_offset = self.height - self.track_height
        self.preview_length = preview_length  # seconds

        self.pixels_per_second = self.track_height / self.preview_length
        self.lenience = 0.1  # seconds +/- per beat

        self.screen = screen

        self.huge_font = Font('font/unifont.ttf', 64)
        self.large_font = Font('font/unifont.ttf', 36)
        self.generic_font = Font('font/unifont.ttf', 26)
        self.small_font = Font('font/unifont.ttf', 20)

        self.beat_width = self.track_height / self.num_layers / 3
        self.beat_height = self.pixels_per_second / 30

        self.layer_separation = (self.track_width - self.num_layers * self.beat_width) / (self.num_layers + 1)
        self.layer_centers = [self.layer_separation * (i + 1) + (self.beat_width * (2 * i + 1) / 2)
                              for i in range(0, self.num_layers)]

        self.clock = clock

        self.latency = latency
        self.average_time_difference = 0

        self.score = 0
        self.num_perfect = self.num_great = self.num_ok = self.num_missed = 0
        self.perfect_color = (128, 255, 255)
        self.great_color = (128, 255, 128)
        self.ok_color = (255, 255, 128)
        self.missed_color = (255, 128, 128)

        self.combo = 0
        self.combo_multiplier = 1 + 0.2 * (min(30, self.combo) // 10)

        self.hit_text_frames = 0
        self.hit_text_max_frames = 30

        self.hit_text = None
        self.hit_text_box = None

        self.track_title_text = self.small_font.render(f'{self.track.title}', True, (255, 255, 255))
        self.track_artist_text = self.small_font.render(f'{self.track.artist}', True, (255, 255, 255))
        self.track_album_text = self.small_font.render(f'{self.track.album}', True, (255, 255, 255))

        self.paused = False

        self.time = 0
        self.playing_screen = True
        self.score_screen = False

        self.restart = False

        self.draw_score = True


    def read_in_beats(self, map_filepath):
        with open(map_filepath, 'rb') as f:
            while 1:
                beat_layer = f.read(1).decode('ascii')
                if not beat_layer:
                    break
                beat_time = unpack('f', f.read(4))[0]

                if beat_layer in self.enabled_layers:
                    self.layers[beat_layer].insert_beat(beat_time)

        for layer in ALL_LAYERS:
            layer_object = self.layers[layer]
            layer_object.count_beats()
            if self.prune_unused_layers and (layer_object.num_beats == 0 or layer not in self.enabled_layers):
                del self.layers[layer]
                if layer in self.enabled_layers:
                    self.enabled_layers.remove(layer)

        self.total_num_beats = sum((self.track.num_beats[layer] for layer in self.enabled_layers))

    def score_beat(self, time_difference):
        if time_difference < self.lenience / 4:
            self.score += int(30 * self.combo_multiplier)
            self.num_perfect += 1
            self.combo += 3
            return 'PERFECT!', self.perfect_color
        elif time_difference < self.lenience / 2:
            self.score += int(20 * self.combo_multiplier)
            self.num_great += 1
            self.combo += 2
            return 'GREAT!', self.great_color
        else:
            self.score += int(10 * self.combo_multiplier)
            self.num_ok += 1
            self.combo += 1
            return 'OK!', self.ok_color

    def calculate_accuracy(self):
        num_hit = self.num_perfect + self.num_great + self.num_ok
        return num_hit / max(1, self.num_missed + num_hit) * 100

    def draw_playing_screen(self):
        if not self.audio_player.stream_open.is_set():
            self.playing_screen = False
            self.score_screen = True
            return

        if not self.paused:
            # Calculate time
            audio_player_time = self.audio_player.get_time()

            if audio_player_time != 0:
                self.average_time_difference += (audio_player_time - self.time - self.average_time_difference) * .02
                self.time += self.average_time_difference * .05

            current_song_time = self.time - self.latency

            # Reset screen
            self.screen.fill((0, 0, 0))

            # Draw borders
            pygame.draw.line(self.screen, (128, 128, 128), (0, 0), (0, self.height), 1)
            pygame.draw.line(self.screen, (128, 128, 128), (self.track_width, 0), (self.track_width, self.height), 1)
            pygame.draw.line(self.screen, (128, 128, 128), (self.width - 1, 0), (self.width - 1, self.height), 1)

            # Draw 1/3 and 2/3 reference lines
            pygame.draw.line(self.screen, (128, 128, 128), (0, self.track_height / 3),
                             (self.track_width, self.track_height / 3), 1)
            pygame.draw.line(self.screen, (128, 128, 128), (0, 2 * self.track_height / 3),
                             (self.track_width, 2 * self.track_height / 3), 1)

            # Draw baseline
            pygame.draw.line(self.screen, (192, 192, 192), (0, self.track_height), (self.track_width, self.track_height), 5)

            # Draw combo progress bar
            if self.combo >= 75:
                self.combo_multiplier = 2.0
            elif self.combo >= 50:
                self.combo_multiplier = 1.5
            elif self.combo >= 25:
                self.combo_multiplier = 1.2
            else:
                self.combo_multiplier = 1.0

            pygame.draw.line(self.screen, (255, 255, 255), (0, self.track_height), (self.track_width * min(75, self.combo) / 75, self.track_height), 7)
            if self.combo < 75:
                pygame.draw.line(self.screen, (0, 0, 0), (self.track_width / 3, self.track_height - 3), (self.track_width / 3, self.track_height + 3), 7)
                pygame.draw.line(self.screen, (0, 0, 0), (self.track_width * 2 / 3, self.track_height - 3), (self.track_width * 2 / 3, self.track_height + 3), 7)

            # Draw progress bar
            pygame.draw.line(self.screen, (255, 255, 255), (0, self.height - 3), (self.track_width * (current_song_time if current_song_time > 0 else 0) / self.track.duration, self.height - 3), 5)

            # Draw track info labels
            self.screen.blit(self.track_title_text, (self.track_width + 20, self.height * .05))
            self.screen.blit(self.track_artist_text, (self.track_width + 20, self.height * .1))
            self.screen.blit(self.track_album_text, (self.track_width + 20, self.height * .15))

            # Draw realtime score labels
            score_text = self.large_font.render(f'{self.score} × {self.combo_multiplier:.1f}', True, (255, 255, 255))
            self.screen.blit(score_text, (self.track_width + 20, self.height * .2))

            accuracy_text = self.large_font.render(f'{self.calculate_accuracy():.2f}%', True, (255, 255, 255))
            self.screen.blit(accuracy_text, (self.track_width + 20, self.height * .275))

            num_perfect_text = self.large_font.render(f'{self.num_perfect}', True, self.perfect_color)
            self.screen.blit(num_perfect_text, (self.track_width + 20, self.height * .35))

            num_great_text = self.large_font.render(f'{self.num_great}', True, self.great_color)
            self.screen.blit(num_great_text, (self.track_width + 110, self.height * .35))

            num_ok_text = self.large_font.render(f'{self.num_ok}', True, self.ok_color)
            self.screen.blit(num_ok_text, (self.track_width + 200, self.height * .35))

            num_missed_text = self.large_font.render(f'{self.num_missed}', True, self.missed_color)
            self.screen.blit(num_missed_text, (self.track_width + 290, self.height * .35))

            # Draw time
            time_text = self.huge_font.render(f'{seconds_to_readable_time(current_song_time)}', True, (255, 255, 255))
            time_text_box = time_text.get_rect()
            time_text_box.center = self.track_width + (self.width - self.track_width) / 2, self.height * .5
            self.screen.blit(time_text, time_text_box)

            # Draw fps
            fps_text = self.small_font.render(f'{self.clock.get_fps():.1f}', True, (255, 255, 255))
            self.screen.blit(fps_text, (self.width - 55, 10))

            # Draw track and beats
            missed = False
            for layer, center in zip(sorted(self.layers.keys()), self.layer_centers):
                layer_object = self.layers[layer]

                # Draw layer track
                pygame.draw.line(self.screen, layer_object.color, (center, 0), (center, self.track_height), layer_object.line_thickness)

                # Draw beats
                for i in range(layer_object.count_remaining_beats() - 1, -1, -1):
                    beat = layer_object.get_beat(i)
                    if beat.time <= current_song_time + self.preview_length:
                        if abs(current_song_time - beat.time) <= self.lenience * .25:
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
                    else:
                        break

                # Draw shadows
                if layer_object.count_shadows() > 0:
                    for shadow in layer_object.shadows:
                        pygame.draw.rect(self.screen, shadow.color,
                                         (center - self.beat_width / 2,
                                          self.pixels_per_second * (self.preview_length - shadow.time + current_song_time) - self.beat_height / 2,
                                          self.beat_width,
                                          self.beat_height))

                    if current_song_time - self.bottom_offset / self.pixels_per_second > layer_object.shadows[-1].time:
                        layer_object.remove_last_shadow()

            # Check events
            for event in pygame.event.get():
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE and current_song_time > 0:
                        self.paused = True
                        self.audio_player.pause()
                    else:
                        for layer in self.enabled_layers:
                            layer_object = self.layers[layer]
                            if event.key == layer_object.key:
                                layer_object.set_line_thickness(5)
                                if layer_object.count_remaining_beats() > 0:
                                    time_difference = abs(layer_object.get_beat(-1).time - current_song_time)
                                    if time_difference <= self.lenience:
                                        beat_accuracy, color = self.score_beat(time_difference)
                                        layer_object.remove_last_beat()

                                        self.hit_text = self.large_font.render(beat_accuracy, True, color)
                                        self.hit_text_box = self.hit_text.get_rect()
                                        self.hit_text_frames = 0
                                break

                elif event.type == pygame.KEYUP:
                    for layer in self.enabled_layers:
                        layer_object = self.layers[layer]
                        if event.key == layer_object.key:
                            layer_object.set_line_thickness(3)
                            break

                elif event.type == pygame.QUIT:
                    self.close_game()
                    self.score_screen = True
                    return

            if missed:
                self.hit_text = self.large_font.render('MISS!', True, self.missed_color)
                self.hit_text_box = self.hit_text.get_rect()
                self.hit_text_frames = 0

                self.combo = 0

            # Draw hit text
            if self.hit_text:
                self.hit_text_box.center = self.track_width / 2, self.height - 50 - self.hit_text_frames / 2
                self.screen.blit(self.hit_text, self.hit_text_box)
                self.hit_text_frames += 1
                if self.hit_text_frames > self.hit_text_max_frames:
                    self.hit_text_frames = 0
                    self.hit_text = None

            # Update display
            pygame.display.flip()

            self.time += self.clock.tick(60) / 1000

        else:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.close_game()
                    return

                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self.paused = False
                        self.audio_player.unpause()
                    elif event.key == pygame.K_r:
                        self.close_game()
                        self.restart = True
                        return
                    elif event.key == pygame.K_BACKSPACE:
                        self.close_game()
                        return

            self.clock.tick(60)

    def draw_score_screen(self):
        if self.draw_score:
            self.screen.fill((0, 0, 0))
            self.draw_score = False

            final_score_perfect_text = self.large_font.render(f'perfect: {self.num_perfect}', True, self.perfect_color)
            final_score_perfect_text_box = final_score_perfect_text.get_rect()
            final_score_perfect_text_box.center = self.width / 2, self.height / 2 - 250
            self.screen.blit(final_score_perfect_text, final_score_perfect_text_box)

            final_score_great_text = self.large_font.render(f'great: {self.num_great}', True, self.great_color)
            final_score_great_text_box = final_score_great_text.get_rect()
            final_score_great_text_box.center = self.width / 2, self.height / 2 - 200
            self.screen.blit(final_score_great_text, final_score_great_text_box)

            final_score_ok_text = self.large_font.render(f'ok: {self.num_ok}', True, self.ok_color)
            final_score_ok_text_box = final_score_ok_text.get_rect()
            final_score_ok_text_box.center = self.width / 2, self.height / 2 - 150
            self.screen.blit(final_score_ok_text, final_score_ok_text_box)

            final_score_missed_text = self.large_font.render(f'missed: {self.num_missed}', True, self.missed_color)
            final_score_missed_text_box = final_score_missed_text.get_rect()
            final_score_missed_text_box.center = self.width / 2, self.height / 2 - 100
            self.screen.blit(final_score_missed_text, final_score_missed_text_box)

            final_score_accuracy_text = self.large_font.render(f'accuracy: {self.calculate_accuracy():.2f}%', True, (255, 255, 255))
            final_score_accuracy_text_box = final_score_accuracy_text.get_rect()
            final_score_accuracy_text_box.center = self.width / 2, self.height / 2 + 20
            self.screen.blit(final_score_accuracy_text, final_score_accuracy_text_box)

            final_score_text = self.large_font.render(f'score: {self.score}', True, (255, 255, 255))
            final_score_text_box = final_score_text.get_rect()
            final_score_text_box.center = self.width / 2, self.height / 2 + 140
            self.screen.blit(final_score_text, final_score_text_box)

            pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT or event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
                if self.score > self.track.high_score:
                    self.track.set_high_score(self.score)
                    self.track.set_high_score_accuracy(self.calculate_accuracy())
                    self.track.set_high_score_layers(''.join((sorted(self.enabled_layers_keys.keys()))))
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
        self.time = -self.audio_player.delay_time + self.audio_player.get_fast_forward_time()
        self.audio_player.play()
        self.display_loop()

    def close_game(self):
        self.audio_player.unpause()
        self.audio_player.stream_open.clear()
        self.playing_screen = False
