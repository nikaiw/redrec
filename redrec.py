#!/usr/bin/env python3

import subprocess
import sys
import os
import shutil
from datetime import datetime
import fcntl
import termios
import tty
import sys

def get_operations_file():
    home_dir = os.path.expanduser("~")
    workspace_dir = os.path.join(home_dir, "workspace")
    os.makedirs(workspace_dir, exist_ok=True)
    return os.path.join(workspace_dir, "operations")

def read_operations():
    operations_file = get_operations_file()
    if os.path.exists(operations_file):
        with open(operations_file, "r") as f:
            fcntl.flock(f, fcntl.LOCK_SH)
            operations = f.read().splitlines()
            fcntl.flock(f, fcntl.LOCK_UN)
            return operations
    return []

def save_operation(operation_name):
    operations_file = get_operations_file()
    operations = read_operations()
    
    if operation_name not in operations:
        with open(operations_file, "a") as f:
            fcntl.flock(f, fcntl.LOCK_EX)
            f.write(f"{operation_name}\n")
            fcntl.flock(f, fcntl.LOCK_UN)

def run_with_asciinema(command, operation_name=None):
    if not shutil.which("asciinema"):
        sys.exit("Error: asciinema is not installed.")
    
    if operation_name is None:
        operation_name = read_operations()[-1] if read_operations() else "currentoperation"

    base_dir = "/home/user/workspace"
    target_dir = os.path.join(base_dir, operation_name)
    os.makedirs(target_dir, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    recording_file = os.path.join(target_dir, f"session_{timestamp}.cast")

    save_operation(operation_name)

    try:
        asciinema_command = ["asciinema", "rec", "-c", command, recording_file]
        result = subprocess.run(asciinema_command)
        if result.returncode != 0:
            sys.exit(f"Error: Command failed with return code {result.returncode}")
        else:
            print(f"Recording saved to {recording_file}")
    except Exception as e:
        sys.exit(f"An error occurred: {e}")

def print_usage():
    usage_text = """
    Usage: RedRec <command> [options]

    <command>        : The command to execute and record with asciinema.

    Options:
    [operation_name] : (Optional) The name of the operation. If not provided,
                       the script will use the last operation or default to "currentoperation".
    -s, --select     : Select a previous operation from a list.

    Examples:
    - To run with the last used or default operation:
      ./RedRec bash

    - To create and use a new operation:
      ./RedRec bash new_operation

    - To select a specific previous operation from a menu:
      ./RedRec bash -s
    """
    print(usage_text)

def getch():
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        ch = sys.stdin.read(1)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    return ch

def clear_previous_lines(num_lines):
    for _ in range(num_lines):
        sys.stdout.write("\033[F")  # Move cursor up one line
        sys.stdout.write("\033[K")  # Clear the line

def select_operation(operations):
    selected_index = 0
    num_operations = len(operations)

    print("Select an operation:")
    while True:
        clear_previous_lines(num_operations)

        for i, operation in enumerate(operations):
            if i == selected_index:
                print(f"> {operation}")
            else:
                print(f"  {operation}")

        key = getch()

        if key == "\x1b":  # Escape sequence
            key += getch() + getch()
            if key == "\x1b[A":  # Up arrow
                selected_index = (selected_index - 1) % num_operations
            elif key == "\x1b[B":  # Down arrow
                selected_index = (selected_index + 1) % num_operations
        elif key in ["\n", "\r"]:  # Enter key
            clear_previous_lines(num_operations + 1)
            return operations[selected_index]
        elif key == "\x03":  # Ctrl+C
            sys.exit(0)

def main():
    if len(sys.argv) < 2 or sys.argv[1] in ("-h", "--help"):
        print_usage()
        sys.exit(1)

    command = sys.argv[1]
    operation_name = None

    if len(sys.argv) > 2:
        if sys.argv[2] in ("-s", "--select"):
            operations = read_operations()
            if not operations:
                sys.exit("No previous operations found.")
            operation_name = select_operation(operations)
        else:
            operation_name = sys.argv[2]

    run_with_asciinema(command, operation_name)

if __name__ == "__main__":
    main()
