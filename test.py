import subprocess
import sys

def run_and_read(cmd: str, inp: str) -> str:
    return subprocess.run(cmd,
        input = inp,
        stdout = subprocess.PIPE,
        universal_newlines = True,
        timeout = 60
    ).stdout

def check_io(prog: str, i: list[str], o: list[str]) -> bool:
    try:
        raw_o1 = run_and_read(['python3', 'src/interpreter.py', 'time', prog], '\n'.join(i))
    except TimeoutExpired:
        sys.stderr.write('Timeout expired on time mode\n')
        return False
    try:
        raw_o2 = run_and_read(['python3', 'src/interpreter.py', 'space', prog], '\n'.join(i))
    except TimeoutExpired:
        sys.stderr.write('Timeout expired on space mode\n')
        return False
    if raw_o1 != raw_o2:
        sys.stderr.write('Time mode and space mode give different outputs.\n')
        return False
    else:
        o1 = raw_o1.splitlines()
        if o1 != o:
            sys.stderr.write(f'Expected: {o}, Got: {o1}\n')
            return False
        else:
            return True

def main():
    tests = [
        ('test/abs.expr', ['101'], ['(Integer 101)']),
        ('test/abs.expr', ['0'], ['(Integer 0)']),
        ('test/abs.expr', ['-501'], ['(Integer 501)']),

        ('test/binary-tree.expr', [], ['1', '2', '3', '4', '5', 'Void']),

        ('test/coroutines.expr', [], [
            'main',
            'task 1',
            'main',
            'task 2',
            'main',
            'task 3',
            'Void'
        ]),

        ('test/dynamic-scope.expr', [], ['100', '200', 'Void']),

        ('test/exception.expr', [], [
            'call n = 2',
            'call n = 1',
            'call n = 0',
            'return n = 0',
            'return n = 1',
            'return n = 2',
            'call n = 2',
            'call n = 1',
            'call n = 0',
            'exception',
            'Void'
        ]),

        ('test/gcd.expr', ['100', '0'], ['100', 'Void']),
        ('test/gcd.expr', ['0', '100'], ['100', 'Void']),
        ('test/gcd.expr', ['30', '30'], ['30', 'Void']),
        ('test/gcd.expr', ['25', '45'], ['5', 'Void']),
        ('test/gcd.expr', ['7', '100'], ['1', 'Void']),

        ('test/intensive.expr', [], ['(Integer 50005000)']),

        ('test/lexical-scope.expr', [], ['1', '100', 'Void']),

        ('test/mixed-scope.expr', [], ['1', '303', 'Void']),

        ('test/multi-stage.expr', [], ['EVAL', 'Void']),

        ('test/mutual-recursion.expr', [], ['10', '9', '8', '7', '6', '5', '4', '3', '2', '1', '0', 'Void']),

        ('test/oop.expr', [], ['1', '2', '100', '2', 'Void']),

        ('test/quicksort.expr', ['0'], ['Void']),
        ('test/quicksort.expr', ['1', '303'], ['303', 'Void']),
        ('test/quicksort.expr', ['3', '1', '3', '7'], ['1', '3', '7', 'Void']),
        ('test/quicksort.expr', ['5', '5', '4', '3', '2', '1'], ['1', '2', '3', '4', '5', 'Void']),
        ('test/quicksort.expr', ['6', '8', '-1', '3', '0', '6', '-5'], ['-5', '-1', '0', '3', '6', '8', 'Void']),

        ('test/string-literals.expr', [], ["aaa\"", "bbbb\\\"", "ccccc\\", "Void"]),

        ('test/string-reverse.expr', ["abcde"], ["edcba", "Void"]),
        ('test/string-reverse.expr', ["12 ccc"], ["ccc 21", "Void"]),
        ('test/string-reverse.expr', ["\t <>///"], ["///>< \t", "Void"]),

        ('test/type.expr', [], ['0', '1', '2', '3', '4', 'Void'])
    ]
    for test in tests:
        sys.stderr.write(f'Running on test {test[0]} with input {test[1]}\n')
        if not check_io(*test):
            sys.exit(f'Failed on test "{test}"')
    sys.stderr.write('Passed all tests\n')

if __name__ == '__main__':
    main()
