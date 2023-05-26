class Int:

    def __init__(self, value):
        self.value = value

class Var:

    def __init__(self, name):
        self.name = name

class Lambda:

    def __init__(self, var_list, expr):
        self.var_list = var_list
        self.expr = expr

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

