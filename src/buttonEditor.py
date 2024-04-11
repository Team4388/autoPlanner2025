import math
import copy
import json

render = None
pathEditor = None
bottomBarRect = None

# leftSidee = True

ogNodes = []
ogCtrlNodes = []
ogRotNodes = []

keyFrames = []

matchLength = 15
TPS = 50

tickTime = round(1/TPS*1000)
matchTicks = matchLength * TPS
displayTickResolution = 4
displayTicks = round(matchTicks / displayTickResolution)

buttonEditColor = (191,0,191)
buttonEditNodeRadius = 6

dragFrameIndex = -1
ogDragFramePos = -1

selFrame = -1

buttonImages = {}
buttonMode = False

buttonPositions = {
  'A': ((1089,494),100),
  'B': ((1187,404),100),
  'X': ((996,411),100),
  'Y': ((1093,321),100),
  
  'Dpad': ((549,619),220),
  
  'Dpad_Up': ((549,561),70),
  'Dpad_Down': ((549,677),70),
  'Dpad_Left': ((485,619),70),
  'Dpad_Right': ((607,619),70),
  
  'Menu': ((832,411),100),
  'Windows': ((629,411),100),
  
  'Left_Stick': ((375,422),150),
  'Right_Stick': ((914,622),150),
  
  'LB': ((352,184),150),
  'RB': ((1100,184),150),
  
  'LT': ((356,67),150),
  'RT': ((1096,67),150)
}



def getKeyframeAtPos(index):
  for frame in keyFrames:
      if frame["timeIndex"] == index:
        return frame
  return None



def getFrameIndex(frame):
  if frame == None:
    return -1
  return keyFrames.index(frame)



def getPosKeyframeAtPos(index):
  for frame in keyFrames:
    if frame["timeIndex"] == index and frame['type'] == 'position':
      return frame
  return None



def getPosKeyframes():
  frames = []
  for keyFrame in keyFrames:
    if keyFrame['type'] == 'position':
      frames.append(keyFrame)
  return frames



def getButtonKeyframes():
  frames = []
  for keyFrame in keyFrames:
    if keyFrame['type'] == 'controller':
      frames.append(keyFrame)
  return frames



def getBezierPointCounts():
  counts = []
  frames = getPosKeyframes()
  for i in range(1,len(frames)):
    counts.append(frames[i]['timeIndex'] - frames[i-1]['timeIndex'])
  return counts



def getPosKeyframeByIndex(index):
  for frame in keyFrames:
    if frame['type'] == 'position' and frame["index"] == index:
      return frame
  return None



def getSurroundingPosFrames(index):
  prevFrame = None
  for i in range(index,-1,-1):
    frame = getPosKeyframeAtPos(i)
    if frame != None and (dragFrameIndex == -1 or not frame == keyFrames[dragFrameIndex]):
      prevFrame = frame
      break
  nextFrame = None
  for i in range(index,displayTicks,1):
    frame = getPosKeyframeAtPos(i)
    if frame != None and (dragFrameIndex == -1 or not frame == keyFrames[dragFrameIndex]):
      nextFrame = frame
      break
    
  if nextFrame == None and prevFrame == None:
      return prevFrame, nextFrame
  # elif nextFrame == None:
  #   return prevFrame, prevFrame
  # elif prevFrame == None:
  #   return nextFrame, nextFrame
  
  return prevFrame, nextFrame



def getLeftButtonFrame(index):
  for i in range(index,0,-1):
    frame = getKeyframeAtPos(i)
    if frame != None and frame['type'] == 'controller':
      return frame
  return None



def getButtonFrameAtPos(index):
  for i in range(len(keyFrames)):
    frame = keyFrames[i]
    if frame != None and frame['type'] == 'controller':
      return frame
  return None




