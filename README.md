# autoPlanner

(WIP) An auto creation tool for Ridgebotics 2025

### Install

```shell
git clone https://https://github.com/Team4388/autoPlanner2025/tree/pyside
cd autoPlanner2025
pip install -r requirements.txt
python3 ./main.py
```

### Usage:

##### "Path Editor" Tab:

- Right click to add nodes
- Left click on specific points to manipulate paths and nodes
- Double click on nodes to delete them
- Double click on control points to make path, and robot movment continuous, while keeping the node clicked the at the same location (Smooth the path)

##### "Button editor" Tab:

- Click on specific frames on the timeline to change to that position
- When selected on a frame, the robot's position in that time should show up.
- Drag positional keyframes around to speed up and speed down the robot's travel between nodes
- While a frame is selected, Press the 'e' key to swap to button mode.
- In button mode select buttons on the driver and operator controllers.

##### "Export" Tab:

- Click export, and save to a file

### Known Bugs:
