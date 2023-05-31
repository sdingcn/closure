import sys
from collections import deque
from typing import Union, Any
from copy import deepcopy

# helper functions

def unfold(value: Union[list[Any], tuple[Any, ...], set[Any], dict[Any]]) -> str:
    if type(value) == list:
        s = '['
    elif type(value) == tuple:
        s = '('
    elif type(value) in [set, dict]:
        s = '{'
    else:
        sys.exit('[Expr Internal Error] unsupported argument given to "unfold"')
    if type(value) in [list, tuple, set]:
        for v in value:
            if type(v) in [list, tuple, set, dict]:
                s += unfold(v)
            else:
                s += str(v)
            s += ', '
        if s[-2:] == ', ':
            s = s[:-2]
    else:
        for k, v in value.items():
            if type(k) == tuple:
                s += unfold(k)
            else:
                s += str(k)
            s += ': '
            if type(v) in [list, tuple, set, dict]:
                s += unfold(v)
            else:
                s += str(v)
            s += ', '
        if s[-2:] == ', ':
            s = s[:-2]
    if type(value) == list:
        s += ']'
    elif type(value) == tuple:
        s += ')'
    else:
        s = '}'
    return s

def truncate(v: Any) -> str:
    return str(v)[:30] + '...'

# lexer

def lex(source: str, debug: bool) -> deque[str]:
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
                sys.exit(f'[Expr Lexer Error] unrecognized character "{chars[0]}"')
            return token
        else:
            return ''

    tokens = deque()
    while True:
        token = next_token()
        if debug:
            sys.stderr.write(f'[Expr Debug] read token {token}\n')
        if token:
            tokens.append(token)
        else:
            break
    return tokens

# AST and parser

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
        return f'(Var {self.name})'

class Lambda(Expr):

    def __init__(self, parent: Union[None, Expr], var_list: list[Var], expr: Expr):
        self.parent = parent
        self.var_list = var_list
        self.expr = expr

    def __str__(self) -> str:
        return f'(Lambda {unfold(self.var_list)} {self.expr})'

class Letrec(Expr):

    def __init__(self, parent: Union[None, Expr], var_expr_list: list[tuple[Var, Expr]], expr: Expr):
        self.parent = parent
        self.var_expr_list = var_expr_list
        self.expr = expr

    def __str__(self) -> str:
        return f'(Letrec {unfold(self.var_expr_list)} {self.expr})'

class If(Expr):

    def __init__(self, parent: Union[None, Expr], cond: Expr, branch1: Expr, branch2: Expr):
        self.parent = parent
        self.cond = cond
        self.branch1 = branch1
        self.branch2 = branch2

    def __str__(self) -> str:
        return f'(If {self.cond} {self.branch1} {self.branch2})'

class Call(Expr):

    def __init__(self, parent: Union[None, Expr], callee: Expr, arg_list: list[Expr]):
        self.parent = parent
        self.callee = callee
        self.arg_list = arg_list

    def __str__(self) -> str:
        return f'(Call {self.callee} {unfold(self.arg_list)})'

class Seq(Expr):

    def __init__(self, parent: Union[None, Expr], expr_list: list[Expr]):
        self.parent = parent
        self.expr_list = expr_list

    def __str__(self) -> str:
        return f'(Seq {unfold(self.expr_list)})'

def parse(tokens: deque[str], debug: bool) -> Expr:
    
    def is_int(token: str) -> bool:
        try:
            int(token)
            return True
        except ValueError:
            return False

    def is_var(token: str) -> bool:
        return token.isalpha()

    def parse_int() -> Int:
        if debug:
            sys.stderr.write('[Expr Debug] entered Int\n')
        value = int(tokens.popleft())
        node = Int(None, value)
        return node

    def parse_lambda() -> Lambda:
        if debug:
            sys.stderr.write('[Expr Debug] entered Lambda\n')
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
        if debug:
            sys.stderr.write('[Expr Debug] entered Letrec\n')
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
        if debug:
            sys.stderr.write('[Expr Debug] entered If\n')
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
        if debug:
            sys.stderr.write('[Expr Debug] entered Var\n')
        name = tokens.popleft()
        node = Var(None, name)
        return node

    def parse_call() -> Call:
        if debug:
            sys.stderr.write('[Expr Debug] entered Call\n')
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
        if debug:
            sys.stderr.write('[Expr Debug] entered Seq\n')
        tokens.popleft() # [
        expr_list = []
        while tokens[0] != ']':
            expr_list.append(parse_expr())
        tokens.popleft() # ]
        if len(expr_list) == 0:
            sys.exit('[Expr Parser Error] zero-length sequence')
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
            sys.exit(f'[Expr Parser Error] unrecognized expression starting with "{tokens[0]}"')
    
    try:
        return parse_expr()
    except IndexError:
        sys.exit('[Expr Parser Error] incomplete expression')

