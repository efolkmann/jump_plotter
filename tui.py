#!/bin/env python

import sys
import unicurses as curses

welcome_text = ["Welcome to Jump Plotter", "Press any key to continue..."]
no_sessions_text = ["No Sessions without annotations found",
                    "Press any key to exit..."]
unpacking_session_text = ["Unpacking Session", "Please be patient..."]
no_input_text= ["No Data Found",
                "Please copy the zipfile to jump_plotter_nu/ directory",
                "Press any key to exit..."]
loading_session_text = ["Loading Session Files...", ]
locating_jumps_text = ["Locating Jumps...", ]
calculating_diffs_text = ["Calculating Differences...", ]
resolving_events_text = ["Resolving Events...", ]
plotting_text = ["Plotting...", ]
help_text = ["a: Hardware Failure -- Synchronized before AND after jump",
             "b: Trust the time vector before the jump",
             "c: Trust the time vector after the jump.",
             "d: Double jump: equal and opposite -- first of two",
             "e: Double jump: equal and opposite -- second of two",
             "h: Help (this screen)",
             "k: Kill the sensor file (Any k will kill whole file)",
             'n: Plot the next axis (X, Y, or Z)',
             "q: Quit",
             "Press any key to continue..."]
thanks_text = ["Thanks for using Jump Plotter", "Press any key to exit..."]


def init_screen():
    stdscr = curses.initscr()
    curses.noecho()
    curses.cbreak()
    curses.clear()
    curses.keypad(stdscr, 1)
    return stdscr


def close_screen(stdscr):
    if stdscr:
        curses.echo()
        curses.nocbreak()
        curses.keypad(stdscr, 0)
        curses.clear()
        curses.endwin()
    return None

def thanks_and_exit(stdscr):
    clear_screen(stdscr)
    display_text(stdscr, thanks_text)
    # stdscr.getch()
    curses.getch()
    close_screen(stdscr)
    sys.exit()



def welcome_screen(stdscr):
    if stdscr:
        display_text(stdscr, welcome_text)
        curses.getch()

        clear_screen(stdscr)
    else:
        tuple(map(print, welcome_text))
    return None


def display_text(stdscr, text):
    if stdscr:
        # stdscr.clear()
        curses.clear()
        # height, width = stdscr.getmaxyx()
        height, width = curses.getmaxyx(stdscr)
        center_y = int(height / 3)
        start_y = center_y - int(len(text) / 2)
        start_x = 0
        for i, line in enumerate(text):
            try:
                # stdscr.addstr(start_y + i, start_x, line)
                curses.mvaddstr(start_y + i, start_x, line)
            except Exception as e:
                close_screen(stdscr)
                print(e)
                sys.exit()
        # stdscr.refresh()
        curses.refresh()
    else:
        tuple(map(print, text))


def help_screen(stdscr):
    clear_screen(stdscr)
    display_text(stdscr, help_text)
    # stdscr.getch()
    curses.getch()


def clear_screen(stdscr):
    # stdscr.erase()
    # stdscr.refresh()
    curses.erase()
    curses.refresh()
