#!/usr/bin/env python
import sys
import heapq
from sokoban import *

def solve(initial_state):
    queue = [initial_state]
    heapq.heapify(queue)
    history = []
    
    while queue:
        s = heapq.heappop(queue)
        hashval = hash(s)

        if hashval in history:
            continue # visited
        elif s.is_goal():
            break # goal
        else:
            if s.is_deadlock():
                continue
            else:
                for move in s.get_moves():
                    heapq.heappush(queue, s.go(move))
        
        history.append(hashval)
    else:
        return None
    
    return s.moves

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: {} <Field File>".format(sys.argv[0]))
        exit(1)
    
    with open(sys.argv[1], "r") as f:
        s = SokobanState(h='manhattan')
        s.load(f)

    moves = solve(s)
    if moves is None:
        print("Solution not found")
    else:
        e = SokobanEmulator(s)
        e.emulate(moves)
