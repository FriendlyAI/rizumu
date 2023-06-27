from os.path import isfile
from pickle import dump, load

import pygame
from pygame.font import Font
from pygame.time import Clock
from pyperclip import paste

from audio_player import AudioPlayer
from game import Game
from library import Library
from track import Track
from util import ALL_LAYERS, seconds_to_readable_time


class Menu:

    EXIT = 0
    TITLE = 1
    SETTINGS = 2
    TRACK_SELECT = 3
    TRACK_SETUP = 4
    NEW_TRACK = 5
    EDIT_TRACK = 6
    SEARCH = 7

    WHITE = (255, 255, 255)
    GRAY = (128, 128, 128)
    A_COLOR = (255, 128, 128)
    B_COLOR = (255, 255, 128)
    C_COLOR = (128, 255, 128)
    D_COLOR = (128, 255, 255)
    E_COLOR = (128, 128, 255)
    F_COLOR = (255, 128, 255)
    SELECTED_COLOR = D_COLOR
    ENABLED_COLOR = C_COLOR
    DISABLED_COLOR = A_COLOR

    DIFFICULTY_COLORS = (C_COLOR, C_COLOR, C_COLOR, B_COLOR, B_COLOR, A_COLOR, D_COLOR, E_COLOR, F_COLOR)

    def __init__(self):
        pygame.mixer.pre_init(frequency=44100, size=-16, channels=2)
        pygame.init()

        self.clock = Clock()

        info = pygame.display.Info()

        self.size = self.width, self.height = 1080, 900
        self.screen = pygame.display.set_mode(self.size, flags=pygame.SCALED | pygame.RESIZABLE, vsync=True)
        pygame.display.set_icon(pygame.image.load('img/icon.png'))
        pygame.display.set_caption('RIZUMU')

        if isfile('library/saved.library'):
            self.library = load(open('library/saved.library', 'rb'))
        else:
            self.library = Library()

        pygame.mouse.set_visible(False)

        self.screen_calls = [self.close_menu,
                             self.draw_menu,
                             self.draw_settings,
                             self.draw_track_select,
                             self.draw_track_setup,
                             self.draw_new_track,
                             self.draw_edit_track,
                             self.draw_search]

        self.delay_time = 2  # Pre-track delay time

        # Audio player
        self.audio_player = AudioPlayer(self.delay_time)

        self.audio_device = 0
        for device in self.audio_player.get_devices():
            if device['name'] == 'External Headphones':
                self.audio_device = device['index']

        err_code = self.audio_player.set_device(self.audio_device)
        if err_code:
            print('FATAL ERROR: Closing.')
            pygame.display.quit()
            return

        self.latency = self.audio_player.device.get_output_latency() * 0

        # In-game options
        self.layers_keys = {'A': [True, None], 'B': [True, None], 'C': [True, None], 'D': [True, None], 'E': [True, None], 'F': [True, None]}
        self.prune_unused_layers = False

        # Difficulty
        self.preview_length = .5
        self.lenience = 0.06  # seconds +/- per beat

        # Fonts
        self.large_font = Font('font/unifont.ttf', 36)
        self.generic_font = Font('font/unifont.ttf', 26)
        self.small_font = Font('font/unifont.ttf', 16)

        # Sound Effects
        self.play_hit_sound = True
        self.bass_hit_sound_data = pygame.mixer.Sound(open('audio/bass.wav', 'rb').read())
        self.high_hit_sound_data = pygame.mixer.Sound(open('audio/high.wav', 'rb').read())
        pygame.mixer.set_num_channels(2)

        # GUI variables
        self.redraw_screen = True
        self.current_screen = Menu.TITLE
        self.last_screen = Menu.TITLE
        self.track_selection_index = 0

        '''
        Main menu screen objects
        '''
        self.main_title = self.large_font.render('RIZUMU', True, Menu.WHITE)
        self.main_title_box = self.main_title.get_rect()
        self.main_title_box.center = self.width / 2, 200

        self.main_play = self.large_font.render('Play', True, Menu.SELECTED_COLOR)
        self.main_play_box = self.main_play.get_rect()
        self.main_play_box.center = self.width / 2, 400

        self.main_settings = self.large_font.render(f'Settings', True, Menu.WHITE)
        self.main_settings_box = self.main_settings.get_rect()
        self.main_settings_box.center = self.width / 2, 500

        '''
        Settings screen objects
        '''

        '''
        Track select screen objects
        '''
        self.selected_tracks = self.library.get_tracks(self.track_selection_index)
        self.select_track_0 = None
        self.select_track_1 = None
        self.select_track_2 = None
        self.select_track_3 = None
        self.select_track_4 = None
        self.select_track_5 = None
        self.select_track_6 = None

        self.render_selected_tracks()

        self.select_track_title = None
        self.select_track_artist = None
        self.select_track_album = None
        self.select_track_high_score = None
        self.select_track_high_score_accuracy = None
        self.select_track_high_score_layers = None
        self.select_track_duration = None
        self.select_track_difficulty = None
        self.select_track_num_beats_A = None
        self.select_track_num_beats_B = None
        self.select_track_num_beats_C = None
        self.select_track_num_beats_D = None
        self.select_track_num_beats_E = None
        self.select_track_num_beats_F = None

        self.render_selected_track_data()

        self.select_edit = self.generic_font.render('e: Edit', True, Menu.WHITE)
        self.select_new = self.generic_font.render('n: New', True, Menu.WHITE)
        self.select_back = self.generic_font.render('⌫ : Back', True, Menu.WHITE)
        self.select_play = self.generic_font.render('⏎ : Play', True, Menu.WHITE)

        '''
        Track setup screen objects
        '''
        self.setup_toggle = self.generic_font.render('⏎ : Select/Toggle', True, Menu.WHITE)
        self.setup_back = self.select_back

        '''
        New track screen objects
        '''
        self.new_track_edit = self.generic_font.render('⏎ : Paste from clipboard', True, Menu.WHITE)
        self.new_track_save = self.generic_font.render('s: Save', True, Menu.WHITE)
        self.new_track_cancel = self.generic_font.render('⌫ : Cancel', True, Menu.WHITE)

        '''
        Edit track screen objects
        '''
        self.edit_track_delete = self.generic_font.render('d: Delete', True, Menu.WHITE)

        '''
        Search track screen objects
        '''

        # Start drawing
        self.display_loop()

    def render_selected_tracks(self):
        def get_color(track):
            if not track:
                return Menu.WHITE
            else:
                return Menu.DIFFICULTY_COLORS[min(8, int(track.difficulty))]

        self.select_track_0 = self.generic_font.render(f'{self.selected_tracks[0]}', True, get_color(self.selected_tracks[0]))
        self.select_track_1 = self.generic_font.render(f'{self.selected_tracks[1]}', True, get_color(self.selected_tracks[1]))
        self.select_track_2 = self.generic_font.render(f'{self.selected_tracks[2]}', True, get_color(self.selected_tracks[2]))
        self.select_track_3 = self.generic_font.render(f'{self.selected_tracks[3]}', True, get_color(self.selected_tracks[3]))
        self.select_track_4 = self.generic_font.render(f'{self.selected_tracks[4]}', True, get_color(self.selected_tracks[4]))
        self.select_track_5 = self.generic_font.render(f'{self.selected_tracks[5]}', True, get_color(self.selected_tracks[5]))
        self.select_track_6 = self.generic_font.render(f'{self.selected_tracks[6]}', True, get_color(self.selected_tracks[6]))

    def render_selected_track_data(self):
        if self.selected_tracks[3]:
            color = Menu.DIFFICULTY_COLORS[min(8, int(self.selected_tracks[3].difficulty))]
            self.select_track_title = self.large_font.render(f'{self.selected_tracks[3].title}', True, color)
            self.select_track_artist = self.generic_font.render(f'{self.selected_tracks[3].artist}', True, Menu.WHITE)
            self.select_track_album = self.generic_font.render(f'{self.selected_tracks[3].album}', True, Menu.WHITE)
            self.select_track_high_score = self.generic_font.render(f'High Score: {self.selected_tracks[3].high_score}', True, Menu.WHITE)
            self.select_track_high_score_accuracy = self.generic_font.render(f'{self.selected_tracks[3].high_score_accuracy:.3f}%', True, Menu.WHITE)
            self.select_track_high_score_layers = self.generic_font.render(f'{self.selected_tracks[3].high_score_layers}', True, Menu.WHITE)
            self.select_track_duration = self.generic_font.render(f'{seconds_to_readable_time(self.selected_tracks[3].duration)}', True, Menu.WHITE)
            self.select_track_difficulty = self.generic_font.render(f'Difficulty: {self.selected_tracks[3].difficulty}', True, color)

            self.select_track_num_beats_A = self.generic_font.render(f'{self.selected_tracks[3].num_beats["A"]}', True, Menu.A_COLOR)
            self.select_track_num_beats_B = self.generic_font.render(f'{self.selected_tracks[3].num_beats["B"]}', True, Menu.B_COLOR)
            self.select_track_num_beats_C = self.generic_font.render(f'{self.selected_tracks[3].num_beats["C"]}', True, Menu.C_COLOR)
            self.select_track_num_beats_D = self.generic_font.render(f'{self.selected_tracks[3].num_beats["D"]}', True, Menu.D_COLOR)
            self.select_track_num_beats_E = self.generic_font.render(f'{self.selected_tracks[3].num_beats["E"]}', True, Menu.E_COLOR)
            self.select_track_num_beats_F = self.generic_font.render(f'{self.selected_tracks[3].num_beats["F"]}', True, Menu.F_COLOR)

    def draw_menu(self):
        label_selection_index = 0
        while 1:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.current_screen = Menu.EXIT
                    return
                elif event.type == pygame.KEYDOWN:
                    self.redraw_screen = True
                    if event.key == pygame.K_UP:
                        self.main_play = self.large_font.render('Play', True, Menu.SELECTED_COLOR)
                        self.main_settings = self.large_font.render(f'Settings', True, Menu.WHITE)
                        label_selection_index = 0
                    elif event.key == pygame.K_DOWN:
                        self.main_play = self.large_font.render('Play', True, Menu.WHITE)
                        self.main_settings = self.large_font.render(f'Settings', True, Menu.SELECTED_COLOR)
                        label_selection_index = 1
                    elif event.key == pygame.K_RETURN:
                        if label_selection_index == 0:
                            self.current_screen = Menu.TRACK_SELECT
                        elif label_selection_index == 1:
                            self.current_screen = Menu.SETTINGS
                        return
                    elif event.key == pygame.K_BACKSPACE:
                        self.current_screen = Menu.EXIT
                        return

            if self.redraw_screen:
                self.redraw_screen = False
                self.screen.fill((0, 0, 0))

                self.screen.blit(self.main_title, self.main_title_box)
                self.screen.blit(self.main_play, self.main_play_box)
                self.screen.blit(self.main_settings, self.main_settings_box)

                pygame.display.flip()

            self.clock.tick(30)

    def draw_settings(self):
        pass

    def draw_track_select(self):
        pygame.key.set_repeat(250, 20)
        while 1:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.current_screen = Menu.EXIT
                    return
                elif event.type == pygame.KEYDOWN:
                    self.redraw_screen = True
                    if event.key == pygame.K_UP:
                        self.track_selection_index = max(self.track_selection_index - 1, 0)
                        self.selected_tracks = self.library.get_tracks(self.track_selection_index)
                        self.render_selected_tracks()
                        self.render_selected_track_data()
                    elif event.key == pygame.K_DOWN:
                        self.track_selection_index = min(self.track_selection_index + 1, len(self.library.saved_tracks) - 1)
                        self.selected_tracks = self.library.get_tracks(self.track_selection_index)
                        self.render_selected_tracks()
                        self.render_selected_track_data()
                    else:
                        if event.key == pygame.K_RETURN:
                            self.current_screen = Menu.TRACK_SETUP
                            return
                        elif event.key == pygame.K_BACKSPACE:
                            self.current_screen = Menu.TITLE
                            return
                        elif event.key == pygame.K_e:
                            self.current_screen = Menu.EDIT_TRACK
                            return
                        elif event.key == pygame.K_n:
                            self.current_screen = Menu.NEW_TRACK
                            return

            if self.redraw_screen:
                self.redraw_screen = False
                self.screen.fill((0, 0, 0))

                pygame.draw.rect(self.screen, Menu.GRAY, (15, 220, self.width - 30, 60), 1)
                pygame.draw.line(self.screen, Menu.GRAY, (0, 500), (self.width, 500))

                self.screen.blit(self.select_track_0, (15, 30))
                self.screen.blit(self.select_track_1, (30, 100))
                self.screen.blit(self.select_track_2, (45, 170))
                select_track_3_text_box = self.select_track_3.get_rect()
                select_track_3_text_box.center = 0, 250
                self.screen.blit(self.select_track_3, (60, select_track_3_text_box[1]))
                self.screen.blit(self.select_track_4, (45, 310))
                self.screen.blit(self.select_track_5, (30, 380))
                self.screen.blit(self.select_track_6, (15, 450))

                self.screen.blit(self.select_edit, (15, self.height - 30))
                self.screen.blit(self.select_new, (165, self.height - 30))
                self.screen.blit(self.select_back, (self.width - 300, self.height - 30))
                self.screen.blit(self.select_play, (self.width - 150, self.height - 30))

                if self.selected_tracks[3]:
                    self.screen.blit(self.select_track_title, (15, 525))
                    self.screen.blit(self.select_track_artist, (15, 600))
                    self.screen.blit(self.select_track_album, (15, 650))
                    self.screen.blit(self.select_track_high_score, (15, 700))
                    self.screen.blit(self.select_track_high_score_accuracy, (self.width * .3, 700))
                    self.screen.blit(self.select_track_high_score_layers, (self.width * .45, 700))
                    self.screen.blit(self.select_track_difficulty, (15, 750))

                    self.screen.blit(self.select_track_num_beats_A, (15, 800))
                    self.screen.blit(self.select_track_num_beats_B, (90, 800))
                    self.screen.blit(self.select_track_num_beats_C, (165, 800))
                    self.screen.blit(self.select_track_num_beats_D, (240, 800))
                    self.screen.blit(self.select_track_num_beats_E, (315, 800))
                    self.screen.blit(self.select_track_num_beats_F, (390, 800))
                    self.screen.blit(self.select_track_duration, (500, 800))

                pygame.display.flip()

            self.clock.tick(60)

    def draw_track_setup(self):
        label_selection_index = 0
        while 1:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.current_screen = Menu.EXIT
                    return
                elif event.type == pygame.KEYDOWN:
                    self.redraw_screen = True
                    if event.key == pygame.K_RETURN:
                        if label_selection_index == 0:
                            pygame.key.set_repeat()
                            self.play_track(self.selected_tracks[3])
                            self.current_screen = Menu.TRACK_SELECT
                            return
                        elif label_selection_index == 1:
                            # toggle prune unused layers
                            self.prune_unused_layers = not self.prune_unused_layers
                        else:
                            # toggle enable for key
                            self.layers_keys[ALL_LAYERS[label_selection_index - 2]][0] = not self.layers_keys[ALL_LAYERS[label_selection_index - 2]][0]
                    elif event.key == pygame.K_BACKSPACE:
                        self.current_screen = Menu.TRACK_SELECT
                        return
                    elif event.key == pygame.K_DOWN:
                        label_selection_index = min(7, label_selection_index + 1)
                        break
                    elif event.key == pygame.K_UP:
                        label_selection_index = max(0, label_selection_index - 1)
                        break
                    elif event.key != pygame.K_ESCAPE and event.key != pygame.K_SPACE:
                        if label_selection_index >= 2:
                            for key, value in self.layers_keys.items():
                                if value[1] == event.key:
                                    self.layers_keys[key][1] = None
                            self.layers_keys[ALL_LAYERS[label_selection_index - 2]][1] = event.key

            if self.redraw_screen:
                self.redraw_screen = False
                self.screen.fill((0, 0, 0))

                start_label = self.large_font.render('START', True, Menu.SELECTED_COLOR if label_selection_index == 0 else Menu.WHITE)
                start_label_text_box = start_label.get_rect()
                start_label_text_box.center = self.width / 2, 200
                self.screen.blit(start_label, start_label_text_box)

                prune_unused_layers_label = self.generic_font.render('Prune unused layers:', True, Menu.SELECTED_COLOR if label_selection_index == 1 else Menu.WHITE)
                prune_unused_layers_enabled_label = self.generic_font.render(f'{self.prune_unused_layers}',
                                                                             True, Menu.ENABLED_COLOR if self.prune_unused_layers else Menu.DISABLED_COLOR)
                self.screen.blit(prune_unused_layers_label, (25, 275))
                self.screen.blit(prune_unused_layers_enabled_label, (325, 275))

                # A layer
                A_label = self.generic_font.render('Layer A:', True, Menu.SELECTED_COLOR if label_selection_index == 2 else Menu.WHITE)
                A_enabled_label = self.generic_font.render(f'{"Enabled" if self.layers_keys["A"][0] else "Disabled"}',
                                                           True, Menu.ENABLED_COLOR if self.layers_keys["A"][0] else Menu.DISABLED_COLOR)
                A_key_label = self.generic_font.render(f'Key: {None if self.layers_keys["A"][1] is None else pygame.key.name(self.layers_keys["A"][1])}', True, Menu.WHITE)
                self.screen.blit(A_label, (25, 350))
                self.screen.blit(A_enabled_label, (175, 350))
                self.screen.blit(A_key_label, (325, 350))

                # B layer
                B_label = self.generic_font.render('Layer B:', True, Menu.SELECTED_COLOR if label_selection_index == 3 else Menu.WHITE)
                B_enabled_label = self.generic_font.render(f'{"Enabled" if self.layers_keys["B"][0] else "Disabled"}',
                                                           True, Menu.ENABLED_COLOR if self.layers_keys["B"][0] else Menu.DISABLED_COLOR)
                B_key_label = self.generic_font.render(f'Key: {None if self.layers_keys["B"][1] is None else pygame.key.name(self.layers_keys["B"][1])}', True, Menu.WHITE)
                self.screen.blit(B_label, (25, 425))
                self.screen.blit(B_enabled_label, (175, 425))
                self.screen.blit(B_key_label, (325, 425))

                # C layer
                C_label = self.generic_font.render('Layer C:', True, Menu.SELECTED_COLOR if label_selection_index == 4 else Menu.WHITE)
                C_enabled_label = self.generic_font.render(f'{"Enabled" if self.layers_keys["C"][0] else "Disabled"}',
                                                           True, Menu.ENABLED_COLOR if self.layers_keys["C"][0] else Menu.DISABLED_COLOR)
                C_key_label = self.generic_font.render(f'Key: {None if self.layers_keys["C"][1] is None else pygame.key.name(self.layers_keys["C"][1])}', True, Menu.WHITE)
                self.screen.blit(C_label, (25, 500))
                self.screen.blit(C_enabled_label, (175, 500))
                self.screen.blit(C_key_label, (325, 500))

                # D layer
                D_label = self.generic_font.render('Layer D:', True, Menu.SELECTED_COLOR if label_selection_index == 5 else Menu.WHITE)
                D_enabled_label = self.generic_font.render(f'{"Enabled" if self.layers_keys["D"][0] else "Disabled"}',
                                                           True, Menu.ENABLED_COLOR if self.layers_keys["D"][0] else Menu.DISABLED_COLOR)
                D_key_label = self.generic_font.render(f'Key: {None if self.layers_keys["D"][1] is None else pygame.key.name(self.layers_keys["D"][1])}', True, Menu.WHITE)
                self.screen.blit(D_label, (25, 575))
                self.screen.blit(D_enabled_label, (175, 575))
                self.screen.blit(D_key_label, (325, 575))

                # E layer
                E_label = self.generic_font.render('Layer E:', True, Menu.SELECTED_COLOR if label_selection_index == 6 else Menu.WHITE)
                E_enabled_label = self.generic_font.render(f'{"Enabled" if self.layers_keys["E"][0] else "Disabled"}',
                                                           True, Menu.ENABLED_COLOR if self.layers_keys["E"][0] else Menu.DISABLED_COLOR)
                E_key_label = self.generic_font.render(f'Key: {None if self.layers_keys["E"][1] is None else pygame.key.name(self.layers_keys["E"][1])}', True, Menu.WHITE)
                self.screen.blit(E_label, (25, 650))
                self.screen.blit(E_enabled_label, (175, 650))
                self.screen.blit(E_key_label, (325, 650))

                # F layer
                F_label = self.generic_font.render('Layer F:', True, Menu.SELECTED_COLOR if label_selection_index == 7 else Menu.WHITE)
                F_enabled_label = self.generic_font.render(f'{"Enabled" if self.layers_keys["F"][0] else "Disabled"}',
                                                           True, Menu.ENABLED_COLOR if self.layers_keys["F"][0] else Menu.DISABLED_COLOR)
                F_key_label = self.generic_font.render(f'Key: {None if self.layers_keys["F"][1] is None else pygame.key.name(self.layers_keys["F"][1])}', True, Menu.WHITE)
                self.screen.blit(F_label, (25, 725))
                self.screen.blit(F_enabled_label, (175, 725))
                self.screen.blit(F_key_label, (325, 725))

                self.screen.blit(self.setup_toggle, (self.width - 450, self.height - 30))
                self.screen.blit(self.setup_back, (self.width - 150, self.height - 30))

                pygame.display.flip()

            self.clock.tick(30)

    def draw_new_track(self):
        label_selection_index = 0
        clipboard = paste()
        new_track_filepath = clipboard if isfile(clipboard) and clipboard[clipboard.rindex('.'):] in ('.flac', '.opus', '.mp3', '.m4a') else None
        new_track = Track(new_track_filepath) if new_track_filepath else None

        while 1:
            for event in pygame.event.get():
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN:
                        if label_selection_index == 0:
                            clipboard = paste()
                            new_track_filepath = clipboard if isfile(clipboard) and clipboard[clipboard.rindex('.'):] in ('.flac', '.opus', '.mp3', '.m4a') else None
                            new_track = Track(new_track_filepath) if new_track_filepath else None
                            break
                        elif label_selection_index == 1:
                            new_track.set_title(paste())
                            break
                        elif label_selection_index == 2:
                            new_track.set_artist(paste())
                            break
                        elif label_selection_index == 3:
                            new_track.set_album(paste())
                            break
                    elif event.key == pygame.K_s:
                        self.current_screen = Menu.TRACK_SELECT
                        if new_track:
                            new_index = self.library.add_track(new_track)
                            self.save_library()
                            if new_index is not None:
                                self.track_selection_index = new_index
                                self.selected_tracks = self.library.get_tracks(self.track_selection_index)
                                self.render_selected_tracks()
                                self.render_selected_track_data()
                        return
                    elif event.key == pygame.K_BACKSPACE:
                        self.current_screen = Menu.TRACK_SELECT
                        return
                    elif event.key == pygame.K_DOWN:
                        label_selection_index = min(3, label_selection_index + 1)
                        break
                    elif event.key == pygame.K_UP:
                        label_selection_index = max(0, label_selection_index - 1)
                        break

            if self.redraw_screen:
                self.screen.fill((0, 0, 0))

                new_track_file_text = self.generic_font.render('Paste filepath from clipboard', True,
                                                               Menu.SELECTED_COLOR if label_selection_index == 0 else Menu.WHITE)
                new_track_file_text_box = new_track_file_text.get_rect()
                new_track_file_text_box.center = self.width / 2, 200
                self.screen.blit(new_track_file_text, new_track_file_text_box)

                clipboard = paste()
                new_track_clipboard_text = self.small_font.render(f'Clipboard: {clipboard}', True, Menu.WHITE)
                self.screen.blit(new_track_clipboard_text, (10, self.height - 200))

                self.screen.blit(self.new_track_edit, (15, self.height - 30))
                self.screen.blit(self.new_track_save, (self.width - 300, self.height - 30))
                self.screen.blit(self.new_track_cancel, (self.width - 150, self.height - 30))

                self.screen.blit(self.generic_font.render(f'Title: {new_track.title if new_track else "None"}', True, Menu.SELECTED_COLOR if label_selection_index == 1 else Menu.WHITE), (10, 300))
                self.screen.blit(self.generic_font.render(f'Artist: {new_track.artist if new_track else "None"}', True, Menu.SELECTED_COLOR if label_selection_index == 2 else Menu.WHITE), (10, 375))
                self.screen.blit(self.generic_font.render(f'Album: {new_track.album if new_track else "None"}', True, Menu.SELECTED_COLOR if label_selection_index == 3 else Menu.WHITE), (10, 450))

                pygame.display.flip()

            self.clock.tick(30)

    def draw_edit_track(self):
        label_selection_index = 0
        track = self.selected_tracks[3]

        old_title = track.title
        old_artist = track.artist
        old_album = track.album

        while 1:
            for event in pygame.event.get():
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN:
                        if label_selection_index == 0:
                            track.set_title(paste())
                            break
                        elif label_selection_index == 1:
                            track.set_artist(paste())
                            break
                        elif label_selection_index == 2:
                            track.set_album(paste())
                            break
                    elif event.key == pygame.K_d:
                        track.delete_map()
                        self.library.remove_track(self.track_selection_index)
                        self.save_library()
                        if self.track_selection_index >= len(self.library.saved_tracks):
                            self.track_selection_index -= 1
                        self.selected_tracks = self.library.get_tracks(self.track_selection_index)
                        self.render_selected_tracks()
                        self.render_selected_track_data()
                        self.current_screen = Menu.TRACK_SELECT
                        return
                    elif event.key == pygame.K_s:
                        if track.title != old_title:
                            self.library.add_track(self.library.remove_track(self.track_selection_index))
                        self.save_library()
                        self.render_selected_tracks()
                        self.render_selected_track_data()
                        self.current_screen = Menu.TRACK_SELECT
                        return
                    elif event.key == pygame.K_BACKSPACE:
                        track.set_title(old_title)
                        track.set_artist(old_artist)
                        track.set_album(old_album)
                        self.current_screen = Menu.TRACK_SELECT
                        return
                    elif event.key == pygame.K_DOWN:
                        label_selection_index = min(2, label_selection_index + 1)
                        break
                    elif event.key == pygame.K_UP:
                        label_selection_index = max(0, label_selection_index - 1)
                        break

            if self.redraw_screen:
                self.screen.fill((0, 0, 0))

                clipboard = paste()
                edit_track_clipboard_text = self.small_font.render(f'Clipboard: {clipboard}', True, Menu.WHITE)
                self.screen.blit(edit_track_clipboard_text, (10, self.height - 200))

                self.screen.blit(self.new_track_edit, (15, self.height - 30))
                self.screen.blit(self.edit_track_delete, (400, self.height - 30))
                self.screen.blit(self.new_track_save, (self.width - 300, self.height - 30))
                self.screen.blit(self.new_track_cancel, (self.width - 150, self.height - 30))

                self.screen.blit(self.generic_font.render(f'Title: {track.title}', True, Menu.SELECTED_COLOR if label_selection_index == 0 else Menu.WHITE), (10, 300))
                self.screen.blit(self.generic_font.render(f'Artist: {track.artist}', True, Menu.SELECTED_COLOR if label_selection_index == 1 else Menu.WHITE), (10, 375))
                self.screen.blit(self.generic_font.render(f'Album: {track.album}', True, Menu.SELECTED_COLOR if label_selection_index == 2 else Menu.WHITE), (10, 450))

                pygame.display.flip()

            self.clock.tick(30)

    def draw_search(self):
        pass

    def display_loop(self):
        while 1:
            self.screen_calls[self.current_screen]()
            if self.current_screen == 0:
                break

    def play_track(self, track):
        if isfile(track.audio_filepath) and isfile(track.map_filepath):
            self.audio_player.idle.wait()
            enabled_layers_keys = {layer: key[1] for layer, key in self.layers_keys.items() if key[0]}
            game = Game(self.screen, self.width, self.height, self.audio_player, track, enabled_layers_keys, self.preview_length, self.lenience, self.prune_unused_layers, self.latency, self.play_hit_sound, [self.bass_hit_sound_data, self.high_hit_sound_data])
            game.start_game()
            while game.restart:
                self.audio_player.idle.wait()
                game = Game(self.screen, self.width, self.height, self.audio_player, track, enabled_layers_keys, self.preview_length, self.lenience, self.prune_unused_layers, self.latency, self.play_hit_sound, [self.bass_hit_sound_data, self.high_hit_sound_data])
                game.start_game()
            self.save_library()
            self.render_selected_track_data()

    def save_library(self):
        dump(self.library, open('library/saved.library', 'wb'))

    def close_menu(self):
        self.save_library()
        self.audio_player.idle.wait()
        self.audio_player.close()
        pygame.display.quit()
