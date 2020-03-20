from beat import Beat


class Layer:
    def __init__(self, layer_id, key):
        self.layer_id = layer_id
        self.color = {
            'A': (255, 128, 128),
            'B': (255, 255, 128),
            'C': (128, 255, 128),
            'D': (128, 255, 255),
            'E': (128, 128, 255),
            'F': (255, 128, 255)
        }[layer_id]
        self.beats = []
        self.num_beats = 0
        self.shadows = []
        self.key = key

        self.line_thickness = 3
        self.key_label_text = None
        self.key_label_text_box = None

    def set_line_thickness(self, num_pixels):
        self.line_thickness = num_pixels

    # Beats
    def count_beats(self):
        self.num_beats = len(self.beats)
        return self.num_beats

    def count_remaining_beats(self):
        return len(self.beats)

    def get_beat(self, index):
        return self.beats[index]

    def insert_beat(self, beat_time):
        self.beats.insert(0, Beat(beat_time))

    def remove_last_beat(self):
        return self.beats.pop()

    # Shadows
    def count_shadows(self):
        return len(self.shadows)

    def get_shadow(self, index):
        return self.shadows[index]

    def insert_shadow(self, beat):
        self.shadows.insert(0, beat)

    def remove_last_shadow(self):
        return self.shadows.pop()
