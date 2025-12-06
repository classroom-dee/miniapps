"""
Crusty the Crazy Coin Collecting Robot And The Lethargic Monster Who Just Wants A Nap
(name TBD)
Move: Arrow keys
Rules: 
- Must get more than <insert difficulty level> coins to see the exit
- Your move is tied to the monster's move
- Monster starts to move after <insert difficulty level> moves
"""
# NICE-TO-HAVES
# TODO: Max possible score/monster entrance/coins distrib and loc -> maybe this can be described as a math solution ?
# ... sum of shortest paths to coins -> monster start turn + difficulty unit = actual monster chase speed
# TODO: Omni directional traversal would be nice (map gen-wise) -> start and goal can be anywhere
# TODO: Would be nice to have a coin image at the center of each cell
# TODO: Monster sprite visibility (or wave it off as a camo monster lol)
# TODO: Leader board with a light db like sqlite or raw json
# TODO: Interface for screen size selecting

# GAME-BREAKING
# TODO: Difficulty options interface
# TODO: Difficulty scales with screen size
# TODO: Render only reachable coins + the number of reachable coins must be >= difficulty

# BUG: Monster and robot dances around in parallel when they are aligned and repeated to go up and down

import pygame
from enum import Enum
from functools import lru_cache
from collections import deque

class ScreenResolution(Enum):
    VGA = 640, 480
    SVGA = 800, 600
    XGA = 1024, 768
    HD = 1280, 720
    WXGA = 1366, 768
    HDPLUS = 1600, 900
    FHD = 1920, 1080
    QHD = 2560, 1440
    UHD = 3840, 2160
    
class Difficulty(Enum):
    """The monster will start moving after this much ticks"""
    HARD = 5
    NORMAL = 10
    EASY = 15

def helper_world_gen(rows, cols):
    """
    Grid generator... a separate module would be nice but for tmc compat...
      - 'x' = impassible
      - 'o' = passable
      - 'c' = coin
      - 's' = start
      - 'g' = exit (goal)
    """
    import random

    # top left start, goal at the bottom right
    sr, sc = 0, 0
    gr, gc = rows - 1, cols - 1

    # Start with everything impassible
    grid = [['x' for _ in range(cols)] for _ in range(rows)]

    # Carve a guaranteed path
    r, c = sr, sc
    path = [(r, c)]
    grid[r][c] = 'o'  # default

    while (r, c) != (gr, gc):
        moves = []
        # possible move options
        if r < gr:
            moves.append((r + 1, c))
        if c < gc:
            moves.append((r, c + 1))

        # choose a move
        r, c = random.choice(moves)
        path.append((r, c))
        grid[r][c] = 'o'

    # for fast lookup
    path_set = set(path)

    # fill the rest of the cells randomly with x / o / c
    for i in range(rows):
        for j in range(cols):
            if (i, j) in path_set:
                continue  # don't overwrite the guaranteed path

            # NOTE: maybe i can mix difficulty into this but for now ...
            rnum = random.random()
            if rnum < 0.2:
                grid[i][j] = 'o'  # 20% chance redundant path
            elif rnum < 0.4:
                grid[i][j] = 'c'  # 20% chance coin
            else:
                grid[i][j] = 'x'  # 60% chance wall

    # Place start and goal
    grid[sr][sc] = 's'
    grid[gr][gc] = 'g'

    return grid

def helper_path_check(next_coord: tuple[int, int], wall_list: set[tuple[int, int]], coin_list: set[tuple[int, int]], goal_list: set[tuple[int, int]], enemy: tuple[int, int]):
    if next_coord == enemy: return 4 # loose
    if next_coord in wall_list: return 0 # don't move
    elif next_coord in coin_list: return 2 # move
    elif next_coord in goal_list: return 3 # win
    else: return 1 # move (no coin)

@lru_cache
def helper_coord_to_matrix(coord: tuple[int, int], scale: tuple[int, int]):
    """Converts a pixel coord to a world coord in (row, column) format"""
    return coord[1] // scale[1], coord[0] // scale[0]

@lru_cache
def helper_chase(bound_world: tuple, monster: tuple[int, int], robot: tuple[int, int]):
    """Assumes that the monster is always wise: no wasted steps"""
    if monster == robot:
        return 0, 0
    
    q = deque([monster])
    prev: dict[tuple, None | tuple] = {monster: None}
    dirs = [(-1, 0), (1, 0), (0, -1), (0, 1)]
    
    rows = len(bound_world)
    cols = len(bound_world[0]) if rows > 0 else 0

    found = False

    while q:
        r, c = q.popleft()
        if (r, c) == robot:
            found = True
            break

        for dr, dc in dirs:
            nr, nc = r + dr, c + dc
            if 0 <= nr < rows and 0 <= nc < cols:
                # walls, visited -> nope
                if bound_world[nr][nc] != 'x' and (nr, nc) not in prev:
                    prev[(nr, nc)] = (r, c)
                    q.append((nr, nc))

    if not found or robot not in prev:
        return 0, 0

    # track back and reverse
    path = []
    cur = robot
    while cur is not None:
        path.append(cur)
        cur = prev[cur]

    if len(path) < 2:
        return 0, 0

    path.reverse()

    # first move
    (mr, mc), (nr, nc) = path[0], path[1]
    dr, dc = nr - mr, nc - mc
    return dc, dr

