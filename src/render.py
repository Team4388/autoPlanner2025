import math
import os
import sys
from pygame.locals import *
import numpy as np

curvePointColor = (255, 255, 0)
curvePointRadius = 2

selTabBorderSize = 2
selTabBorderIndent = 3

nodeSquareRadius = 35
nodeSquareColor = (127, 127, 127, 0.5)
nodeSquareWidth = 3

nodeTickLength = 5

def image_path(relative_path):
  try:
    base_path = sys._MEIPASS
  except Exception:
    base_path = os.path.abspath(".")

  return os.path.join(base_path, relative_path)


class render():
  

  def __init__(self, pg, screen, topBarHeight, bottomBarHeight):
    self.pg = pg
    self.screen = screen

    self.topBarHeight = topBarHeight
    self.bottomBarHeight = bottomBarHeight
    
    self.width = self.screen.get_width()
    self.height = self.screen.get_width() * (643/1286)
    self.rect = (0, self.topBarHeight, self.width, self.height+bottomBarHeight)
    
    self.font = self.pg.font.Font(None, 25)

    self.fieldImg = self.loadImg("images/Field.png")
    self.offsetSize = self.fieldImg.get_width() / self.width
    self.fieldImg = pg.transform.scale(self.fieldImg, (self.width, self.height))
    
    self.elements = []
    
    
    
    
  def invert(self, img):
    inv = self.pg.Surface(img.get_rect().size, self.pg.SRCALPHA)
    inv.fill((255,255,255))
    inv.blit(img, (0,0), None, BLEND_RGB_SUB)
    return inv
  
  

  def line(self, color, pos1, pos2, width):
    self.pg.draw.line(self.screen, color, pos1, pos2, round(width/self.offsetSize))

  

  def circle(self, color, pos, radius):
    self.pg.draw.circle(self.screen, color, pos, radius/self.offsetSize)

  

  def drawrect(self, color, rect):
    self.pg.draw.rect(self.screen, color, rect)
    
    
    
  # def drawText(self, text, color,):
    
  #   text = self.font.render(text, True, color)
    
  #   rect = text.get_rect()
    
  #   self.screen.blit(text, rect)
  #   # text_rect = text.get_rect(center=(rect[0]+(rect[2]/2), rect[1]+(rect[3]/2)))

  

  def isInRect(self, pos, rect):
    return pos[0] >= rect[0] and \
            pos[0] <= rect[0]+rect[2] and \
            pos[1] >= rect[1] and \
            pos[1] <= rect[1]+rect[3]



  def image(self, img, rect):
    self.screen.blit(self.pg.transform.scale(img, (rect[2], rect[3])), rect)
  
  
  
  def loadImg(self, path):
    return self.pg.image.load(image_path(path)).convert_alpha()
  


  def robotSquare(self, pos, rot):
    pos1 = ((math.sin(rot + math.pi*-0.25)*nodeSquareRadius/self.offsetSize) + pos[0],
            (math.cos(rot + math.pi*-0.25)*nodeSquareRadius/self.offsetSize) + pos[1])
    pos2 = ((math.sin(rot + math.pi*0.25)*nodeSquareRadius/self.offsetSize) + pos[0],
            (math.cos(rot + math.pi*0.25)*nodeSquareRadius/self.offsetSize) + pos[1])
    pos3 = ((math.sin(rot + math.pi*0.75)*nodeSquareRadius/self.offsetSize) + pos[0],
            (math.cos(rot + math.pi*0.75)*nodeSquareRadius/self.offsetSize) + pos[1])
    pos4 = ((math.sin(rot + math.pi*1.25)*nodeSquareRadius/self.offsetSize) + pos[0],
            (math.cos(rot + math.pi*1.25)*nodeSquareRadius/self.offsetSize) + pos[1])

    pos5 = ((math.sin(rot)*(nodeSquareRadius+nodeTickLength)/self.offsetSize) + pos[0],
            (math.cos(rot)*(nodeSquareRadius+nodeTickLength)/self.offsetSize) + pos[1])
    pos6 = ((math.sin(rot)*(nodeSquareRadius-nodeTickLength)/self.offsetSize) + pos[0],
            (math.cos(rot)*(nodeSquareRadius-nodeTickLength)/self.offsetSize) + pos[1])

    self.line(nodeSquareColor, pos1, pos2, nodeSquareWidth*self.offsetSize)
    self.line(nodeSquareColor, pos2, pos3, nodeSquareWidth*self.offsetSize)
    self.line(nodeSquareColor, pos3, pos4, nodeSquareWidth*self.offsetSize)
    self.line(nodeSquareColor, pos4, pos1, nodeSquareWidth*self.offsetSize)
    
    self.line(nodeSquareColor, pos5, pos6, nodeSquareWidth*self.offsetSize)


  

  def bezier(self, p0, p1, p2, curvePointCount):
    #for p in [p0, p1, p2]:
    #    pg.draw.circle(self.screen, (255, 255, 255), p, 5)
    for t in np.arange(0, 1, 1/curvePointCount):
      px = p0[0]*(1-t)**2 + 2*(1-t)*t*p1[0] + p2[0]*t**2
      py = p0[1]*(1-t)**2 + 2*(1-t)*t*p1[1] + p2[1]*t**2
      self.circle(curvePointColor, (px, py), curvePointRadius)
    self.circle(curvePointColor, p2, curvePointRadius)
        #self.drawrect(curvePointColor, (round(px+0.5), round(py+0.5), curvePointRadius, curvePointRadius))

  

  def clear(self):
    self.pg.draw.rect(self.screen, (0, 0, 0), self.rect)

  

  def drawField(self):
    self.screen.blit(self.fieldImg, self.rect)

  

  def renderElements(self, pos):
    for elem in self.elements:
      if elem['type'] == 'button' and elem['getIsVisible']():
        # print(elem['getIsSelected']())
        self.renderButton(elem['rect'], elem['text'], elem['getIsSelected'](), pos)

  

  def clickElement(self, pos):
    for elem in self.elements:
      if elem['type'] == 'button' and elem['getIsVisible']() and self.isInRect(pos, elem['rect']):
        elem['onClick'](pos)

  

  def update(self):
    self.pg.display.update()
  
  

  def addButton(self, rect, text, getIsSelected, getIsVisible, onClick):
    self.elements.append({
      "type": "button",
      "text": text,
      "getIsSelected": getIsSelected,
      "getIsVisible": getIsVisible,
      "onClick": onClick,
      "rect": rect
    })
  
  

  def renderButton(self, rect, text, selected, mousePos):
    
    # print(isInRect(mousePos, rect))
    
    if self.isInRect(mousePos, rect):
      color = (16,64,32)
    else:
      color = (16,16,32)
      
    if selected:
      borderColor = (0,255,0)
    else:
      borderColor = (64,127,127)
  
    text = self.font.render(text, True, (255,255,255))
    text_rect = text.get_rect(center=(rect[0]+(rect[2]/2), rect[1]+(rect[3]/2)))
        
    self.pg.draw.rect(self.screen, color, rect)
    rect = (rect[0]+selTabBorderIndent,rect[1]+selTabBorderIndent,
            rect[2]-selTabBorderIndent*2,rect[3]-selTabBorderIndent*2)
    self.pg.draw.rect(self.screen, borderColor, rect)
    rect = (rect[0]+selTabBorderSize,rect[1]+selTabBorderSize,
            rect[2]-selTabBorderSize*2,rect[3]-selTabBorderSize*2)
    self.pg.draw.rect(self.screen, color, rect)
  
    self.screen.blit(text, text_rect)
    
    self.update()