# runtime classes

class Value:
    
    def __init__(self):
        pass

    def __str__(self) -> str:
        return 'value'

class Integer(Value):

    def __init__(self, value: int):
        self.value = value

    def __str__(self) -> str:
        return str(self.value)

class Closure(Value):

    def __init__(self, env: list[tuple[str, int]], fun: Lambda):
        self.env = env
        self.fun = fun

    def __str__(self) -> str:
        return f'(closure {unfold(self.env)} {self.fun})'

class Void(Value):

    def __init__(self):
        pass

    def __str__(self) -> str:
        return 'void'

# the layer class for the evaluation stack; each layer contains the expression currently under evaluation
class Layer:

    def __init__(self,
            env: list[tuple[str, int]],
            expr: Expr,
            pc: int,
            local: dict[str, Any]
        ):
        self.env = env
        self.expr = expr
        self.pc = pc # program counter (the i-th step of evaluating this layer)
        self.local = local

    def __str__(self) -> str:
        return f'(layer {unfold(self.env)} {self.expr} {self.pc} {unfold(self.local)})'

class Continuation(Value):

    def __init__(self, stack: list[Layer]):
        self.stack = stack

    def __str__(self) -> str:
        return f'(continuation {unfold(self.stack)})'

# the global state
class State:

    def __init__(self, expr: Expr):
        self.stack = [Layer([], expr, 0, {})]
        self.store = {}
        self.location = 0

    def __str__(self) -> str:
        return f'(state {unfold(self.stack)} {unfold(self.store)} {self.location})'

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
    sys.exit(f'[Expr Runtime Error] undefined variable "{var}"')

def dynamic_lookup(var: str, stack: list[Layer]) -> int: # TODO
    pass

# interpreter

