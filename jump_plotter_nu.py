#!/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import csv
import typing  # noqa
import asyncio
import zipfile
import configparser
import operator as op
import itertools as its
from array import array
import multiprocessing as mp

import matplotlib.pyplot as plt
import tui


async def load_file(file: str) -> dict:
    handle = open(file, 'r')
    reader = csv.DictReader(handle)
    reader = tuple(reader)
    handle.close()
    acc = {}
    for key in reader[0].keys():
        data = map(op.itemgetter(key), reader)
        data = map(lambda x: 'nan' if x == '' else x, data)
        data = map(float, data)
        data = array('d', data)
        acc[key] = data
    return acc


async def load_session_files(session: str) -> dict:
    config = configparser.ConfigParser()
    config.read('config.ini')
    session_dir = os.path.join(config['paths']['workdir'], session)
    filenames = os.listdir(session_dir)
    files = map(os.path.join,
                its.repeat(session_dir),
                filenames)
    data = [load_file(file) for file in files]
    data = await asyncio.gather(*data)
    data = zip(filenames, data)
    data = dict(data)
    return data


def diff(signal: array) -> array:
    A = signal[:-1]
    B = signal[1:]
    diff = map(op.sub, B, A)
    diff = array('d', diff)
    return diff


def locate_jumps_in_file(args: tuple) -> tuple[dict]:
    data, sensor_key = args
    try:
        time = memoryview(data[sensor_key]['Time(ms)'])
    except KeyError:
        breakpoint()
    time_diff = diff(time)
    time_diff_abs = map(abs, time_diff)
    is_jump = map(op.gt, time_diff_abs, its.repeat(10))
    jumps = its.compress(range(len(time)), is_jump)
    jumps = array('i', jumps)
    if not jumps:
        return None
    mags = op.itemgetter(*jumps)(time_diff)
    times = op.itemgetter(*jumps)(time)
    if not hasattr(mags, '__iter__'):
        mags = [mags]
        times = [times]
    mags = array('d', mags)
    times = array('d', times)
    try:
        iterable = zip(its.repeat(sensor_key), jumps, mags, times)
    except Exception:
        breakpoint()
    acc = []
    for foo in iterable:
        bar = {'session': data['instance'],
               'csv_path': foo[0],
               'jump_idx': foo[1],
               'jump_mag': foo[2],
               'jump_time': foo[3],
               'jump_key': '_'.join((str(foo[1]), foo[0]))
               }

        acc.append(bar)
    return acc


def opposite(mag: float, mag_next: float) -> bool:
    if op.gt(mag, 0):
        return op.lt(mag_next, 0)
    else:
        return op.gt(mag_next, 0)


def is_fwd(jump: dict) -> bool:
    return op.gt(float(jump['jump_mag']), 0)


def is_similar(mag: float, mag_next: float) -> bool:
    threshold = 0.50
    mag = op.abs(mag)
    mag_next = op.abs(mag_next)
    upper = op.mul(mag, op.add(1, threshold))
    lower = op.mul(mag, op.sub(1, threshold))
    A = op.lt(mag_next, upper)
    B = op.gt(mag_next, lower)
    return op.and_(A, B)


def detect_jump_types(iterable: tuple) -> tuple:
    acc = []
    enumerated = enumerate(iterable)
    for ii, jump in enumerated:
        if op.lt(ii + 1, len(iterable)):
            next_mag = float(iterable[ii + 1]['jump_mag'])
            mag = float(jump['jump_mag'])
            if opposite(mag, next_mag):
                if is_similar(mag, next_mag):
                    acc.append(1)
                    acc.append(2)
                    next(enumerated)
                else:
                    if is_fwd(jump):
                        acc.append(3)
                    else:
                        acc.append(4)
            else:
                if is_fwd(jump):
                    acc.append(3)
                else:
                    acc.append(4)
        else:
            if is_fwd(jump):
                acc.append(3)
            else:
                acc.append(4)
    proc = map(op.setitem, iterable, its.repeat('jump_bin'), acc)
    tuple(proc)
    return iterable


