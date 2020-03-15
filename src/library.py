from track import Track


class Library:
    def __init__(self):
        self.saved_tracks = []

    def add_track(self, audio_filepath):
        # TODO: binary insert
        self.saved_tracks.append(Track(audio_filepath))
        self.sort_library()

    def sort_library(self):
        self.saved_tracks.sort(key=repr)

    def get_tracks(self, center_index):
        tracks = []
        for i in range(center_index - 3, center_index + 4):
            if -1 < i < len(self.saved_tracks):
                tracks.append(self.saved_tracks[i])
            else:
                tracks.append('')
        return tracks

    def search(self, query):
        matches = []
        return matches
