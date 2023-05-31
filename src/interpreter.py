import sys
from collections import deque
from typing import Union, Any

# lexer

def lex(source: str) -> deque[str]:
    chars = deque(source)

    def next_token() -> str:
        while chars and chars[0].isspace():
            chars.popleft()
        if chars:
            if chars[0].isdigit():
                token = ''
                while chars and chars[0].isdigit():
                    token += chars.popleft()
            elif chars[0] in ('-', '+') and (len(chars) > 1 and chars[1].isdigit()):
                token = chars.popleft()
                while chars and chars[0].isdigit():
                    token += chars.popleft()
            elif chars[0].isalpha():
                token = ''
                while chars and chars[0].isalpha():
                    token += chars.popleft()
            elif chars[0] in ('(', ')', '{', '}', '[', ']', '='):
                token = chars.popleft()
            else:
                sys.exit(f'[Expr Lexer] error: unrecognized character "{chars[0]}"')
            return token
        else:
            return ''

    tokens = deque()
    while True:
        token = next_token()
        if token:
            tokens.append(token)
        else:
            break
    return tokens

# AST and parser

def unfold_to_string(value: Union[list[Any], tuple[Any, ...]]) -> str:
    if type(value) == list:
        s = '['
    elif type(value) == tuple:
        s = '('
    else:
        sys.exit('[Expr Internal] error: wrong type of argument given to "unfold_to_string"')
    for e in value:
        if type(e) == list or type(e) == tuple:
            s += unfold_to_string(e)
        else:
            s += str(e)
        s += ' '
    if s[-1] == ' ':
        s = s[:-1]
    if type(value) == list:
        s += ']'
    elif type(value) == tuple:
        s += ')'
    else:
        sys.exit('[Expr Internal] error: wrong type of argument given to "unfold_to_string"')
    return s

class Expr:

    def __init__(self):
        pass

    def __str__(self) -> str:
        return 'Expr'

class Int(Expr):

    def __init__(self, parent: Union[None, Expr], value: int):
        self.parent = parent
        self.value = value

    def __str__(self) -> str:
        return f'(Int {self.value})'

class Var(Expr):

    def __init__(self, parent: Union[None, Expr], name: str):
        self.parent = parent
        self.name = name

    def __str__(self) -> str:
        return f'(Var "{self.name}")'

class Lambda(Expr):

    def __init__(self, parent: Union[None, Expr], var_list: list[Var], expr: Expr):
        self.parent = parent
        self.var_list = var_list
        self.expr = expr

    def __str__(self) -> str:
        return f'(Lambda {unfold_to_string(self.var_list)} {str(self.expr)})'

class Letrec(Expr):

    def __init__(self, parent: Union[None, Expr], var_expr_list: list[tuple[Var, Expr]], expr: Expr):
        self.parent = parent
        self.var_expr_list = var_expr_list
        self.expr = expr

    def __str__(self) -> str:
        return f'(Letrec {unfold_to_string(self.var_expr_list)} {str(self.expr)})'

class If(Expr):

    def __init__(self, parent: Union[None, Expr], cond: Expr, branch1: Expr, branch2: Expr):
        self.parent = parent
        self.cond = cond
        self.branch1 = branch1
        self.branch2 = branch2

    def __str__(self) -> str:
        return f'(If {str(self.cond)} {str(self.branch1)} {str(self.branch2)})'

class Call(Expr):

    def __init__(self, parent: Union[None, Expr], callee: Expr, arg_list: list[Expr]):
        self.parent = parent
        self.callee = callee
        self.arg_list = arg_list

    def __str__(self) -> str:
        return f'(Call {str(self.callee)} {unfold_to_string(self.arg_list)})'

class Seq(Expr):

    def __init__(self, parent: Union[None, Expr], expr_list: list[Expr]):
        self.parent = parent
        self.expr_list = expr_list

    def __str__(self) -> str:
        return f'(Seq {unfold_to_string(self.expr_list)})'

