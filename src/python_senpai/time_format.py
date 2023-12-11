import pyperclip
import pandas as pd


def msec_to_timestr(x):
    sec = x / 1000
    hours = sec // 3600
    remain = sec - (hours*3600)
    minutes = remain // 60
    seconds = remain - (minutes * 60)
    return f'{int(hours)}:{int(minutes):02}:{int(seconds):02}'


def msec_to_timestr_with_fff(x):
    sec = x / 1000
    hours = sec // 3600
    remain = sec - (hours*3600)
    minutes = remain // 60
    seconds = remain - (minutes * 60)
    fff = x % 1000
    return f'{int(hours)}:{int(minutes):02}:{int(seconds):02}.{int(fff):03}'


def timedelta_to_str(td):
    hours = td.seconds // 3600
    remain = td.seconds - (hours*3600)
    minutes = remain // 60
    seconds = remain - (minutes * 60)
    fff = td.microseconds // 1000
    return f'{int(hours)}:{int(minutes):02}:{int(seconds):02}.{int(fff):03}'


def copy_to_clipboard(msec):
    pyperclip.copy(msec_to_timestr_with_fff(msec))


def timestr_to_msec(timestr):
    timedelta = pd.to_timedelta(timestr)
    sec = timedelta.total_seconds()
    return sec * 1000
