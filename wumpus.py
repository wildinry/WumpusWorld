from flask import Flask, render_template, request, jsonify, session
import random
import sys
import json
import time

from agent_logic import AgentKnowledge

CONFIG_FILE = "wumpus_config.txt"

# Global variables to hold the single instance of the game state
global agent, world, config
agent = None
world = None
config = None 


"""
percepts are what the agent may **percieve**. 
"""

def parse_coords(s):
    # Takes in input coordinates and spits out their zero-index (assuming 1-indexed)
    try:
        row, column = s.split(",", 1)
        row = int(row)
        col = column[:-1]
        column = int(col)
        return (row - 1, column - 1)
    except ValueError:
        raise ValueError(f"Invalid coordinate format: '{s}'. Expected 'row col' (1-indexed).")

def load_config_from_file(filepath):
    config = dict()
    config["SIZE"] = 4
    config["START_POS"] = (0, 0)
    config["PITS"] = set()
    config["MAX_MOVES"] = 20

    try:
        with open(filepath, 'r') as config_file:
            for line in config_file:
                line = line.strip()
                if not line or line.startswith('#'): continue
                
                try:
                    key, value_with_comment = line.split('[', 1)
                except ValueError:
                    print(f"Skipping line without '[' separator: '{line}'", file=sys.stderr)
                    continue
                    
                key = key.strip().upper()

                if '#' in value_with_comment:
                    args = value_with_comment.split('#')[0].strip()
                else:
                    args = value_with_comment.strip()


                print(f"Read line {line}")
                try:
                    
                    if key == 'W': 
                        config["WUMPUS"] = parse_coords(args)
                    elif key == 'G': 
                        config["GOLD"] = parse_coords(args)
                    elif key == 'P': 
                        config["PITS"].add(parse_coords(args))
                        
                except Exception as e:
                    print(f"Error parsing line: '{line}'. Details: {e}", file=sys.stderr)
                    sys.exit(1)

    except FileNotFoundError:
        print(f"Configuration file not found: {filepath}", file=sys.stderr)
        sys.exit(1)
        
    required_keys = ['WUMPUS', 'GOLD', 'PITS'] # Removed Size and Start
    missing_keys = [k for k in required_keys if k not in config]
    if missing_keys:
        print(f"Missing required configuration keys in {filepath}: {', '.join(missing_keys)}", file=sys.stderr)
        sys.exit(1)
            
    return config

class WumpusWorld:
    """
    models the objective truth about the game board.
    """
    def __init__(self, wumpus_pos, pits, paradise_pos):
        self.size = 4
        self.wumpus_pos = wumpus_pos
        self.pits = pits
        self.paradise_pos = paradise_pos
        self.breezes = set()
        self.stenches = set()
        self.glows = set()

        self._generate_percepts()
        assert not(wumpus_pos[0]<2 and wumpus_pos[1]<2), "Invalid wumpus starting position! You need to give the player a fair chance!"
        for pit in pits:
            assert not(pit[0]<2 and pit[1]<2), "Invalid pit starting position! You have to give the player a fair chance!"

    def _get_neighbors(self, row, coolumn):
        neighbors = []
        for dr, dc in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
            nr, nc = row + dr, coolumn + dc
            if 0 <= nr < self.size and 0 <= nc < self.size:
                neighbors.append((nr, nc))
        return neighbors

    def _generate_percepts(self):
        # for all rows r and all columns c
        for r in range(self.size):
            for c in range(self.size):
                # if (r, c) is a wumpus, its neighbors have stench
                if (r, c) == self.wumpus_pos:
                    for nr, nc in self._get_neighbors(r, c):
                        self.stenches.add((nr, nc))
                
                # if (r, c) is a pit, its neighbors have stench
                if (r, c) in self.pits:
                    for nr, nc in self._get_neighbors(r, c):
                        self.breezes.add((nr, nc))

                # if (r, c) is gold/paradise, its neigbors are glowing
                if (r, c) == self.paradise_pos:
                    for nr, nc in self._get_neighbors(r, c):
                        self.glows.add((nr, nc))

                

    def get_percepts(self, r, c):
        percepts = set()
        if (r, c) in self.stenches:
            percepts.add("Stench")
        if (r, c) in self.breezes:
            percepts.add("Breeze")
        if (r, c) in self.glows:
            percepts.add("Glitter") # NOTE: Changed from glitter to glowing, might need to change back

        return percepts

    def is_deadly(self, r, c):
        return (r, c) == self.wumpus_pos or (r, c) in self.pits

    def is_paradise(self, r, c):
        return (r,c) == self.paradise_pos

