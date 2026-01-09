# Situational Awareness & Collision Risk System

A real-time radar simulation and collision avoidance system built with **FastAPI** and **HTML5 Canvas**. This system visualizes vessel traffic, calculates collision risks (CPA/TCPA), and simulates an "infinite ocean" environment.

## Features
* **Real-time Radar Display:** Smooth, high-performance rendering using the HTML5 Canvas API.
* **Collision Risk Analysis:** Automatically calculates Closest Point of Approach (CPA) and Time to CPA (TCPA) to detect collision threats.
* **Infinite Simulation:** Ships move continuously; targets outside the view range are automatically respawned relative to the own ship.
* **Interactive Controls:**
    * **Pan:** Click and drag to move the camera (relative to ship).
    * **Zoom:** Mouse wheel to zoom in/out.
    * **Select:** Click ships to view details or edit speed/heading.
* **WebSocket Streaming:** Low-latency state updates (20Hz).

## Tech Stack
* **Backend:** Python, FastAPI, Uvicorn (WebSockets)
* **Frontend:** Vanilla JavaScript, HTML5, CSS3
* **Protocol:** WebSocket (State Sync), HTTP (Control Actions)

## Installation

1.  **Clone the repository**
    ```bash
    git clone https://github.com/dhanushl0l/collision-system.git
    cd collision-system
    ```
2.  **Install Dependencies**
    ```bash
    pip install -r requirements.txt
    ```
3.  **Run the Server**
    ```bash
    uvicorn app.main:app --reload
    ```
    *Or use the provided setup script:*
    ```bash
    ./setup.sh
    ```
## Usage
1.  Open your browser to **http://localhost:8000**
2.  The "OWN" ship is the green marker in the center.
3.  **Red/Orange targets** indicate collision risks.
4.  Click any target to modify its Speed and Heading.