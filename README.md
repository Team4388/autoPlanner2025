# autoPlanner

(WIP) An auto creation tool for Ridgebotics 2024

### Install
```shell
git clone https://github.com/astatin3/autoPlanner
cd autoPlanner
pip install -r requirements.txt
python3 ./main.py
```
### Usage:

##### "Path Editor" Tab: 
- Click to add nodes
- Click on specific points to manipulate paths and nodes

##### "Button editor" Tab:
- Click on specific frames on the timeline to change to that position
- When selected on a frame, the robot's position in that time should show up.
- Drag positional keyframes around to speed up and speed down the robot's travel between nodes
- While a frame is selected, Press the 'e' key to swap to button mode.
- In button mode select buttons on the driver and operator controllers.

##### "Export" Tab:
- Click export, and save to a file

### Known Bugs:
- Because the variables don't get transferred over yet, you must click on the button editor tab before exporting.
- The driver controller's movement stick is rotated by 90 degrees (Maybe)