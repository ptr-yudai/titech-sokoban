import time
import os

class SokobanState(object):
    MOVE_LEFT   = 1
    MOVE_RIGHT  = 2
    MOVE_UP     = 3
    MOVE_BOTTOM = 4
    
    def __init__(self, moves=[], robot=None, box=[], storage=[], obstacles=[], size=None):
        """ Initialize and reset this instance """
        self.moves = moves
        self.robot = robot
        self.box = box
        self.storage = storage
        self.obstacles = obstacles
        self.size = size
    
    def load(self, fstream):
        x, y = 0, 0
        width = 0
        
        # Load state from file
        while True:
            c = fstream.read(1)
            if c == '':
                break
            elif c == '\n':
                width = max(x, width)
                x = -1
                y += 1
            else:
                if c == '#':
                    # Obstacle
                    self.obstacles.append((x, y))
                elif c == '@':
                    # Robot
                    if self.robot is None:
                        self.robot = (x, y)
                    else:
                        raise SokobanException("Only one robot can exist")
                elif c == '$':
                    # Box
                    self.box.append((x, y))
                elif c == '.':
                    # Storage
                    self.storage.append((x, y))
                elif c != ' ':
                    # Space
                    raise SokobanException(
                        "Invalid char `{}` found in field".format(c)
                    )
            x += 1
        
        # Error check
        if self.robot is None:
            raise SokobanException("Robot does not exist")
        if len(self.box) > len(self.storage):
            raise SokobanException("Too many boxes for the storage")

        self.size = (width, y)

    def is_goal(self):
        """ Check if this state is the goal state """
        for box in self.box:
            if box not in self.storage:
                return False
        return True

    def is_deadlock(self):
        """ Check if a box is in deadlock
        A box is in deadlock if one of the following states hold:
         ##  #$  $#  ##
         #$  ##  ##  $#
        """
        for box in self.box:
            if box in self.storage: continue # ignore
            
            obj_l = (box[0]-1, box[1]) in self.obstacles
            obj_r = (box[0]+1, box[1]) in self.obstacles
            obj_u = (box[0], box[1]-1) in self.obstacles
            obj_b = (box[0], box[1]+1) in self.obstacles
            obj_ul = (box[0]-1, box[1]-1) in self.obstacles
            obj_ur = (box[0]+1, box[1]-1) in self.obstacles
            obj_bl = (box[0]-1, box[1]+1) in self.obstacles
            obj_br = (box[0]+1, box[1]+1) in self.obstacles

            if obj_l and obj_ul and obj_u:
                return True
            if obj_l and obj_bl and obj_b:
                return True
            if obj_r and obj_br and obj_b:
                return True
            if obj_r and obj_ur and obj_u:
                return True
        
        return False

    def get_moves(self):
        """ Find available moves """
        moves = []
        obj = [None] * 4
        candidate = [(self.robot[0] - 1, self.robot[1]),
                     (self.robot[0] + 1, self.robot[1]),
                     (self.robot[0], self.robot[1] - 1),
                     (self.robot[0], self.robot[1] + 1)]

        # Check for obstacles
        for i in range(4):
            obj[i] = (candidate[i] in self.obstacles, False)

        # Check for boxes
        for box in self.box:
            if box not in candidate: continue
            direction = candidate.index(box)
            # Try to move this box
            fbox = [(box[0] - 1, box[1]),
                    (box[0] + 1, box[1]),
                    (box[0], box[1] - 1),
                    (box[0], box[1] + 1)]
            if fbox[direction] in self.obstacles or fbox[direction] in self.box:
                obj[direction] = (True, True)
            else:
                obj[direction] = (False, True)

        # Find available moves
        if not obj[0][0]: moves.append((self.MOVE_LEFT, obj[0][1]))
        if not obj[1][0]: moves.append((self.MOVE_RIGHT, obj[1][1]))
        if not obj[2][0]: moves.append((self.MOVE_UP, obj[2][1]))
        if not obj[3][0]: moves.append((self.MOVE_BOTTOM, obj[3][1]))

        return moves

    def go(self, m):
        """ Move to next state (No assertion made!) """
        direction, move_box = m
        next_box = list(self.box)

        if direction == self.MOVE_LEFT:
            # Move to left
            next_robot = (self.robot[0] - 1, self.robot[1])
            if move_box:
                next_box.remove(next_robot)
                next_box.append((next_robot[0] - 1, next_robot[1]))
        elif direction == self.MOVE_RIGHT:
            # Move to right
            next_robot = (self.robot[0] + 1, self.robot[1])
            if move_box:
                next_box.remove(next_robot)
                next_box.append((next_robot[0] + 1, next_robot[1]))
        elif direction == self.MOVE_UP:
            # Move to up
            next_robot = (self.robot[0], self.robot[1] - 1)
            if move_box:
                next_box.remove(next_robot)
                next_box.append((next_robot[0], next_robot[1] - 1))
        elif direction == self.MOVE_BOTTOM:
            # Move to bottom
            next_robot = (self.robot[0], self.robot[1] + 1)
            if move_box:
                next_box.remove(next_robot)
                next_box.append((next_robot[0], next_robot[1] + 1))
        else:
            raise SokobanException("No such move")

        return SokobanState(
            moves = self.moves + [(direction, move_box)],
            robot = next_robot,
            box = next_box,
            storage = self.storage,
            obstacles = self.obstacles,
            size = self.size
        )

    def __str__(self):
        output = ''
        for y in range(self.size[1]):
            for x in range(self.size[0]):
                if (x, y) == self.robot:
                    output += '@'
                elif (x, y) in self.obstacles:
                    output += '#'
                elif (x, y) in self.box:
                    output += '$'
                elif (x, y) in self.storage:
                    output += '.'
                else:
                    output += ' '
            output += '\n'
        return output

    def __hash__(self):
        return hash((
            self.robot,
            tuple(self.box)
        ))

class SokobanEmulator(object):
    def __init__(self, initial_state):
        self.initial_state = initial_state

    def emulate(self, moves, interval=0.1, clear=True):
        s = self.initial_state
        print(s)

        for step, move in enumerate(moves):
            time.sleep(interval)
            if clear:
                os.system("clear")
            print("STEP:{}  /  MOVE:{}".format(step+1, move))
            s = s.go(move)
            print(s)
    
class SokobanException(Exception):
    pass
