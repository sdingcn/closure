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
    if debug:
        sys.stderr.write('[Expr Debug] *** starting lexer ***\n')

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
        # skip whitespaces
        while chars and chars[0].isspace():
            space = chars.popleft()
            if space == '\n':
                line += 1
                col = 1
            else:
                col += 1
        # read the next token
        if chars:
            sl = SourceLocation(line, col)
            # integer without +/-
            if chars[0].isdigit():
                val = ''
                while chars and chars[0].isdigit():
                    val += chars.popleft()
                    col += 1
            # integer with +/-
            elif chars[0] in ('-', '+'):
                if len(chars) > 1 and chars[1].isdigit():
                    val = chars.popleft()
                    col += 1
                    while chars and chars[0].isdigit():
                        val += chars.popleft()
                        col += 1
                else:
                    sys.exit(f'[Expr Lexer Error] incomplete integer literal at {sl}')
            # variable / intrinsic / keyword
            elif chars[0].isalpha():
                val = ''
                while chars and chars[0].isalpha():
                    val += chars.popleft()
                    col += 1
            # special symbol
            elif chars[0] in ('(', ')', '{', '}', '[', ']', '='):
                val = chars.popleft()
                col += 1
            # string
            elif chars[0] == '"':
                val = chars.popleft()
                col += 1
                while chars and (chars[0] != '"' or (chars[0] == '"' and count_trailing_escape(val) % 2 != 0)):
                    val += chars.popleft()
                    if val[-1] == '\n':
                        line += 1
                        col = 1
                    else:
                        col += 1
                if chars and chars[0] == '"':
                    val += chars.popleft()
                    col += 1
                else:
                    sys.exit(f'[Expr Lexer Error] incomplete string literal at {sl}')
            # comment
            elif chars[0] == '#':
                chars.popleft()
                col += 1
                while chars and chars[0] != '\n':
                    chars.popleft()
                    col += 1
                return next_token()
            else:
                sys.exit(f'[Expr Lexer Error] unsupported character {chars[0]} at {sl}')
            token = Token(sl, val)
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
    ''' Normally we don't create instances of this base class. '''

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
        return f'(Str {self.sl} {self.value})'

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
    if debug:
        sys.stderr.write('[Expr Debug] *** starting parser ***\n')
    
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
        # check keywords before var to avoid recognizing keywords as vars
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
    ''' Normally we don't create instances of this base class. '''
    
    def __init__(self):
        pass

    def __str__(self) -> str:
        return 'Value'

class Void(Value):

    def __init__(self):
        # the location of this value (object) in the store (if allocated)
        self.location = None

    def __str__(self) -> str:
        return 'Void'

class Integer(Value):

    def __init__(self, value: int):
        self.location = None
        self.value = value

    def __str__(self) -> str:
        return f'(Integer {self.value})'

class String(Value):

    def __init__(self, value: str):
        self.location = None
        self.value = value

    def __str__(self) -> str:
        return f'(String {self.value})'

class Closure(Value):

    def __init__(self, env: list[tuple[str, int]], fun: Lambda):
        self.location = None
        self.env = env
        self.fun = fun

    def __str__(self) -> str:
        return f'(Closure {unfold(self.env)} {self.fun})'

class Layer:
    '''The layer class in the evaluation stack, where each layer is the expression currently under evaluation'''

    def __init__(self,
            # env will be shared among layers in each frame
            env: list[tuple[str, int]], 
            expr: Expr,
            pc: int,
            local: dict[str, Union[Value, list[Value]]],
            frame: bool
        ):
        # environment for the evaluation of the current expression
        self.env = env 
        # the current expression under evaluation
        self.expr = expr
        # program counter (the pc-th step of evaluating this expression)
        self.pc = pc
        # variables local to this evaluation layer
        self.local = local
        # whether this layer starts a frame (a closure call or the initial layer)
        self.frame = frame

    def __str__(self) -> str:
        return f'(Layer {unfold(self.env)} {self.expr} {self.pc} {unfold(self.local)} {self.frame})'

class Continuation(Value):

    def __init__(self, stack: list[Layer]):
        self.location = None
        # we only need to store the stack, because objects in the heap are immutable
        self.stack = stack

    def __str__(self) -> str:
        return f'(Continuation {unfold(self.stack)})'