def interpret(tree: Expr, debug: bool) -> Value:
    intrinsics = ['add', 'sub', 'mul', 'div', 'mod', 'lt', 'void', 'get', 'put', 'callcc', 'exit']
    state = State(tree)
    value = None

    while True:
        # TODO: maybe call GC once for every 100 iterations
        if len(state.stack) == 0:
            return value
        layer = state.stack[-1]
        node = layer.expr
        if debug:
            sys.stderr.write(f'[Expr Debug] evaluating {truncate(node)}\n')
        if type(node) == Int:
            value = Integer(node.value)
            state.stack.pop()
        elif type(node) == Lambda:
            value = Closure(layer.env, node)
            state.stack.pop()
        elif type(node) == Letrec:
            if layer.pc == 0:
                layer.local['new_env'] = layer.env[:]
                for v, e in node.var_expr_list:
                    loc = state.new(Void())
                    layer.local['new_env'].append((v.name, loc))
                layer.pc += 1
            elif layer.pc <= len(node.var_expr_list):
                if layer.pc > 1:
                    last_location = lexical_lookup(node.var_expr_list[layer.pc - 2][0].name, layer.local['new_env'])
                    state.store[last_location] = value
                v, e = node.var_expr_list[layer.pc - 1]
                state.stack.append(Layer(layer.local['new_env'][:], e, 0, {}))
                layer.pc += 1
            elif layer.pc == len(node.var_expr_list) + 1:
                if layer.pc > 1:
                    last_location = lexical_lookup(node.var_expr_list[layer.pc - 2][0].name, layer.local['new_env'])
                    state.store[last_location] = value
                state.stack.append(Layer(layer.local['new_env'][:], node.expr, 0, {}))
                layer.pc += 1
            else:
                state.stack.pop()
        elif type(node) == If:
            if layer.pc == 0:
                state.stack.append(Layer(layer.env[:], node.cond, 0, {}))
                layer.pc += 1
            elif layer.pc == 1:
                if value.value != 0:
                    state.stack.append(Layer(layer.env[:], node.branch1, 0, {}))
                else:
                    state.stack.append(Layer(layer.env[:], node.branch2, 0, {}))
                layer.pc += 1
            else:
                state.stack.pop()
        elif type(node) == Var:
            value = state.store[lexical_lookup(node.name, layer.env)]
            state.stack.pop()
        elif type(node) == Call:
            if type(node.callee) == Var and node.callee.name in intrinsics:
                if layer.pc == 0:
                    layer.local['arg_vals'] = []
                    layer.pc += 1
                elif layer.pc <= len(node.arg_list):
                    if layer.pc > 1:
                        layer.local['arg_vals'].append(value)
                    state.stack.append(Layer(layer.env[:], node.arg_list[layer.pc - 1], 0, {}))
                    layer.pc += 1
                else:
                    if layer.pc > 1:
                        layer.local['arg_vals'].append(value)
                    if node.callee.name == 'add':
                        value = Integer(layer.local['arg_vals'][0].value + layer.local['arg_vals'][1].value)
                    elif node.callee.name == 'sub':
                        value = Integer(layer.local['arg_vals'][0].value - layer.local['arg_vals'][1].value)
                    elif node.callee.name == 'mul':
                        value = Integer(layer.local['arg_vals'][0].value * layer.local['arg_vals'][1].value)
                    elif node.callee.name == 'div':
                        value = Integer(layer.local['arg_vals'][0].value / layer.local['arg_vals'][1].value)
                    elif node.callee.name == 'mod':
                        value = Integer(layer.local['arg_vals'][0].value % layer.local['arg_vals'][1].value)
                    elif node.callee.name == 'lt':
                        value = Integer(1) if layer.local['arg_vals'][0].value < layer.local['arg_vals'][1].value else Integer(0)
                    elif node.callee.name == 'void':
                        value = Void()
                    elif node.callee.name == 'get':
                        try:
                            s = input()
                            value = Integer(int(s.strip()))
                        except ValueError:
                            sys.exit(f'[Expr Runtime Error] unsupported input "{s}"')
                    elif node.callee.name == 'put':
                        print(layer.local['arg_vals'][0].value)
                        value = Void()
                    elif node.callee.name == 'callcc': # this is like calling a function
                        state.stack.pop()
                        state.stack.append(Layer(layer.local['arg_vals'][0].env[:]
                            + [(layer.local['arg_vals'][0].fun.var_list[0].name, state.new(Continuation(deepcopy(state.stack))))],
                            layer.local['arg_vals'][0].fun.expr, 0, {}))
                        if debug:
                            sys.stderr.write('[Expr Debug] captured continuation\n')
                        continue
                    elif node.callee.name == 'exit':
                        if debug:
                            sys.stderr.write('[Expr Debug] execution stopped by the "exit" intrinsic function\n')
                    state.stack.pop()
            else:
                if layer.pc == 0:
                    state.stack.append(Layer(layer.env[:], node.callee, 0, {}))
                    layer.pc += 1
                elif layer.pc == 1:
                    layer.local['callee'] = value
                    layer.local['arg_vals'] = []
                    layer.pc += 1
                elif layer.pc - 1 <= len(node.arg_list):
                    if layer.pc - 1 > 1:
                        layer.local['arg_vals'].append(value)
                    state.stack.append(Layer(layer.env[:], node.arg_list[layer.pc - 2], 0, {}))
                    layer.pc += 1
                elif layer.pc - 1 == len(node.arg_list) + 1:
                    if layer.pc - 1 > 1:
                        layer.local['arg_vals'].append(value)
                    if type(layer.local['callee']) == Closure:
                        layer.local['new_env'] = layer.local['callee'].env[:]
                        for i, v in enumerate(layer.local['callee'].fun.var_list):
                            layer.local['new_env'].append((v.name, state.new(layer.local['arg_vals'][i])))
                        state.stack.append(Layer(layer.local['new_env'][:], layer.local['callee'].fun.expr, 0, {}))
                        layer.pc += 1
                    elif type(layer.local['callee']) == Continuation:
                        state.stack = deepcopy(layer.local['callee'].stack)
                        if debug:
                            sys.stderr.write('[Expr Debug] applied continuation, stack switched\n')
                        continue
                else:
                    state.stack.pop()
        elif type(node) == Seq:
            if layer.pc < len(node.expr_list):
                state.stack.append(Layer(layer.env[:], node.expr_list[layer.pc], 0, {}))
                layer.pc += 1
            else:
                state.stack.pop()
        else:
            sys.exit(f'[Expr Runtime Error] unrecognized AST node "{node}"')

# main entry

def main(option: str, source: str) -> None:
    if option == 'run':
        tokens = lex(source, False)
        tree = parse(tokens, False)
        result = interpret(tree, False)
        print(result)
    elif option == 'debug':
        sys.stderr.write('[Expr Debug] *** starting lexer ***\n')
        tokens = lex(source, True)
        sys.stderr.write('[Expr Debug] *** starting parser ***\n')
        tree = parse(tokens, True)
        sys.stderr.write('[Expr Debug] *** starting interpreter ***\n')
        result = interpret(tree, True)
        print(result)
    elif option == 'dump-ast':
        tokens = lex(source, False)
        tree = parse(tokens, False)
        print(tree)

if __name__ == '__main__':
    if len(sys.argv) != 3 or sys.argv[1] not in ['run', 'debug', 'dump-ast']:
        sys.exit(
            'Usage:\n'
            f'\tpython3 {sys.argv[0]} run <source-file>\n'
            f'\tpython3 {sys.argv[0]} debug <source-file>\n'
            f'\tpython3 {sys.argv[0]} dump-ast <source-file>'
        )
    with open(sys.argv[2], 'r') as f:
        main(sys.argv[1], f.read())
