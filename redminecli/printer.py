import termcolor

banner = lambda x : termcolor.cprint(x, "cyan")
debug = lambda x: termcolor.cprint(x, "white")
info = lambda x: termcolor.cprint(x, "white")
title = lambda x: termcolor.cprint(x, "blue", "on_white")
warning = lambda x: termcolor.cprint(x, "magenta")
error = lambda x: termcolor.cprint(x, "red")
fatal = lambda x: termcolor.cprint(x, "red", "on_white")
success = lambda x: termcolor.cprint(x, "green")
