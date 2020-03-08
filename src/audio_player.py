from subprocess import Popen, PIPE
from threading import Thread
from time import sleep

from pyaudio import PyAudio


class AudioPlayer(Thread):
    def __init__(self):
        super().__init__()
        self.pyaudio = PyAudio()

        self.frame_size = 512
        self.sample_rate = 44100
        self.frame_time = self.frame_size / self.sample_rate
        self.sample_width = 2  # bytes
        self.channels = 2
        self.chunk_size = self.frame_size * self.sample_width * self.channels

        self.device = None
        self.data_stream = None

        self.stream_open = False
        self.start_time = None

    def get_devices(self):
        return [self.pyaudio.get_device_info_by_index(i)
                for i in range(self.pyaudio.get_device_count())
                if self.pyaudio.get_device_info_by_index(i)['maxOutputChannels'] == self.channels]

    def set_device(self, device_index):
        self.device = self.pyaudio.open(format=self.pyaudio.get_format_from_width(self.sample_width),
                                        channels=self.channels,
                                        rate=self.sample_rate,
                                        output=True,
                                        output_device_index=device_index)

    def open_audio(self, filepath):
        if not self.device:
            print('Device not initialized')
            return

        ffmpeg_command = ['ffmpeg', '-i', filepath, '-loglevel', 'error', '-f', 's16le', '-ac', str(self.channels),
                          '-ar', str(self.sample_rate), '-']
        self.data_stream = Popen(ffmpeg_command, stdout=PIPE, stderr=PIPE).stdout
        self.device.start_stream()

        self.stream_open = True

    def stop_stream(self):
        self.stream_open = False

        if self.data_stream:
            self.data_stream.flush()
            self.data_stream = None
        self.device.stop_stream()

    def play_chunk(self):
        chunk = self.data_stream.read(self.chunk_size)
        if chunk:
            self.device.write(chunk)
        else:
            self.stop_stream()

    def get_time(self):
        if not self.start_time:
            return -1
        return self.device.get_time() - self.start_time

    def close(self):
        self.stop_stream()
        self.device.close()
        self.pyaudio.terminate()

    def run(self):
        sleep(2)
        self.start_time = self.device.get_time()
        while self.stream_open:
            self.play_chunk()
        self.close()
