import crossfiledialog
import struct
import copy

pg = None
buttonEditor = None
events = []

#Save according to https://github.com/Team4388/2024AcrossTheRidgebotiverse/blob/Prep-For-Denver/src/main/java/frc4388/robot/commands/Autos/neo%20AutoRecoding%20format.txt


moveMultiplier = 0.1
rotMultiplier = 1


def buttonsToBytes(buttons):
  data = 0
  for i in range(16):
    data |= buttons[i] << i
  return data.to_bytes(2, "little", signed=True)


def toByte(num):
  if num > 255:
    raise OverflowError
  return num.to_bytes(1, 'big', signed=False)



def toShort(num):
  if num > 65535:
    raise OverflowError
  return num.to_bytes(2, 'big', signed=True)


def toInt(num):
  return struct.pack('>i', num)


def toDouble(num):
  return struct.pack('>d', num)
  



class xboxController:
  def __init__(self):
    self.buttons = [False for i in range(16)]
    self.leftStick = (0,0)
    self.rightStick = (0,0)
    self.LT = -1
    self.RT = -1
    self.POV = -1
    

def getPOVhat(up, down, left, right):
  if up and right:
    return 45
  elif right and down:
    return 135
  elif down and left:
    return 225
  elif left and up:
    return 315
  elif up:
    return 0
  elif right:
    return 90
  elif down:
    return 180
  elif left:
    return 270
  else:
    return -1
  



def getSticksAtFrame(index):
  
  fractionIndex = round(index/buttonEditor.displayTickResolution)
  
  newpos, newrot = buttonEditor.getRobotAtIndex(fractionIndex)
  oldpos, oldrot = buttonEditor.getRobotAtIndex(fractionIndex-1)
  
  # print(oldrot-newrot)
  
  diffPos = ((oldpos[0]-newpos[0])*moveMultiplier, (oldpos[1]-newpos[1])*moveMultiplier)
  diffRot = (oldrot-newrot)*rotMultiplier
  
  if abs(diffPos[0]) > 1 or abs(diffPos[1]) > 1 or abs(diffRot) > 1:
    print("Error! Robot moved too fast!, Try to edit 'Multiplier' values in export.py")
    return (0, 0), 0
  
  
  print(diffPos)
  
  # print(diffRot)
  
  return diffPos, diffRot



def getControllersAtFrame(index):
  controllers = [xboxController(), xboxController()]
  if index >= buttonEditor.matchTicks:
    return controllers
  
  pos, rot = getSticksAtFrame(index)
  
  controllers[0].leftStick = pos
  controllers[0].rightStick = (rot,0)
  
  btns = buttonEditor.getLeftButtonFrame(index)
  if btns == None:
    btns = buttonEditor.createBlankController()
  else:
    btns = btns['controllers']
  
  for i in range(len(controllers)):
    ctrlr = btns[i]
    
    controllers[i].buttons[0] = ctrlr['A']
    controllers[i].buttons[1] = ctrlr['B']
    controllers[i].buttons[2] = ctrlr['X']
    controllers[i].buttons[3] = ctrlr['Y']
    
    controllers[i].buttons[4] = ctrlr['LB']
    controllers[i].buttons[5] = ctrlr['RB']
    
    controllers[i].buttons[6] = ctrlr['Menu']
    controllers[i].buttons[7] = ctrlr['Windows']
  
    controllers[i].buttons[8] = ctrlr['Left_Stick']
    controllers[i].buttons[9] = ctrlr['Right_Stick']    
    
    controllers[i].LT = (ctrlr['LT']*2)-1
    controllers[i].RT = (ctrlr['RT']*2)-1
    
    controllers[i].POV = getPOVhat(ctrlr['Dpad_Up'], ctrlr['Dpad_Down'], 
                                    ctrlr['Dpad_Left'], ctrlr['Dpad_Right'])

    
  
  return controllers



def getFrameData(index):
  controllers = getControllersAtFrame(index)
  data = b''
  for ctrlr in controllers:
    # print(ctrlr.leftStick[0])
    data += toDouble(ctrlr.leftStick[0])
    data += toDouble(ctrlr.leftStick[1])
    data += toDouble(ctrlr.LT)
    data += toDouble(ctrlr.RT)
    data += toDouble(ctrlr.rightStick[0])
    data += toDouble(ctrlr.rightStick[1])
    
    data += buttonsToBytes(ctrlr.buttons)
    
    # for btn in ctrlr.buttons:
    #   data += toBit(data)
    #   print(toBit(data))
    
    data += toShort(ctrlr.POV)
    
  data += toInt(index * buttonEditor.tickTime)
  
  return data



def getHeader():
  header =  toByte(6)     # Num Axes per controller
  header += toByte(1)     # Num POVs
  header += toByte(2)     # Num Controllers
  header += toShort(buttonEditor.matchTicks) # Num Frames
  return header


        
def getData():
  data = b''
  for i in range(buttonEditor.matchTicks):
    data += getFrameData(i)
  return getHeader() + data



def save():
  path = crossfiledialog.save_file('Save auto file', './')
  # path = "./file.txt"
  with open(path, "wb") as f:
    f.write(getData())

class export:
  name = "Export"

  def __init__(self, tmppg, tmprender, tmpbuttonEditor):
    global pg
    pg = tmppg
    global render
    render = tmprender
    global buttonEditor
    buttonEditor = tmpbuttonEditor
    
    self.loaded = False
    
    def getIsSelected():
      return False
    
    def getIsVisible():
      return self.loaded
    
    def onClick(pos):
      save()
    
    render.addButton((round(render.width/4),round(render.screen.get_height()/4),round(render.width/2),round(render.height/2)), 
                     "Export", getIsSelected, getIsVisible, onClick)

  def mouseDown(self, pos):
    pass

  def mouseUp(self, pos):
    pass

  def mouseMove(self, pos):
    pass

  def doubleClick(self, pos):
    pass

  def keyDown(self, key):
    pass

  def load(self):
    self.loaded = True
    
    # for keyFrame in buttonEditor.keyFrames:
    #   keyFrame['timeIndex'] = keyFrame['timeIndex'] * buttonEditor.displayTickResolution
    
    
    render.clear()
    pg.display.update()
    
  def unload(self):
    self.loaded = False
    
    # for keyFrame in buttonEditor.keyFrames:
    #   keyFrame['timeIndex'] = round(keyFrame['timeIndex'] / buttonEditor.displayTickResolution)