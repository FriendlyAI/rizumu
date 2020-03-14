from subprocess import Popen
from sys import argv

from audio_player import AudioPlayer
from game import Game
from track import Track

if len(argv) > 1:
    Popen(['bin/ctaff', '-i', argv[1], '-o', 'tmp/out.track']).wait()

    delay_time = 3
    preview_length = 1.2
    prune_unused_layers = False

    audio_player = AudioPlayer(delay_time)
    audio_player.set_device(1)
    audio_player.open_audio(argv[1])

    enabled_layers_keys = {'A': 's', 'B': 'd', 'C': 'f', 'D': 'j', 'E': 'k', 'F': 'l'}
    # enabled_layers_keys = {'A': 's', 'B': 'd', 'C': 'f', 'D': 'j'}
    # enabled_layers_keys = {'C': 'f', 'D': 'j', 'E': 'k', 'F': 'l'}
    # enabled_layers_keys = {'A': 's', 'B': 'd', 'F': 'l'}
    # enabled_layers_keys = {'C': 'f', 'D': 'j', 'E': 'k'}
    # enabled_layers_keys = {'A': 'f', 'B': 'j'}

    game = Game(audio_player, Track(argv[1]), enabled_layers_keys, preview_length, prune_unused_layers)
    game.start_game()
