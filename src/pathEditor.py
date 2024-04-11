import math
from pygame.locals import *

nodeColor = (255, 255, 255)
nodeRadius = 12

rotNodeDist = 35
rotNodeColor = (255, 0, 255)
rotNodeRadius = 8

lineApproximationLineColor = (127, 127, 127, 0.5)
lineApproximationLineWidth = 3

curveEditPointColor = (0, 255, 255)
curveEditPointRadius = 8

curvePointCount = 80

nodes = []
curveEditPoints = []
nodeRotations = []

clickType = -1
clickIndex = -1

render = None




def refresh():
  render.clear()
  render.drawField()
  
  for i in range(0,len(curveEditPoints)):
    render.line(lineApproximationLineColor, nodes[i], curveEditPoints[i], lineApproximationLineWidth)
    render.line(lineApproximationLineColor, curveEditPoints[i], nodes[i+1], lineApproximationLineWidth)
    
    render.bezier(nodes[i], curveEditPoints[i], nodes[i+1], curvePointCount)
    
    render.circle(curveEditPointColor, curveEditPoints[i], curveEditPointRadius)
  for i in range(0,len(nodeRotations)):
    posX = (math.sin(nodeRotations[i])*rotNodeDist/render.offsetSize) + nodes[i][0]
    posY = (math.cos(nodeRotations[i])*rotNodeDist/render.offsetSize) + nodes[i][1]
    render.circle(rotNodeColor, (posX, posY), rotNodeRadius)
    render.robotSquare(nodes[i], nodeRotations[i])
  for pos in nodes:

    render.circle(nodeColor, pos, nodeRadius)
  render.update()



def getElemAt(pos):
  for i in range(0,len(nodes)):
    if getDist(pos, nodes[i], nodeRadius):
      return 0, i
  for i in range(0,len(nodeRotations)):
    posX = (math.sin(nodeRotations[i])*rotNodeDist/render.offsetSize) + nodes[i][0]
    posY = (math.cos(nodeRotations[i])*rotNodeDist/render.offsetSize) + nodes[i][1]
    if getDist(pos, (posX, posY), nodeRadius):
      return 2, i
  for i in range(0,len(curveEditPoints)):
    if getDist(pos, curveEditPoints[i], curveEditPointRadius):
      return 1, i
  return -1, -1



def getDist(pos1, pos2, dist):
  return math.sqrt(math.pow(pos1[0]-pos2[0], 2) + math.pow(pos1[1]-pos2[1], 2)) <= dist



def addNode(pos):
  nodes.append(pos)
  if len(nodes) > 1:
    index = len(nodes)-1
    # Middle point between current point and previous point
    editPos = (nodes[index-1][0]+pos[0])/2,(nodes[index-1][1]+pos[1])/2
    curveEditPoints.append(editPos)
    nodeRotations.append(nodeRotations[index-1])
  else:
    nodeRotations.append(math.pi/2)
  refresh()



def nearestCirclePoint(center, pos, R):
  vX = pos[0] - center[0]
  vY = pos[1] - center[1]
  magV = math.sqrt(vX*vX + vY*vY)
  aX = center[0] + vX / magV * R
  aY = center[1] + vY / magV * R
  return (aX, aY)



def points2rad(center, pos):
  diffX = center[0] - pos[0]
  diffY = center[1] - pos[1]
  return -math.atan2(diffY, diffX) - (math.pi/2)

class pathEditor:
  name = "Path Editor"
  

  def __init__(self, tmprender):
    # global screen
    # screen = tmpscreen
    global render
    render = tmprender

    refresh()



  def mouseDown(self, pos):
    global clickType
    global clickIndex
    clickType, clickIndex = getElemAt(pos)
    if clickType == -1:
      addNode(pos)
    
    

  def mouseUp(self, pos):
    global clickType
    global clickIndex
    if clickType != -1:
      clickType = -1
      clickIndex = -1

    

  def mouseMove(self, pos):
    if clickType != -1:
      if clickType == 0:
        nodes[clickIndex] = pos
      if clickType == 1:
        curveEditPoints[clickIndex] = pos
      if clickType == 2:
        nodeRotations[clickIndex] = points2rad(nodes[clickIndex], nearestCirclePoint(nodes[clickIndex], pos, rotNodeDist/render.offsetSize))
      refresh()

    

  def doubleClick(self, pos):
    clickType, clickIndex = getElemAt(pos)
    if clickType == -1:
      pass
    elif clickType == 0:
        if clickIndex > 0:
          if clickIndex < len(nodes)-1:
            newPos = (nodes[clickIndex-1][0]+nodes[clickIndex][0])/2,(nodes[clickIndex-1][1]+nodes[clickIndex][1])/2
            curveEditPoints[clickIndex] = newPos
          curveEditPoints.pop(clickIndex-1)
        elif clickIndex == 0 and len(nodes) > 1:
          curveEditPoints.pop(clickIndex)
        nodes.pop(clickIndex) 
        nodeRotations.pop(clickIndex)
        refresh()
    
  def keyDown(self, key):
    pass

  def load(self):
    refresh()
  
  def unload(self):
    pass