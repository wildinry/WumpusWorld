import math

class AgentKnowledge:
    """Manages the agent's internal knowledge base and inference, prioritizing propositional deduction."""
    
    def __init__(self, size, start_pos):
        self.size = size
        # Knowledge map: 2D array of dictionaries storing cell states
        self.knowledge_map = [
            [{
                'visited': False,
                'percepts': set(),
                'is_safe': False,
                'prob_pit': 0.0,
                'prob_wumpus': 0.0
            } for _ in range(size)] for _ in range(size)
        ]
        
        # Start cell is always safe
        self.knowledge_map[start_pos[0]][start_pos[1]]['is_safe'] = True
        self.start_pos = start_pos # Store for reference

    def _get_neighbors(self, r, c):
        """Returns valid (r, c) neighbors for a given cell (0-indexed)."""
        neighbors = []
        for dr, dc in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
            nr, nc = r + dr, c + dc
            if 0 <= nr < self.size and 0 <= nc < self.size:
                neighbors.append((nr, nc))
        return neighbors
        
    def _get_unknown_neighbors(self, r, c):
        """Returns list of (nr, nc) that are unvisited AND not certain safe."""
        unknown = []
        for nr, nc in self._get_neighbors(r, c):
            cell = self.knowledge_map[nr][nc]
            
            # An 'unknown' cell must not be visited and must not be PROVEN SAFE
            if cell['visited'] or cell['is_safe']:
                continue
                
            unknown.append((nr, nc))
        return unknown

    def update_percepts(self, r, c, percepts):
        """Update the knowledge map after visiting (r, c)."""
        cell = self.knowledge_map[r][c]
        cell['visited'] = True
        cell['percepts'] = percepts
        cell['is_safe'] = True 
        cell['prob_pit'] = 0.0 
        cell['prob_wumpus'] = 0.0
        
        # PROPOSITIONAL LOGIC: MODUS TOLLENS (Rule of Elimination)
        # If (r,c) is SAFE (true) AND silent (Breeze, Stench = false), 
        # then all neighbors MUST be safe. (Axiom 1 & 2 negated)
        if not 'Breeze' in percepts and not 'Stench' in percepts:
            for nr, nc in self._get_neighbors(r, c):
                neighbor = self.knowledge_map[nr][nc]
                if not neighbor['visited']:
                    neighbor['is_safe'] = True
                    neighbor['prob_pit'] = 0.0
                    neighbor['prob_wumpus'] = 0.0
    
    def update_probabilities(self):
        """Recalculate probabilities based on all visited cells with percepts."""
        
        # 1. Reset probabilities for non-visited, non-safe cells
        for r in range(self.size):
            for c in range(self.size):
                cell = self.knowledge_map[r][c]
                if not cell['visited'] and not cell['is_safe']:
                    cell['prob_pit'] = 0.0
                    cell['prob_wumpus'] = 0.0
                
        pit_evidence = {}
        wumpus_evidence = {}
        
        for r in range(self.size):
            for c in range(self.size):
                cell = self.knowledge_map[r][c]
                if cell['visited']:
                    
                    # Breeze Calculation (Pit Probability)
                    if 'Breeze' in cell['percepts']:
                        all_neighbors = self._get_neighbors(r, c)
                        unknown_neighbors = [pos for pos in all_neighbors if not self.knowledge_map[pos[0]][pos[1]]['is_safe']]

                        # PROPOSITIONAL LOGIC: DEDUCTION BY ELIMINATION
                        # If Breeze is present, and only ONE neighbor is not proven safe, 
                        # that neighbor MUST contain the Pit. (Disjunction simplifies to one term)
                        if len(unknown_neighbors) == 1:
                            nr, nc = unknown_neighbors[0]
                            self.knowledge_map[nr][nc]['prob_pit'] = 1.0 # Certainty
                            self.knowledge_map[nr][nc]['is_safe'] = False # Not safe!
                        
                        # PROBABILISTIC INFERENCE (Only if Elimination fails)
                        elif len(unknown_neighbors) > 1:
                            # Distribute probability equally among all remaining unknowns
                            prob_increment = 1.0 / len(unknown_neighbors)
                            for nr, nc in unknown_neighbors:
                                pit_evidence[(nr, nc)] = pit_evidence.get((nr, nc), []) + [prob_increment]


                    # Stench Calculation (Wumpus Probability)
                    if 'Stench' in cell['percepts']:
                        all_neighbors = self._get_neighbors(r, c)
                        unknown_neighbors = [pos for pos in all_neighbors if not self.knowledge_map[pos[0]][pos[1]]['is_safe']]

                        # PROPOSITIONAL LOGIC: DEDUCTION BY ELIMINATION
                        if len(unknown_neighbors) == 1:
                            nr, nc = unknown_neighbors[0]
                            self.knowledge_map[nr][nc]['prob_wumpus'] = 1.0 # Certainty
                            self.knowledge_map[nr][nc]['is_safe'] = False # Not safe!

                        # PROBABILISTIC INFERENCE (Only if Elimination fails)
                        elif len(unknown_neighbors) > 1:
                            prob_increment = 1.0 / len(unknown_neighbors)
                            for nr, nc in unknown_neighbors:
                                wumpus_evidence[(nr, nc)] = wumpus_evidence.get((nr, nc), []) + [prob_increment]
        
        # 3. Apply the maximum evidence for probabilistic distribution cases
        for (r, c), evidences in pit_evidence.items():
            current_prob = self.knowledge_map[r][c]['prob_pit']
            # Only update if current certainty is not already 1.0 (from elimination)
            if current_prob < 1.0:
                self.knowledge_map[r][c]['prob_pit'] = max(current_prob, max(evidences))
            
        for (r, c), evidences in wumpus_evidence.items():
            current_prob = self.knowledge_map[r][c]['prob_wumpus']
            if current_prob < 1.0:
                self.knowledge_map[r][c]['prob_wumpus'] = max(current_prob, max(evidences))
                                
    def query(self, r, c):
        """Replies with the status of any chamber based on agent knowledge."""
        if not (0 <= r < self.size and 0 <= c < self.size):
            return {"error": "Invalid Chamber Coordinates."}

        cell = self.knowledge_map[r][c]
        
        response = {
            'coords': (r + 1, c + 1), 
            'status': 'UNKNOWN',
            'percepts_observed': 'None',
            'inferred_percepts': 'None',
            'prob_pit': cell['prob_pit'],
            'prob_wumpus': cell['prob_wumpus']
        }
        
        # Status Logic
        if cell['prob_pit'] >= 1.0 or cell['prob_wumpus'] >= 1.0:
            response['status'] = 'DEFINITELY DANGEROUS'
        elif cell['is_safe']:
            response['status'] = 'SAFE'
        
        # If the chamber was visited, report the OBSERVED percepts
        if cell['visited']:
            response['status'] = 'SAFE (VISITED)'
            percepts = [p for p in cell['percepts'] if p in ('Breeze', 'Stench', 'Glitter')]
            response['percepts_observed'] = ", ".join(percepts) if percepts else 'None'
            
        # If unvisited, check for certainty about Breeze/Stench based on neighbors
        if not cell['visited']:
            inferred_list = []
            if cell['prob_pit'] >= 1.0:
                inferred_list.append("Pit CERTAIN (Prob=1.0)")
            if cell['prob_wumpus'] >= 1.0:
                inferred_list.append("Wumpus CERTAIN (Prob=1.0)")

            if inferred_list:
                response['inferred_percepts'] = " / ".join(inferred_list)
            
        return response
        
    def get_knowledge_grid_data(self, agent_pos):
        """Returns the grid data suitable for JSON/web transmission."""
        grid_data = []
        for r in range(self.size):
            for c in range(self.size):
                cell = self.knowledge_map[r][c]
                is_agent = (r, c) == agent_pos
                
                cell_class = 'unknown'
                if cell['visited']:
                    cell_class = 'visited'
                elif cell['is_safe']:
                    cell_class = 'safe'
                
                display_symbol = '?'
                if is_agent:
                    display_symbol = 'A'
                elif cell['visited']:
                    percepts = "".join([p[0] for p in cell['percepts'] if p in ('Breeze', 'Stench', 'Glitter')])
                    display_symbol = percepts if percepts else 'V'
                
                danger_class = ''
                total_prob = cell['prob_pit'] + cell['prob_wumpus']
                if total_prob > 0.9:
                    danger_class = 'danger-high'
                elif total_prob > 0.0:
                    danger_class = 'danger-low'
                
                grid_data.append({
                    'r': r, 'c': c,
                    'symbol': display_symbol,
                    'class': f'{cell_class} {danger_class}',
                    'r_1idx': r + 1, 'c_1idx': c + 1 
                })
        
        return grid_data