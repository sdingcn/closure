import sys
import time
import tracemalloc
from collections import deque
from typing import Union, Any
from copy import deepcopy

### helper functions

def unfold(value: Union[list[Any], tuple[Any, ...], set[Any], dict[Any, Any]]) -> str:
    '''Recursively unfold a container to a readable string'''
    if type(value) == list:
        s = '['
    elif type(value) == tuple:
        s = '('
    elif type(value) in [set, dict]:
        s = '{'
    else:
        sys.exit('[Expr Internal Error] unsupported argument given to unfold')
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

### lexer

class SourceLocation:

    def __init__(self, line: int, col: int):
        self.line = line
        self.col = col

    def __str__(self) -> str:
        return f'(SourceLocation {self.line} {self.col})'

class Token:

    def __init__(self, sl: SourceLocation, val: str):
        self.sl = sl
        self.val = val

    def __str__(self) -> str:
        return f'(Token {self.sl} {self.val})'

def lex(source: str, debug: bool) -> deque[Token]:
    chars = deque(source)
    line = 1
    col = 1

    def count_trailing_escape(s: str) -> int:
        l = len(s)
        cnt = 0
        pos = l - 1
        while pos >= 0:
            if s[pos] == '\\':
                cnt += 1
                pos -= 1
            else:
                break
        return cnt

    def next_token() -> Union[None, Token]:
        nonlocal line, col
        while chars and chars[0].isspace():
            space = chars.popleft()
            col += 1
            if space == '\n':
                line += 1
                col = 1
        if chars:
            sl = SourceLocation(line, col)
            if chars[0].isdigit():
                val = ''
                while chars and chars[0].isdigit():
                    val += chars.popleft()
            elif chars[0] in ('-', '+'):
                if len(chars) > 1 and chars[1].isdigit():
                    val = chars.popleft()
                    while chars and chars[0].isdigit():
                        val += chars.popleft()
                else:
                    sys.exit(f'[Expr Lexer Error] incomplete integer literal at {sl}')
            elif chars[0].isalpha():
                val = ''
                while chars and chars[0].isalpha():
                    val += chars.popleft()
            elif chars[0] in ('(', ')', '{', '}', '[', ']', '='):
                val = chars.popleft()
            elif chars[0] == '"':
                val = chars.popleft()
                while chars and (chars[0] != '"' or (chars[0] == '"' and count_trailing_escape(val) % 2 != 0)):
                    val += chars.popleft()
                if chars and chars[0] == '"':
                    val += chars.popleft()
                else:
                    sys.exit(f'[Expr Lexer Error] incomplete string literal at {sl}')
            else:
                sys.exit(f'[Expr Lexer Error] unsupported character {chars[0]} at {sl}')
            token = Token(sl, val)
            col += len(val)
            return token
        else:
            return None

    tokens = deque()
    while True:
        token = next_token()
        if token:
            if debug:
                sys.stderr.write(f'[Expr Debug] read token {token}\n')
            tokens.append(token)
        else:
            break
    return tokens

### parser

class Expr:

    def __init__(self):
        pass

    def __str__(self) -> str:
        return 'Expr'

class Int(Expr):

    def __init__(self, sl: SourceLocation, parent: Union[None, Expr], value: int):
        self.sl = sl
        self.parent = parent
        self.value = value

    def __str__(self) -> str:
        return f'(Int {self.sl} {self.value})'

class Str(Expr):

    def __init__(self, sl: SourceLocation, parent: Union[None, Expr], value: str):
        self.sl = sl
        self.parent = parent
        self.value = value

    def __str__(self) -> str:
        return f'(Int {self.sl} {self.value})'

class Var(Expr):

    def __init__(self, sl: SourceLocation, parent: Union[None, Expr], name: str):
        self.sl = sl
        self.parent = parent
        self.name = name

    def __str__(self) -> str:
        return f'(Var {self.sl} {self.name})'

class Lambda(Expr):

    def __init__(self, sl: SourceLocation, parent: Union[None, Expr], var_list: list[Var], expr: Expr):
        self.sl = sl
        self.parent = parent
        self.var_list = var_list
        self.expr = expr

    def __str__(self) -> str:
        return f'(Lambda {self.sl} {unfold(self.var_list)} {self.expr})'

