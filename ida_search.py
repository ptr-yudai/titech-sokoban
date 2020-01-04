#!/usr/bin/env python
import sys
from sokoban import *

def solve(initial_state):
    bound = initial_state.h()
    stack = [initial_state]
    
    while True:
        history = []
        t = search(list(stack), 0, bound, history)
        if isinstance(t, SokobanState):
            break
        if t == 1 << 32:
            return None
        bound = t
    else:
        return None

    return t.moves

def search(path, g, bound, history):
    node = path.pop()
    f = g + node.h()
    hashval = hash(node)
    if hashval in history:
        return 1 << 32
    else:
        history.append(hashval)
    
    if f > bound: return f
    if node.is_goal(): return node
    minimum = 1 << 32

    for move in node.get_moves():
        state = node.go(move)
        if state:
            path.append(state)
            t = search(list(path), g + 1, bound, history)
            if isinstance(t, SokobanState):
                return t
            if t < minimum:
                minimum = t
            path.pop()

    return minimum

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: {} <Field File>".format(sys.argv[0]))
        exit(1)
    
    with open(sys.argv[1], "r") as f:
        s = SokobanState()
        s.load(f)

    moves = solve(s)
    print(len(moves))
    #"""
    if moves is None:
        print("Solution not found")
    else:
        e = SokobanEmulator(s)
        e.emulate(moves)
    #"""