def getRobotAtIndex(index):
  prevFrame, nextFrame = getSurroundingPosFrames(index)
  
  # print(prevFrame)
  # print(nextFrame)
  
  if prevFrame == None and nextFrame == None:
    return (0,0), 0 
  if prevFrame == None:
    return nextFrame['position'], nextFrame['rotation']
  elif nextFrame == None:
    return prevFrame['position'], prevFrame['rotation']
  elif nextFrame['timeIndex'] - prevFrame['timeIndex'] == 0:
    return prevFrame['position'], prevFrame['rotation']
  
  relPos = -((prevFrame['timeIndex'] - index)/(nextFrame['timeIndex'] - prevFrame['timeIndex']))
  
  pos = calcBezierPoint(prevFrame['position'], ogCtrlNodes[prevFrame['index']], nextFrame['position'], relPos)

  if prevFrame['rotation'] - nextFrame['rotation'] < -math.pi:
    rot = ((nextFrame['rotation']-prevFrame['rotation']-math.pi*2)*relPos) + prevFrame['rotation']
  elif prevFrame['rotation'] - nextFrame['rotation'] > math.pi:
    rot = ((nextFrame['rotation']-prevFrame['rotation']+math.pi*2)*relPos) + prevFrame['rotation']
  else:
    rot = ((nextFrame['rotation']-prevFrame['rotation'])*relPos) + prevFrame['rotation']
  
  # diff = (nextFrame['rotation']-prevFrame['rotation'])
  # if diff >= math.pi:
  #   rot = ((nextFrame['rotation']-prevFrame['rotation']-math.pi*2)*relPos) + prevFrame['rotation']
  # elif diff <= math.pi:
  #   rot = ((nextFrame['rotation']-prevFrame['rotation']+math.pi*2)*relPos) + prevFrame['rotation']
  # else:
  #   rot = ((nextFrame['rotation']-prevFrame['rotation'])*relPos) + prevFrame['rotation']

  
  return pos, rot
    


# def getTimeBarColor(index):
#   frame = getKeyframeAtPos(index)
#   if frame == None:
#     return (0,0,0)
#   if frame['type'] == 'position':
#     return (127,127,0)
#   elif frame['type'] == 'controller':
#     return buttonEditColor
      
#   return (16,16,32)



def calcBezierPoint(p0, p1, p2, t):
  px = p0[0]*(1-t)**2 + 2*(1-t)*t*p1[0] + p2[0]*t**2
  py = p0[1]*(1-t)**2 + 2*(1-t)*t*p1[1] + p2[1]*t**2
  return (px, py)




def reloadBar(pos):
  toggle = False
  for i in range(displayTicks):
    x1 = i * (render.width/(displayTicks))
    x2 = (render.width/(displayTicks))
    rect = (x1, bottomBarRect[1], x2, bottomBarRect[3])
    
    color = (0, 0, 0)
    
    if i == selFrame:
      color = (color[0]+64,color[1]+64,color[2]+64)
    if render.isInRect(pos, rect):
      color = (color[0]+64,color[1]+64,color[2]+64)
      if dragFrameIndex != -1 and getKeyframeAtPos(i) == None:
        if keyFrames[dragFrameIndex]['type'] == 'position':
          prevFrame, nextFrame = getSurroundingPosFrames(ogDragFramePos)
          
          if prevFrame == nextFrame: 
            pass
          elif prevFrame == None:
            if i < nextFrame['timeIndex']:
              keyFrames[dragFrameIndex]['timeIndex'] = i
          elif nextFrame == None:
            if i > prevFrame['timeIndex']:
              keyFrames[dragFrameIndex]['timeIndex'] = i
          elif i > prevFrame['timeIndex'] and i < nextFrame['timeIndex']:
            keyFrames[dragFrameIndex]['timeIndex'] = i
            
        else:
          keyFrames[dragFrameIndex]['timeIndex'] = i
    else:
      color = (color[0]+16+(toggle*16),color[1]+16+(toggle*16),color[2]+32+(toggle*16))
      
      
    frame = getKeyframeAtPos(i)
    if frame == None:
      pass
    elif frame['type'] == 'position':
      color = (191,191,0)
    elif frame['type'] == 'controller':
      color = buttonEditColor
    
    toggle = not toggle
    
    render.drawrect(color, rect)
    # renderSelectIndicator(i)
  render.update()



