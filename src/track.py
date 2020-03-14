class Track:
    def __init__(self, audio_filepath):
        self.audio_filepath = audio_filepath
        self.track_filepath = 'tmp/out.track'
        # self.track_filepath = None
        self.title = None
        self.artist = None
        self.album = None
        self.duration = 300
        # self.duration = 0
        self.num_beats = [0] * 6
        self.difficulty = None
        self.high_scores = {}
