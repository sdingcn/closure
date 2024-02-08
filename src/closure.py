import sys
import re
from collections import deque
from typing import Union, Callable
from copy import deepcopy

### helper functions and classes

class SourceLocation:

    def __init__(self, line: int = 1, col: int = 1):
        self.line = line
        self.col = col

    def __str__(self) -> str:
        if self.line <= 0 or self.col <= 0:
            return f'(SourceLocation N/A)'
        return f'(SourceLocation {self.line} {self.col})'

    def revert(self) -> None:
        self.line = 1
        self.col = 1

    def update(self, char: str) -> None:
        if char == '\n':
            self.line += 1
            self.col = 1
        else:
            self.col += 1

def lexer_error(sl: SourceLocation, msg: str) -> None:
    sys.exit(f'[Lexer Error {sl}] {msg}')

def parser_error(sl: SourceLocation, msg: str) -> None:
    sys.exit(f'[Parser Error {sl}] {msg}')

def runtime_error(sl: SourceLocation, msg: str) -> None:
    sys.exit(f'[Runtime Error {sl}] {msg}')

### lexer

class Token:

    def __init__(self, sl: SourceLocation, src: str):
        self.sl = sl
        self.src = src

def lex(source: str) -> deque[Token]:
    charset = set(
        "abcdefghijklmnopqrstuvwxyz"
        "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        "0123456789"
        "`~!@#$%^&*()-_=+[{]}\\|;:'\",<.>/?"
        " \t\n"
    )
    sl = SourceLocation()
    for char in source:
        if char not in charset:
            lexer_error(sl, 'unsupported character')
        sl.update(char)
    sl.revert()
    chars = deque(source)

    def count_trailing_escape(s: str) -> int:
        cnt = 0
        pos = len(s) - 1
        while pos >= 0 and s[pos] == '\\':
            cnt += 1
            pos -= 1
        return cnt

    integer_regex = re.compile(r'[+-]?(0|[1-9][0-9]*)')

    def next_token() -> Union[None, Token]:
        nonlocal sl
        # skip whitespaces
        while chars and chars[0].isspace():
            sl.update(chars.popleft())
        # read the next token
        if chars:
            sl_copy = deepcopy(sl)
            src = ''
            # number literal
            if chars[0].isdigit() or chars[0] in ('-', '+'):
                while chars and (chars[0].isdigit() or (chars[0] in ('-', '+'))):
                    src += chars.popleft()
                    sl.update(src[-1])
                if not integer_regex.fullmatch(src):
                    lexer_error(sl, 'invalid number literal')
            # variable / keyword
            elif chars[0].isalpha():
                while chars and (chars[0].isalpha() or chars[0].isdigit() or chars[0] == '_'):
                    src += chars.popleft()
                    sl.update(src[-1])
            # intrinsic
            elif chars[0] == '.':
                while chars and (not (chars[0].isspace() or chars[0] == ')')):
                    src += chars.popleft()
                    sl.update(src[-1])
            # special symbol
            elif chars[0] in '(){}[]=@&':
                src += chars.popleft()
                sl.update(src[-1])
            # string literal
            elif chars[0] == '"':
                src += chars.popleft()
                sl.update(src[-1])
                while chars and (chars[0] != '"' or (chars[0] == '"' and count_trailing_escape(src) % 2 != 0)):
                    # All original characters are kept, including real newlines (not escape sequences like "\n").
                    src += chars.popleft()
                    sl.update(src[-1])
                if chars and chars[0] == '"':
                    src += chars.popleft()
                    sl.update(src[-1])
                else:
                    lexer_error(sl, 'incomplete string literal')
            # comment
            elif chars[0] == '#':
                sl.update(chars.popleft())
                while chars and chars[0] != '\n':
                    sl.update(chars.popleft())
                # next_token() will consume the newline character and recursively continue.
                return next_token()
            else:
                lexer_error(sl, 'unsupported token starting character')
            return Token(sl_copy, src)
        # end of character stream
        else:
            return None

    # lexer entry
    tokens = deque()
    while True:
        token = next_token()
        if token:
            tokens.append(token)
        else:
            break
    return tokens

