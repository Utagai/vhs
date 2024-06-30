import os
import re
import subprocess
import sys
from shutil import move
from colorama import init, Fore, Style
import argparse
import shutil

init(autoreset=True)

def ensure_directory_exists(directory):
    if not os.path.exists(directory):
        os.makedirs(directory)

def sanitize_filename(filename):
    return "".join(c if c.isalnum() or c in (' ', '.', '_') else "_" for c in filename)

def move_output_files(tape_name):
    output_files = ['output.mp4', 'output.gif']
    ensure_directory_exists('test_out')

    sanitized_name = sanitize_filename(tape_name)

    for output_file in output_files:
        if os.path.exists(output_file):
            new_name = f'test_out/{sanitized_name}.{output_file.split(".")[-1]}'
            move(output_file, new_name)

def build_vhs():
    print(f'{Fore.YELLOW}Building vhs...')
    try:
        result = subprocess.run(['go', 'build'], capture_output=True, text=True)
        if result.returncode != 0:
            print(f'{Fore.RED}Error: vhs failed to build.')
            print(result.stderr)
            return False
        else:
            print(f'{Fore.GREEN}vhs built successfully.')
            return True
    except Exception as e:
        print(f'{Fore.RED}Error running go build: {e}')
        return False

def run_test(tape_path):
    print(f'{Fore.CYAN}Running: {tape_path}')
    if os.path.exists(tape_path):
        try:
            process = subprocess.Popen(['./vhs', tape_path], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            for line in iter(process.stdout.readline, ''):
                print(line, end=Fore.GREEN)

            process.stdout.close()
            process.wait()
            if process.returncode != 0:
                print(f'{Fore.RED}Errors:')
                for line in iter(process.stderr.readline, ''):
                    print(line, end=Fore.RED)

            process.stderr.close()

            tape_name = os.path.splitext(os.path.basename(tape_path))[0]
            move_output_files(tape_name)
        except Exception as e:
            print(f'{Fore.RED}Error running vhs on {tape_path}: {e}')
    else:
        print(f'{Fore.RED}Error: {tape_path} does not exist')

def get_test_cases():
    test_dir = 'tests'
    return [os.path.join(test_dir, f) for f in os.listdir(test_dir) if f.endswith('.tape')]

def filter_test_cases(test_cases, regex):
    pattern = re.compile(regex)
    return [case for case in test_cases if pattern.match(os.path.splitext(os.path.basename(case))[0])]

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Run e2e tests.')
    parser.add_argument('--run', type=str, help='Regex pattern to match test cases to run', required=False)
    args = parser.parse_args()

    for root, dirs, files in os.walk('test_out'):
        for file in files:
            os.remove(os.path.join(root, file))
        for dir in dirs:
            shutil.rmtree(os.path.join(root, dir))

    if build_vhs():
        test_cases = get_test_cases()
        if args.run:
            cases_to_run = filter_test_cases(test_cases, args.run)
        else:
            cases_to_run = test_cases

        for case in cases_to_run:
            run_test(case)