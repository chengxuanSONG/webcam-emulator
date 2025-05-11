import os
import sys

# Toggle to True to suppress all C/C++ level stderr output (e.g., OpenCV internal errors)
SUPPRESS_STDERR = False

if SUPPRESS_STDERR:
    def suppress_c_stderr():
        if os.name == 'nt':
            devnull = 'nul'
        else:
            devnull = '/dev/null'
        sys.stderr.flush()
        f = open(devnull, 'w')
        os.dup2(f.fileno(), sys.stderr.fileno())
    suppress_c_stderr()

from ui.main_window import launch_app

if __name__ == '__main__':
    launch_app()