def clickBar(pos):
  for i in range(displayTicks):
    x1 = i * (render.width/(displayTicks))
    x2 = (render.width/(displayTicks))
    rect = (x1, bottomBarRect[1], x2, bottomBarRect[3])
    
    if render.isInRect(pos, rect):
      global selFrame
      global dragFrameIndex
      global ogDragFramePos
      selFrame = i
      if dragFrameIndex == -1:
        dragFrameIndex = getFrameIndex(getKeyframeAtPos(i))      
        ogDragFramePos = i
      return
    
    
    
def createBlankController():
  returnArr = []
  for i in range(len(controllerRects)):
    returnArr.append({
      'A': False,
      'B': False,
      'X': False,
      'Y': False,
      'Dpad_Up': False,
      'Dpad_Down': False,
      'Dpad_Left': False,
      'Dpad_Right': False,
      'Menu': False,
      'Windows': False,
      'Left_Stick': False,
      'Right_Stick': False,
      'LB': False,
      'RB': False,
      'LT': False,
      'RT': False
    })
  return returnArr




def toggleControllerButton(btnStr, controllerIndex):
  global keyFrames
  lastFrame = getLeftButtonFrame(selFrame)
  if lastFrame == None:
    keyFrames.append({
      "type": "controller",
      "timeIndex": selFrame,
      "controllers": createBlankController()
    })
    frame = keyFrames[len(keyFrames)-1]
  elif lastFrame['timeIndex'] != selFrame:
    keyFrames.append({
      "type": "controller",
      "timeIndex": selFrame,
      "controllers": copy.deepcopy(lastFrame['controllers'])
    })
    frame = keyFrames[len(keyFrames)-1]
  else:
    frame = lastFrame
    
  if not btnStr in ['Dpad_Up', 'Dpad_Down', 'Dpad_Left', 'Dpad_Right']:
    
    frame['controllers'][controllerIndex][btnStr] = not frame['controllers'][controllerIndex][btnStr]
  
  # Dpad Stuff
  elif frame['controllers'][controllerIndex][btnStr] == True:
    for btn in ['Dpad_Up', 'Dpad_Down', 'Dpad_Left', 'Dpad_Right']:
      frame['controllers'][controllerIndex][btn] = False
  else:
    for btn in ['Dpad_Up', 'Dpad_Down', 'Dpad_Left', 'Dpad_Right']:
      frame['controllers'][controllerIndex][btn] = False
    frame['controllers'][controllerIndex][btnStr] = True
  
  



def getControllerButtons(controllerIndex):
  frame = getLeftButtonFrame(selFrame)
  if frame == None:
    return createBlankController()[0]
  else:
    return frame['controllers'][controllerIndex]



def renderXboxControllers():
  for i in range(len(controllerRects)):
    
    rect = controllerRects[i]
      
    offsetSize = rect[2]/buttonImages['Controller'].get_width()
  
    def offsetControllerButton(index):
      pos, size = buttonPositions[index]
      rect2 = ((pos[0]-(size/2), pos[1]-(size/2), size, size))
      return (rect[0]+(rect2[0])*offsetSize,rect[1]+(rect2[1])*offsetSize,rect2[2]*offsetSize,rect2[2]*offsetSize)
    
    render.image(buttonImages['Controller'], rect)
    
    btns = getControllerButtons(i)
    
    for btn in ['A','B','X','Y','Menu','Windows','LB','RB','LT','RT','Left_Stick','Right_Stick']:
      if btns[btn]:
        render.image(render.invert(buttonImages[btn]), offsetControllerButton(btn))
      else:
        render.image(buttonImages[btn], offsetControllerButton(btn))

    if btns['Dpad_Up']:
      render.image(buttonImages['Dpad_Up'], offsetControllerButton('Dpad'))
    elif btns['Dpad_Down']:
      render.image(buttonImages['Dpad_Down'], offsetControllerButton('Dpad'))
    elif btns['Dpad_Left']:
      render.image(buttonImages['Dpad_Left'], offsetControllerButton('Dpad'))
    elif btns['Dpad_Right']:
      render.image(buttonImages['Dpad_Right'], offsetControllerButton('Dpad'))
    else:
      render.image(buttonImages['Dpad'], offsetControllerButton('Dpad'))
      

    # for btn in ['Dpad_Up','Dpad_Down','Dpad_Left','Dpad_Right']:
    #   if
    #   render.drawrect((255,255,255), offsetControllerButton(btn))
  
  
  
