#!/bin/env python

import curses


def curses_init():
    # initialize curses
    screen = curses.initscr()

    # turn off echoing of keys
    curses.noecho()
    curses.raw()
    curses.cbreak()

    # enable keypad mode
    screen.keypad(True)

    # clear the screen
    screen.erase()
    return screen


# define a function to display text to the user
def display_text(screen, text):
    # get the height and width of the screen
    height, width = screen.getmaxyx()

    # calculate the center of the screen
    center_y = int(height / 3)

    # calculate the starting position for the text
    start_y = center_y - int(len(text) / 2)
    start_x = 0

    # loop through each line of text and display it on the screen
    for i, line in enumerate(text):
        try:
            screen.addstr(start_y + i, start_x, line)
        except:
            pass

    # refresh the screen to display the changes
    screen.refresh()


def help_screen(screen):
    help_text = ["A: All remaining jumps are hardware failures",
                 "a: Hardware Failure",
                 # "b: Translate time proceeding jump backwards.",
                 "b: Trust the time vector before the jump",
                 # "c: Translate time preceeding jump forward.",
                 "c: Trust the time vector after the jump.",
                 "d: Double jump: equal and opposite",
                 "h: Help (this screen)",
                 "k: Kill the sensor file (Any k will kill whole file)",
                 'n: Plot the next axis (X, Y, or Z)',
                 "q: Quit",
                 "Press any key to continue..."]
    clear_screen(screen)
    display_text(screen, help_text)
    screen.getch()


def get_jump_soln(screen, bin_no):
    # get the height and width of the screen
    height, width = screen.getmaxyx()

    # calculate the center of the screen
    center_y = int(height / 2)
    if bin_no == '3':
        default_solution = "a"
    elif bin_no == '4':
        default_solution = ""
    elif bin_no == '2':
        default_solution = "d"
    else:
        default_solution = ""
    text = [f"Enter solution [{default_solution}]: "]
    # calculate the starting position for the input
    start_y = center_y + 10
    # start_x = center_x - 10
    start_x = 0

    # display a prompt for the user to enter input
    screen.addstr(start_y, start_x, text[0])

    # get the input from the user
    # curses.flushinp()
    user_input = screen.getch(start_y, start_x + 19)
    curses.flushinp()
    user_input = chr(user_input)

    screen.refresh()

    screen.erase()
    if user_input == '\n':
        return default_solution
    return user_input


#def get_input(screen):
#    # get the height and width of the screen
#    height, width = screen.getmaxyx()
#
#    # calculate the center of the screen
#    center_y = int(height / 2)
#    text = ["Enter your input: "]
#    # calculate the starting position for the input
#    start_y = center_y + 10
#    # start_x = center_x - 10
#    start_x = 0
#
#    # display a prompt for the user to enter input
#    screen.addstr(start_y, start_x, text[0])
#
#    # get the input from the user
#    user_input = screen.getstr(start_y, start_x + 17)
#
#    # return the input
#    return user_input
#
#
def clear_screen(screen):
    screen.erase()
    screen.refresh()
