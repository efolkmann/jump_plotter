#!/bin/env python

import os
import sys
import configparser
import itertools as its
import operator as op
import random
import csv
import json
import curses
import multiprocessing as mp


from complicated_plot import plot_files
import loaders as ldrs
import tui


def get_session(jump_data):
    iterable = its.groupby(jump_data, op.itemgetter('instance'))
    for instance, jump_records in iterable:
        jump_records = list(jump_records)
        yield instance, jump_records


def iterate_axes():
    axes = ('X', 'Y', 'Z')
    for axis in its.cycle(axes):
        yield axis


def check_for_jumps(file, jump_record):
    return op.contains(file, jump_record['csv_path'])


def is_event(pair):
    A = op.ne(pair[0]['Event'], '8')
    B = op.eq(pair[1]['Event'], '8')
    return op.and_(A, B)


def make_jump_text(ii, jump_record):
    keus = ('Jump:', 'Bin:', 'Mag:')
    line = (ii, jump_record['jump_bin'], jump_record['jump_mag'])
    line = zip(keus, line)
    line = its.chain.from_iterable(line)
    line = map(str, line)
    line = ' '.join(line)
    return line


def user_input_func(screen, jump_record, text, ii):
    if screen:
        tui.clear_screen(screen)
        tui.display_text(screen, text)
        user_input = tui.get_jump_soln(screen, jump_record['jump_bin'])
        tui.clear_screen(screen)
    else:
        print('Bin: ' + str(jump_record['jump_bin']))
        print('Jump: ' + str(ii))
        user_input = input("Enter annotation: ")
    return user_input


def check_user_input(user_input):
    if user_input:
        test = user_input in 'Aabcdehknq#'
        return test
    else:
        return False


def jump_annotated(user_input):
    if user_input:
        return user_input in 'Aabcdek'
    else:
        return False


def next_axis_selected(user_input):
    return user_input in 'n'


def _quit(user_input):
    return user_input in 'q'


def _help(user_input):
    return user_input in 'h'

def _breakpoint(user_input):
    return user_input in '#'


def init_instance(screen, jump_data):
    config = configparser.ConfigParser()
    config.read('plot.conf')
    # display some text to the user
    # clear the screen
    output_path = config['paths']['output']
    for instance, session in get_session(jump_data):
        if screen:
            tui.clear_screen(screen)
        text = ["Please be patient, the plotter is loading...",
                "Press h for help",
                "",
                f"Instance: {instance}",
                f"Number of jumps: {len(session)}",]
        if screen:
            tui.display_text(screen, text)
        file_set = set()
        for ii, file in enumerate(session):
            filename = os.path.basename(file['csv_path'])
            if filename not in file_set:
                file_set.add(filename)
        text.append(f"Files with time jump discontinuities: {len(file_set)}")
        if screen:
            tui.clear_screen(screen)
            tui.display_text(screen, text)

            text.append("Loading Sensor Files...")
            tui.clear_screen(screen)
            tui.display_text(screen, text)
            tui.clear_screen(screen)
        # Find files related to this jump record
        files = ldrs.find_files(instance)

        # Load the associated data
        data = ldrs.load_data(files)

        text.append("Locating ECF...")
        ecf = ldrs.load_ecf(instance)
        if screen:
            tui.clear_screen(screen)
            tui.display_text(screen, text)

            text.append("Plotting...")
            tui.clear_screen(screen)
            tui.display_text(screen, text)
        else:
            for tt in text:
                print(tt)
        acc_dict = {}
        acc_dict['text'] = text
        acc_dict['data'] = data
        acc_dict['ecf'] = ecf
        acc_dict['files'] = files
        acc_dict['session'] = session
        yield acc_dict


def make_default_kill_dict(session):
    acc = {}
    for filename, jumps in its.groupby(session, key=lambda x: x['csv_path']):
        jumps = map(op.itemgetter('in_ev_window'), jumps)
        jumps = map(op.eq, its.repeat('t'), jumps)
        jumps = filter(bool, jumps)
        acc[filename] = len(tuple(jumps)) > 9
    return acc


def save_output(output_rows):
    return None

