import pyperclip


def msec_to_timestr(x):
    sec = x / 1000
    hours = sec // 3600
    remain = sec - (hours*3600)
    minutes = remain // 60
    seconds = remain - (minutes * 60)
    return f'{int(hours)}:{int(minutes):02}:{int(seconds):02}'


def copy_to_clipboard(msec):
    # pyperclip.copy(msec_to_timestr(msec))
    pyperclip.copy(f"{msec:.0f}")
