import sys
from math import ceil
from struct import unpack
from time import time

import pygame
from pygame.font import Font
from pygame.time import Clock

from audio_player import AudioPlayer

# SONG

a = AudioPlayer()

a.set_device(1)
a.open_audio("""
tmp/tmp.flac
""".strip())

# GAME
pygame.init()

beats = {'A': [], 'B': []}
shadows = {'A': [], 'B': []}

with open('tmp/out.track', 'rb') as f:
    while 1:
        beat_layer = f.read(1).decode('ascii')
        if not beat_layer:
            break
        beat_time = unpack('f', f.read(4))[0]
        beats[beat_layer].insert(0, beat_time)

track_height = 600
bottom_offset = 100
preview_length = 1.5  # seconds

size = width, height = 400, track_height + bottom_offset
speed = [2, 2]
black = 0, 0, 0

height_time = 2  # sec, 10 pixels/sec = 600 pixels
pixels_per_second = track_height / preview_length  # 400 pixels = 1 sec
lenience = 0.06  # seconds +/- per beat

screen = pygame.display.set_mode(size)

num_layers = 2

beat_width = 150 / num_layers
beat_height = 30

layer_separation = (width - num_layers * beat_width) / (num_layers + 1)
layer_centers = [layer_separation * (i + 1) + (beat_width * (2 * i + 1) / 2) for i in range(0, num_layers)]
layer_keys = {'A': pygame.K_f, 'B': pygame.K_j}

clock = Clock()
font = Font('font/neuropol.ttf', 32)

latency = a.device.get_output_latency() * .2

start = time() + 2  # 2 second pre-delay
score = 0

score_label_frames = 0
score_label_max_frames = 45

score_text = None
text_box = None


def close_game():
    print(f'Final score: {score}')
    pygame.quit()
    sys.exit()


a.start()
while 1:
    if not a.stream_open:
        close_game()

    audio_player_time = a.get_time()
    current_song_time = time() - start

    if audio_player_time != -1:
        start += (current_song_time - audio_player_time) * .1

    current_song_time -= latency

    screen.fill(black)

    missed = False
    for layer, center in zip(sorted(beats.keys()), layer_centers):
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
                                  (
                                              preview_length - beat_time + current_song_time) * pixels_per_second - beat_height / 2,
                                  beat_width,
                                  beat_height))
        for i in range(len(shadows[layer]) - 1, -1, -1):
            beat_time = shadows[layer][i]
            pygame.draw.rect(screen, (255, 150, 150),
                             (center - beat_width / 2,
                              (preview_length - beat_time + current_song_time) * pixels_per_second - beat_height / 2,
                              beat_width,
                              beat_height))
        if len(shadows[layer]) > 0 and current_song_time - .2 - latency > shadows[layer][-1]:
            shadows[layer].pop()

    if missed:
        score_text = font.render('Miss!', True, (255, 75, 75))
        text_box = score_text.get_rect()
        score_label_frames = 0

    pygame.draw.line(screen, (75, 150, 255), (0, track_height), (width, track_height), 10)

    if score_text:
        text_box.center = width / 2, height / 2 - score_label_frames
        screen.blit(score_text, text_box)
        score_label_frames += 1
        if score_label_frames > score_label_max_frames:
            score_label_frames = 0
            score_text = None

    pygame.display.flip()

    for event in pygame.event.get():
        if event.type == pygame.KEYDOWN:
            if event.key == layer_keys['A'] and len(beats['B']) > 0:
                time_difference = abs(beats['A'][-1] - current_song_time)
                if time_difference < lenience:
                    print(beats['A'][-1] - current_song_time)
                    score_value = ceil((lenience - time_difference) * 50)
                    beats['A'].pop()
                    score += score_value

                    score_text = font.render(f'+{score_value}', True, (248, 164, 255))
                    text_box = score_text.get_rect()
                    score_label_frames = 0

            elif event.key == layer_keys['B'] and len(beats['B']) > 0:
                time_difference = abs(beats['B'][-1] - current_song_time)
                if time_difference < lenience:
                    print(beats['B'][-1] - current_song_time)
                    score_value = ceil((lenience - time_difference) * 50)
                    beats['B'].pop()
                    score += score_value

                    score_text = font.render(f'+{score_value}', True, (248, 164, 255))
                    text_box = score_text.get_rect()
                    score_label_frames = 0

        elif event.type == pygame.QUIT:
            a.stream_open = False
            close_game()

    clock.tick(60)
    pygame.display.set_caption(f'{clock.get_fps():.1f} | {current_song_time:.1f} | {score}')
