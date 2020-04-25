from subprocess import Popen, PIPE, DEVNULL
from threading import Thread, Event
from time import sleep

from pyaudio import PyAudio


class AudioPlayer:
    def __init__(self, delay_time):
        self.pyaudio = PyAudio()

        self.frame_size = 512
        self.sample_rate = 44100
        self.frame_time = self.frame_size / self.sample_rate
        self.sample_width = 2  # bytes
        self.channels = 2
        self.chunk_size = self.frame_size * self.sample_width * self.channels

        self.device = None
        self.ffmpeg_process = None
        self.data_stream = None

        self.stream_open = Event()
        self.unpaused = Event()
        self.unpaused.set()
        self.idle = Event()
        self.idle.set()

        self.time = 0
        self.delay_time = delay_time

        self.fast_forward_time = 0

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

        self.ffmpeg_process = Popen(ffmpeg_command, stdout=PIPE, stderr=DEVNULL)
        self.data_stream = self.ffmpeg_process.stdout
        
        self.device.start_stream()

        if self.fast_forward_time == 0:
            self.fast_forward_time = self.device.get_write_available() / self.frame_size * self.frame_time

        self.stream_open.set()

    def get_time(self):
        return self.time

    def pause(self):
        self.unpaused.clear()

    def unpause(self):
        self.unpaused.set()

    def play_chunk(self):
        if self.unpaused.is_set():
            chunk = self.data_stream.read(self.chunk_size)
            if chunk:
                self.time += self.frame_time / 2
                self.device.write(chunk)
                self.time += self.frame_time / 2
            else:
                self.stream_open.clear()
        else:
            self.device.stop_stream()
            self.unpaused.wait()
            self.device.start_stream()

    def stop_stream(self):
        self.stream_open.clear()
        self.device.stop_stream()

        if self.ffmpeg_process.poll():
            self.ffmpeg_process.kill()

        if self.data_stream:
            self.data_stream.flush()
            self.data_stream = None

    def close(self):
        self.device.close()
        self.pyaudio.terminate()

    def play(self):
        self.idle.clear()
        Thread(target=self.play_thread).start()

    def play_thread(self):
        sleep(self.delay_time)
        while self.stream_open.is_set():
            self.play_chunk()
        self.stop_stream()
        self.time = 0
        self.idle.set()