def resolve_events(data: dict) -> dict:
    event_file = filter(lambda x: 'event' in x or 'ECF' in x, data.keys())
    event_file = next(event_file, None)


    event_data = data[event_file]

    first_event_idx = enumerate(its.pairwise(event_data['Event']))
    first_event_idx = filter(lambda x: op.and_(op.ne(x[1][0], 8),
                                               op.eq(x[1][1], 8)),
                             first_event_idx)
    first_event_idx = next(first_event_idx)
    first_event_idx = first_event_idx[0]

    last_event_idx = reversed(event_data['Event'])
    last_event_idx = enumerate(its.pairwise(last_event_idx))
    last_event_idx = filter(lambda x: op.and_(op.eq(x[1][0], 8),
                                              op.ne(x[1][1], 8)),
                            last_event_idx)
    last_event_idx = next(last_event_idx)
    last_event_idx = last_event_idx[0]
    # -1 to account for 0 based indexing                       vvv
    last_event_idx = len(event_data['Event']) - last_event_idx - 1

    first_time = event_data['Sensor Time(ms)'][first_event_idx]
    last_time = event_data['Sensor Time(ms)'][last_event_idx]
    data['first_time'] = first_time
    data['last_time'] = last_time
    return data


def is_in_ev_window(data: dict, jump: dict) -> dict:
    A = op.gt(jump['jump_time'], data['first_time'])
    B = op.lt(jump['jump_time'], data['last_time'])
    in_ev_window = op.and_(A, B)
    jump['in_ev_window'] = in_ev_window
    return jump


def enumerate_jump(args: tuple) -> dict:
    ii, jump = args
    jump['jump_no'] = ii
    return jump


def locate_jumps_in_session(data: dict,
                            pool: mp.Pool,
                            debug: bool = False) -> dict:
    sensors = filter(lambda x: 'event' not in x, data.keys())
    sensors = filter(lambda x: 'ECF' not in x, sensors)
    sensors = filter(lambda x: 'csv' in x, sensors)
    sensors = tuple(sensors)
    args = zip(its.repeat(data), sensors)
    if debug:
        jumps = map(locate_jumps_in_file, args)
    else:
        jumps = pool.map(locate_jumps_in_file, args)
    jumps = filter(bool, jumps)
    jumps = map(detect_jump_types, jumps)
    jumps = its.chain.from_iterable(jumps)
    jumps = tuple(jumps)
    jumps = map(is_in_ev_window, its.repeat(data), jumps)
    jumps = map(enumerate_jump, enumerate(jumps))
    jumps = tuple(jumps)
    return jumps


def square(x: float) -> float:
    return pow(x, 2)


def sqrt(x: float) -> float:
    return pow(x, 1/2)


def calculate_mag(triaxial: tuple[array]) -> array:
    magnitude = zip(*triaxial)
    magnitude = map(map, its.repeat(square), magnitude)
    magnitude = map(sum, magnitude)
    magnitude = map(sqrt, magnitude)
    magnitude = array('d', magnitude)
    return magnitude


def calculate_jyl_per_instrument(sensor: dict,
                                 instrument: str) -> array:
    axes = filter(lambda x: instrument in x, sensor.keys())
    axes = tuple(axes)
    axes = op.itemgetter(*axes)(sensor)
    axes = map(memoryview, axes)
    magnitude = calculate_mag(axes)
    mag_diff = diff(magnitude)
    abs_diff = map(abs, mag_diff)
    abs_diff = its.chain([float('nan')], abs_diff)
    abs_diff = array('d', abs_diff)
    return abs_diff


def calculate_jyl_from_file(args: tuple) -> array:
    sensor, instruments = args
    diffs = map(calculate_jyl_per_instrument,
                its.repeat(sensor),
                instruments)
    jyl = map(sum, zip(*diffs))
    jyl = array('d', jyl)
    return jyl


