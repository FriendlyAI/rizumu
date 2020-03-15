ALL_LAYERS = ('A', 'B', 'C', 'D', 'E', 'F')


def seconds_to_readable_time(seconds):
    seconds = seconds if seconds > 0 else 0
    return f'{int(seconds // 60)}:{seconds % 60:04.1f}'