class WumpusAgent:
    """
    Represents our hero. Has access to their world and their knowledge base.
    """
    def __init__(self, world, knowledge_size, start_pos, max_moves):
        self.world : WumpusWorld = world
        self.knowledge : AgentKnowledge = AgentKnowledge(knowledge_size, start_pos)
        self.r, self.c = start_pos
        self.moves_made = 0
        self.max_moves = max_moves
        self.alive = True
        
        initial_percepts = self.world.get_percepts(self.r, self.c)
        self.knowledge.update_percepts(self.r, self.c, initial_percepts)
        self.knowledge.update_probabilities()

    def _get_neighbors(self, r, c):
        return self.world._get_neighbors(r, c) 

    # Chooses the best move to make
    # Returns the (row,column) of next move
    def _choose_next_move(self):
        
        neighbors = self._get_neighbors(self.r, self.c)

        safe_unvisited_moves = []
        for nr, nc in neighbors:
            cell = self.knowledge.knowledge_map[nr][nc]
            if not cell['visited'] and cell['is_safe']:
                safe_unvisited_moves.append((nr, nc))

        # Else, move back to known visited node
        visited_moves = [(nr, nc) for nr, nc in neighbors if self.knowledge.knowledge_map[nr][nc]['visited']]

        print(f"""
              Choosing next move:
              {neighbors = }
              {safe_unvisited_moves = }
              {visited_moves = }
              """)
        
        # Prioritize unvisited nodes.
        if safe_unvisited_moves:
            return random.choice(safe_unvisited_moves) # Oh, it's random. Fair, but i would have preferred some hierarchy 

        return random.choice(visited_moves) 

        # best_unknown_move = None
        # min_danger_prob = float('inf')
        #
        # explorable_moves = []
        # for nr, nc in neighbors:
        #     cell = self.knowledge.knowledge_map[nr][nc]
        #     if not cell['visited']:
        #         total_danger = cell['prob_pit'] + cell['prob_wumpus']
        #         explorable_moves.append(((nr, nc), total_danger))
        #
        # if explorable_moves:
        #     best_unknown_move, min_danger_prob = min(explorable_moves, key=lambda x: x[1])
        #     return best_unknown_move
        #
        # print("WARNING! NOT MOVING FOR SOME REASON")
        # return self.r, self.c

    def decide_next_move(self):
        new_r, new_c = self._choose_next_move()
        direction = {(-1, 0): 'up',(1, 0): 'down',(0, -1): 'left',(0, 1): 'right'}.get((new_r - self.r, new_c - self.c), None)
        print(f"Got direction: {direction} from {new_r, new_c}")
        return self.move(direction)


    # returns (move_success, message)
    # move_success: if the move was succedssfully executed.
    # message: message to the player/user
    def move(self, direction):
        if not self.alive or self.moves_made >= self.max_moves:
            return False, "Simulation Ended."

        if self.world.is_paradise(self.r, self.c):
            return False, f"No need to move from paradise! You already won!"

        print(f"recieved {direction}")
        r, c = self.r, self.c
        dr, dc = {'up': (-1, 0), 'down': (1, 0), 'left': (0, -1), 'right': (0, 1)}.get(direction.lower(), (0, 0))
        
        new_r, new_c = r + dr, c + dc
        
        if not (0 <= new_r < self.world.size and 0 <= new_c < self.world.size):
            return False, "Move cancelled: Out of bounds."

        # make the move
        self.r, self.c = new_r, new_c
        self.moves_made += 1
        
        # terminate game if agent missteps.
        if self.world.is_deadly(self.r, self.c):
            self.alive = False
            danger = "Wumpus" if (self.r, self.c) == self.world.wumpus_pos else "Pit"
            return False, f"TRAGEDY! Agent died at ({new_r + 1}, {new_c + 1}) due to a {danger}."

        percepts = self.world.get_percepts(self.r, self.c)
        self.knowledge.update_percepts(self.r, self.c, percepts)
        self.knowledge.update_probabilities()

        if self.world.is_paradise(self.r, self.c):
            return True, f"Found paradise at ({new_r+1}, {new_c+1})! Horray!"

        return True, f"Moved to ({new_r + 1}, {new_c + 1}). Percepts: {', '.join(percepts) if percepts else 'None'}"

    def has_won(self):
        return self.world.is_paradise(self.r, self.c)

