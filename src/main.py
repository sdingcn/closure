import sys
from lexer import lex
from syntax import *
from parser import parse
from dynamic import *
from interpreter import interpret

def main():
    source = sys.stdin.read()
    tokens = lex(source)
    tree = parse(tokens)
    result = interpret(tree)
    if type(result) == Integer:
        print(result.value)
    elif type(result) == Closure:
        print('Closure')
    elif type(result) == Void:
        print('Void')

if __name__ == '__main__':
    main()
