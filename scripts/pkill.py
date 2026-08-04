#!/usr/bin/env python3

import sys
import os
import signal

def main():
    args = sys.argv[1:]
    sig = signal.SIGTERM
    exact = False
    full = False
    pattern = None

    # Parse arguments
    idx = 0
    while idx < len(args):
        arg = args[idx]
        if arg == '--':
            if idx + 1 < len(args):
                pattern = args[idx + 1]
            break
        elif arg.startswith('-') and arg[1:].isdigit():
            sig = int(arg[1:])
        elif arg == '-x':
            exact = True
        elif arg == '-f':
            full = True
        elif not arg.startswith('-'):
            pattern = arg
            break
        idx += 1

    if not pattern:
        sys.exit(1)

    my_pid = os.getpid()
    killed_any = False

    # Iterate through all process directories in /proc
    for pid_str in os.listdir('/proc'):
        if not pid_str.isdigit():
            continue
            
        pid = int(pid_str)
        if pid == my_pid:
            continue

        try:
            if full:
                # -f: Match against the full command line
                with open(f'/proc/{pid}/cmdline', 'r') as f:
                    cmd_parts = [x for x in f.read().split('\x00') if x]
                    full_cmd = " ".join(cmd_parts)
                
                if pattern in full_cmd:
                    os.kill(pid, sig)
                    killed_any = True
            else:
                # Default/-x: Match against the process name (15-char limit in Linux)
                proc_name = ""
                with open(f'/proc/{pid}/status', 'r') as f:
                    for line in f:
                        if line.startswith('Name:'):
                            proc_name = line.split(':', 1)[1].strip()
                            break
                            
                if exact:
                    if proc_name == pattern:
                        os.kill(pid, sig)
                        killed_any = True
                else:
                    if pattern in proc_name:
                        os.kill(pid, sig)
                        killed_any = True
        except (FileNotFoundError, ProcessLookupError, PermissionError):
            # Process died while we were inspecting it, or we lack permissions
            continue

    # Standard pkill behavior
    sys.exit(0 if killed_any else 1)

if __name__ == '__main__':
    main()