app = Flask(__name__)
app.secret_key = b'_5#y2L"F4Q8z\n\xec]/' # why do we need this??

def init_game():
    global agent, world, config
    
    config_data = load_config_from_file(CONFIG_FILE)
    
    # NOTE: although never changed, we can dial if we wanted to
    GRID_SIZE = 4
    START_POS = (0,0)
    WUMPUS_POS = config_data['WUMPUS']
    GOLD_POS = config_data['GOLD']
    PIT_POSITIONS = config_data['PITS']
    MAX_MOVES = config_data.get('MAX_MOVES', 10)

    world = WumpusWorld(WUMPUS_POS, PIT_POSITIONS, GOLD_POS)
    agent = WumpusAgent(world, GRID_SIZE, START_POS, MAX_MOVES)
    config = config_data
    
    return world, agent, config


##############################################################
# Webpage interface functions
#   The following functions give the webpage the ability 
#   to interact with the program. Not necessary for logic,
#   but it is good for showing what happens when each button
#   is pressed.
##############################################################




@app.route('/')
def index():
    global config 
    if config is None:
        init_game()
        
    return render_template('index.html', size=config['SIZE'])

@app.route('/state', methods=['GET'])
def get_state():
    global agent, config
    if agent is None:
        init_game() 
    
    state = {
        'grid_data': agent.knowledge.get_knowledge_grid_data((agent.r, agent.c)),
        'agent_status': {
            'alive': agent.alive,
            'has_won': agent.has_won(),
            'moves_made': agent.moves_made,
            'max_moves': agent.max_moves,
            'current_pos': (agent.r + 1, agent.c + 1),
            'game_over': not agent.alive or agent.moves_made >= agent.max_moves
        },
        'grid_size': config['SIZE']
    }
    
    return jsonify(state)

@app.route('/move/<direction>', methods=['POST'])
def handle_move(direction):
    global agent
    if agent is None:
        init_game()
    
    success, message = agent.move(direction)
    
    return jsonify({"success": success, "message": message})


@app.route('/decide_move', methods=['POST'])
def handle_decide_move():
    global agent 
    if agent is None:
        init_game()

    success, message = agent.decide_next_move()
    
    return jsonify({"success": success, "message": message})

@app.route('/query/<int:r_1idx>/<int:c_1idx>', methods=['GET'])
def handle_query(r_1idx, c_1idx):
    global agent
    if agent is None:
        init_game()
        
    internal_r, internal_c = r_1idx - 1, c_1idx - 1
    
    result = agent.knowledge.query(internal_r, internal_c)
    
    if 'coords' in result:
        result['coords'] = list(result['coords'])
        
    return jsonify(result)

@app.route('/reset', methods=['POST'])
def reset_game():
    init_game()
    return jsonify({'success': True})

@app.route('/export', methods=['POST'])
def handle_expoort():
    global agent

    agent.knowledge.export_to("KB.txt")

    return jsonify({'success': True})


if __name__ == '__main__':
    print("Starting Wumpus World Agent Simulator (Flask)...")
    
    try:
        world, agent, config = init_game()
        print("Initial game state loaded successfully.")
    except Exception as e:
        print(f"FATAL CONFIGURATION ERROR: {e}")
        sys.exit(1)

    app.run(debug=True)