class Letrec(Expr):

    def __init__(self, sl: SourceLocation, parent: Union[None, Expr], var_expr_list: list[tuple[Var, Expr]], expr: Expr):
        self.sl = sl
        self.parent = parent
        self.var_expr_list = var_expr_list
        self.expr = expr

    def __str__(self) -> str:
        return f'(Letrec {self.sl} {unfold(self.var_expr_list)} {self.expr})'

class If(Expr):

    def __init__(self, sl: SourceLocation, parent: Union[None, Expr], cond: Expr, branch1: Expr, branch2: Expr):
        self.sl = sl
        self.parent = parent
        self.cond = cond
        self.branch1 = branch1
        self.branch2 = branch2

    def __str__(self) -> str:
        return f'(If {self.sl} {self.cond} {self.branch1} {self.branch2})'

class Call(Expr):

    def __init__(self, sl: SourceLocation, parent: Union[None, Expr], callee: Expr, arg_list: list[Expr]):
        self.sl = sl
        self.parent = parent
        self.callee = callee
        self.arg_list = arg_list

    def __str__(self) -> str:
        return f'(Call {self.sl} {self.callee} {unfold(self.arg_list)})'

class Seq(Expr):

    def __init__(self, sl: SourceLocation, parent: Union[None, Expr], expr_list: list[Expr]):
        self.sl = sl
        self.parent = parent
        self.expr_list = expr_list

    def __str__(self) -> str:
        return f'(Seq {self.sl} {unfold(self.expr_list)})'

def parse(tokens: deque[Token], debug: bool) -> Expr:
    
    def is_int(token: Token) -> bool:
        try:
            int(token.val)
            return True
        except ValueError:
            return False

    def is_str(token: Token) -> bool:
        return len(token.val) and token.val[0] == '"'

    def is_var(token: Token) -> bool:
        return token.val.isalpha()

    def consume(expected: str) -> Token:
        if not tokens:
            sys.exit(f'[Expr Parser Error] incomplete token stream')
        token = tokens.popleft()
        if token.val == expected:
            return token
        else:
            sys.exit(f'[Expr Parser Error] expected {expected}, got {token}')

    def parse_int() -> Int:
        if not tokens:
            sys.exit(f'[Expr Parser Error] incomplete token stream')
        token = tokens.popleft()
        if not is_int(token):
            sys.exit(f'[Expr Parser Error] expected an integer, got {token}')
        node = Int(token.sl, None, int(token.val))
        return node

    def parse_str() -> Str:
        if not tokens:
            sys.exit(f'[Expr Parser Error] incomplete token stream')
        token = tokens.popleft()
        if not is_str(token):
            sys.exit(f'[Expr Parser Error] expected a string, got {token}')
        node = Str(token.sl, None, eval(token.val))
        return node

    def parse_lambda() -> Lambda:
        start = consume('lambda')
        consume('(')
        if not tokens:
            sys.exit(f'[Expr Parser Error] incomplete token stream')
        var_list = []
        while tokens and is_var(tokens[0]):
            var_list.append(parse_var())
        consume(')')
        consume('{')
        expr = parse_expr()
        consume('}')
        node = Lambda(start.sl, None, var_list, expr)
        for v in node.var_list:
            v.parent = node
        node.expr.parent = node
        return node

    def parse_letrec() -> Letrec:
        start = consume('letrec')
        consume('(')
        if not tokens:
            sys.exit(f'[Expr Parser Error] incomplete token stream')
        var_expr_list = []
        while tokens and is_var(tokens[0]):
            v = parse_var()
            consume('=')
            e = parse_expr()
            var_expr_list.append((v, e))
        consume(')')
        consume('{')
        expr = parse_expr()
        consume('}')
        node = Letrec(start.sl, None, var_expr_list, expr)
        for v, e in node.var_expr_list:
            v.parent = node
            e.parent = node
        node.expr.parent = node
        return node

    def parse_if() -> If:
        start = consume('if')
        cond = parse_expr()
        consume('then')
        branch1 = parse_expr()
        consume('else')
        branch2 = parse_expr()
        node = If(start.sl, None, cond, branch1, branch2)
        node.cond.parent = node
        node.branch1.parent = node
        node.branch2.parent = node
        return node

    def parse_var() -> Var:
        if not tokens:
            sys.exit(f'[Expr Parser Error] incomplete token stream')
        token = tokens.popleft()
        if not is_var(token):
            sys.exit(f'[Expr Parser Error] expected a variable, got {token}')
        node = Var(token.sl, None, token.val)
        return node

    def parse_call() -> Call:
        start = consume('(')
        callee = parse_expr()
        if not tokens:
            sys.exit(f'[Expr Parser Error] incomplete token stream')
        arg_list = []
        while tokens and tokens[0].val != ')':
            arg_list.append(parse_expr())
        consume(')')
        node = Call(start.sl, None, callee, arg_list)
        node.callee.parent = node
        for a in node.arg_list:
            a.parent = node
        return node

    def parse_seq() -> Seq:
        start = consume('[')
        if not tokens:
            sys.exit(f'[Expr Parser Error] incomplete token stream')
        expr_list = []
        while tokens and tokens[0].val != ']':
            expr_list.append(parse_expr())
        if len(expr_list) == 0:
            sys.exit('[Expr Parser Error] zero-length sequence at {start}')
        consume(']')
        node = Seq(start.sl, None, expr_list)
        for e in node.expr_list:
            e.parent = node
        return node

    def parse_expr() -> Expr:
        if not tokens:
            sys.exit(f'[Expr Parser Error] incomplete token stream')
        if debug:
            sys.stderr.write(f'[Expr Debug] parsing expression starting with {tokens[0]}\n')
        if is_int(tokens[0]):
            return parse_int()
        elif is_str(tokens[0]):
            return parse_str()
        elif tokens[0].val == 'lambda':
            return parse_lambda()
        elif tokens[0].val == 'letrec':
            return parse_letrec()
        elif tokens[0].val == 'if':
            return parse_if()
        elif is_var(tokens[0]):
            return parse_var()
        elif tokens[0].val == '(':
            return parse_call()
        elif tokens[0].val == '[':
            return parse_seq()
        else:
            sys.exit(f'[Expr Parser Error] unrecognized expression starting with {tokens[0]}')
    
    expr = parse_expr()
    if tokens:
        sys.exit(f'[Expr Parser Error] redundant token stream starting at {tokens[0]}')
    return expr

