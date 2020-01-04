import time

class SokobanState(object):
    MOVE_LEFT   = 1
    MOVE_RIGHT  = 2
    MOVE_UP     = 3
    MOVE_BOTTOM = 4
    
    def __init__(self,
                 moves=[],
                 robot=None,
                 box=[],
                 storage=[],
                 obstacles=[],
                 size=None,
                 dead=None,
                 frozen=None,
                 depth=0,
                 h='manhattan'):
        """ Initialize and reset this instance """
        self.moves = moves
        self.robot = robot
        self.box = box
        self.storage = storage
        self.obstacles = obstacles
        self.size = size
        self.depth = 0
        self.hname = h
        if dead is not None:
            self.dead = dead
        if frozen is not None:
            self.frozen = frozen
        if h == 'manhattan':
            self.h = self.manhattan_dist
        elif h == 'euclidean':
            self.h = self.euclidean_dist
        else:
            raise SokobanException(
                'Undefined heuristic function `{}`'.format(h)
            )
    
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
        self.dead = self.find_dead_square()
        self.frozen = {box: False for box in self.box}

    def is_goal(self):
        """ Check if this state is the goal state """
        for box in self.box:
            if box not in self.storage:
                return False
        return True

    def find_dead_square(self):
        """ Search for dead square
        """
        dead_square = set()
        for y in range(self.size[1]):
            for x in range(self.size[0]):
                dead_square.add((x, y))
        dead_square -= self.find_safe_space()
        dead_square -= set(self.obstacles)
        return dead_square

    def find_safe_space(self):
        """ Search for safe space
        """
        safe = set()
        for storage in self.storage:
            safe = safe.union(self._find_safe_space(storage))
        return safe

    def _find_safe_space(self, initial_box):
        stack = [initial_box]
        safe = set()
        visited = []
        
        while len(stack) > 0:
            box = stack.pop()
            if box in visited:
                continue

            visited.append(box)
            safe.add(box)
            for d in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                next_pos = (box[0]+d[0], box[1]+d[1])
                step_pos = (next_pos[0]+d[0], next_pos[1]+d[1])
                if next_pos in self.obstacles:
                    continue
                if step_pos not in self.obstacles:
                    stack.append(next_pos)

        return safe
    
    def is_deadlock(self):
        """ Check if a box is in deadlock
        """
        # Detect dead square deadlocks
        for box in self.box:
            if box in self.dead:
                return True
        
        return False

    def check_frozen(self, box, frozen):
        """ Check for frozen deadlocks """
        horizontal_lock = vertical_lock = False
        if box not in frozen:
            return False

        # 1. Check for obstacles
        if (box[0] - 1, box[1]) in self.obstacles: horizontal_lock = True
        elif (box[0] + 1, box[1]) in self.obstacles: horizontal_lock = True
        if (box[0], box[1] - 1) in self.obstacles: vertical_lock = True
        elif (box[0], box[1] + 1) in self.obstacles: vertical_lock = True

        # 2. Check for deadlocks
        if (box[0] - 1, box[1]) in self.dead and (box[0] + 1, box[1]) in self.dead: horizontal_lock = True
        if (box[0], box[1] - 1) in self.dead and (box[0], box[1] + 1) in self.dead: vertical_lock = True

        # 3. Check for frozen blocks
        if (box[0] - 1, box[1]) in frozen:
            if frozen[(box[0] - 1, box[1])]:
                horizontal_lock = True
        elif (box[0] + 1, box[1]) in frozen:
            if frozen[(box[0] + 1, box[1])]:
                horizontal_lock = True
        if (box[0], box[1] - 1) in frozen:
            if frozen[(box[0], box[1] - 1)]:
                vertical_lock = True
        elif (box[0], box[1] + 1) in frozen:
            if frozen[(box[0], box[1] + 1)]:
                vertical_lock = True

        # Detect lock
        if horizontal_lock and vertical_lock:
            frozen[box] = True
            if box not in self.storage:
                return True
        else:
            frozen[box] = False
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
        next_frozen = self.frozen.copy()

        if direction == self.MOVE_LEFT:
            # Move to left
            next_robot = (self.robot[0] - 1, self.robot[1])
            moved_box = (next_robot[0] - 1, next_robot[1])
        elif direction == self.MOVE_RIGHT:
            # Move to right
            next_robot = (self.robot[0] + 1, self.robot[1])
            moved_box = (next_robot[0] + 1, next_robot[1])
        elif direction == self.MOVE_UP:
            # Move to up
            next_robot = (self.robot[0], self.robot[1] - 1)
            moved_box = (next_robot[0], next_robot[1] - 1)
        elif direction == self.MOVE_BOTTOM:
            # Move to bottom
            next_robot = (self.robot[0], self.robot[1] + 1)
            moved_box = (next_robot[0], next_robot[1] + 1)
        else:
            raise SokobanException("No such move")
        
        if move_box:
            next_box.remove(next_robot)
            next_box.append(moved_box)

            # Update frozen state
            next_frozen[moved_box] = next_frozen[next_robot]
            del next_frozen[next_robot]

            # Check for freeze deadlock
            if self.check_frozen(moved_box, next_frozen):
                return None
        
        return SokobanState(
            moves = self.moves + [(direction, move_box)],
            robot = next_robot,
            box = next_box,
            storage = self.storage,
            obstacles = self.obstacles,
            size = self.size,
            dead = self.dead,
            frozen = next_frozen,
            depth = self.depth + 1,
            h = self.hname
        )

    def manhattan_dist(self):
        """ Calculate Manhattan distance """
        dist = 0
        for box in self.box:
            min_dist = 1 << 32
            for storage in self.storage:
                d = abs(box[0] - storage[0]) + abs(box[1] - storage[1])
                if min_dist > d:
                    min_dist = d
            dist += min_dist
        return dist

    def euclidean_dist(self):
        """ Calculate Euclidean distance """
        dist = 0.0
        for box in self.box:
            # distance between box and nearest storage
            min_dist = 1 << 32
            for storage in self.storage:
                d = ((box[0]-storage[0])**2 + (box[1]-storage[1])**2)**0.5
                if min_dist > d:
                    min_dist = d
            dist += min_dist
        return dist

    def g(self):
        return len(self.moves)

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

    def __lt__(self, other):
        return self.h() + self.g() < other.h() + other.g()

class SokobanEmulator(object):
    def __init__(self, initial_state):
        self.initial_state = initial_state

    def emulate(self, moves, interval=0.1, clear=True):
        s = self.initial_state
        print(s)

        for step, move in enumerate(moves):
            time.sleep(interval)
            if clear:
                print("\x1b[2J\x1b[H", end="")
            print("STEP:{}  /  MOVE:{}".format(step+1, move))
            s = s.go(move)
            print(s)
    
class SokobanException(Exception):
    pass