def calculate_jyl_in_session(data: dict,
                             pool: mp.Pool,
                             debug: bool = False) -> dict:
    instruments = ('Vel', 'Acc',)
    sensor_keys = filter(lambda x: 'event' not in x, data.keys())
    sensor_keys = filter(lambda x: 'ECF' not in x, sensor_keys)
    sensor_keys = filter(lambda x: 'csv' in x, sensor_keys)
    sensor_keys = tuple(sensor_keys)
    sensors = op.itemgetter(*sensor_keys)(data)
    args = zip(sensors, its.repeat(instruments))
    if debug:
        jyls = map(calculate_jyl_from_file, args)
    else:
        jyls = pool.map(calculate_jyl_from_file, args)
    jyls = dict(zip(sensor_keys, jyls))
    return jyls


def scale_data_for_visual(stream: array, ii: int) -> array:
    stream = memoryview(stream)
    valid = map(op.eq, stream, stream)
    valid = its.compress(stream, valid)
    valid = array('d', valid)
    min_val = min(valid)
    max_val = max(valid)
    stream_range = max_val - min_val
    scaled = map(op.sub, stream, its.repeat(min_val))
    scaled = map(op.truediv, scaled, its.repeat(stream_range))
    scaled = map(op.add, scaled, its.repeat(ii))
    scaled = array('d', scaled)
    return scaled


def complicated_plot(args: dict) -> None:
    n_sensors = len(args['jyls'])
    sensor_keys = tuple(args['jyls'].keys())
    fig, axs = plt.subplots(3, sharex=True, figsize=(16, 9))
    for ii in range(n_sensors):
        sensor = sensor_keys[ii]
        time = args['data'][sensor]['Time(ms)']
        accl = filter(lambda x: 'Acc' in x, args['data'][sensor].keys())
        accl = filter(lambda x: args['axis'] in x, accl)
        accl = args['data'][sensor][next(accl)]
        accl = scale_data_for_visual(accl, ii)
        gyro = filter(lambda x: 'Velo' in x, args['data'][sensor].keys())
        gyro = filter(lambda x: args['axis'] in x, gyro)
        gyro = args['data'][sensor][next(gyro)]
        gyro = scale_data_for_visual(gyro, ii)
        scaled_jyl = scale_data_for_visual(args['jyls'][sensor], ii)
        axs[0].plot(time, accl, )
        axs[1].plot(time, gyro, )
        axs[2].plot(time, scaled_jyl, )
        for jump in filter(lambda x: sensor in x['csv_path'], args['jumps']):
            # 170 is the no of samples in a page               vvvv
            jump_loc = slice(jump['jump_idx'], jump['jump_idx']+170)
            jump_time = time[jump_loc]
            jump_accl = accl[jump_loc]
            jump_gyro = gyro[jump_loc]
            jump_jyl = scaled_jyl[jump_loc]
            for ii, stream in enumerate((jump_accl, jump_gyro, jump_jyl)):
                axs[ii].scatter(jump_time, stream, c='black')
                axs[ii].annotate(str(jump['jump_no']),
                                 xy=(jump_time[0], stream[0] + 0.25))
    for ii in range(3):
        axs[ii].axvspan(args['data']['first_time'],
                        args['data']['last_time'],
                        color='grey', alpha=1/3,
                        label='Data Collection Window')
    axs[0].set_title(' '.join([args['csv_path'], args['axis']+'-axis']))
    axs[0].set_ylabel('Accelerometers')
    axs[0].legend(loc='upper left')
    axs[1].set_ylabel('Gyroscopes')
    axs[2].set_ylabel('Diffs')
    axs[2].set_xlabel('Time(ms)')
    plt.show()
    return None


def test_for_default_kill(jumps: list) -> dict:
    groups = its.groupby(jumps, op.itemgetter('csv_path'))
    groups = tuple(groups)
    group_len = map(lambda x: len(list(x[1])), groups)
    is_kill = map(op.gt, group_len, its.repeat(9))  # 10 or more
    csv_paths = map(op.itemgetter(0), groups)
    kill_dict = dict(zip(csv_paths, is_kill))
    return kill_dict