### runtime

class Value:
    
    def __init__(self):
        pass

    def __str__(self) -> str:
        return 'value'

class Void(Value):

    def __init__(self):
        pass

    def __str__(self) -> str:
        return 'void'

class Integer(Value):

    def __init__(self, value: int):
        self.value = value

    def __str__(self) -> str:
        return str(self.value)

class String(Value):

    def __init__(self, value: str):
        self.value = value

    def __str__(self) -> str:
        return self.value

class Closure(Value):

    def __init__(self, env: list[tuple[str, int]], fun: Lambda):
        self.env = env
        self.fun = fun

    def __str__(self) -> str:
        return f'(closure {unfold(self.env)} {self.fun})'

class Layer:
    '''The layer class in the evaluation stack, where each layer is the expression currently under evaluation'''

    def __init__(self,
            env: list[tuple[str, int]], # env will be shared among layers in each frame
            expr: Expr,
            pc: int,
            local: dict[str, Union[Value, list[Value]]],
            frame: bool
        ):
        self.env = env # environment for the evaluation of the current expression
        self.expr = expr # the current expression under evaluation
        self.pc = pc # program counter (the pc-th step of evaluating this expression)
        self.local = local # variables local to this evaluation layer
        self.frame = frame # whether this layer starts a frame (a closure call or the initial layer)

    def __str__(self) -> str:
        return f'(layer {unfold(self.env)} {self.expr} {self.pc} {unfold(self.local)})'

class Continuation(Value):

    def __init__(self, stack: list[Layer]):
        self.stack = stack

    def __str__(self) -> str:
        return f'(continuation {unfold(self.stack)})'

