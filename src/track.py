class Track:
    def __init__(self, audio_filepath):
        self.audio_filepath = audio_filepath
        self.track_filepath = 'tmp/out.track'
        self.artist = None
        self.title = None
        self.duration = 0
        self.num_beats = 0
        self.difficulty = None