def controllerClick(pos):
  for i in range(len(controllerRects)):
    
    rect = controllerRects[i]
  
    offsetSize = rect[2]/buttonImages['Controller'].get_width()
  
    def offsetControllerButton(index):
      pos, size = buttonPositions[index]
      rect2 = ((pos[0]-(size/2), pos[1]-(size/2), size, size))
      return (rect[0]+(rect2[0])*offsetSize,rect[1]+(rect2[1])*offsetSize,rect2[2]*offsetSize,rect2[2]*offsetSize)

    for btn in ['A','B','X','Y','Menu','Windows','LB','RB','LT','RT','Left_Stick','Right_Stick','Dpad_Up','Dpad_Down','Dpad_Left','Dpad_Right']:
      if render.isInRect(pos, offsetControllerButton(btn)):
        toggleControllerButton(btn, i)
        
        


def renderTimeText():
  if selFrame == -1:
    return
  seconds = round((((selFrame*displayTickResolution)+1)/matchTicks)*matchLength,2)
  text = f'{str(seconds)} s / {str(matchLength)}.0 s'

  text = render.font.render(text, True, (255,255,255))
  
  # global leftSide
  
  # if leftSide:
  #   rect = text.get_rect(bottomright=(render.width,render.height+render.topBarHeight))
  # else:
  rect = text.get_rect(bottomleft=(0,render.height+render.topBarHeight))
  
  render.screen.blit(text, rect)




