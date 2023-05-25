import sys
from collections import deque

# lexing

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

# parsing

class Int:
    def __init__(self, value):
        self.value = value

class Var:
    def __init__(self, name):
        self.name = name

class Lambda:
    def __init__(self, var_list, expr_list):
        self.var_list = var_list
        self.expr_list = expr_list

class Letrec:
    def __init__(self, var_expr_list, expr):
        self.var_expr_list = var_expr_list
        self.expr = expr

class If:
    def __init__(self, cond, branch1, branch2):
        self.cond = cond
        self.branch1 = branch1
        self.branch2 = branch2

class Call:
    def __init__(self, fun, arg_list):
        self.fun = fun
        self.arg_list = arg_list

class Seq:
    def __init__(self, expr_list):
        self.expr_list = expr_list

def parse(tokens):

    def is_int(s):
        try:
            int(s)
            return True
        except ValueError:
            return False

    def is_var(s):
        return s.isalpha()

    def parse_int():
        pass

    def parse_var():
        pass

    def parse_lambda():
        pass

    def parse_letrec():
        pass

    def parse_if():
        pass

    def parse_call():
        pass

    def parse_seq():
        pass

    if is_int(tokens[0]):
        return parse_int()
    elif is_var(tokens[0]):
        return parse_var()
    elif tokens[0] == 'lambda':
        return parse_lambda()
    elif tokens[0] == 'letrec':
        return parse_letrec()
    elif tokens[0] == 'if':
        return parse_if()
    elif tokens[0] == '(':
        return parse_call()
    elif tokens[0] == '[':
        return parse_seq()

# interpreting

class Integer:
    pass

class Closure:
    pass

class Void:
    pass

class Frame:
    pass

def interpret(tree):
    store = {}
    stack = []

# main entry

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