### parser

class ExprNode:
    ''' Normally we don't create instances of this base class. '''
    pass

class IntegerNode(ExprNode):

    def __init__(self, sl: SourceLocation, i: int):
        self.sl = sl
        self.i = i

class StringNode(ExprNode):

    def __init__(self, sl: SourceLocation, s: str):
        self.sl = sl
        self.s = s

class IntrinsicNode(ExprNode):

    def __init__(self, sl: SourceLocation, name: str):
        self.sl = sl
        self.name = name

class VariableNode(ExprNode):

    def __init__(self, sl: SourceLocation, name: str):
        self.sl = sl
        self.name = name

class SetNode(ExprNode):

    def __init__(self, sl: SourceLocation, var: VariableNode, expr: ExprNode):
        self.sl = sl
        self.var = var
        self.expr = expr

class LambdaNode(ExprNode):

    def __init__(self, sl: SourceLocation, var_list: list[VariableNode], expr: ExprNode):
        self.sl = sl
        self.var_list = var_list
        self.expr = expr

class LetrecNode(ExprNode):

    def __init__(self, sl: SourceLocation, var_expr_list: list[tuple[VariableNode, ExprNode]], expr: ExprNode):
        self.sl = sl
        self.var_expr_list = var_expr_list
        self.expr = expr

class IfNode(ExprNode):

    def __init__(self, sl: SourceLocation, cond: ExprNode, branch1: ExprNode, branch2: ExprNode):
        self.sl = sl
        self.cond = cond
        self.branch1 = branch1
        self.branch2 = branch2

class CallNode(ExprNode):

    def __init__(self, sl: SourceLocation, callee: ExprNode, arg_list: list[ExprNode]):
        self.sl = sl
        self.callee = callee
        self.arg_list = arg_list

class SequenceNode(ExprNode):

    def __init__(self, sl: SourceLocation, expr_list: list[ExprNode]):
        self.sl = sl
        self.expr_list = expr_list

class QueryNode(ExprNode):

    def __init__(self, sl: SourceLocation, var: VariableNode, expr: ExprNode):
        self.sl = sl
        self.var = var
        self.expr = expr

class AccessNode(ExprNode):

    def __init__(self, sl: SourceLocation, var: VariableNode, expr: ExprNode):
        self.sl = sl
        self.var = var
        self.expr = expr