def get_user_input(jump: dict,
                   stdscr: typing.Any = None) -> str:
    text = ['Press h for help or q to quit']
    text += ['Jump No. {}'.format(jump['jump_no'])]
    text += ['Jump magnitude: {:.2f} ms'.format(jump['jump_mag'])]
    text += ['Jump time: {:.2f} ms'.format(jump['jump_time'])]
    # text += 'Jump bin: {}\n'.format(jump['jump_bin'])
    if stdscr is None:
        tuple(map(print, text))
        user_input = input('Enter jump soln: ')
    else:
        text += ['Enter jump solution: ']
        tui.display_text(stdscr, text)
        # user_input = stdscr.getkey()
        user_input = tui.curses.getkey()
    return user_input


def plot_next_axis(plot_dict: dict) -> dict:
    plot_dict['proc'].terminate()
    plot_dict['proc'].join()
    plot_dict['args']['axis'] = next(plot_dict['axes'])
    plot_dict['proc'] = mp.Process(target=plot_dict['func'],
                                   args=(plot_dict['args'],))
    plot_dict['proc'].start()
    return plot_dict


def terminate_plot(plot_dict: dict) -> dict:
    plot_dict['proc'].terminate()
    plot_dict['proc'].join()
    return plot_dict


def get_annotation(jump: dict, kill_dict: dict, plot_dict: dict,
                   stdscr: typing.Any) -> dict:
    if kill_dict[jump['csv_path']]:
        jump['jump_soln'] = 'k'
        return jump
    elif jump['jump_bin'] == 1:
        jump['jump_soln'] = 'd'
        return jump
    elif jump['jump_bin'] == 2:
        jump['jump_soln'] = 'e'
        return jump
    elif (jump['jump_bin'] == 3) or (jump['jump_bin'] == 4):
        if not jump['in_ev_window']:
            jump['jump_soln'] = None
            return jump
        user_input = get_user_input(jump, stdscr)
        if user_input not in 'abcdekhnq':
            get_annotation(jump, kill_dict, plot_dict, stdscr)
        else:
            if user_input == 'k':
                jump['jump_soln'] = 'k'
                kill_dict[jump['csv_path']] = True
            elif user_input == 'n':
                plot_dict = plot_next_axis(plot_dict)
                tui.curses.endwin()
                stdscr = tui.init_screen()
                get_annotation(jump, kill_dict, plot_dict, stdscr)
            elif user_input == 'q':
                terminate_plot(plot_dict)
                tui.close_screen(stdscr)
                sys.exit(0)
            elif user_input == 'h':
                tui.help_screen(stdscr)
                get_annotation(jump, kill_dict, plot_dict, stdscr)
            else:
                jump['jump_soln'] = user_input
    else:
        raise ValueError('invalid jump_bin: {}'.format(jump['jump_bin']))
    return jump


def annotate_jump(jump_iter: iter, acc: list,
                  kill_dict: dict, plot_dict: dict,
                  stdscr=None) -> list:
    jump = next(jump_iter, None)
    if not jump:
        return acc
    else:
        acc.append(get_annotation(jump, kill_dict, plot_dict, stdscr))
        return annotate_jump(jump_iter, acc, kill_dict, plot_dict, stdscr)


def get_jump_annotations(jumps: tuple, plot_dict: dict, stdscr=None) -> tuple:
    kill_dict = test_for_default_kill(jumps)
    jump_iter = iter(jumps)
    jumps = annotate_jump(jump_iter, [], kill_dict, plot_dict, stdscr)
    return jumps


def show_plot_test(jumps: tuple) -> bool:

    A = map(op.itemgetter('jump_bin'), jumps)
    A = map(op.eq, A, its.repeat(1))

    B = map(op.itemgetter('jump_bin'), jumps)
    B = map(op.eq, B, its.repeat(2))

    test = map(op.or_, A, B)
    return not all(test)


