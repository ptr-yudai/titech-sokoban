#!/usr/bin/env python
import sys
from sokoban import *

def solve(initial_state):
    stack = [initial_state]
    history = []
    
    while stack:
        s = stack.pop()
        hashval = hash(s)
        if hashval in history:
            continue # visited
        
        history.append(hashval)
        if s.is_goal():
            break # goal
        else:
            if s.is_deadlock():
                continue
            else:
                for move in s.get_moves():
                    state = s.go(move)
                    if state:
                        stack.append(state)
    else:
        return None
    
    return s.moves

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
