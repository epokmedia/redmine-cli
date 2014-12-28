__author__ = 'zhu'

import atexit
import os
import readline

historyPath = None

def save_history():
    readline.write_history_file(historyPath)


def register(path):
    global historyPath
    historyPath = path
    if os.path.exists(historyPath):
        readline.read_history_file(historyPath)
    readline.set_history_length(100)
    atexit.register(save_history)