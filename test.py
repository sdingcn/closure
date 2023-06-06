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
        ('test/abs.expr', ['101'], ['101']),
        ('test/abs.expr', ['0'], ['0']),
        ('test/abs.expr', ['-501'], ['501']),

        ('test/gcd.expr', ['100', '0'], ['100', 'void']),
        ('test/gcd.expr', ['0', '100'], ['100', 'void']),
        ('test/gcd.expr', ['30', '30'], ['30', 'void']),
        ('test/gcd.expr', ['25', '45'], ['5', 'void']),
        ('test/gcd.expr', ['7', '100'], ['1', 'void']),

        ('test/mutual-recursion.expr', [], ['10', '9', '8', '7', '6', '5', '4', '3', '2', '1', '0', 'void']),

        ('test/quicksort.expr', ['0'], ['void']),
        ('test/quicksort.expr', ['1', '303'], ['303', 'void']),
        ('test/quicksort.expr', ['3', '1', '3', '7'], ['1', '3', '7', 'void']),
        ('test/quicksort.expr', ['5', '5', '4', '3', '2', '1'], ['1', '2', '3', '4', '5', 'void']),
        ('test/quicksort.expr', ['6', '8', '-1', '3', '0', '6', '-5'], ['-5', '-1', '0', '3', '6', '8', 'void']),

        ('test/lexical-scope.expr', [], ['1', '100', 'void']),

        ('test/dynamic-scope.expr', [], ['100', '200', 'void']),

        ('test/mixed-scope.expr', [], ['1', '303', 'void']),

        ('test/continuation.expr', [], ['3', '2', '1', '1', '2', '3', '3', '2', '1', '300']),

        ('test/type.expr', [], ['0', '1', '2', '3', '4', 'void']),

        ('test/oop.expr', [], ['1', '2', '100', '2', 'void']),

        ('test/intensive.expr', [], ['50005000']),

        ('test/binary-tree.expr', [], ['1', '2', '3', '4', '5', 'void']),

        ('test/string-reverse.expr', ["abcde"], ["edcba", "void"]),
        ('test/string-reverse.expr', ["12 ccc"], ["ccc 21", "void"]),
        ('test/string-reverse.expr', ["\t <>///"], ["///>< \t", "void"]),

        ('test/string-literals.expr', [], ["aaa\"", "bbbb\\\"", "ccccc\\", "void"])
    ]
    for test in tests:
        sys.stderr.write(f'Running on test {test[0]} with input {test[1]}\n')
        if not check_io(*test):
            sys.exit(f'Failed on test "{test}"')
    sys.stderr.write('Passed all tests\n')

if __name__ == '__main__':
    main()
