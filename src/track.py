from subprocess import Popen
from time import time

from mutagen.flac import FLAC
from mutagen.mp3 import MP3
from mutagen.mp4 import MP4
from mutagen.oggopus import OggOpus

from util import ALL_LAYERS


class Track:
    def __init__(self, audio_filepath, track_filepath=None):
        self.audio_filepath = audio_filepath
        self.track_filepath = track_filepath
        self.title = None
        self.artist = None
        self.album = None
        self.duration = 0
        self.num_beats = {layer: 0 for layer in ALL_LAYERS}
        self.difficulty = None
        self.high_score = 0

        self.get_tags()
        self.generate_track_file()

    def get_tags(self):
        file_extension = self.audio_filepath[self.audio_filepath.rindex('.'):]
        if file_extension == '.flac':
            reader = FLAC(self.audio_filepath)
            tags, info = reader.tags, reader.info
            self.title = tags.get('TITLE', ['UNKNOWN'])[0]
            self.artist = tags.get('ARTIST', ['UNKNOWN'])[0]
            self.album = tags.get('ALBUM', ['UNKNOWN'])[0]
            self.duration = int(info.length)

        elif file_extension == '.opus':
            reader = OggOpus(self.audio_filepath)
            tags, info = reader.tags, reader.info
            self.title = tags.get('TITLE', ['UNKNOWN'])[0]
            self.artist = tags.get('ARTIST', ['UNKNOWN'])[0]
            self.album = tags.get('ALBUM', ['UNKNOWN'])[0]
            self.duration = int(info.length)

        elif file_extension == '.mp3':
            reader = MP3(self.audio_filepath)
            tags, info = reader.tags, reader.info
            self.title = tags.get('TIT2', ['UNKNOWN'])[0]
            self.artist = tags.get('TPE1', ['UNKNOWN'])[0]
            self.album = tags.get('TALB', ['UNKNOWN'])[0]
            self.duration = int(info.length)

        elif file_extension == '.m4a':
            reader = MP4(self.audio_filepath)
            tags, info = reader.tags, reader.info
            self.title = tags.get('\xa9nam', ['UNKNOWN'])[0]
            self.artist = tags.get('\xa9ART', ['UNKNOWN'])[0]
            self.album = tags.get('\xa9alb', ['UNKNOWN'])[0]
            self.duration = int(info.length)

        else:
            return

    def generate_track_file(self):
        if not self.track_filepath:
            cleaned_artist = self.artist.replace('/', '／')
            cleaned_title = self.title.replace('/', '／')
            cleaned_album = self.album.replace('/', '／')
            self.track_filepath = f'library/tracks/{cleaned_artist} - {cleaned_title} - {cleaned_album} {int(time())}.track'

        Popen(['bin/ctaff', '-i', self.audio_filepath, '-o', f'{self.track_filepath}']).wait()

        with open(self.track_filepath, 'rb') as f:
            while 1:
                beat_layer = f.read(1).decode('ascii')
                if not beat_layer:
                    break
                f.read(4)  # discard beat time
                self.num_beats[beat_layer] += 1

        beat_to_time_ratio = int(sum((self.num_beats[layer] for layer in self.num_beats.keys())) // self.duration)
        if beat_to_time_ratio >= 5:
            self.difficulty = 5
        else:
            self.difficulty = beat_to_time_ratio

    def set_track_filepath(self, track_filepath):
        self.track_filepath = track_filepath

    def set_title(self, title):
        self.title = title

    def set_artist(self, artist):
        self.artist = artist

    def set_album(self, album):
        self.album = album

    def set_high_score(self, score):
        self.high_score = score

    def __repr__(self):
        return self.title