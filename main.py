#!/bin/env python

import os
import sys
import configparser
import itertools as its
import operator as op
import random
import csv
import curses
import multiprocessing as mp


from complicated_plot import plot_files
import loaders as ldrs
import tui


def get_session(jump_data):
    iterable = its.groupby(jump_data, op.itemgetter('instance'))
    for instance, jump_records in iterable:
        jump_records = list(jump_records)
        bin_nos = map(op.itemgetter('bin'), jump_records)
        bin_nos = map(op.eq, bin_nos, its.repeat('2'))
        if all(bin_nos):
            continue
        yield instance, jump_records


def iterate_axes():
    axes = ('X', 'Y', 'Z')
    for axis in its.cycle(axes):
        yield axis


def check_for_jumps(file, jump_record):
    return op.contains(file, jump_record['file'])


def is_event(pair):
    A = op.ne(pair[0]['Event'], '8')
    B = op.eq(pair[1]['Event'], '8')
    return op.and_(A, B)


def make_jump_text(ii, jump_record):
    keus = ('Jump:', 'Bin:', 'Mag:')
    line = (ii, jump_record['bin'], jump_record['mag'])
    line = zip(keus, line)
    line = its.chain.from_iterable(line)
    line = map(str, line)
    line = ' '.join(line)
    return line


def user_input_func(screen, jump_record, text):
    if screen:
        tui.clear_screen(screen)
        tui.display_text(screen, text)
        user_input = tui.get_jump_soln(screen, jump_record['bin'])
        tui.clear_screen(screen)
    else:
        user_input = input("Enter annotation: ")
    return user_input


def check_user_input(user_input):
    test = user_input in 'Aabcdhknq'
    return test


def jump_annotated(user_input):
    return user_input in 'Aabcdk'


def next_axis_selected(user_input):
    return user_input in 'n'


def _quit(user_input):
    return user_input in 'q'


def _help(user_input):
    return user_input in 'h'


def init_instance(screen, jump_data):
    config = configparser.ConfigParser()
    config.read('plot.conf')
    # display some text to the user
    welcome_text = ["Welcome to the Jump Plotter!",
                    "Press any key to continue..."]
    if screen:
        tui.clear_screen(screen)
        tui.display_text(screen, welcome_text)

        # wait for the user to press a key
        screen.getch()

    # clear the screen
    output_path = config['paths']['output']
    if os.path.exists(output_path):
        output_handle = open(output_path, 'r+')
        output_reader = csv.DictReader(output_handle)
        output = tuple(output_reader)
    else:
        output_handle = open(output_path, 'w')
        output = ()
    for instance, session in get_session(jump_data):
        if not output:
            writer_keys = list(session[0].keys())
            writer_keys.append('solution')
            output_writer = csv.DictWriter(output_handle, writer_keys)
            if output_handle.tell() == 0:
                output_writer.writeheader()
        else:
            writer_keys = list(output[0].keys())
            output_writer = csv.DictWriter(output_handle, writer_keys)
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
            filename = os.path.basename(file['file'])
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
        acc_dict['output_writer'] = output_writer
        acc_dict['output_handle'] = output_handle
        yield acc_dict


def crank_handle(screen, jump_data):
    for instance_dict in init_instance(screen, jump_data):
        text = instance_dict['text']
        data = instance_dict['data']
        ecf = instance_dict['ecf']
        files = instance_dict['files']
        session = instance_dict['session']
        output_writer = instance_dict['output_writer']
        output_handle = instance_dict['output_handle']
        all_register = False
        user_input = None
        kill_register = False
        kill_file = ''
        for ii, jump_record in enumerate(session):
            axis_register = False
            jump_register = False
            text.append(make_jump_text(ii, jump_record))
            output_row = jump_record
            if all_register and 'user_input' in locals():
                output_row['solution'] = user_input
                output_writer.writerow(output_row)
                output_handle.flush()
                continue
            for axis in iterate_axes():
                args = (data, files, ecf, session, axis)
                if screen:
                    if 'proc' not in locals():
                        proc = mp.Process(target=plot_files, args=args)
                else:
                    plot_files(*args)
                if jump_register:
                    output_writer.writerow(output_row)
                    output_handle.flush()
                    break
                if all_register:
                    break
                if screen:
                    if not proc.is_alive():
                        proc.start()
                while True:
                    user_input = None
                    if not kill_register:
                        user_input = user_input_func(screen, jump_record, text)
                        if not check_user_input(user_input):
                            curses.flash()
                            continue
                    else:
                        if kill_file == jump_record['file']:
                            user_input = 'k'
                        else:
                            kill_register = False
                            kill_file = ''
                            user_input = user_input_func(screen, jump_record, text)
                            if not check_user_input(user_input):
                                curses.flash()
                                continue
                    if jump_annotated(user_input):
                        jump_record['solution'] = user_input
                        jump_register = True
                        if user_input == 'A':
                            user_input = user_input.lower()
                            all_register = True
                        text.append(f"Solution: {user_input}")
                        output_row['solution'] = user_input
                        tui.display_text(screen, text)
                        if not kill_register:
                            if user_input == 'k':
                                kill_file = jump_record['file']
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
                    if _quit(user_input):
                        if screen:
                            proc.terminate()
                            proc.join()
                            curses.endwin()
                        output_handle.close()
                        return None
        if screen:
            if proc.is_alive() or 'proc' in locals():
                proc.terminate()
                proc.join()
                del proc

    if screen:
        curses.endwin()
    output_handle.close()
    return 'Zero'


def main():
    config = configparser.ConfigParser()
    config.read('./plot.conf')

    debug = False
    instance = None

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
    while True:
#        jump_data = ldrs.get_work(config)
#        jump_data = list(jump_data)
#
#        A = random.randint(0, len(jump_data))
#        B = random.randint(A, len(jump_data))
#        jump_data = jump_data[A:B]
#        first = jump_data[0]['instance']
#        jump_data = filter(lambda x: x['instance'] != first, jump_data)
#        jump_data = tuple(jump_data)
        jump_data = ldrs.interrater_validation(config)
        if not jump_data:
            continue
        flop = crank_handle(screen, jump_data)
        if not flop:
            break

    return None


if __name__ == '__main__':
    main()
