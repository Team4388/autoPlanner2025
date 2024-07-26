# Auto Planner

(WIP) An auto creation tool for Ridgebotics 2025

### Install:

```shell
git clone https://https://github.com/Team4388/autoPlanner2025/tree/pyside
cd autoPlanner2025
pip install -r requirements.txt
python3 ./main.py
```
#
## Usage:

### "Path Editor" Tab:

- Right click to add nodes
- Left click on specific points to manipulate paths and nodes:
    - Drag cyan circles (Control points) to change the shape of the path
    - Drag magenta nodes change the rotation of the robot
    - Drag white numbers (Nodes) to change the position of the robot
- Double click on nodes to delete them
- Double click on control points to make path, and robot movment continuous, while keeping the node clicked the at the same location (Smooth the path)
- Press the 'r' key to delete the whole auto

### "Button editor" Tab:

- Click on specific frames on the timeline to change to that position
    - Pressing or holding the left or right arrow keys will move the current frame
- When selected on a frame, the robot's position in that time should show up.
- Drag positional keyframes around to speed up and speed down the robot's travel between nodes
- Pressing the 'e' key will pause and unpause the auto playback

### "Export" Tab (not made yet):

- Click export, and save to a file

### Known Bugs:

- Smoothing function is janky sometimes