class State:
    '''The state class for the interpretation, where each state object completely determines the current state (stack and store)'''

    def __init__(self, expr: Expr):
        self.stack = [Layer([], expr, 0, {}, True)]
        self.store = {}
        self.location = 0 # the next available addess in the store

    def __str__(self) -> str:
        return f'(state {unfold(self.stack)} {unfold(self.store)} {self.location})'

    def new(self, value: Value) -> int:
        self.store[self.location] = value
        self.location += 1
        return self.location - 1

    def gc(self, value) -> int: # TODO: may want to change the heap (store) to a list and do memory compaction (and relocation) after each GC
        visited_closures = set()
        visited_stacks = set()
        visited_locations = set()

        def mark_closure(closure: Closure) -> None:
            if id(closure) not in visited_closures:
                visited_closures.add(id(closure))
                for v, l in closure.env:
                    mark_location(l)
        
        def mark_stack(stack: list[Layer]) -> None:
            if id(stack) not in visited_stacks:
                visited_stacks.add(id(stack))
                for layer in stack:
                    if layer.frame:
                        for v, l in layer.env:
                            mark_location(l)
                    if layer.local:
                        for name, value in layer.local.items():
                            if type(value) == Closure:
                                mark_closure(value)
                            elif type(value) == Continuation:
                                mark_stack(value.stack)
                            elif type(value) == list:
                                for elem in value:
                                    if type(elem) == Closure:
                                        mark_closure(elem)
                                    elif type(elem) == Continuation:
                                        mark_stack(elem.stack)
                            

        def mark_location(location: int) -> None:
            if location not in visited_locations:
                visited_locations.add(location)
                val = self.store[location]
                if type(val) == Closure:
                    mark_closure(val)
                elif type(val) == Continuation:
                    mark_stack(val.stack)

        def sweep() -> int:
            to_remove = set()
            for k, v in self.store.items():
                if k not in visited_locations:
                    to_remove.add(k)
            for k in to_remove:
                del self.store[k]
            return len(to_remove)

        if type(value) == Closure:
            mark_closure(value)
        elif type(value) == Continuation:
            mark_stack(value.stack)
        mark_stack(self.stack)
        return sweep()

def check_args(vals: list[Value], ts: list[type]) -> bool:
    if len(vals) != len(ts):
        return False
    for i in range(len(vals)):
        if type(vals[i]) != ts[i]:
            return False
    return True

def is_lexical_name(name: str) -> bool:
    return name[0].islower()

def is_dynamic_name(name: str) -> bool:
    return name[0].isupper()

def filter_lexical(env: list[tuple[str, int]]) -> list[tuple[str, int]]:
    lex_env = []
    for v, l in env:
        if is_lexical_name(v):
            lex_env.append((v, l))
    return lex_env

def lookup_env(sl: SourceLocation, name: str, env: list[tuple[str, int]]) -> int:
    for i in range(len(env) - 1, -1, -1):
        if env[i][0] == name:
            return env[i][1]
    sys.exit(f'[Expr Runtime Error] undefined variable {name} at {sl} (intrinsic functions cannot be treated as variables)')

def lookup_stack(sl: SourceLocation, name: str, stack: list[Layer]) -> int:
    for i in range(len(stack) - 1, -1, -1):
        if stack[i].frame:
            for j in range(len(stack[i].env) - 1, -1, -1):
                if stack[i].env[j][0] == name:
                    return stack[i].env[j][1]
    sys.exit(f'[Expr Runtime Error] undefined variable {name} at {sl} (intrinsic functions cannot be treated as variables)')

### interpreter

