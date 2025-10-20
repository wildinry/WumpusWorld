# README - Wumpus World Agent Simulator

By Ryan, Jeff, and Danny

## Project Overview
This project implements a Wumpus World exploring agent using Python and the Flask web framework. The agent is designed to explore a 4x4 cave system, update its knowledge base after each move based on observed percepts (Stench, Breeze), and calculate the probability of danger (Wumpus or Pit) in unknown chambers. The output is a visually appealing, interactive webpage. This project is meant to show the implementation of propositional logic based algorithms.

## Implementation Details
* **Language:** Python 3.x
* **Framework:** Flask (for web server and interaction)
* **Core Logic:** The game engine and agent movement are in `app.py`. The knowledge base, inference rules, and probability calculations are completely separated into `agent_logic.py`.
* **Initialization:** The program accepts `wumpus_config.txt` for all starting parameters (size, Wumpus/Pit/Gold locations).
* **Interface:** A web page served by Flask allows for move controls and a visual representation of the agent's knowledge map.

## Requirements and Setup
### 1. Python Installation

The project requires **Python 3.6** or newer.

#### Windows Installation

1.  **Download:** Get the latest Python 3 installer from the [official Python website](https://www.python.org/downloads/windows/).
2.  **Run Installer:** Execute the downloaded file.
3.  **Crucial Step:** On the first installer screen, **check the box** that says **"Add python.exe to PATH"** before clicking "Install Now." This allows you to run Python commands from any terminal window.
4.  **Verify:** Open a new Command Prompt or PowerShell and confirm the installation:
    ```bash
    python --version
    ```

#### Linux/WSL Installation

Python 3 is usually pre-installed. If not, use your system's package manager.

1.  **Verify:** Open a terminal and check the version:
    ```bash
    python3 --version
    ```
2.  **Install (e.g., Debian/Ubuntu):**
    ```bash
    sudo apt update
    sudo apt install python3 python3-venv
    ```

#### Optional: you may want to start a virtual environment with the following commands:

Linux/Unix/WSL (**Recommended**, this was our method)
```bash
python3 -m venv venv     # creates a virtual environment called "venv"
source ./venv/bin/activate
```
Windows Command prompt
```bat
python3 -m venv venv     
venv\Scripts\activate.bat
```
Windows Powershell
```powershell
python3 -m venv venv     
venv\Scripts\Activate.ps1
```

1.  **Dependencies:** Ensure Python 3 is installed. Install Flask:
    ```bash
    pip install Flask
    ```
2.  **File Structure:** Maintain the structure provided: `app.py`, `agent_logic.py`, `wumpus_config.txt`, `templates/`, and `static/`.
3.  **Run Program:** Execute the main application file from the command line:
    ```bash
    python wumpus.py
    ```
4.  **Access:** Open your web browser and navigate to the local address provided by Flask (typically `http://127.0.0.1:5000/`).

## How to Interact
* **Moves:** Use the UP, DOWN, LEFT, RIGHT buttons to command the agent.
* **Knowledge Query:** Click on any cell in the "Agent Knowledge Map" grid. The sidebar will update to show the chamber's detailed status (SAFE, UNKNOWN, DANGER, Percepts, and probabilities).

## Knowledge Base (KB)
The initial knowledge base is detailed in `KB.txt`. The agent uses a combination of symbolic logic (Stench $\Leftrightarrow$ Wumpus adjacent) and probabilistic inference (distributing probability among unknown neighbors) to update its state.