class SomeGame:
    directions = {pygame.K_DOWN: (0, 1), pygame.K_UP: (0, -1), pygame.K_LEFT: (-1, 0), pygame.K_RIGHT: (1, 0)}

    def __init__(self, resolution: ScreenResolution, difficulty: Difficulty):
        self.difficulty = difficulty
        self.score = 0
        pygame.init()

        # image assets
        self.images: list[pygame.Surface] = []
        self.scale = 0, 0
        self.load_assets()
        
        # world dimension in blocks and pixels
        self.pix_h = 0
        self.pix_w = 0
        self.blocks_h = 0
        self.blocks_v = 0

        # world generation
        self.world: list[list[str]] = []
        self.resolution = self.generate_world(resolution.value)

        # draw world init
        self.window = pygame.display.set_mode((self.pix_w, self.pix_h))
        pygame.display.set_caption("Crusty the Crazy Coin Collecting Robot And The Lethargic Monster Who Just Wants A Nap")
        self.game_board = pygame.Surface((self.scale[0] * self.blocks_h, self.scale[1] * self.blocks_v))
        self.character_layer = pygame.Surface((self.scale[0] * self.blocks_h, self.scale[1] * self.blocks_v), pygame.SRCALPHA)
        # self.character_layer.set_alpha(0)
        self.coins, self.walls, self.goals = self.draw_world()

        # dialog
        self.dialog_rect = pygame.Rect(self.pix_w // 2 - 100, self.pix_h // 2 - 100, 200, 200)
        self.font = pygame.font.SysFont("Gothic", 24)
        self.new_game_btn_rect = pygame.Rect(self.dialog_rect.centerx - 40, self.dialog_rect.bottom - 45, 80, 30)
        self.quit_btn_rect = pygame.Rect(self.new_game_btn_rect.left + 80, self.dialog_rect.bottom - 45, 60, 30)

        # main loop
        self.game_state = 1 # 1: playing, 3: won, 4: lost
        self.clock = pygame.time.Clock()
        self.is_map_due_update = False
        self.monster_loc = (-self.scale[0], 0)
        self.robot_loc = (0, 0)
        self.game_tick = 0
        self.main()

    def load_assets(self, test=False):
        import os
        asset_path = "X:\\TMC\\tmcdata\\mooc-programming-25\\part14-01_own_game\\src" if test else ""
        assets = ['coin.png', 'door.png', 'monster.png', 'robot.png']

        for a in assets:
            self.images.append(pygame.image.load(os.path.join(asset_path, a)))
        self.scale = self.images[-1].get_width(), self.images[-1].get_height()
        # add raw surface tiles for passables and walls
        self.images.append(pygame.Surface(self.scale))
        self.images.append(pygame.Surface(self.scale, pygame.SRCALPHA))
        self.images[-2].fill((255, 100, 50)) # walls
        self.images[-1].set_alpha(0)
        self.images[-1].fill((0, 0, 0, 0)) # passables
    
    def generate_world(self, resolution: tuple[int, int]):
        self.pix_w, self.pix_h = resolution
        self.blocks_h, self.blocks_v = self.pix_w // self.scale[0], self.pix_h // self.scale[1]
        self.world = helper_world_gen(self.blocks_v, self.blocks_h)
        return resolution
    
    def draw_world(self):
        self.window.fill((100, 100, 100))
        self.game_board.fill((0, 0, 0))
        self.window.blit(self.game_board, (0, 0))
        coins, walls, goals = set(), set(), set() # for collision detection
        for i, r in enumerate(self.world):
            for j, cell in enumerate(r):
                # add board walls
                if i == 0:
                    walls.add((j * self.scale[0], -self.scale[1]))
                if j == 0:
                    walls.add((-self.scale[0], i * self.scale[1]))
                if j == len(r) - 1:
                    walls.add(((j + 1) * self.scale[0], i * self.scale[1]))
                if i == len(self.world) - 1:
                    walls.add((j * self.scale[0], (i + 1) * self.scale[1]))
                
                # draw
                coord = j * self.scale[0], i * self.scale[1]
                match cell:
                    case 'x':
                        self.window.blit(self.images[-2], coord)
                        walls.add(coord)
                    case 'c':
                        self.window.blit(self.images[0], coord)
                        coins.add(coord)
                    case 'o' | 's':
                        self.window.blit(self.images[-1], coord)
                    case 'g':
                        # only show the door when score is above threshold
                        if self.score >= self.difficulty.value:
                            self.window.blit(self.images[1], coord)
                            goals.add(coord)
                        else:
                            self.window.blit(self.images[-1], coord)
                    case _:
                        raise Exception("Invalid cell marker")
        return coins, walls, goals
    
    def draw_characters(self, monster_loc, robot_loc):
        self.character_layer.fill((0, 0, 0, 0))
        self.character_layer.blit(self.images[2], monster_loc)
        self.character_layer.blit(self.images[3], robot_loc)
        self.window.blit(self.character_layer, (0, 0))
        pygame.display.flip()

    # world draw is tied to character movement(game tick) -> not unnecessary re draw
    def toggle_map_update_flag(self): self.is_map_due_update = not self.is_map_due_update

    def chase_robot(self):
        """
        Make a bounding box between monster,
        convert global coords to bounding box local coords,
        and search for the best route
        : Not using bb -- using whole world now.
        """
        # bounding_box = (
        #     (min(self.monster_loc[0], self.robot_loc[0]), min(self.monster_loc[1], self.robot_loc[1])), 
        #     (max(self.monster_loc[0], self.robot_loc[0]), max(self.monster_loc[1], self.robot_loc[1]))
        # )
        monster_direction = (0, 0)
        if self.difficulty.value <= self.game_tick:
            monster_coord = helper_coord_to_matrix(self.monster_loc, self.scale)
            if monster_coord == (0, -1):
                monster_direction = (1, 0)
            else:
                # tl, br = (helper_coord_to_matrix(bounding_box[0], self.scale), helper_coord_to_matrix(bounding_box[1], self.scale))
                # bound_world = tuple(tuple(row[tl[1]:br[1]+1]) for row in self.world[tl[0]:br[0]+1])
                bound_world = tuple(''.join(s for s in row) for row in self.world) # i could just pass self.world and not do caching
                # global to local
                # m_r, m_c = helper_coord_to_matrix(self.monster_loc, self.scale)
                # r_r, r_c = helper_coord_to_matrix(self.robot_loc, self.scale) 
                # monster_direction = helper_chase(
                #     bound_world, 
                #     (m_r - tl[0], m_c - tl[1]), 
                #     (r_r - tl[0], r_c - tl[1]) 
                # )
                monster_direction = helper_chase(
                    bound_world,
                    helper_coord_to_matrix(self.monster_loc, self.scale),
                    helper_coord_to_matrix(self.robot_loc, self.scale)
                )

        return self.monster_loc[0] + monster_direction[0] * self.scale[0], self.monster_loc[1] + monster_direction[1] * self.scale[1]

    def end_game_dialog(self, game_state: int):
        """On game-end, the display.flip() is called from here instead of draw_characters()"""
        # call dialog box
        pygame.draw.rect(self.window, (100, 100, 100), self.dialog_rect)
        
        # display text
        text = f'You have {"won" if game_state == 3 else "lost"}!'
        text_object = self.font.render(text, False, (255, 0, 0) if game_state == 4 else (0, 255, 0))
        text_rect = text_object.get_rect(center=(self.dialog_rect.centerx, self.dialog_rect.top + 40))
        self.window.blit(text_object, text_rect)
        
        # new game / quit button
        pygame.draw.rect(self.window, (180, 180, 180), self.new_game_btn_rect)
        pygame.draw.rect(self.window, (180, 180, 180), self.quit_btn_rect)
        new_game_btn_text = self.font.render("New game", False, (0, 0, 0))
        quit_btn_text = self.font.render("Quit", False, (0, 0, 0))
        new_game_text_rect = new_game_btn_text.get_rect(center=self.new_game_btn_rect.center)
        quit_text_rect = quit_btn_text.get_rect(center=self.quit_btn_rect.center)
        self.window.blit(new_game_btn_text, new_game_text_rect)
        self.window.blit(quit_btn_text, quit_text_rect)

        pygame.display.flip()
        
    def move_judge(self, orig: tuple[int, int], new: tuple[int, int], result: int):
        match result:
            case 0: return orig # wall -> don't move
            case 1: return new # passable -> move
            case 2:
                self.coins.remove(new)
                self.score += 1
                self.world[new[1] // self.scale[1]][new[0] // self.scale[0]] = 'o'
                return new
            case 3 | 4: 
                self.game_state = result
                return new
            case _:
                raise Exception("Invalid path indicator")

    def move_characters(self, robot_direction):
        # player move first and then calculate monster move
        r_new_loc = (self.robot_loc[0] + robot_direction[0] * self.scale[0], self.robot_loc[1] + robot_direction[1] * self.scale[1])
        path_result = helper_path_check(r_new_loc, self.walls, self.coins, self.goals, self.monster_loc)
        
        self.robot_loc = self.move_judge((self.robot_loc[0], self.robot_loc[1]), r_new_loc, path_result)
        self.monster_loc = self.chase_robot()
        if self.monster_loc == self.robot_loc: # it doesn't look good here but...
            self.game_state = 4

    def reset(self): 
        self.world: list[list[str]] = []
        self.generate_world(self.resolution)

        self.game_state = 1 # 1: playing, 3: won, 4: lost
        
        self.monster_loc = (-self.scale[0], 0)
        self.robot_loc = (0, 0)
        self.score = 0
        self.game_tick = 0

    def event_handler(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                exit()
            # check move, if a coin is eaten, change state
            # both actor's movements are tied to single key down
            if event.type == pygame.KEYDOWN and event.key in SomeGame.directions.keys():
                self.game_tick += 1
                self.move_characters(SomeGame.directions[event.key])
                self.toggle_map_update_flag()
            
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self.new_game_btn_rect.collidepoint(event.pos):
                    self.reset()
                    self.toggle_map_update_flag()
                if self.quit_btn_rect.collidepoint(event.pos):
                    exit()
    
    def draw_score(self):
        color = (0, 255, 0) if self.score >= self.difficulty.value else (255, 0, 0)
        txt = self.font.render(f"Coins: {self.score}", False, color)
        w, h = txt.get_width(), txt.get_height()
        self.window.blit(txt, (self.pix_w - w, self.pix_h - h))

    def main(self):
        while True:
            self.event_handler()
            self.draw_score()

            if self.is_map_due_update:
                self.coins, self.walls, self.goals = self.draw_world()
                self.toggle_map_update_flag()
            
            if self.game_state == 1:
                self.draw_characters(self.monster_loc, self.robot_loc)
            else:
                self.end_game_dialog(self.game_state)
            
            self.clock.tick(60)


if __name__ == "__main__":
    SomeGame(ScreenResolution.HD, Difficulty.HARD)
