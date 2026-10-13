'''
This module provides various constants for text color and formatting. To preview a limited selection
of colors, run this script. Not all IDEs will display ANSI colors correctly.

Author: Lino Mercado_Esquivias
'''

# Cursor
RESET_TERMINAL  = "\033c"   # resets: terminal, cursor, scrollback, 
                            # colors, formatting, and more
CLEAR_TERMINAL  = "\033[3J\033[2J\033[H"
HIDE_CURSOR     = "\033[?25l"
RESTORE_CURSOR  = "\033[?25h"

# Style
RESET           = "\033[0m"
BOLD            = "\033[01m"
DISABLE         = "\033[02m"
UNDERLINE       = "\033[04m"
REVERSE         = "\033[07m"
INVISIBLE       = "\033[08m"
STRIKE_THROUGH  = "\033[09m"

# Text (foreground) color
BLACK           = "\033[30m"
RED             = "\033[31m"
GREEN           = "\033[32m"
ORANGE          = "\033[33m"
BLUE            = "\033[34m"
PURPLE          = "\033[35m"
CYAN            = "\033[36m"
LIGHT_GRAY      = "\033[37m"
DARK_GRAY       = "\033[90m"
LIGHT_RED       = "\033[91m"
LIGHT_GREEN     = "\033[92m"
YELLOW          = "\033[93m"
LIGHT_BLUE      = "\033[94m"
PINK            = "\033[95m"
LIGHT_CYAN      = "\033[96m"

# Background color
BLACK_BCKGND        = "\033[40m"
RED_BCKGND          = "\033[41m"
GREEN_BCKGND        = "\033[42m"
ORANGE_BCKGND       = "\033[43m"
BLUE_BCKGND         = "\033[44m"
PURPLE_BCKGND       = "\033[45m"
CYAN_BCKGND         = "\033[46m"
LIGHT_GRAY_BCKGND   = "\033[47m"

def main():
    # Print formatting options
    print(CLEAR_TERMINAL, end='')
    print(BOLD + LIGHT_RED + ORANGE_BCKGND + "FORMATTING OPTIONS:" + RESET)
    print(                    "NORMAL"                 )
    print(BOLD              + "BOLD"            + RESET)
    print(DISABLE           + "DISABLE"         + RESET)
    print(UNDERLINE         + "UNDERLINE"       + RESET)
    print(REVERSE           + "REVERSE"         + RESET)
    print(INVISIBLE         + "INVISIBLE"       + RESET + " <- INVISIBLE")
    print(STRIKE_THROUGH    + "STRIKE_THROUGH"  + RESET)
    print()

    # Print text color options
    print(BOLD + LIGHT_RED + ORANGE_BCKGND + "TEXT COLOR OPTIONS:" + RESET)
    print(BLACK       + "BLACK      " + RESET)
    print(LIGHT_GRAY  + "LIGHT_GRAY " + RESET)
    print(DARK_GRAY   + "DARK_GRAY  " + RESET)
    print(RED         + "RED        " + RESET)
    print(LIGHT_RED   + "LIGHT_RED  " + RESET)
    print(ORANGE      + "ORANGE     " + RESET)
    print(YELLOW      + "YELLOW     " + RESET)
    print(GREEN       + "GREEN      " + RESET)
    print(LIGHT_GREEN + "LIGHT_GREEN" + RESET)
    print(BLUE        + "BLUE       " + RESET)
    print(LIGHT_BLUE  + "LIGHT_BLUE " + RESET)
    print(CYAN        + "CYAN       " + RESET)
    print(LIGHT_CYAN  + "LIGHT_CYAN " + RESET)
    print(PURPLE      + "PURPLE     " + RESET)
    print(PINK        + "PINK       " + RESET)
    print()

    # Print background color options
    print(BOLD + LIGHT_RED + ORANGE_BCKGND + "BACKGROUND COLOR OPTIONS:" + RESET)
    print(RED_BCKGND        + "RED BACKGROUND"          + RESET)
    print(ORANGE_BCKGND     + "ORANGE BACKGROUND"       + RESET)
    print(GREEN_BCKGND      + "GREEN BACKGROUND"        + RESET)
    print(BLUE_BCKGND       + "BLUE BACKGROUND"         + RESET)
    print(CYAN_BCKGND       + "CYAN BACKGROUND"         + RESET)
    print(PURPLE_BCKGND     + "PURPLE BACKGROUND"       + RESET)
    print(BLACK_BCKGND      + "BLACK BACKGROUND"        + RESET)
    print(LIGHT_GRAY_BCKGND + "LIGHT_GRAY BACKGROUND"   + RESET)

if __name__ == "__main__":
    main()