class buttonEditor:
  name = "Button Editor"

  def __init__(self, tmprender, tmppathEditor):
    global render
    global pathEditor
    render = tmprender
    pathEditor = tmppathEditor
    
    global indicatorBarHeight
    indicatorBarHeight = round(render.screen.get_width()/displayTicks)
    
    global bottomBarRect
    bottomBarRect = (0, (render.screen.get_height()-render.bottomBarHeight), render.screen.get_width(), render.bottomBarHeight)

    global buttonImages
    buttonImages = {
      "Controller": render.loadImg('images/XboxOne_Diagram_Simple.png'),
      
      "A": render.loadImg('images/XboxOne_A.png'),
      "B": render.loadImg('images/XboxOne_B.png'),
      "X": render.loadImg('images/XboxOne_X.png'),
      "Y": render.loadImg('images/XboxOne_Y.png'),
      
      "Dpad": render.loadImg('images/XboxOne_Dpad.png'),
      "Dpad_Up": render.loadImg('images/XboxOne_Dpad_Up.png'),
      "Dpad_Down": render.loadImg('images/XboxOne_Dpad_Down.png'),
      "Dpad_Left": render.loadImg('images/XboxOne_Dpad_Left.png'),
      "Dpad_Right": render.loadImg('images/XboxOne_Dpad_Right.png'),
      
      "Menu": render.loadImg('images/XboxOne_Menu.png'),
      "Windows": render.loadImg('images/XboxOne_Windows.png'),
      
      "Left_Stick": render.loadImg('images/XboxOne_Left_Stick.png'),
      "Left_Stick_Click": render.loadImg('images/XboxOne_Left_Stick_Click.png'),
      "Right_Stick": render.loadImg('images/XboxOne_Right_Stick.png'),
      "Right_Stick_Click": render.loadImg('images/XboxOne_Right_Stick_Click.png'),
      
      
      "LB": render.loadImg('images/XboxOne_LB.png'),
      "RB": render.loadImg('images/XboxOne_RB.png'),
      "LT": render.loadImg('images/XboxOne_LT.png'),
      "RT": render.loadImg('images/XboxOne_RT.png')
      
    }
    
    ControllerSize = (render.width/2, render.width*(buttonImages['Controller'].get_height()/buttonImages['Controller'].get_width())/2)
    ControllerYOffset = (render.height-ControllerSize[1])/2
    global controllerRects
    controllerRects = [
      (0, render.topBarHeight+ControllerYOffset, ControllerSize[0], ControllerSize[1]),
      (ControllerSize[0], render.topBarHeight+ControllerYOffset, ControllerSize[0], ControllerSize[1])
    ]

  def refresh(self):
    render.clear()
    if not buttonMode:
      global ogNodes
      global ogCtrlNodes
      global ogRotNodes
      
      render.drawField()
      
      pointCounts = getBezierPointCounts()
      for i in range(0,len(ogCtrlNodes)):
        render.bezier(ogNodes[i], ogCtrlNodes[i], ogNodes[i+1], pointCounts[i])
      
      buttonFrames = getButtonKeyframes()
      for frame in buttonFrames:
        pos, rot = getRobotAtIndex(frame['timeIndex'])
        render.circle(buttonEditColor, pos, buttonEditNodeRadius)
            
      if selFrame != -1 and len(ogNodes) > 0:
        pos, rot = getRobotAtIndex(selFrame)
        render.robotSquare(pos, rot)
      
      
    else:
      renderXboxControllers()
      
    renderTimeText()
      
    reloadBar((0,0))
    render.update()
          
    

  def mouseDown(self, pos):
    if buttonMode and pos[1] < bottomBarRect[1]:
      controllerClick(pos)
      self.refresh()
    elif pos[1] > bottomBarRect[1]:
      clickBar(pos)
      self.refresh()

    

  def mouseUp(self, pos):
    global dragFrameIndex
    if dragFrameIndex != -1:
      dragFrameIndex = -1
      ogDragFramePos = -1
      self.refresh()
      reloadBar((0, 0))

    

  def mouseMove(self, pos):
    global dragFrameIndex
    if dragFrameIndex != -1 or pos[1] > bottomBarRect[1]:
      reloadBar(pos)
    
    # global leftSide
      
    # if leftSide and pos[0] > (render.width/2):
    #   leftSide = False
    #   self.refresh()
    # if not leftSide and pos[0] < (render.width/2):
    #   leftSide = True
    #   self.refresh()

    # if pos[1] > bottomBarRect[1]:

    

  def doubleClick(self, pos):
    pass
    # if pos[1] > bottomBarRect[1]:
    #   clickBar(pos)
    #   self.refresh()
    

  def keyDown(self, key):
    global selFrame
    global buttonMode
    if key == render.pg.K_LEFT and selFrame > 0:
      selFrame -= 1
      self.refresh()
    elif key == render.pg.K_RIGHT and selFrame < displayTicks-1:
      selFrame += 1
      self.refresh()
    elif buttonMode and key == render.pg.K_DELETE and selFrame != -1:
      frame = getKeyframeAtPos(selFrame)
      if frame != None and frame['type'] != 'position':
        global keyFrames
        keyFrames.remove(frame)
      self.refresh()
    elif selFrame != -1 and key == render.pg.K_e:
      buttonMode = not buttonMode
      self.refresh()
    

  def updateNodes(self, loadKeyframes):
    global ogNodes
    global ogCtrlNodes
    global ogRotNodes
    ogNodes = pathEditor.nodes.copy()
    ogCtrlNodes = pathEditor.curveEditPoints.copy()
    ogRotNodes = pathEditor.nodeRotations.copy()
    
    if not loadKeyframes:
      return
    
    for i in range(len(ogNodes)):
      frame = getPosKeyframeByIndex(i)
      frame['position'] = ogNodes[i]
      frame['rotation'] = ogRotNodes[i]

    

  def load(self):
    global selFrame
    global buttonMode
    selFrame = -1
    buttonMode = False
    
    global ogNodes
    global ogCtrlNodes
    global ogRotNodes
    
    if len(ogNodes) != len(pathEditor.nodes):
      
      global keyFrames
      
      for i in range(len(keyFrames)-1,-1,-1):
        if keyFrames[i]['type'] == 'position':
          keyFrames.pop(i)
      
      self.updateNodes(False)
      
      for i in range(len(ogNodes)):
        if len(ogNodes) == 1:
          timeIndex = 0
        else:
          timeIndex = round((i)/(len(ogNodes)-1) * (displayTicks-1))
        keyFrames.append({
          "type": "position",
          "timeIndex": timeIndex,
          "index": i,
          "position": ogNodes[i],
          "rotation": ogRotNodes[i]
        })
    else:
      self.updateNodes(True)
      
    self.refresh()
  
    
  def unload(self):
    pass