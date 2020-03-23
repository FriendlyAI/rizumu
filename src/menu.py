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
from util import seconds_to_readable_time


class Menu:

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

    DIFFICULTY_COLORS = (C_COLOR, C_COLOR, B_COLOR, B_COLOR, A_COLOR, D_COLOR, E_COLOR, F_COLOR)

    def __init__(self):
        pygame.init()

        self.clock = Clock()

        info = pygame.display.Info()

        self.size = self.width, self.height = int(info.current_w * .75), info.current_h
        self.screen = pygame.display.set_mode(self.size, flags=pygame.SCALED | pygame.FULLSCREEN)
        # pygame.display.set_icon(pygame.image.load('img/icon.png'))

        if isfile('library/saved.library'):
            self.library = load(open('library/saved.library', 'rb'))
        else:
            self.library = Library()

        self.delay_time = 2
        self.audio_device = 1

        self.audio_player = AudioPlayer(self.delay_time)
        self.audio_player.set_device(self.audio_device)

        pygame.mouse.set_visible(False)

        # In-game options
        self.enabled_layers_keys = {'A': ord('s'), 'B': ord('d'), 'C': ord('f'), 'D': ord('j'), 'E': ord('k'), 'F': ord('l')}
        # self.enabled_layers_keys = {'B': ord('d'), 'D': ord('j'), 'F': ord('l')}
        # self.enabled_layers_keys = {'C': ord('f'), 'D': ord('j'), 'E': ord('k')}
        # self.enabled_layers_keys = {'A': ord('f'), 'B': ord('j')}
        self.preview_length = 1.2
        self.prune_unused_layers = False
        self.latency = self.audio_player.device.get_output_latency() * 0

        # Fonts
        self.large_font = Font('font/unifont.ttf', 36)
        self.generic_font = Font('font/unifont.ttf', 26)
        self.small_font = Font('font/unifont.ttf', 16)

        # GUI variables
        self.redraw_screen = True
        self.current_screen = Menu.TITLE
        self.last_screen = Menu.TITLE
        self.label_selection_index = 0
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
        self.select_track_0 = self.generic_font.render(f'{self.selected_tracks[0]}', True, Menu.WHITE)
        self.select_track_1 = self.generic_font.render(f'{self.selected_tracks[1]}', True, Menu.WHITE)
        self.select_track_2 = self.generic_font.render(f'{self.selected_tracks[2]}', True, Menu.WHITE)
        self.select_track_3 = self.generic_font.render(f'{self.selected_tracks[3]}', True, Menu.SELECTED_COLOR)
        self.select_track_4 = self.generic_font.render(f'{self.selected_tracks[4]}', True, Menu.WHITE)
        self.select_track_5 = self.generic_font.render(f'{self.selected_tracks[5]}', True, Menu.WHITE)
        self.select_track_6 = self.generic_font.render(f'{self.selected_tracks[6]}', True, Menu.WHITE)

    def render_selected_track_data(self):
        if self.selected_tracks[3]:
            self.select_track_title = self.large_font.render(f'{self.selected_tracks[3].title}', True, Menu.D_COLOR)
            self.select_track_artist = self.generic_font.render(f'{self.selected_tracks[3].artist}', True, Menu.WHITE)
            self.select_track_album = self.generic_font.render(f'{self.selected_tracks[3].album}', True, Menu.WHITE)
            self.select_track_high_score = self.generic_font.render(f'High Score: {self.selected_tracks[3].high_score}', True, Menu.WHITE)
            self.select_track_high_score_accuracy = self.generic_font.render(f'{self.selected_tracks[3].high_score_accuracy:.2f}%', True, Menu.WHITE)
            self.select_track_high_score_layers = self.generic_font.render(f'{self.selected_tracks[3].high_score_layers}', True, Menu.WHITE)
            self.select_track_duration = self.generic_font.render(f'{seconds_to_readable_time(self.selected_tracks[3].duration)}', True, Menu.WHITE)
            self.select_track_difficulty = self.generic_font.render(f'Difficulty: {self.selected_tracks[3].difficulty}', True, Menu.DIFFICULTY_COLORS[min(7, int(self.selected_tracks[3].difficulty))])

            self.select_track_num_beats_A = self.generic_font.render(f'{self.selected_tracks[3].num_beats["A"]}', True, Menu.A_COLOR)
            self.select_track_num_beats_B = self.generic_font.render(f'{self.selected_tracks[3].num_beats["B"]}', True, Menu.B_COLOR)
            self.select_track_num_beats_C = self.generic_font.render(f'{self.selected_tracks[3].num_beats["C"]}', True, Menu.C_COLOR)
            self.select_track_num_beats_D = self.generic_font.render(f'{self.selected_tracks[3].num_beats["D"]}', True, Menu.D_COLOR)
            self.select_track_num_beats_E = self.generic_font.render(f'{self.selected_tracks[3].num_beats["E"]}', True, Menu.E_COLOR)
            self.select_track_num_beats_F = self.generic_font.render(f'{self.selected_tracks[3].num_beats["F"]}', True, Menu.F_COLOR)

    def draw_menu(self):
        self.label_selection_index = 0
        while 1:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.current_screen = 0
                    return
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_UP:
                        self.main_play = self.large_font.render('Play', True, Menu.SELECTED_COLOR)
                        self.main_settings = self.large_font.render(f'Settings', True, Menu.WHITE)
                        self.label_selection_index = 0
                        self.redraw_screen = True
                    elif event.key == pygame.K_DOWN:
                        self.main_play = self.large_font.render('Play', True, Menu.WHITE)
                        self.main_settings = self.large_font.render(f'Settings', True, Menu.SELECTED_COLOR)
                        self.label_selection_index = 1
                        self.redraw_screen = True
                    elif event.key == pygame.K_RETURN:
                        if self.label_selection_index == 0:
                            self.current_screen = Menu.TRACK_SELECT
                            self.redraw_screen = True
                        elif self.label_selection_index == 1:
                            self.current_screen = Menu.SETTINGS
                            self.redraw_screen = True
                        return
                    elif event.key == pygame.K_BACKSPACE:
                        self.current_screen = 0
                        return

            if self.redraw_screen:
                self.redraw_screen = False
                self.screen.fill((0, 0, 0))

                self.screen.blit(self.main_title, self.main_title_box)
                self.screen.blit(self.main_play, self.main_play_box)
                self.screen.blit(self.main_settings, self.main_settings_box)

                pygame.display.flip()

            self.clock.tick(30)

    # noinspection PyArgumentList
    def draw_track_select(self):
        pygame.key.set_repeat(250, 25)
        while 1:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.current_screen = 0
                    return
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_UP:
                        self.track_selection_index = max(self.track_selection_index - 1, 0)
                        self.selected_tracks = self.library.get_tracks(self.track_selection_index)
                        self.render_selected_tracks()
                        self.render_selected_track_data()
                        self.redraw_screen = True
                    elif event.key == pygame.K_DOWN:
                        self.track_selection_index = min(self.track_selection_index + 1, len(self.library.saved_tracks) - 1)
                        self.selected_tracks = self.library.get_tracks(self.track_selection_index)
                        self.render_selected_tracks()
                        self.render_selected_track_data()
                        self.redraw_screen = True
                    else:
                        if event.key == pygame.K_RETURN:
                            self.redraw_screen = True
                            pygame.key.set_repeat()
                            self.play_track(self.selected_tracks[3])
                            pygame.key.set_repeat(250, 25)

                        elif event.key == pygame.K_BACKSPACE:
                            self.redraw_screen = True
                            self.current_screen = Menu.TITLE
                            return
                        elif event.key == pygame.K_e:
                            self.redraw_screen = True
                            self.current_screen = Menu.EDIT_TRACK
                            return
                        elif event.key == pygame.K_n:
                            self.redraw_screen = True
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

    def draw_new_track(self):
        self.label_selection_index = 0
        clipboard = paste()
        new_track_filepath = clipboard if isfile(clipboard) and clipboard[clipboard.rindex('.'):] in ('.flac', '.opus', '.mp3', '.m4a') else None
        new_track = Track(new_track_filepath) if new_track_filepath else None

        while 1:
            for event in pygame.event.get():
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN:
                        if self.label_selection_index == 0:
                            clipboard = paste()
                            new_track_filepath = clipboard if isfile(clipboard) and clipboard[clipboard.rindex('.'):] in ('.flac', '.opus', '.mp3', '.m4a') else None
                            new_track = Track(new_track_filepath) if new_track_filepath else None
                            break
                        elif self.label_selection_index == 1:
                            new_track.set_title(paste())
                            break
                        elif self.label_selection_index == 2:
                            new_track.set_artist(paste())
                            break
                        elif self.label_selection_index == 3:
                            new_track.set_album(paste())
                            break
                    elif event.key == pygame.K_s:
                        self.current_screen = Menu.TRACK_SELECT
                        if new_track:
                            new_index = self.library.add_track(new_track)
                            if new_index:
                                self.track_selection_index = new_index
                                self.selected_tracks = self.library.get_tracks(self.track_selection_index)
                                self.render_selected_tracks()
                                self.render_selected_track_data()
                        return
                    elif event.key == pygame.K_BACKSPACE:
                        self.current_screen = Menu.TRACK_SELECT
                        return
                    elif event.key == pygame.K_DOWN:
                        self.label_selection_index = min(3, self.label_selection_index + 1)
                        break
                    elif event.key == pygame.K_UP:
                        self.label_selection_index = max(0, self.label_selection_index - 1)
                        break

            if self.redraw_screen:
                self.screen.fill((0, 0, 0))

                new_track_file_text = self.generic_font.render('Paste filepath from clipboard', True,
                                                               Menu.SELECTED_COLOR if self.label_selection_index == 0 else Menu.WHITE)
                new_track_file_text_box = new_track_file_text.get_rect()
                new_track_file_text_box.center = self.width / 2, 200
                self.screen.blit(new_track_file_text, new_track_file_text_box)

                clipboard = paste()
                new_track_clipboard_text = self.small_font.render(f'Clipboard: {clipboard}', True, Menu.WHITE)
                self.screen.blit(new_track_clipboard_text, (10, self.height - 200))

                self.screen.blit(self.new_track_edit, (15, self.height - 30))
                self.screen.blit(self.new_track_save, (self.width - 300, self.height - 30))
                self.screen.blit(self.new_track_cancel, (self.width - 150, self.height - 30))

                self.screen.blit(self.generic_font.render(f'Title: {new_track.title if new_track else "None"}', True, Menu.SELECTED_COLOR if self.label_selection_index == 1 else Menu.WHITE), (10, 300))
                self.screen.blit(self.generic_font.render(f'Artist: {new_track.artist if new_track else "None"}', True, Menu.SELECTED_COLOR if self.label_selection_index == 2 else Menu.WHITE), (10, 375))
                self.screen.blit(self.generic_font.render(f'Album: {new_track.album if new_track else "None"}', True, Menu.SELECTED_COLOR if self.label_selection_index == 3 else Menu.WHITE), (10, 450))

                pygame.display.flip()

            self.clock.tick(30)

    def draw_edit_track(self):
        self.label_selection_index = 0
        track = self.selected_tracks[3]

        old_title = track.title
        old_artist = track.artist
        old_album = track.album

        while 1:
            for event in pygame.event.get():
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN:
                        if self.label_selection_index == 0:
                            track.set_title(paste())
                            break
                        elif self.label_selection_index == 1:
                            track.set_artist(paste())
                            break
                        elif self.label_selection_index == 2:
                            track.set_album(paste())
                            break
                    elif event.key == pygame.K_d:
                        self.library.remove_track(self.track_selection_index)
                        if self.track_selection_index >= len(self.library.saved_tracks):
                            self.track_selection_index -= 1
                        self.selected_tracks = self.library.get_tracks(self.track_selection_index)
                        self.render_selected_tracks()
                        self.render_selected_track_data()
                        self.current_screen = Menu.TRACK_SELECT
                        return
                    elif event.key == pygame.K_s:
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
                        self.label_selection_index = min(2, self.label_selection_index + 1)
                        break
                    elif event.key == pygame.K_UP:
                        self.label_selection_index = max(0, self.label_selection_index - 1)
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

                self.screen.blit(self.generic_font.render(f'Title: {track.title}', True, Menu.SELECTED_COLOR if self.label_selection_index == 0 else Menu.WHITE), (10, 300))
                self.screen.blit(self.generic_font.render(f'Artist: {track.artist}', True, Menu.SELECTED_COLOR if self.label_selection_index == 1 else Menu.WHITE), (10, 375))
                self.screen.blit(self.generic_font.render(f'Album: {track.album}', True, Menu.SELECTED_COLOR if self.label_selection_index == 2 else Menu.WHITE), (10, 450))

                pygame.display.flip()

            self.clock.tick(30)

    def display_loop(self):
        while 1:
            if self.current_screen == Menu.TITLE:
                self.draw_menu()
            elif self.current_screen == Menu.TRACK_SELECT:
                self.draw_track_select()
            elif self.current_screen == Menu.NEW_TRACK:
                self.draw_new_track()
            elif self.current_screen == Menu.EDIT_TRACK:
                self.draw_edit_track()
            else:
                break

        self.close_menu()

    def play_track(self, track):
        game = Game(self.screen, self.width, self.height, self.clock, self.audio_player, track, self.enabled_layers_keys, self.preview_length, self.prune_unused_layers, self.latency)
        game.start_game()
        while game.restart:
            self.audio_player.idle.wait()
            game = Game(self.screen, self.width, self.height, self.clock, self.audio_player, track, self.enabled_layers_keys, self.preview_length, self.prune_unused_layers, self.latency)
            game.start_game()

        self.render_selected_track_data()

    def save_library(self):
        dump(self.library, open('library/saved.library', 'wb'))

    def close_menu(self):
        self.save_library()
        self.audio_player.idle.wait()
        self.audio_player.close()
