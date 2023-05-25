import sys
from collections import deque

def lex(source):
    chars = deque(source)
    def next_token():
        pass
    tokens = deque()
    while True:
        token = next_token()
        if token:
            tokens.append(token)
        else:
            break
    return tokens

class Var:
    pass

class Int:
    pass

class Binop:
    pass

class Expr:
    pass

def parse(tokens):
    def parse_var():
        pass
    def parse_int():
        pass
    def parse_binop():
        pass
    def parse_expr():
        pass
    return parse_expr()

def interpret(tree, env):
    if type(tree) == Var:
        pass
    elif type(tree) == Int:
        pass
    elif type(tree) == Op:
        pass
    elif type(tree) == Expr:
        pass
    else:
        pass

def main():
    source = sys.stdin.read()
    tokens = lex(source)
    tree = parse(tokens)
    result = interpret(tree, [])
    if type(result) == int:
        print(result)
    else:
        print('function')

if __name__ == '__main__':
    main()
