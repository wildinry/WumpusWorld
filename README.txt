# README.txt - Wumpus World Agent Simulator

## Project Overview
This project implements a Wumpus World exploring agent using Python and the Flask web framework. The agent is designed to explore a 4x4 cave system, update its knowledge base after each move based on observed percepts (Stench, Breeze), and calculate the probability of danger (Wumpus or Pit) in unknown chambers. The output is a visually appealing, interactive webpage.

## Implementation Details
* **Language:** Python 3.x
* **Framework:** Flask (for web server and interaction)
* **Core Logic:** The game engine and agent movement are in `app.py`. The knowledge base, inference rules, and probability calculations are completely separated into `agent_logic.py`.
* **Initialization:** The program accepts `wumpus_config.txt` for all starting parameters (size, Wumpus/Pit/Gold locations).
* **Interface:** A web page served by Flask allows for move controls and a visual representation of the agent's knowledge map.

## Requirements and Setup
1.  **Dependencies:** Ensure Python 3 is installed. Install Flask:
    ```bash
    pip install Flask
    ```
2.  **File Structure:** Maintain the structure provided: `app.py`, `agent_logic.py`, `wumpus_config.txt`, `templates/`, and `static/`.
3.  **Run Program:** Execute the main application file from the command line:
    ```bash
    python app.py
    ```
4.  **Access:** Open your web browser and navigate to the local address provided by Flask (typically `http://127.0.0.1:5000/`).

## How to Interact
* **Moves:** Use the UP, DOWN, LEFT, RIGHT buttons to command the agent.
* **Knowledge Query:** Click on any cell in the "Agent Knowledge Map" grid. The sidebar will update to show the chamber's detailed status (SAFE, UNKNOWN, DANGER, Percepts, and probabilities).

## Knowledge Base (KB)
The initial knowledge base is detailed in `KB.txt`. The agent uses a combination of symbolic logic (Stench $\Leftrightarrow$ Wumpus adjacent) and probabilistic inference (distributing probability among unknown neighbors) to update its state.