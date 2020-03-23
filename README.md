# rizumu

A simple rhythm game for any song using beat maps generated by [ctaff](https://github.com/FriendlyAI/ctaff).

## Libraries
- [ctaff](https://github.com/FriendlyAI/ctaff)
   - Compile executable to `bin/`
- Installed with `pip install -r requirements.txt`
    - [mutagen](https://mutagen.readthedocs.io/en/latest/) >= 1.44.0
    - [PyAudio](https://people.csail.mit.edu/hubert/pyaudio/) >= 0.2.11
    - [Pygame](https://www.pygame.org/) >= 2.0.0.dev6
    - [pyperclip](https://github.com/asweigart/pyperclip) >= 1.7.0

## Dependencies
- [FFmpeg](https://www.ffmpeg.org/)
    - Command-line tools required
- [PortAudio](http://www.portaudio.com/) (on macOS)
   - `brew install portaudio`
   - `brew link portaudio`