def write_output(annotations: list) -> None:
    if not annotations:
        return None
    config = configparser.ConfigParser()
    config.read('config.ini')
    if not os.path.exists(config['paths']['output']):
        handle = open(config['paths']['output'], 'w')
        writer = csv.DictWriter(handle, fieldnames=annotations[0].keys())
        writer.writeheader()
        writer.writerows(annotations)
        handle.close()
    else:
        handle = open(config['paths']['output'], 'a')
        writer = csv.DictWriter(handle, fieldnames=annotations[0].keys())
        writer.writerows(annotations)
        handle.close()
    return None


def process(pool: mp.Pool, debug: bool, session: str) -> None:
    if debug:
        stdscr = None
    else:
        stdscr = tui.init_screen()
    text = ['Session {}:\n'.format(session)]
    text += tui.loading_session_text
    tui.display_text(stdscr, text)
    data = asyncio.run(load_session_files(session))
    data['instance'] = session
    text += tui.resolving_events_text
    tui.display_text(stdscr, text)
    data = resolve_events(data)
    text += tui.locating_jumps_text
    tui.display_text(stdscr, text)
    jumps = locate_jumps_in_session(data, pool, debug)
    text += tui.calculating_diffs_text
    tui.display_text(stdscr, text)
    jyls = calculate_jyl_in_session(data, pool, debug)
    show_plot = show_plot_test(jumps)
    tui.display_text(stdscr, text)
    axes = its.cycle(('X', 'Y', 'Z'))
    plot_dict = {'func': complicated_plot,
                 'args': {'data': data,
                          'jumps': jumps,
                          'jyls': jyls,
                          'axis': next(axes),
                          'csv_path': session},
                 'axes': axes,
                 'proc': None}
    if show_plot:
        text += tui.plotting_text
        tui.display_text(stdscr, text)
        proc = mp.Process(target=plot_dict['func'],
                          args=(plot_dict['args'],))
        proc.start()
        plot_dict['proc'] = proc
    annotations = get_jump_annotations(jumps, plot_dict, stdscr)
    write_output(annotations)
    if show_plot:
        plot_dict['proc'].terminate()
        plot_dict['proc'].join()
    if not debug:
        tui.clear_screen(stdscr)
        tui.close_screen(stdscr)
    return annotations


def unpack_data(config: configparser.ConfigParser,
                stdscr: typing.Any = None) -> None:
    if not os.path.isdir(config['paths']['workdir']):
        tui.display_text(stdscr, tui.unpacking_session_text)
        if not os.path.exists(config['paths']['input']):
            tui.display_text(stdscr, tui.no_input_text)
            tui.curses.getch()
            tui.close_screen(stdscr)
            sys.exit(1)
        handle = zipfile.ZipFile(config['paths']['input'], 'r')
        handle.extractall(config['paths']['workdir'])
        handle.close()
        tui.clear_screen(stdscr)
    return None


def get_work(config):
    sessions = os.listdir(config['paths']['workdir'])
    if os.path.exists(config['paths']['output']):
        handle = open(config['paths']['output'], 'r')
        reader = csv.DictReader(handle)
        completed = map(op.itemgetter('session'), reader)
        completed = set(completed)
        handle.close()
    else:
        completed = set()
    todo = sorted(set(sessions).difference(completed))
    return todo


def main():
    if '-d' in sys.argv:
        debug = True
        stdscr = None
    else:
        debug = False
        stdscr = tui.init_screen()
    tui.welcome_screen(stdscr)
    config = configparser.ConfigParser()
    config.read('config.ini')
    unpack_data(config, stdscr)
    todo = get_work(config)[:]
    if not todo:
        tui.display_text(stdscr, tui.no_sessions_text)
        tui.curses.getch()
        tui.close_screen(stdscr)
        sys.exit(0)
        return None
    tui.display_text(stdscr, tui.plotting_text)
    tui.close_screen(stdscr)
    pool = mp.Pool(mp.cpu_count())
    proc = map(process,
               its.repeat(pool),
               its.repeat(debug),
               todo)
    tuple(proc)
    pool.close()
    pool.join()
    stdscr = tui.init_screen()
    tui.display_text(stdscr, tui.thanks_text)
    tui.curses.getch()
    tui.close_screen(stdscr)
    return None



if __name__ == '__main__':
    main()
