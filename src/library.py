from track import Track


class Library:
    def __init__(self):
        self.saved_tracks = []

    def add_track(self, audio_filepath):
        new_track = Track(audio_filepath)
        sort_title = new_track.title.lower()

        start_index = 0
        end_index = len(self.saved_tracks)

        if end_index == 0:
            self.saved_tracks.append(new_track)
            new_track.generate_track_file()
            return 0
        else:
            while 1:
                middle_index = (start_index + end_index) // 2

                if start_index == end_index:
                    self.saved_tracks.insert(middle_index, new_track)
                    new_track.generate_track_file()
                    return middle_index
                elif sort_title == self.saved_tracks[middle_index].title.lower():
                    if self.saved_tracks[middle_index] == new_track:
                        return
                    else:
                        self.saved_tracks.insert(middle_index, new_track)
                        new_track.generate_track_file()
                        return middle_index
                elif sort_title > self.saved_tracks[middle_index].title.lower():
                    start_index = middle_index + 1
                elif sort_title < self.saved_tracks[middle_index].title.lower():
                    end_index = middle_index

    def remove_track(self, index):
        self.saved_tracks.pop(index)

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