def crank_handle(screen, jump_data):
    instance_dict = next(init_instance(screen, jump_data), None)
    if not instance_dict:
        return None
    text = instance_dict['text']
    data = instance_dict['data']
    ecf = instance_dict['ecf']
    files = instance_dict['files']
    session = instance_dict['session']
    default_kill_dict = make_default_kill_dict(session)
    all_register = False
    user_input = None
    kill_register = False
    exit_register = False
    kill_file = ''
    output_rows = []
    for ii, jump_record in enumerate(session):
        if exit_register:
            break
        axis_register = False
        jump_register = False
        if len(text) > 10:
            end = text[-2:]
            text = text[:7] + end
        text.append(make_jump_text(ii, jump_record))
        output_row = jump_record
        if all_register and 'user_input' in locals():
            output_row['jump_soln'] = user_input
            output_rows.append(output_row)
            continue
        for axis in iterate_axes():
            break_registers = (exit_register, axis_register, all_register)
            if any(break_registers):
                break
            args = (data, files, ecf, session, axis)
            if screen:
                if 'proc' not in locals():
                    proc = mp.Process(target=plot_files, args=args)
            else:
                pass
                plot_files(*args)
            if jump_register:
                output_rows.append(output_row)
                break
            if screen:
                if not proc.is_alive():
                    proc.start()
            while True:
                if exit_register:
                    break
                user_input = None
                # Get user input
                #
                # First, check the kill register. If it's not set,
                # get user input
                if not kill_register:
                    # Check if this file has > 9 jumps, if so set
                    # to kill
                    if default_kill_dict[jump_record['csv_path']]:
                        user_input = 'k'
                    else:
                        # When fewer than 10 jumps, check if th current
                        # jump  is a paired jump and set default solutions
                        if jump_record['jump_bin'] == '1':
                            user_input = 'd'
                        elif jump_record['jump_bin'] == '2':
                            user_input = 'e'
                        # Otherwise, get user input
                        else:
                            user_input = user_input_func(screen,
                                                         jump_record,
                                                         text,
                                                         ii)
                            if not check_user_input(user_input):
                                if screen:
                                    curses.flash()
                                continue
                # When the kill-register is set
                else:
                    # Check if the kill-file is set to the current file
                    if kill_file == jump_record['csv_path']:
                        user_input = 'k'
                    # If the kill-file is not the current file, reset
                    # the kill register and get user input
                    else:
                        kill_register = False
                        kill_file = ''
                        user_input = user_input_func(screen, jump_record,
                                                     text, ii)
                        if not check_user_input(user_input):
                            curses.flash()
                            continue
                # Use user-input
                #
                # This code only executes if a jump_annotations was
                # entered above.
                if jump_annotated(user_input):
                    jump_record['jump_soln'] = user_input
                    jump_register = True
                    if user_input == 'A':
                        user_input = user_input.lower()
                        all_register = True
                    text.append(f"Solution: {user_input}")
                    output_row['jump_soln'] = user_input
                    output_rows.append(output_row)
                    if screen:
                        tui.display_text(screen, text)
                    else:
                        for tt in text:
                            print(tt)
                    if not kill_register:
                        if user_input == 'k':
                            kill_file = jump_record['csv_path']
                            kill_register = True
                    break
                if _help(user_input):
                    tui.help_screen(screen)
                    tui.clear_screen(screen)
                    tui.display_text(screen, text)
                    continue
                if next_axis_selected(user_input):
                    if screen:
                        proc.terminate()
                        proc.join()
                        del proc
                    break
                if _breakpoint(user_input):
                    if screen:
                        proc.terminate()
                        proc.join()
                        del proc
                    else:
                        breakpoint()
                if _quit(user_input):
                    if screen:
                        if proc.is_alive() or 'proc' in locals():
                            proc.terminate()
                            proc.join()
                            del proc
                        curses.endwin()
                    exit_register = True
                    break
#                    output_handle.close()

    if screen:
        if 'proc' in locals():
            if proc.is_alive():
                proc.terminate()
                proc.join()
                del proc

    if screen:
        curses.endwin()
    config = configparser.ConfigParser()
    config.read('./plot.conf')
    output_path = config['paths']['output']
    writer_keys = ('jump_key', 'csv_path', 'instance', 'in_ev_window',
                       'jump_time', 'jump_idx', 'jump_mag', 'jump_bin',
                       'jump_soln',)
    if os.path.getsize(output_path) > 0:
        output_handle = open(output_path, 'a')
    else:
        output_handle = open(output_path, 'w')
        output_writer = csv.DictWriter(output_handle, writer_keys)
        output_writer.writeheader()

    unique_output = set([json.dumps(x) for x in output_rows])
    output_rows = [json.loads(x) for x in unique_output]
    output_writer = csv.DictWriter(output_handle, writer_keys)
    output_writer.writerows(output_rows)

    output_handle.flush()
    output_handle.close()
    return exit_register


def main():
    config = configparser.ConfigParser()
    config.read('./plot.conf')

    debug = False
    instance = None
    exit_register = False

    for arg in sys.argv[1:]:
        if arg == "-d":
            debug = True
        elif arg.startswith("-i"):
            instance = arg[2:]
        else:
            print("Invalid flag: " + arg)
    if debug:
        screen = None
    else:
        screen = tui.curses_init()
        welcome_text = ["Welcome to the Jump Plotter!",
                        "Press any key to continue..."]
        tui.clear_screen(screen)
        tui.display_text(screen, welcome_text)

        # wait for the user to press a key
        screen.getch()
        curses.endwin()
    while True:
        # ldrs.get_work is hard-coded to select 3M jumps
        jump_data = ldrs.load_jumps(config)
        jump_data = ldrs.get_work(config, jump_data)
        if len(jump_data) == 0:
            print("No work left, thanks!")
            return None
        jump_data = ldrs.select_one(jump_data)
        if debug:
            screen = None
        else:
            screen = tui.curses_init()
        exit_register = crank_handle(screen, jump_data)
        if screen:
            curses.endwin()
        if exit_register:
            return None
    return None


if __name__ == '__main__':
    main()
