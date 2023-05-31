import subprocess
import sys

def run_and_read(cmd: str, inp: str) -> str:
    return subprocess.run(cmd,
        input = inp,
        stdout = subprocess.PIPE,
        stderr = subprocess.STDOUT,
        universal_newlines = True,
        timeout = 5
    ).stdout

def check_io(prog: str, i: list[str], o: list[str]) -> bool:
    o1 = list(map(lambda s: s.strip(), run_and_read(['python3', 'src/interpreter.py', 'run', prog], '\n'.join(i)).split()))
    if o1 == o:
        return True
    else:
        print(f'Expected: {o}, got: {o1}')
        return False

def main():
    tests = [
        ('test/abs.expr', ['101'], ['101']),
        ('test/abs.expr', ['0'], ['0']),
        ('test/abs.expr', ['-501'], ['501']),

        ('test/gcd.expr', ['100', '0'], ['100', 'Void']),
        ('test/gcd.expr', ['0', '100'], ['100', 'Void']),
        ('test/gcd.expr', ['30', '30'], ['30', 'Void']),
        ('test/gcd.expr', ['25', '45'], ['5', 'Void']),
        ('test/gcd.expr', ['7', '100'], ['1', 'Void']),

        ('test/mutual-recursion.expr', [], ['10', '9', '8', '7', '6', '5', '4', '3', '2', '1', '0', 'Void']),

        ('test/quicksort.expr', ['0'], ['Void']),
        ('test/quicksort.expr', ['1', '303'], ['303', 'Void']),
        ('test/quicksort.expr', ['3', '1', '3', '7'], ['1', '3', '7', 'Void']),
        ('test/quicksort.expr', ['5', '5', '4', '3', '2', '1'], ['1', '2', '3', '4', '5', 'Void']),
        ('test/quicksort.expr', ['6', '8', '-1', '3', '0', '6', '-5'], ['-5', '-1', '0', '3', '6', '8', 'Void']),

        ('test/lexical-scope.expr', [], ['1']),

        ('test/garbage-collection.expr', [], ['0', '2', '2', '1', '0', '2', '0', '3', 'Void']),

        ('test/continuation.expr', [], ['3', '2', '1', '1', '2', '3', '3', '2', '1', '300'])
    ]
    for test in tests:
        print('.')
        if not check_io(*test):
            sys.exit(f'Failed on test "{test}"')
    print('All tests passed')

if __name__ == '__main__':
    main()
