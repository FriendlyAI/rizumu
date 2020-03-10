import sys
from math import ceil
from struct import unpack
from time import time

import pygame
from pygame.font import Font
from pygame.time import Clock


def main(audio_player):
    pygame.init()

    beats = {}

    with open('tmp/out.track', 'rb') as f:
        while 1:
            beat_layer = f.read(1).decode('ascii')
            if not beat_layer:
                break
            beat_time = unpack('f', f.read(4))[0]
            if beat_layer not in beats.keys():
                beats[beat_layer] = []
            beats[beat_layer].insert(0, beat_time)

    used_layers = ('A', 'B', 'C', 'D', 'E')
    layer_keys = {'A': 'd', 'B': 'f', 'C': 'j', 'D': 'k', 'E': 'l'}

    # used_layers = ('A', 'B', 'E')
    # layer_keys = {'A': 'd', 'B': 'f', 'E': 'j'}

    # used_layers = ('C', 'D', 'E')
    # layer_keys = {'C': 'f', 'D': 'j', 'E': 'k'}

    # used_layers = ('C', 'E')
    # layer_keys = {'C': 'f', 'E': 'j'}

    # used_layers = ('A', 'B')
    # layer_keys = {'A': 'f', 'B': 'j'}

    for key in list(beats.keys()):
        if key not in used_layers:
            del beats[key]

    shadows = {layer: [] for layer in beats.keys()}

    track_height = 600
    bottom_offset = 100
    preview_length = 1.5  # seconds

    size = width, height = 400, track_height + bottom_offset

    pixels_per_second = track_height / preview_length  # 400 pixels = 1 sec
    lenience = 0.05 + .005 * len(beats.keys())  # seconds +/- per beat

    # pygame.display.set_icon(pygame.image.load('img/icon.png'))
    screen = pygame.display.set_mode(size)
    font = Font('font/good times.ttf', 24)

    num_layers = len(beats.keys())

    beat_width = 150 / num_layers
    beat_height = 16

    layer_separation = (width - num_layers * beat_width) / (num_layers + 1)
    layer_centers = [layer_separation * (i + 1) + (beat_width * (2 * i + 1) / 2) for i in range(0, num_layers)]

    layer_labels = []
    for layer, center in zip(sorted(beats.keys()), layer_centers):
        text = font.render(layer_keys[layer], True, (255, 255, 255))
        text_box = text.get_rect()
        text_box.center = center, track_height + 40
        layer_labels.append((text, text_box))

    clock = Clock()

    latency = audio_player.device.get_output_latency() * .75

    start = time() + 2 - audio_player.get_fast_forward_time()  # 2 second pre-delay

    score = 0

    score_label_frames = 0
    score_label_max_frames = 45

    score_text = None
    score_text_box = None

    paused = False
    pause_time = 0

    def close_game():
        print(f'Final score: {score}')
        pygame.quit()
        sys.exit()

    audio_player.start()
    while 1:

        if not audio_player.stream_open.is_set():
            close_game()

        if not paused:
            audio_player_time = audio_player.get_time()
            current_song_time = time() - start

            if audio_player_time != 0:
                difference = current_song_time - audio_player_time
                if abs(difference) > 0.1:
                    start += difference * .1
                elif abs(difference) > 0.03:
                    start += difference * .05
                else:
                    start += difference * .01

            current_song_time -= latency

            screen.fill((0, 0, 0))

            pygame.draw.line(screen, (128, 128, 128), (0, track_height / 3), (width, track_height / 3), 1)

            pygame.draw.line(screen, (128, 128, 128), (0, 2 * track_height / 3), (width, 2 * track_height / 3), 1)

            pygame.draw.line(screen, (75, 150, 255), (0, track_height), (width, track_height), 9)

            missed = False
            for layer, center in zip(sorted(beats.keys()), layer_centers):
                pygame.draw.line(screen, (75, 150, 255), (center, 0), (center, track_height), 3)
                for i in range(len(beats[layer]) - 1, -1, -1):
                    beat_time = beats[layer][i]
                    if current_song_time - .1 - latency <= beat_time <= current_song_time + preview_length:
                        y = (preview_length - beat_time + current_song_time) * pixels_per_second - beat_height / 2
                        if abs(y - track_height) / pixels_per_second <= lenience:
                            color = (50, 200, 50)
                        elif (y - track_height) / pixels_per_second > lenience:
                            shadows[layer].insert(0, beats[layer].pop())
                            color = (255, 150, 150)
                            missed = True
                        else:
                            color = (255, 255, 255)
                        pygame.draw.rect(screen, color,
                                         (center - beat_width / 2,
                                          pixels_per_second * (preview_length - beat_time + current_song_time) - beat_height / 2,
                                          beat_width,
                                          beat_height))
                for i in range(len(shadows[layer]) - 1, -1, -1):
                    beat_time = shadows[layer][i]
                    pygame.draw.rect(screen, (255, 150, 150),
                                     (center - beat_width / 2,
                                      pixels_per_second * (preview_length - beat_time + current_song_time) - beat_height / 2,
                                      beat_width,
                                      beat_height))
                if len(shadows[layer]) > 0 and current_song_time - .2 - latency > shadows[layer][-1]:
                    shadows[layer].pop()

            for text, text_box in layer_labels:
                screen.blit(text, text_box)

            if missed:
                score_text = font.render('miss', True, (255, 75, 75))
                score_text_box = score_text.get_rect()
                score_label_frames = 0

            if score_text:
                score_text_box.center = width / 2, 100 - score_label_frames
                screen.blit(score_text, score_text_box)
                score_label_frames += 1
                if score_label_frames > score_label_max_frames:
                    score_label_frames = 0
                    score_text = None

            pygame.display.flip()

            for event in pygame.event.get():
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        audio_player.pause()
                        paused = True
                        pause_time = time()
                    else:
                        for key in beats.keys():
                            if event.key == ord(layer_keys[key]) and len(beats[key]) > 0:
                                time_difference = abs(beats[key][-1] - current_song_time)
                                if time_difference < lenience:
                                    score_value = ceil((lenience - time_difference) * 50)
                                    beats[key].pop()
                                    score += score_value

                                    score_text = font.render(f'+{score_value}', True, (255, 255, 255))
                                    score_text_box = score_text.get_rect()
                                    score_label_frames = 0

                elif event.type == pygame.QUIT:
                    audio_player.unpause()
                    audio_player.stream_open.clear()
                    close_game()

            pygame.display.set_caption(f'{clock.get_fps():.1f} | {current_song_time:.1f} | {score}')

        else:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    audio_player.unpause()
                    audio_player.stream_open.clear()
                    close_game()
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    audio_player.unpause()
                    paused = False
                    start += time() - pause_time

        clock.tick(60)