def parse(tokens: deque[Token]) -> ExprNode:
    is_number_token = lambda token: len(token.src) and (token.src[0].isdigit() or token.src[0] in ('-', '+'))
    is_string_token = lambda token: len(token.src) and token.src[0] == '"'
    is_intrinsic_token = lambda token: len(token.src) and token.src[0] == '.'
    is_variable_token = lambda token: len(token.src) and token.src[0].isalpha()
    is_token = lambda s: lambda token: token.src == s

    def consume(predicate: Callable) -> Token:
        if not tokens:
            parser_error(SourceLocation(-1, -1), 'incomplete token stream')
        token = tokens.popleft()
        if not predicate(token):
            parser_error(token.sl, 'unexpected token')
        return token

    def parse_number() -> IntegerNode:
        token = consume(is_number_token)
        return IntegerNode(token.sl, int(token.src))

    def parse_string() -> StringNode:
        token = consume(is_string_token)
        content = deque(token.src[1:-1])
        s = ''
        while content:
            char = content.popleft()
            if char == '\\':
                if content:
                    nxt = content.popleft()
                    if nxt == '\\':
                        s += '\\'
                    elif nxt == '"':
                        s += '"'
                    elif nxt == 't':
                        s += '\t'
                    elif nxt == 'n':
                        s += '\n'
                    else:
                        parser_error(token.sl, 'unsupported escape sequence')
                else:
                    parser_error(token.sl, 'incomplete escape sequence')
            else:
                s += char
        return StringNode(token.sl, s)

    def parse_intrinsic() -> IntrinsicNode:
        token = consume(is_intrinsic_token)
        return IntrinsicNode(token.sl, token.src)

    def parse_set() -> SetNode:
        start = consume(is_token('set'))
        var = parse_variable()
        expr = parse_expr()
        return SetNode(start.sl, var, expr)

    def parse_lambda() -> LambdaNode:
        start = consume(is_token('lambda'))
        consume(is_token('('))
        var_list = []
        while tokens and is_variable_token(tokens[0]):
            var_list.append(parse_variable())
        consume(is_token(')'))
        expr = parse_expr()
        return LambdaNode(start.sl, var_list, expr)

    def parse_letrec() -> LetrecNode:
        start = consume(is_token('letrec'))
        consume(is_token('('))
        var_expr_list = []
        while tokens and is_variable_token(tokens[0]):
            v = parse_variable()
            consume(is_token('='))
            e = parse_expr()
            var_expr_list.append((v, e))
        consume(is_token(')'))
        expr = parse_expr()
        return LetrecNode(start.sl, var_expr_list, expr)

    def parse_if() -> IfNode:
        start = consume(is_token('if'))
        cond = parse_expr()
        branch1 = parse_expr()
        branch2 = parse_expr()
        return IfNode(start.sl, cond, branch1, branch2)

    def parse_variable() -> VariableNode:
        token = consume(is_variable_token)
        return VariableNode(token.sl, token.src)

    def parse_call() -> CallNode:
        start = consume(is_token('('))
        if not tokens:
            parser_error(start.sl, 'incomplete token stream')
        if is_intrinsic_token(tokens[0]):
            callee = parse_intrinsic()
        else:
            callee = parse_expr()
        arg_list = []
        while tokens and tokens[0].src != ')':
            arg_list.append(parse_expr())
        consume(is_token(')'))
        return CallNode(start.sl, callee, arg_list)

    def parse_sequence() -> SequenceNode:
        start = consume(is_token('['))
        expr_list = []
        while tokens and tokens[0].src != ']':
            expr_list.append(parse_expr())
        if len(expr_list) == 0:
            parser_error(start.sl, 'zero-length sequence')
        consume(is_token(']'))
        return SequenceNode(start.sl, expr_list)

    def parse_query() -> QueryNode:
        start = consume(is_token('@'))
        var = parse_variable()
        expr = parse_expr()
        return QueryNode(start.sl, var, expr)

    def parse_access() -> AccessNode:
        start = consume(is_token('&'))
        var = parse_variable()
        expr = parse_expr()
        return AccessNode(start.sl, var, expr)

    def parse_expr() -> ExprNode:
        if not tokens:
            parser_error(SourceLocation(-1, -1), 'incomplete token stream')
        elif is_number_token(tokens[0]):
            return parse_number()
        elif is_string_token(tokens[0]):
            return parse_string()
        elif tokens[0].src == 'set':
            return parse_set()
        elif tokens[0].src == 'lambda':
            return parse_lambda()
        elif tokens[0].src == 'letrec':
            return parse_letrec()
        elif tokens[0].src == 'if':
            return parse_if()
        # check keywords before var to avoid recognizing keywords as vars
        elif is_variable_token(tokens[0]):
            return parse_variable()
        elif tokens[0].src == '(':
            return parse_call()
        elif tokens[0].src == '[':
            return parse_sequence()
        elif tokens[0].src == '@':
            return parse_query()
        elif tokens[0].src == '&':
            return parse_access()
        else:
            parser_error(tokens[0].sl, 'unrecognized token')
    
    # parser entry
    expr = parse_expr()
    if tokens:
        parser_error(tokens[0].sl, 'redundant token(s)')
    return expr

### runtime

class Value:
    ''' Normally we don't create instances of this base class. '''
    pass

