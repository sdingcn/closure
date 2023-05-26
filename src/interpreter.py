from syntax import *
from dynamic import *
from collector import collect

def interpret(tree):
    store = {}
    location = 0

    def new(value):
        store[location] = value
        location += 1
        return location

    stack = []
    env = []


    def recurse(node, env):
        pass

    return recurse(tree, env)