def interpret(tree: Expr, debug: bool) -> Value:
    intrinsics = ['void',
                  'add', 'sub', 'mul', 'div', 'mod', 'lt',
                  'strlen', 'strslice', 'strcat', 'strlt', 'strint',
                  'getline',
                  'put',
                  'callcc',
                  'type',
                  'exit']
    state = State(tree)
    value = None
    ops = 0 # number of operations

    while True:
        
        # end of evaluation
        if len(state.stack) == 0:
            return value

        # GC control
        if ops == 1000: # TODO: may need a better heuristic for triggering GC (e.g. generation-based GC)
            cnt = state.gc(value)
            if debug:
                sys.stderr.write(f'[Expr Debug] GC collected {cnt} store cells\n')
            ops = 0
        ops += 1

        # evaluating the current layer
        layer = state.stack[-1]
        if debug:
            sys.stderr.write(f'[Expr Debug] evaluating AST node of type {type(layer.expr)} at {layer.expr.sl}\n')
        if type(layer.expr) == Int:
            value = Integer(layer.expr.value)
            state.stack.pop()
        elif type(layer.expr) == Str:
            value = String(layer.expr.value)
            state.stack.pop()
        elif type(layer.expr) == Lambda:
            value = Closure(filter_lexical(layer.env), layer.expr)
            state.stack.pop()
        elif type(layer.expr) == Letrec:
            if layer.pc == 0: # create locations and bind variables to them
                for v, e in layer.expr.var_expr_list:
                    layer.env.append((v.name, state.new(Void())))
                layer.pc += 1
            elif layer.pc <= len(layer.expr.var_expr_list): # evaluate binding expressions
                if layer.pc > 1: # update location content
                    var = layer.expr.var_expr_list[layer.pc - 2][0]
                    last_location = lookup_env(var.sl, var.name, layer.env)
                    state.store[last_location] = value
                state.stack.append(Layer(layer.env, layer.expr.var_expr_list[layer.pc - 1][1], 0, {}, False))
                layer.pc += 1
            elif layer.pc == len(layer.expr.var_expr_list) + 1: # evaluate body expression
                if layer.pc > 1: # update location content
                    var = layer.expr.var_expr_list[layer.pc - 2][0]
                    last_location = lookup_env(var.sl, var.name, layer.env)
                    state.store[last_location] = value
                state.stack.append(Layer(layer.env, layer.expr.expr, 0, {}, False))
                layer.pc += 1
            else: # finish letrec
                for i in range(len(layer.expr.var_expr_list)):
                    layer.env.pop()
                state.stack.pop()
        elif type(layer.expr) == If:
            if layer.pc == 0: # evaluate the condition
                state.stack.append(Layer(layer.env, layer.expr.cond, 0, {}, False))
                layer.pc += 1
            elif layer.pc == 1: # choose the branch to evaluate
                if type(value) != Integer:
                    sys.exit(f'[Expr Runtime Error] the condition of {layer.expr} evaluated to a value ({value}) of wrong type')
                if value.value != 0:
                    state.stack.append(Layer(layer.env, layer.expr.branch1, 0, {}, False))
                else:
                    state.stack.append(Layer(layer.env, layer.expr.branch2, 0, {}, False))
                layer.pc += 1
            else: # finish if
                state.stack.pop()
        elif type(layer.expr) == Var:
            if debug:
                sys.stderr.write(f'[Expr Debug] looking up the variable {layer.expr}\n')
            if is_lexical_name(layer.expr.name):
                value = state.store[lookup_env(layer.expr.sl, layer.expr.name, layer.env)]
            else:
                value = state.store[lookup_stack(layer.expr.sl, layer.expr.name, state.stack)]
            state.stack.pop()
        elif type(layer.expr) == Call:
            if type(layer.expr.callee) == Var and layer.expr.callee.name in intrinsics: # intrinsic call
                if layer.pc == 0: # initialize args
                    layer.local['args'] = []
                    layer.pc += 1
                elif layer.pc <= len(layer.expr.arg_list): # evaluate arguments
                    if layer.pc > 1:
                        layer.local['args'].append(value)
                    state.stack.append(Layer(layer.env, layer.expr.arg_list[layer.pc - 1], 0, {}, False))
                    layer.pc += 1
                else: # intrinsic call doesn't need to grow the stack, so this is the final step for this call
                    if layer.pc > 1:
                        layer.local['args'].append(value)
                    intrinsic = layer.expr.callee.name
                    args = layer.local['args']
                    if intrinsic == 'void':
                        if len(args) != 0:
                            sys.exit(f'[Expr Runtime Error] wrong number/type of arguments given to {layer.callee}')
                        value = Void()
                    elif intrinsic == 'add':
                        if not check_args(args, [Integer, Integer]):
                            sys.exit(f'[Expr Runtime Error] wrong number/type of arguments given to {layer.callee}')
                        value = Integer(args[0].value + args[1].value)
                    elif intrinsic == 'sub':
                        if not check_args(args, [Integer, Integer]):
                            sys.exit(f'[Expr Runtime Error] wrong number/type of arguments given to {layer.callee}')
                        value = Integer(args[0].value - args[1].value)
                    elif intrinsic == 'mul':
                        if not check_args(args, [Integer, Integer]):
                            sys.exit(f'[Expr Runtime Error] wrong number/type of arguments given to {layer.callee}')
                        value = Integer(args[0].value * args[1].value)
                    elif intrinsic == 'div':
                        if not check_args(args, [Integer, Integer]):
                            sys.exit(f'[Expr Runtime Error] wrong number/type of arguments given to {layer.callee}')
                        value = Integer(args[0].value // args[1].value)
                    elif intrinsic == 'mod':
                        if not check_args(args, [Integer, Integer]):
                            sys.exit(f'[Expr Runtime Error] wrong number/type of arguments given to {layer.callee}')
                        value = Integer(args[0].value % args[1].value)
                    elif intrinsic == 'lt':
                        if not check_args(args, [Integer, Integer]):
                            sys.exit(f'[Expr Runtime Error] wrong number/type of arguments given to {layer.callee}')
                        value = Integer(1) if args[0].value < args[1].value else Integer(0)
                    elif intrinsic == 'strlen':
                        if not check_args(args, [String]):
                            sys.exit(f'[Expr Runtime Error] wrong number/type of arguments given to {layer.callee}')
                        value = Integer(len(args[0].value))
                    elif intrinsic == 'strslice':
                        if not check_args(args, [String, Integer, Integer]):
                            sys.exit(f'[Expr Runtime Error] wrong number/type of arguments given to {layer.callee}')
                        start = args[1].value
                        end = args[2].value
                        value = String(args[0].value[start:end])
                    elif intrinsic == 'strcat':
                        if not check_args(args, [String, String]):
                            sys.exit(f'[Expr Runtime Error] wrong number/type of arguments given to {layer.callee}')
                        value = String(args[0].value + args[1].value)
                    elif intrinsic == 'strlt':
                        if not check_args(args, [String, String]):
                            sys.exit(f'[Expr Runtime Error] wrong number/type of arguments given to {layer.callee}')
                        value = Integer(1) if args[0].value < args[1].value else Integer(0)
                    elif intrinsic == 'strint':
                        if not check_args(args, [String]):
                            sys.exit(f'[Expr Runtime Error] wrong number/type of arguments given to {layer.callee}')
                        value = Integer(int(args[0].value))
                    elif intrinsic == 'getline':
                        if len(args) != 0:
                            sys.exit(f'[Expr Runtime Error] wrong number/type of arguments given to {layer.callee}')
                        try:
                            value = String(input())
                        except EOFError:
                            value = ''
                    elif intrinsic == 'put':
                        if not (len(args) >= 1 and all(map(lambda v : type(v) == Integer or type(v) == String, args))):
                            sys.exit(f'[Expr Runtime Error] wrong number/type of arguments given to {layer.callee}')
                        output = ''
                        for v in args:
                            if type(v) == Integer:
                                output += str(v.value)
                            else:
                                output += v.value
                        print(output, end = '', flush = True)
                        value = Void()
                    elif intrinsic == 'callcc':
                        if not check_args(args, [Closure]):
                            sys.exit(f'[Expr Runtime Error] wrong number/type of arguments given to {layer.callee}')
                        state.stack.pop()
                        cont = Continuation(deepcopy(state.stack)) # obtain the continuation (this deepcopy will not copy the store)
                        if debug:
                            sys.stderr.write(f'[Expr Debug] captured continuation {cont}\n')
                        closure = args[0]
                        # make a closure call layer and pass in the continuation
                        state.stack.append(Layer(closure.env[:] + [(closure.fun.var_list[0].name, state.new(cont))], closure.fun.expr, 0, {}, True))
                        continue # we already popped the stack in the callcc case
                    elif intrinsic == 'type':
                        if len(args) != 1:
                            sys.exit(f'[Expr Runtime Error] wrong number/type of arguments given to {layer.callee}')
                        arg = args[0]
                        if type(arg) == Void:
                            value = Integer(0)
                        elif type(arg) == Integer:
                            value = Integer(1)
                        elif type(arg) == String:
                            value = Integer(2)
                        elif type(arg) == Closure:
                            value = Integer(3)
                        elif type(arg) == Continuation:
                            value = Integer(4)
                        else:
                            sys.exit(f'[Expr Runtime Error] the intrinsic call {layer.expr} got a value ({arg}) of unknown type')
                    elif intrinsic == 'exit':
                        if len(args) != 0:
                            sys.exit(f'[Expr Runtime Error] wrong number/type of arguments given to {layer.callee}')
                        if debug:
                            sys.exit(f'[Expr Debug] execution stopped by the intrinsic call {layer.expr}')
                        else:
                            sys.exit()
                    state.stack.pop()
            else: # closure or continuation call
                if layer.pc == 0: # evaluate the callee
                    state.stack.append(Layer(layer.env, layer.expr.callee, 0, {}, False))
                    layer.pc += 1
                elif layer.pc == 1: # initialize args
                    layer.local['callee'] = value
                    layer.local['args'] = []
                    layer.pc += 1
                elif layer.pc - 1 <= len(layer.expr.arg_list): # evaluate arguments
                    if layer.pc - 1 > 1:
                        layer.local['args'].append(value)
                    state.stack.append(Layer(layer.env, layer.expr.arg_list[layer.pc - 2], 0, {}, False))
                    layer.pc += 1
                elif layer.pc - 1 == len(layer.expr.arg_list) + 1: # evaluate the call
                    if layer.pc - 1 > 1:
                        layer.local['args'].append(value)
                    callee = layer.local['callee']
                    args = layer.local['args']
                    if type(callee) == Closure:
                        closure = callee
                        if len(args) != len(closure.fun.var_list): # types will be checked inside the closure call
                            sys.exit(f'[Expr Runtime Error] wrong number/type of arguments given to {layer.callee}')
                        new_env = closure.env[:]
                        for i, v in enumerate(closure.fun.var_list):
                            new_env.append((v.name, state.new(args[i])))
                        state.stack.append(Layer(new_env, closure.fun.expr, 0, {}, True))
                        layer.pc += 1
                    elif type(callee) == Continuation:
                        cont = callee
                        if len(args) != 1: # the "value" variable already contains the last evaluation result of the arg
                            sys.exit(f'[Expr Runtime Error] wrong number/type of arguments given to {layer.callee}')
                        state.stack = deepcopy(cont.stack)
                        if debug:
                            sys.stderr.write(f'[Expr Debug] applied continuation {cont}, stack switched\n')
                        continue # the stack has been replaced, so we don't need to pop the previous stack's call layer
                    else:
                        sys.exit(f'[Expr Runtime Error] {layer.expr.callee} (whose evaluation result is {callee}) is not callable')
                else: # finish the call
                    state.stack.pop()
        elif type(layer.expr) == Seq:
            if layer.pc < len(layer.expr.expr_list): # evaluate the expressions, without the need of storing the results to local
                state.stack.append(Layer(layer.env, layer.expr.expr_list[layer.pc], 0, {}, False))
                layer.pc += 1
            else: # finish the sequence
                state.stack.pop()
        else:
            sys.exit(f'[Expr Runtime Error] unrecognized AST node {layer.expr}')

### main

def main(option: str, source: str) -> None:
    if option == 'run':
        start_time = time.time()
        tokens = lex(source, False)
        tree = parse(tokens, False)
        result = interpret(tree, False)
        print(result, flush = True)
        end_time = time.time()
        sys.stderr.write(f'Total Time (seconds): {end_time - start_time}\n')
    elif option == 'debug':
        # in debug mode the interpreter is much slower but the memory overhead shouldn't change a lot
        # and tracemalloc can slow-down the interpreter
        # so we measure space here and measure time in normal execution
        tracemalloc.start() 
        sys.stderr.write('[Expr Debug] *** starting lexer ***\n')
        tokens = lex(source, True)
        sys.stderr.write('[Expr Debug] *** starting parser ***\n')
        tree = parse(tokens, True)
        sys.stderr.write('[Expr Debug] *** starting interpreter ***\n')
        result = interpret(tree, True)
        print(result, flush = True)
        current_memory, peak_memory = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        sys.stderr.write(f'Peak Memory (KiB): {peak_memory / 1024}\n')
    elif option == 'dump-ast':
        tokens = lex(source, False)
        tree = parse(tokens, False)
        print(tree, flush = True)

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
