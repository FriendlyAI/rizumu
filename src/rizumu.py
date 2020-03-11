from subprocess import Popen
from sys import argv

from audio_player import AudioPlayer
from game import Game
from track import Track

Popen(['bin/ctaff', '-i', argv[1], '-o', 'tmp/out.track']).wait()

delay_time = 3

audio_player = AudioPlayer(delay_time)
audio_player.set_device(1)
audio_player.open_audio(argv[1])

enabled_layers_keys = {'A': 's', 'B': 'd', 'C': 'j', 'D': 'k', 'E': 'l'}
# enabled_layers_keys = {'A': 'd', 'B': 'f', 'E': 'j'}
# enabled_layers_keys = {'A': 'd', 'B': 'f', 'C': 'j'}
# enabled_layers_keys = {'B': 'f', 'E': 'j'}
# enabled_layers_keys = {'C': 'f', 'E': 'j'}
# enabled_layers_keys = {'A': 'f', 'B': 'j'}
# enabled_layers_keys = {'C': 'f', 'D': 'j', 'E': 'k'}

game = Game(audio_player, Track(argv[1]), enabled_layers_keys)
game.start_game()