def parse(tokens: deque[str]) -> Expr:
    
    def is_int(token: str) -> bool:
        try:
            int(token)
            return True
        except ValueError:
            return False

    def is_var(token: str) -> bool:
        return token.isalpha()

    def parse_int() -> Int:
        value = int(tokens.popleft())
        node = Int(None, value)
        return node

    def parse_lambda() -> Lambda:
        tokens.popleft() # lambda
        tokens.popleft() # (
        var_list = []
        while tokens[0].isalpha():
            var_list.append(parse_var())
        tokens.popleft() # )
        tokens.popleft() # {
        expr = parse_expr()
        tokens.popleft() # }
        node = Lambda(None, var_list, expr)
        for v in node.var_list:
            v.parent = node
        node.expr.parent = node
        return node

    def parse_letrec() -> Letrec:
        tokens.popleft() # letrec
        tokens.popleft() # (
        var_expr_list = []
        while tokens[0].isalpha():
            v = parse_var()
            tokens.popleft() # =
            e = parse_expr()
            var_expr_list.append((v, e))
        tokens.popleft() # )
        tokens.popleft() # {
        expr = parse_expr()
        tokens.popleft() # }
        node = Letrec(None, var_expr_list, expr)
        for v, e in node.var_expr_list:
            v.parent = node
            e.parent = node
        node.expr.parent = node
        return node

    def parse_if() -> If:
        tokens.popleft() # if
        cond = parse_expr()
        tokens.popleft() # then
        branch1 = parse_expr()
        tokens.popleft() # else
        branch2 = parse_expr()
        node = If(None, cond, branch1, branch2)
        node.cond.parent = node
        node.branch1.parent = node
        node.branch2.parent = node
        return node

    def parse_var() -> Var:
        name = tokens.popleft()
        node = Var(None, name)
        return node

    def parse_call() -> Call:
        tokens.popleft() # (
        callee = parse_expr()
        arg_list = []
        while tokens[0] != ')':
            arg_list.append(parse_expr())
        tokens.popleft() # )
        node = Call(None, callee, arg_list)
        node.callee.parent = node
        for a in node.arg_list:
            a.parent = node
        return node

    def parse_seq() -> Seq:
        tokens.popleft() # [
        expr_list = []
        while tokens[0] != ']':
            expr_list.append(parse_expr())
        tokens.popleft() # ]
        if len(expr_list) == 0:
            sys.exit('[Expr Parser] error: zero-length sequence')
        node = Seq(None, expr_list)
        for e in node.expr_list:
            e.parent = node
        return node

    def parse_expr() -> Expr:
        if is_int(tokens[0]):
            return parse_int()
        elif tokens[0] == 'lambda':
            return parse_lambda()
        elif tokens[0] == 'letrec':
            return parse_letrec()
        elif tokens[0] == 'if':
            return parse_if()
        elif is_var(tokens[0]):
            return parse_var()
        elif tokens[0] == '(':
            return parse_call()
        elif tokens[0] == '[':
            return parse_seq()
        else:
            sys.exit(f'[Expr Parser] error: unrecognized expression starting with "{tokens[0]}"')
    
    try:
        return parse_expr()
    except IndexError:
        sys.exit('[Expr Parser] error: incomplete expression')

# runtime values

class Value:
    
    def __init__(self):
        pass

class Integer(Value):

    def __init__(self, value: int):
        self.value = value

class Closure(Value):

    def __init__(self, env: list[tuple[str, int]], fun: Lambda):
        self.env = env
        self.fun = fun

class Continuation(Value):

    def __init__(self):
        pass

class Void(Value):

    def __init__(self):
        pass

# runtime state

class Layer:

    def __init__(self,
            env: list[tuple[str, int]],
            expr: Expr,
            pc: Union[None, int],
            local: dict[str, Any]
        ):
        self.env = env
        self.expr = expr
        # program counter inside the current layer
        # None means just started (the layer has just been pushed onto the stack)
        # other value (integer) i means the next step is the i-th step
        self.pc = pc
        self.local = local # local variable names start with '#'

class State:

    def __init__(self, expr: Expr):
        # this is not a call stack
        # it is an "evaluation stack" where each layer is a syntax construct
        # a call stack can be obtained by partitioning the evaluation stack according to function layers
        self.stack = [Layer([], expr, None, {})]
        self.store = {}
        self.location = 0

    def new(self, value: Value) -> int:
        self.store[self.location] = value
        self.location += 1
        return self.location - 1

    def collect(self) -> int: # TODO
        visited = set()

        def mark(loc: int) -> None:
            visited.add(loc)
            if type(self.store[loc]) == Closure:
                for v, l in self.store[loc].env:
                    if l not in visited:
                        mark(l)

        def sweep() -> int:
            to_remove = set()
            for k, v in self.store.items():
                if k not in visited:
                    to_remove.add(k)
            for k in to_remove:
                del self.store[k]
            return len(to_remove)

        for layer in self.stack:
            for v, l in layer.env:
                mark(l)
        return sweep()

