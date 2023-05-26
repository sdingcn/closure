class Integer:

    def __init__(self, value):
        self.value = value

class Closure:

    def __init__(self, env, fun):
        self.env = env
        self.fun = fun

class Void:

    def __init__(self):
        pass

class Frame:

    def __init__(self):
        self.env = []

    def push(self, var, loc):
        self.env.append((var, loc))

    def pop(self):
        self.env.pop()