class Void(Value):

    def __init__(self):
        # the location of this value (object) in the store (if allocated)
        self.location = None

    def __str__(self) -> str:
        return '<void>'

class Integer(Value):

    def __init__(self, i: Union[int, bool]):
        self.location = None
        if type(i) == bool:
            self.i = 1 if i else 0
        else:
            self.i = i

    def __str__(self) -> str:
        return str(self.i)

class String(Value):

    def __init__(self, s: str):
        self.location = None
        self.s = s

    def __str__(self) -> str:
        return self.s

class Closure(Value):

    def __init__(self, env: list[tuple[str, int]], fun: LambdaNode):
        self.location = None
        self.env = env
        self.fun = fun

    def __str__(self) -> str:
        return f'<closure evaluated at {self.fun.sl}>'

class Layer:
    '''Each layer on the stack contains the (sub-)expression currently under evaluation.'''

    def __init__(self, env: list[tuple[str, int]], expr: ExprNode, frame: bool = False):
        # whether this layer starts a new call frame
        self.frame = frame
        # environment (shared among layers in each call frame) for the evaluation of the current expression
        self.env = env 
        # the current expression under evaluation
        self.expr = expr
        # program counter (the pc-th step of evaluating this expression)
        self.pc = 0
        # temporary variables for this layer, where variables can only hold Values or lists of Values
        self.local = {}

def check_or_exit(sl: SourceLocation, args: list[Value], ts: list[type]) -> bool:
    ''' check whether arguments conform to types '''
    if len(args) != len(ts):
        runtime_error(sl, 'wrong number of arguments given to callee')
    for i in range(len(args)):
        if not isinstance(args[i], ts[i]):
            runtime_error(sl, 'wrong type of arguments given to callee')

def lookup_env(name: str, env: list[tuple[str, int]]) -> Union[int, None]:
    ''' variable lookup '''
    for i in range(len(env) - 1, -1, -1):
        if env[i][0] == name:
            return env[i][1]
    return None

