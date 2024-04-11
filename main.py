import math
from copy import copy

import pygame as pg
from pygame.locals import *
from sys import exit
import numpy as np

import src.render as render

import src.pathEditor as pathEditor
import src.buttonEditor as buttonEditor
import src.export as export

doubleClickDuration = 200

pg.init()
pg.font.init()

topBarHeight = 40
bottomBarHeight = 60

screen_width = 1200
screen_height = (screen_width * (643/1286)) + topBarHeight + bottomBarHeight

screen = pg.display.set_mode((screen_width, screen_height))#, pg.RESIZABLE)
pg.display.set_caption("Auto Planner")

render = render.render(pg, screen, topBarHeight, bottomBarHeight)

tabIndex = 0
tabs = [
    pathEditor.pathEditor(render),
    buttonEditor.buttonEditor(render, pathEditor),
    export.export(pg, render, buttonEditor)
]

tabs[tabIndex].load()

def addTab(i):
    x1 = i * (screen_width/(len(tabs)))
    x2 = (screen_width/(len(tabs)))
    rect = (x1, 0, x2, topBarHeight)
    
    def getIsSelected():
        global tabIndex
        return tabIndex == i
    
    def getIsVisible():
        return True
    
    def onClick(pos):
        global tabIndex
        tabs[tabIndex].unload()
        tabIndex = i
        tabs[tabIndex].load()
        render.renderElements(pos)
        pg.display.update()
    
    render.addButton(rect, tabs[i].name, getIsSelected, getIsVisible, onClick)
            
for i in range(len(tabs)):
    addTab(i)
    
render.renderElements((screen_width/2, screen_height/2))

running = True
last_click = -1

def offsetPos(pos):
    return (pos[0],pos[1])

while running:
    for event in pg.event.get():
        
        if event.type == pg.MOUSEMOTION:
            pos = pg.mouse.get_pos()
            render.renderElements(pos)
            if pos[1] > topBarHeight:
                tabs[tabIndex].mouseMove(offsetPos(pos))
            # refreshTabs(pos)
        
        elif event.type == pg.MOUSEBUTTONDOWN:
            pos = pg.mouse.get_pos()
            render.clickElement(pos)
            if pos[1] > topBarHeight:
                now = pg.time.get_ticks()
                if now - last_click <= doubleClickDuration:
                    tabs[tabIndex].doubleClick(offsetPos(pos))   
                else:
                    tabs[tabIndex].mouseDown(offsetPos(pos))
                last_click = pg.time.get_ticks()
            # else:
                # clickTab(pos)
        
        elif event.type == pg.MOUSEBUTTONUP:
            pos = pg.mouse.get_pos()
            if pos[1] > topBarHeight:
                tabs[tabIndex].mouseUp(offsetPos(pos))

        elif event.type == pg.KEYDOWN:
            tabs[tabIndex].keyDown(event.key)
            if event.key == pg.K_TAB:
                tabs[tabIndex].unload()
                tabIndex = (tabIndex + 1) % len(tabs)
                tabs[tabIndex].load()
                render.renderElements(pg.mouse.get_pos())

        elif event.type == pg.QUIT:
            running = False
            
pg.quit()
