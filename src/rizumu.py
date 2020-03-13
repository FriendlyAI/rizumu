from subprocess import Popen
from sys import argv

from audio_player import AudioPlayer
from game import Game
from track import Track

if len(argv) > 1:
    Popen(['bin/ctaff', '-i', argv[1], '-o', 'tmp/out.track']).wait()

    delay_time = 3
    preview_length = 1.5

    audio_player = AudioPlayer(delay_time)
    audio_player.set_device(1)
    audio_player.open_audio(argv[1])

    enabled_layers_keys = {'A': 's', 'B': 'd', 'C': 'f', 'D': 'j', 'E': 'k', 'F': 'l'}

    print(f'Device delay: {audio_player.device.get_output_latency()}')

    game = Game(audio_player, Track(argv[1]), enabled_layers_keys, preview_length)
    game.start_game()
