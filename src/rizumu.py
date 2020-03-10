from subprocess import Popen
from sys import argv

from audio_player import AudioPlayer
from game import main

process = Popen(['bin/ctaff', '-i', argv[1], '-o', 'tmp/out.track'])
process.wait()

audio_player = AudioPlayer()
audio_player.set_device(1)
audio_player.open_audio(argv[1])

main(audio_player)