class State:
    '''The state class for the interpretation, where each state object completely determines the current state (stack and store)'''

    def __init__(self, expr: Expr):
        self.stack = [Layer([], expr, 0, {}, True)]
        # the heap
        self.store = []
        # the next available addess in the store
        self.location = 0
        # private values
        self._ref_size = 8
        self._empty_store_size = sys.getsizeof(self.store)

    def __str__(self) -> str:
        return f'(State {unfold(self.stack)} {unfold(self.store)} {self.location})'

    def get_store_capacity(self) -> int:
        # capacity >= length
        return (sys.getsizeof(self.store) - self._empty_store_size) // self._ref_size

    def new(self, value: Value) -> int:
        ''' heap space allocation '''
        if self.location < len(self.store):
            self.store[self.location] = value
            value.location = self.location
        else:
            # the self.store array is managed by Python and will automatically grow
            self.store.append(value)
            value.location = self.location
        self.location += 1
        return self.location - 1

    def mark(self, value: Value) -> tuple[set[int], list[Value]]:
        # ids
        visited_closures = set()
        # ids
        visited_stacks = set()
        # integer locations
        visited_locations = set()
        # Python references
        visited_values = []

        def mark_closure(closure: Closure) -> None:
            if id(closure) not in visited_closures:
                visited_closures.add(id(closure))
                visited_values.append(closure)
                for v, l in closure.env:
                    mark_location(l)
        
        def mark_stack(stack: list[Layer]) -> None:
            if id(stack) not in visited_stacks:
                visited_stacks.add(id(stack))
                visited_values.append(stack)
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
        
        # mark both the value and the stack
        if type(value) == Closure:
            mark_closure(value)
        elif type(value) == Continuation:
            mark_stack(value.stack)
        mark_stack(self.stack)
        # returning visited_values is for relocating their internal location values
        return (visited_locations, visited_values)

    def sweep_and_compact(self, visited_locations: set[int]) -> tuple[int, dict[int, int]]:
        removed = 0
        # old location -> new location
        relocation = {}
        n = len(self.store)
        i = 0
        j = 0
        while j < n:
            if j in visited_locations:
                self.store[i] = self.store[j]
                self.store[i].location = i
                relocation[j] = i
                i += 1
            else:
                removed += 1
            j += 1
        # adjust the next available location
        self.location = i
        return (removed, relocation)
    
    def relocate(self, visited_values: list[Value], relocation: dict[int, int]) -> None:
        # don't need to recursively update because all descendant objects are in visited_values
        for value in visited_values: 
            if type(value) == Closure:
                for i in range(len(value.env)):
                    value.env[i] = (value.env[i][0], relocation[value.env[i][1]])
            elif type(value) == list:
                for layer in value:
                    if layer.frame:
                        for i in range(len(layer.env)):
                            layer.env[i] = (layer.env[i][0], relocation[layer.env[i][1]])

    def gc(self, value) -> int:
        ''' mark-and-sweep garbage collection '''
        visited_locations, visited_values = self.mark(value)
        removed, relocation = self.sweep_and_compact(visited_locations)
        self.relocate(visited_values, relocation)
        return removed

def check_args_error_exit(callee: Expr, args: list[Value], ts: list[type]) -> bool:
    ''' check whether arguments conform to types '''
    if len(args) != len(ts):
        sys.exit(f'[Expr Runtime Error] wrong number of arguments given to {callee}')
    for i in range(len(args)):
        if not isinstance(args[i], ts[i]):
            sys.exit(f'[Expr Runtime Error] wrong type of arguments given to {callee}')

def is_lexical_name(name: str) -> bool:
    return name[0].islower()

def is_dynamic_name(name: str) -> bool:
    return name[0].isupper()

def filter_lexical(env: list[tuple[str, int]]) -> list[tuple[str, int]]:
    ''' find out lexical variable-location pairs in an environment '''
    lex_env = []
    for v, l in env:
        if is_lexical_name(v):
            lex_env.append((v, l))
    return lex_env

def lookup_env(sl: SourceLocation, name: str, env: list[tuple[str, int]]) -> int:
    ''' lexically scoped variable lookup '''
    for i in range(len(env) - 1, -1, -1):
        if env[i][0] == name:
            return env[i][1]
    sys.exit(f'[Expr Runtime Error] undefined variable {name} at {sl} (intrinsic functions cannot be treated as variables)')

def lookup_stack(sl: SourceLocation, name: str, stack: list[Layer]) -> int:
    ''' dynamically scoped variable lookup '''
    for i in range(len(stack) - 1, -1, -1):
        if stack[i].frame:
            for j in range(len(stack[i].env) - 1, -1, -1):
                if stack[i].env[j][0] == name:
                    return stack[i].env[j][1]
    sys.exit(f'[Expr Runtime Error] undefined variable {name} at {sl} (intrinsic functions cannot be treated as variables)')