# runtime pure helper functions

def lexical_lookup(var: str, env: list[tuple[str, int]]) -> int:
    for i in range(len(env) - 1, -1, -1):
        if env[i][0] == var:
            return env[i][1]
    sys.exit(f'[Expr Runtime] error: undefined variable "{var}"')

# interpreter

def interpret(tree: Expr) -> Value:
    intrinsics = ['add', 'sub', 'mul', 'div', 'mod', 'lt', 'void', 'get', 'put', 'callcc', 'exit']
    state = State(tree)
    value = None

    while True:
        if len(state.stack) == 0:
            return value
        layer = state.stack[-1]
        node = layer.expr
        if type(node) == Int:
            value = Integer(node.value)
            state.stack.pop()
        elif type(node) == Lambda:
            value = Closure(layer.env, node)
            state.stack.pop()
        elif type(node) == Letrec:
            if layer.pc == None:
                layer.local['new_env'] = layer.env[:]
                for v, e in node.var_expr_list:
                    loc = state.new(Void())
                    layer.local['new_env'].append((v.name, loc))
                layer.pc = 0
            else:
                if layer.pc < len(node.var_expr_list):
                    if layer.pc > 0:
                        last_location = lexical_lookup(node.var_expr_list[layer.pc - 1], layer.local['new_env'])
                        state.store[last_location] = value
                    v, e = node.var_expr_list[layer.pc]
                    state.stack.append(Layer(layer.local['new_env'][:], e, None, {}))
                    layer.pc += 1
                elif layer.pc == len(node.var_expr_list):
                    if layer.pc > 0:
                        last_location = lexical_lookup(node.var_expr_list[layer.pc - 1], layer.local['new_env'])
                        state.store[last_location] = value
                    state.stack.append(Layer(layer.local['new_env'][:], node.expr, None, {}))
                    layer.pc += 1
                else:
                    state.stack.pop()
        elif type(node) == If:
            if layer.pc == None:
                state.stack.append(Layer(layer.env[:], node.cond, None, {}))
                layer.pc = 0
            elif layer.pc == 1:
                if value.value != 0:
                    state.stack.append(Layer(layer.env[:], node.branch1, None, {}))
                else:
                    state.stack.append(Layer(layer.env[:], node.branch2, None, {}))
                layer.pc += 1
            else:
                state.stack.pop()
        elif type(node) == Var:
            value = lexical_lookup(node.name, layer.env)
            state.stack.pop()
        elif type(node) == Call:
            if type(node.callee) == Var and node.callee.name in intrinsics:
                if layer.pc == None:
                    layer.local['arg_vals'] = []
                    layer.pc = 0
                elif layer.pc < len(node.arg_list):
                    layer.pc += 1
                elif layer.pc == len(node.arg_list):
                    if node.callee.name == 'callcc':
                        pass # this is like calling a function
                    else:
                        value = ()
                        state.stack.pop()
            else:
                if layer.pc == None:
                    pass
                    layer.pc = 0
                elif layer.pc == 0:
                    layer.local['callee'] = value
                    layer.pc += 1
                elif layer.pc <= len(node.arg_list):
                    layer.pc += 1
                else:
                    if type(layer.local['callee']) == Closure:
                        pass
                    elif type(layer.local['callee']) == Continuation:
                        pass
        elif type(state.pc) == Seq:
            pass
        else:
            sys.exit(f'[Expr Runtime] error: unrecognized AST node "{node}"')

# main entry

def main(option: str, source: str) -> None:
    tokens = lex(source)
    tree = parse(tokens)
    if option == 'run':
        result = interpret(tree)
        if type(result) == Integer:
            print(result.value)
        elif type(result) == Closure:
            print('Closure')
        elif type(result) == Continuation:
            print('Continuation')
        elif type(result) == Void:
            print('Void')
        else:
            sys.exit(f'[Expr Main] error: unknown evaluation result "{result}"')
    elif option == 'dump-ast':
        print(tree)
    else:
        sys.exit(f'[Expr Main] error: unknown command-line option "{option}"')

if __name__ == '__main__':
    if len(sys.argv) != 3:
        sys.exit(
            'Usage\n'
            f'python3 {sys.argv[0]} run <source-file>'
            f'python3 {sys.argv[0]} dump-ast <source-file>'
        )
    with open(sys.argv[2], 'r') as f:
        main(sys.argv[1], f.read())