class State:
    '''The class for the complete execution state'''

    def __init__(self, expr: ExprNode):
        # stack
        main_env = []
        self.stack = [Layer(main_env, None, True), Layer(main_env, expr)]
        # heap
        self.store = []
        # evaluation result
        self.value = None
        # output message buffer (ignore the 'location' of output values)
        self.output_buffer = []

    def clean(self) -> None:
        self.stack = []
        self.store = []

    def step(self) -> bool:
        layer = self.stack[-1]
        if layer.expr is None:
            # found the main frame, which is the end of evaluation
            self.clean()
            return False
        elif type(layer.expr) == IntegerNode:
            self.value = Integer(layer.expr.i)
            self.stack.pop()
        elif type(layer.expr) == StringNode:
            self.value = String(layer.expr.s)
            self.stack.pop()
        elif type(layer.expr) == SetNode:
            if layer.pc == 0:
                self.stack.append(Layer(layer.env, layer.expr.expr))
                layer.pc += 1
            else:
                loc = lookup_env(layer.expr.var.name, layer.env)
                if loc is None:
                    runtime_error(layer.expr.sl, 'undefined variable')
                val = deepcopy(self.value)
                val.location = loc
                self.store[loc] = val
                self.value = Void()
                self.stack.pop()
        elif type(layer.expr) == LambdaNode:
            # closures always save all variables (no matter whether they are used in the body or not)
            # so you can use the @ query in an intuitive way
            self.value = Closure(layer.env[:], layer.expr)
            self.stack.pop()
        elif type(layer.expr) == LetrecNode:
            # bind (deepcopy) the result value to each variable
            if 1 < layer.pc <= len(layer.expr.var_expr_list) + 1:
                loc = lookup_env(layer.expr.var_expr_list[layer.pc - 2][0].name, layer.env)
                if loc is None:
                    runtime_error(var.sl, 'undefined variable')
                val = deepcopy(self.value)
                val.location = loc
                self.store[loc] = val
            # letrec always create new locations
            if layer.pc == 0:
                for v, _ in layer.expr.var_expr_list:
                    layer.env.append((v.name, self._new(Void())))
                layer.pc += 1
            # evaluate binding expressions
            elif layer.pc <= len(layer.expr.var_expr_list):
                self.stack.append(Layer(layer.env, layer.expr.var_expr_list[layer.pc - 1][1]))
                layer.pc += 1
            # evaluate body expression
            elif layer.pc == len(layer.expr.var_expr_list) + 1:
                self.stack.append(Layer(layer.env, layer.expr.expr))
                layer.pc += 1
            # finish letrec
            else:
                # this is necessary because letrec layer's env is shared with its frame
                for i in range(len(layer.expr.var_expr_list)):
                    layer.env.pop()
                # no need to update self.value: inherited
                self.stack.pop()
        elif type(layer.expr) == IfNode:
            # evaluate the condition
            if layer.pc == 0:
                self.stack.append(Layer(layer.env, layer.expr.cond))
                layer.pc += 1
            # choose the branch to evaluate
            elif layer.pc == 1:
                if type(self.value) != Integer:
                    runtime_error(layer.expr.cond.sl, 'wrong condition type')
                if self.value.i != 0:
                    self.stack.append(Layer(layer.env, layer.expr.branch1))
                else:
                    self.stack.append(Layer(layer.env, layer.expr.branch2))
                layer.pc += 1
            # finish if
            else:
                # no need to update self.value: inherited
                self.stack.pop()
        elif type(layer.expr) == VariableNode:
            loc = lookup_env(layer.expr.name, layer.env)
            if loc is None:
                runtime_error(layer.expr.sl, 'undefined variable')
            self.value = self.store[loc]
            self.stack.pop()
        elif type(layer.expr) == CallNode:
            # intrinsic call
            if type(layer.expr.callee) == IntrinsicNode:
                # evaluation result for each argument
                if 1 < layer.pc <= len(layer.expr.arg_list) + 1:
                    layer.local['args'].append(self.value)
                # initialize args
                if layer.pc == 0:
                    layer.local['args'] = []
                    layer.pc += 1
                # evaluate arguments
                elif layer.pc <= len(layer.expr.arg_list):
                    self.stack.append(Layer(layer.env, layer.expr.arg_list[layer.pc - 1]))
                    layer.pc += 1
                # intrinsic call doesn't need to grow the stack, so this is the final step for this call
                else:
                    intrinsic = layer.expr.callee.name
                    args = layer.local['args']
                    # a gigantic series of if conditions, one for each intrinsic function
                    if intrinsic == '.+':
                        check_or_exit(layer.expr.sl, args, [Integer, Integer])
                        self.value = Integer(args[0].i + args[1].i)
                    elif intrinsic == '.-':
                        check_or_exit(layer.expr.sl, args, [Integer, Integer])
                        self.value = Integer(args[0].i - args[1].i)
                    elif intrinsic == '.*':
                        check_or_exit(layer.expr.sl, args, [Integer, Integer])
                        self.value = Integer(args[0].i * args[1].i)
                    elif intrinsic == './':
                        check_or_exit(layer.expr.sl, args, [Integer, Integer])
                        self.value = Integer(args[0].i // args[1].i)
                    elif intrinsic == '.%':
                        check_or_exit(layer.expr.sl, args, [Integer, Integer])
                        self.value = Integer(args[0].i % args[1].i)
                    elif intrinsic == '.<':
                        check_or_exit(layer.expr.sl, args, [Integer, Integer])
                        self.value = Integer(args[0].i < args[1].i)
                    elif intrinsic == '.slen':
                        check_or_exit(layer.expr.sl, args, [String])
                        self.value = Integer(len(args[0].s))
                    elif intrinsic == '.ssub':
                        check_or_exit(layer.expr.sl, args, [String, Integer, Integer])
                        self.value = String(args[0].s[args[1].i : args[2].i])
                    elif intrinsic == '.s+':
                        check_or_exit(layer.expr.sl, args, [String, String])
                        self.value = String(args[0].s + args[1].s)
                    elif intrinsic == '.s<':
                        check_or_exit(layer.expr.sl, args, [String, String])
                        self.value = Integer(args[0].s < args[1].s)
                    elif intrinsic == '.s->i':
                        check_or_exit(layer.expr.sl, args, [String])
                        node = parse(deque([Token(layer.expr.sl, args[0].s)]))
                        if not isinstance(node, IntegerNode):
                            runtime_error(layer.expr.sl, '.strnum is applied to non-number-string')
                        self.value = Integer(node.i)
                    elif intrinsic == '.send':
                        if not (len(args) == 2 and
                                isinstance(args[0], Integer) and
                                (isinstance(args[1], Integer) or isinstance(args[1], String))):
                            runtime_error(layer.expr.sl, 'wrong number/type of arguments given to .send')
                        self.output_buffer.append((args[0], args[1]))
                        # the return value of .send is void
                        self.value = Void()
                    elif intrinsic == '.v?':
                        check_or_exit(layer.expr.sl, args, [Value])
                        self.value = Integer(isinstance(args[0], Void))
                    elif intrinsic == '.n?':
                        check_or_exit(layer.expr.sl, args, [Value])
                        self.value = Integer(isinstance(args[0], Integer))
                    elif intrinsic == '.s?':
                        check_or_exit(layer.expr.sl, args, [Value])
                        self.value = Integer(isinstance(args[0], String))
                    elif intrinsic == '.c?':
                        check_or_exit(layer.expr.sl, args, [Value])
                        self.value = Integer(isinstance(args[0], Closure))
                    elif intrinsic == '.exit':
                        check_or_exit(layer.expr.sl, args, [])
                        self.clean()
                        return False
                    else:
                        runtime_error(layer.expr.sl, 'unrecognized intrinsic function call')
                    self.stack.pop()
            # closure call
            else:
                # evaluation result for each argument
                if 2 < layer.pc <= len(layer.expr.arg_list) + 2:
                    layer.local['args'].append(self.value)
                # evaluate the callee
                if layer.pc == 0:
                    self.stack.append(Layer(layer.env, layer.expr.callee))
                    layer.pc += 1
                # initialize callee and args
                elif layer.pc == 1:
                    layer.local['callee'] = self.value
                    layer.local['args'] = []
                    layer.pc += 1
                # evaluate arguments
                elif layer.pc <= len(layer.expr.arg_list) + 1:
                    self.stack.append(Layer(layer.env, layer.expr.arg_list[layer.pc - 2]))
                    layer.pc += 1
                # evaluate the call
                elif layer.pc == len(layer.expr.arg_list) + 2:
                    callee = layer.local['callee']
                    args = layer.local['args']
                    if type(callee) != Closure:
                        runtime_error(layer.expr.sl, 'calling non-callable object')
                    # types will be checked inside the closure call
                    if len(args) != len(callee.fun.var_list):
                        runtime_error(layer.expr.sl, 'wrong number of arguments given to callee')
                    new_env = callee.env[:]
                    for i, v in enumerate(callee.fun.var_list):
                        # pass by reference
                        addr = args[i].location if args[i].location != None else self._new(args[i])
                        new_env.append((v.name, addr))
                    # evaluate the closure call
                    self.stack.append(Layer(new_env, callee.fun.expr, True))
                    layer.pc += 1
                # finish the (closure) call
                else:
                    # no need to update self.value: inherited
                    self.stack.pop()
        elif type(layer.expr) == SequenceNode:
            # evaluate the expressions, without the need of storing the results to local
            if layer.pc < len(layer.expr.expr_list):
                self.stack.append(Layer(layer.env, layer.expr.expr_list[layer.pc]))
                layer.pc += 1
            # finish the sequence
            else:
                # no need to update self.value: inherited
                self.stack.pop()
        elif type(layer.expr) == QueryNode:
            # evaluate the closure
            if layer.pc == 0:
                self.stack.append(Layer(layer.env, layer.expr.expr))
                layer.pc += 1
            else:
                if type(self.value) != Closure:
                    runtime_error(layer.expr.sl, 'variable query applied to non-closure type')
                # the closure's value is already in "self.value", so we just use it and then update it
                self.value = Integer(not (lookup_env(layer.expr.var.name, self.value.env) is None))
                self.stack.pop()
        elif type(layer.expr) == AccessNode:
            # evaluate the closure
            if layer.pc == 0:
                self.stack.append(Layer(layer.env, layer.expr.expr))
                layer.pc += 1
            else:
                if type(self.value) != Closure:
                    runtime_error(layer.expr.sl, 'lexical variable access applied to non-closure type')
                # again, "self.value" already contains the closure's evaluation result
                loc = lookup_env(layer.expr.var.name, self.value.env)
                if loc is None:
                    runtime_error(layer.expr.sl, 'undefined variable')
                self.value = self.store[loc]
                self.stack.pop()
        else:
            runtime_error(layer.expr.sl, 'unrecognized AST node')
        return True
    
    def execute(self) -> None:
        ctr = 0
        while self.step():
            ctr += 1
            if ctr % 10000 == 0:
                sys.stderr.write('GC collected: ' + str(self._gc()) + '\n')

    def _new(self, value: Value) -> int:
        self.store.append(value)
        loc = len(self.store) - 1
        value.location = loc
        return loc

    def _traverse(self, value_callback: Callable, location_callback: Callable) -> None:
        # ids
        visited_values = set()
        # locations
        visited_locations = set()

        def traverse_value(value: Value) -> None:
            if id(value) not in visited_values:
                value_callback(value)
                visited_values.add(id(value))
                if type(value) == Closure:
                    for _, loc in value.env:
                        traverse_location(loc)

        def traverse_location(location: int) -> None:
            if location not in visited_locations:
                location_callback(location)
                visited_locations.add(location)
                traverse_value(self.store[location])

        for layer in self.stack:
            if layer.frame:
                for _, loc in layer.env:
                    traverse_location(loc)
                if layer.local:
                    for _, v in layer.local.items():
                        traverse_value(v)
        traverse_value(self.value)

    def _mark(self) -> set[int]:
        visited_locations = set()
        self._traverse(lambda _: None, lambda location: visited_locations.add(location))
        return visited_locations

    def _sweep_and_compact(self, visited_locations: set[int]) -> tuple[int, dict[int, int]]:
        removed = 0
        # maps old locations to new locations
        relocation_dict = {}
        n = len(self.store)
        i, j = 0, 0
        while j < n:
            if j in visited_locations:
                self.store[i] = self.store[j]
                self.store[i].location = i
                relocation_dict[j] = i
                i += 1
            else:
                removed += 1
            j += 1
        self.store = self.store[:i]
        return (removed, relocation_dict)
    
    def _relocate(self, relocation_dict: dict[int, int]) -> None:
        
        def value_callback(value: Value) -> None:
            if type(value) == Closure:
                for i in range(len(value.env)):
                    value.env[i] = (value.env[i][0], relocation_dict[value.env[i][1]])

        self._traverse(value_callback, lambda _: None)

    def _gc(self) -> int:
        visited_locations = self._mark()
        removed, relocation_dict = self._sweep_and_compact(visited_locations)
        self._relocate(relocation_dict)
        return removed
        
### main

if __name__ == '__main__':
    state = State(parse(lex(sys.stdin.read())))
    state.execute()
    sys.stdout.write(f'[Note] output buffer:\n')
    for l, v in state.output_buffer:
        sys.stdout.write(f'({l}, {v})\n')
    sys.stdout.write(f'[Note] evaluation value = {state.value}\n')