### interpreter

def interpret(tree: Expr, debug: bool) -> Value:
    if debug:
        sys.stderr.write('[Expr Debug] *** starting interpreter ***\n')

    intrinsics = ['void',
                  'add', 'sub', 'mul', 'div', 'mod', 'lt',
                  'strlen', 'strslice', 'strcat', 'strlt', 'strint',
                  'getline',
                  'put',
                  'callcc',
                  'type',
                  'eval',
                  'exit']
    
    # state
    state = State(tree)
    # the evaluation result of the last stack layer
    value = None

    # used for GC control
    insufficient_capacity = -1

    # we just adjust "state.stack" and "value"
    # the evaluation will automatically continue along the while loop
    while True:
        
        # end of evaluation
        if len(state.stack) == 0:
            return value

        # GC control
        capacity = state.get_store_capacity()
        # insufficient_capacity is the last capacity where GC failed
        if capacity > insufficient_capacity:
            if state.location >= 0.8 * capacity:
                cnt = state.gc(value)
                if debug:
                    sys.stderr.write(f'[Expr Debug] GC collected {cnt} store cells\n')
                # GC failed to release enough memory, meaning that the capacity needs to grow
                if state.location >= 0.8 * capacity:
                    insufficient_capacity = capacity
                # after GC the current capacity is enough so we keep the previous insufficient_capacity
                else:
                    pass
        # the capacity is insufficient, so we allow it to naturally grow and don't run GC before the growing
        else:
            pass

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
            # create locations and bind variables to them
            if layer.pc == 0:
                for v, e in layer.expr.var_expr_list:
                    layer.env.append((v.name, state.new(Void())))
                layer.pc += 1
            # evaluate binding expressions
            elif layer.pc <= len(layer.expr.var_expr_list):
                # update location content
                if layer.pc > 1:
                    var = layer.expr.var_expr_list[layer.pc - 2][0]
                    last_location = lookup_env(var.sl, var.name, layer.env)
                    state.store[last_location] = value
                state.stack.append(Layer(layer.env, layer.expr.var_expr_list[layer.pc - 1][1], 0, {}, False))
                layer.pc += 1
            # evaluate body expression
            elif layer.pc == len(layer.expr.var_expr_list) + 1:
                # update location content
                if layer.pc > 1:
                    var = layer.expr.var_expr_list[layer.pc - 2][0]
                    last_location = lookup_env(var.sl, var.name, layer.env)
                    state.store[last_location] = value
                state.stack.append(Layer(layer.env, layer.expr.expr, 0, {}, False))
                layer.pc += 1
            # finish letrec
            else:
                for i in range(len(layer.expr.var_expr_list)):
                    layer.env.pop()
                state.stack.pop()
        elif type(layer.expr) == If:
            # evaluate the condition
            if layer.pc == 0:
                state.stack.append(Layer(layer.env, layer.expr.cond, 0, {}, False))
                layer.pc += 1
            # choose the branch to evaluate
            elif layer.pc == 1:
                if type(value) != Integer:
                    sys.exit(f'[Expr Runtime Error] the condition of {layer.expr} evaluated to a value ({value}) of wrong type')
                if value.value != 0:
                    state.stack.append(Layer(layer.env, layer.expr.branch1, 0, {}, False))
                else:
                    state.stack.append(Layer(layer.env, layer.expr.branch2, 0, {}, False))
                layer.pc += 1
            # finish if
            else:
                state.stack.pop()
        elif type(layer.expr) == Var:
            if debug:
                sys.stderr.write(f'[Expr Debug] looking up the variable {layer.expr}\n')
            # two types of variables
            if is_lexical_name(layer.expr.name):
                value = state.store[lookup_env(layer.expr.sl, layer.expr.name, layer.env)]
            else:
                value = state.store[lookup_stack(layer.expr.sl, layer.expr.name, state.stack)]
            state.stack.pop()
        elif type(layer.expr) == Call:
            # intrinsic call
            if type(layer.expr.callee) == Var and layer.expr.callee.name in intrinsics:
                # initialize args
                if layer.pc == 0:
                    layer.local['args'] = []
                    layer.pc += 1
                # evaluate arguments
                elif layer.pc <= len(layer.expr.arg_list):
                    if layer.pc > 1:
                        layer.local['args'].append(value)
                    state.stack.append(Layer(layer.env, layer.expr.arg_list[layer.pc - 1], 0, {}, False))
                    layer.pc += 1
                # intrinsic call doesn't need to grow the stack, so this is the final step for this call
                else:
                    if layer.pc > 1:
                        layer.local['args'].append(value)
                    intrinsic = layer.expr.callee.name
                    args = layer.local['args']
                    # a gigantic series of if conditions, one for each intrinsic function
                    if intrinsic == 'void':
                        check_args_error_exit(layer.expr.callee, args, [])
                        value = Void()
                    elif intrinsic == 'add':
                        check_args_error_exit(layer.expr.callee, args, [Integer, Integer])
                        value = Integer(args[0].value + args[1].value)
                    elif intrinsic == 'sub':
                        check_args_error_exit(layer.expr.callee, args, [Integer, Integer])
                        value = Integer(args[0].value - args[1].value)
                    elif intrinsic == 'mul':
                        check_args_error_exit(layer.expr.callee, args, [Integer, Integer])
                        value = Integer(args[0].value * args[1].value)
                    elif intrinsic == 'div':
                        check_args_error_exit(layer.expr.callee, args, [Integer, Integer])
                        value = Integer(args[0].value // args[1].value)
                    elif intrinsic == 'mod':
                        check_args_error_exit(layer.expr.callee, args, [Integer, Integer])
                        value = Integer(args[0].value % args[1].value)
                    elif intrinsic == 'lt':
                        check_args_error_exit(layer.expr.callee, args, [Integer, Integer])
                        value = Integer(1) if args[0].value < args[1].value else Integer(0)
                    elif intrinsic == 'strlen':
                        check_args_error_exit(layer.expr.callee, args, [String])
                        value = Integer(len(args[0].value))
                    elif intrinsic == 'strslice':
                        check_args_error_exit(layer.expr.callee, args, [String, Integer, Integer])
                        start = args[1].value
                        end = args[2].value
                        value = String(args[0].value[start:end])
                    elif intrinsic == 'strcat':
                        check_args_error_exit(layer.expr.callee, args, [String, String])
                        value = String(args[0].value + args[1].value)
                    elif intrinsic == 'strlt':
                        check_args_error_exit(layer.expr.callee, args, [String, String])
                        value = Integer(1) if args[0].value < args[1].value else Integer(0)
                    elif intrinsic == 'strint':
                        check_args_error_exit(layer.expr.callee, args, [String])
                        value = Integer(int(args[0].value))
                    elif intrinsic == 'getline':
                        check_args_error_exit(layer.expr.callee, args, [])
                        try:
                            value = String(input())
                        except EOFError:
                            value = ''
                    elif intrinsic == 'put':
                        if not (len(args) >= 1 and all(map(lambda v : isinstance(v, Value), args))):
                            sys.exit(f'[Expr Runtime Error] wrong number/type of arguments given to {layer.expr.callee}')
                        output = ''
                        for v in args:
                            if type(v) == Void:
                                output += '<void>'
                            elif type(v) == Integer:
                                output += str(v.value)
                            elif type(v) == String:
                                output += v.value
                            elif type(v) == Closure:
                                output += '<closure>'
                            elif type(v) == Continuation:
                                output += '<continuation>'
                        print(output, end = '', flush = True)
                        # the return value of put is void
                        value = Void()
                    elif intrinsic == 'callcc':
                        check_args_error_exit(layer.expr.callee, args, [Closure])
                        state.stack.pop()
                        # obtain the continuation (this deepcopy will not copy the store)
                        cont = Continuation(deepcopy(state.stack))
                        if debug:
                            sys.stderr.write(f'[Expr Debug] captured continuation {cont}\n')
                        closure = args[0]
                        # make a closure call layer and pass in the continuation
                        addr = cont.location if cont.location != None else state.new(cont)
                        state.stack.append(Layer(closure.env[:] + [(closure.fun.var_list[0].name, addr)], closure.fun.expr, 0, {}, True))
                        # we already popped the stack in this case, so just continue the evaluation
                        continue
                    elif intrinsic == 'type':
                        check_args_error_exit(layer.expr.callee, args, [Value])
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
                    elif intrinsic == 'eval':
                        check_args_error_exit(layer.expr.callee, args, [String])
                        arg = args[0]
                        if debug:
                            sys.stderr.write(f'[Expr Debug] eval started a new interpreter instance at {layer.expr}\n')
                            value = debug_run(arg.value)
                            sys.stderr.write(f'[Expr Debug] eval stopped the new interpreter instance at {layer.expr}\n')
                        else:
                            value = normal_run(arg.value)
                    elif intrinsic == 'exit':
                        check_args_error_exit(layer.expr.callee, args, [])
                        if debug:
                            sys.stderr.write(f'[Expr Debug] execution stopped by the intrinsic call {layer.expr}\n')
                        # the interpreter returns 0
                        sys.exit()
                    state.stack.pop()
            # closure or continuation call
            else:
                # evaluate the callee
                if layer.pc == 0:
                    state.stack.append(Layer(layer.env, layer.expr.callee, 0, {}, False))
                    layer.pc += 1
                # initialize callee and args
                elif layer.pc == 1:
                    layer.local['callee'] = value
                    layer.local['args'] = []
                    layer.pc += 1
                # evaluate arguments
                elif layer.pc - 1 <= len(layer.expr.arg_list):
                    if layer.pc - 1 > 1:
                        layer.local['args'].append(value)
                    state.stack.append(Layer(layer.env, layer.expr.arg_list[layer.pc - 2], 0, {}, False))
                    layer.pc += 1
                # evaluate the call
                elif layer.pc - 1 == len(layer.expr.arg_list) + 1:
                    if layer.pc - 1 > 1:
                        layer.local['args'].append(value)
                    callee = layer.local['callee']
                    args = layer.local['args']
                    if type(callee) == Closure:
                        closure = callee
                        # types will be checked inside the closure call
                        if len(args) != len(closure.fun.var_list):
                            sys.exit(f'[Expr Runtime Error] wrong number/type of arguments given to {layer.expr.callee}')
                        new_env = closure.env[:]
                        for i, v in enumerate(closure.fun.var_list):
                            addr = args[i].location if args[i].location != None else state.new(args[i])
                            new_env.append((v.name, addr))
                        # evaluate the closure call
                        state.stack.append(Layer(new_env, closure.fun.expr, 0, {}, True))
                        layer.pc += 1
                    elif type(callee) == Continuation:
                        cont = callee
                        # the "value" variable already contains the last evaluation result of the args, so we just continue
                        if len(args) != 1:
                            sys.exit(f'[Expr Runtime Error] wrong number/type of arguments given to {layer.expr.callee}')
                        # replace the stack
                        state.stack = deepcopy(cont.stack)
                        if debug:
                            sys.stderr.write(f'[Expr Debug] applied continuation {cont}, stack switched\n')
                        # the stack has been replaced, so we don't need to pop the previous stack's call layer
                        # the previous stack is simply discarded
                        continue
                    else:
                        sys.exit(f'[Expr Runtime Error] {layer.expr.callee} (whose evaluation result is {callee}) is not callable')
                # finish the call
                else:
                    state.stack.pop()
        elif type(layer.expr) == Seq:
            # evaluate the expressions, without the need of storing the results to local
            if layer.pc < len(layer.expr.expr_list):
                state.stack.append(Layer(layer.env, layer.expr.expr_list[layer.pc], 0, {}, False))
                layer.pc += 1
            # finish the sequence
            else:
                state.stack.pop()
        else:
            sys.exit(f'[Expr Runtime Error] unrecognized AST node {layer.expr}')

### main

def normal_run(source: str) -> Value:
    tokens = lex(source, False)
    tree = parse(tokens, False)
    result = interpret(tree, False)
    return result

def debug_run(source: str) -> Value:
    tokens = lex(source, True)
    tree = parse(tokens, True)
    result = interpret(tree, True)
    return result

def main(option: str, source: str) -> None:
    if option == 'run':
        print(normal_run(source))
    elif option == 'time':
        start_time = time.time()
        print(normal_run(source))
        end_time = time.time()
        sys.stderr.write(f'Total time (seconds): {end_time - start_time}\n')
    elif option == 'space':
        tracemalloc.start() 
        print(normal_run(source))
        current_memory, peak_memory = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        sys.stderr.write(f'Peak memory (KiB): {peak_memory / 1024}\n')
    elif option == 'debug':
        print(debug_run(source))
    elif option == 'dump-ast':
        tokens = lex(source, False)
        tree = parse(tokens, False)
        print(tree)

if __name__ == '__main__':
    if len(sys.argv) != 3 or sys.argv[1] not in ['run', 'time', 'space', 'debug', 'dump-ast']:
        sys.exit(
            'Usage:\n'
            f'\tpython3 {sys.argv[0]} run <source-file>\n'
            f'\tpython3 {sys.argv[0]} time <source-file>\n'
            f'\tpython3 {sys.argv[0]} space <source-file>\n'
            f'\tpython3 {sys.argv[0]} debug <source-file>\n'
            f'\tpython3 {sys.argv[0]} dump-ast <source-file>'
        )
    with open(sys.argv[2], 'r') as f:
        main(sys.argv[1], f.read())
