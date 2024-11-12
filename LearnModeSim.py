import tkinter as tk
from PIL import Image, ImageTk
import math
from win32api import GetMonitorInfo, MonitorFromPoint
import platform as pl
import os
import pygame
import random
import time
from simFuncsTables import *

G = 6.67e-11
TIME = 3600*24*0.5
currentBody = None
currentGraph = "vel"

#initiate sim scale (set later)
simScale = 0

#calculates the mass to size function using max and min radius against their masses.
def computeMassToSizeFunction(maxRadius, minRadius, maxMass, minMass, exponent):
    gradient = (maxRadius-minRadius)/((maxMass-minMass) * 10**exponent)
    intercept = -1*gradient*minMass*10**exponent + minRadius
    return gradient, intercept


#a body class is created which contains the standrard method and attributes to be inherited
class body: 
    def __init__(self, inputName, inputMass): 
        self.name = inputName
        #2*10**30 kg is 100 pixel(radius).
        self.massToSizeFactor = 100/(2*10**30)
        self.bodyRadius = inputMass*self.massToSizeFactor
        self.mass = inputMass
        self.xOrd = 0
        self.yOrd = 0
        self.informationFile = ""
        self.image = ""
    #return range of coordinates where the user should click to select body
    def getClickRange(self):
        xMin = self.xOrd - self.bodyRadius
        xMax = self.xOrd + self.bodyRadius
        yMin = self.yOrd - self.bodyRadius
        yMax = self.yOrd + self.bodyRadius
        return [xMin,xMax], [yMin, yMax]


#a star class is created which inherits the methods and attributes of the star class.
class star(body):
    def __init__(self, inputName, inputMass):
        super(star,self).__init__(inputName,inputMass)
        self.type ="star"
        self.colourCode = (255,88,0) #orange
        self.xOrd = simWidth/2
        self.yOrd = simHeight/2
    #method which draws star in centre of frame
    def addBody(self, screen):
        pygame.draw.circle(screen, self.colourCode,(self.xOrd,self.yOrd), self.bodyRadius)
    #adds image instead of drawing a circle
    def addImage(self, screen):
        screen.blit(self.image, (self.xOrd - self.bodyRadius,self.yOrd - self.bodyRadius))
    def detectCollision(self, list):
        for body in list:
            if body.name == self.name: #check if other is self (all bodies wil have unique names)
                pass
            else:
                distance = math.sqrt((self.xOrd-body.xOrd) ** 2 + (self.yOrd-body.yOrd) ** 2)
                #remove body if collision occurs
                if distance <= self.bodyRadius + body.bodyRadius:
                    body.removeBody(list)
                    return body, False
        return None, False
                    



#create dictionary of colours to randomly pick thorugh when adding bodies
planetColours = {"Red":(255,0,0), "Green":(0,255,0), "Blue":(0,0,255),"Yellow": (255,255,0), "Brown": (139, 115, 85), "Aqua": (127, 255, 212),"Violet": (138, 43, 226),"Dark Green": (0, 100, 0), "Coral": (139, 62, 47)}
#planet class which inherits from body.
class planet(body):
    def __init__(self, inputName, inputMass, inputRadius, inputVelocity):
        super(planet,self).__init__(inputName,inputMass)
        #set initial conditions in case teh scenario is saved
        self.type = "planet"
        self.radius = inputRadius
        self.screenRadius = self.radius*simScale
        #set attributes used in movement
        self.xOrd = simWidth/2 - self.screenRadius
        self.yOrd = simHeight/2
        self.velX = 0
        self.velY = inputVelocity*1000 # convert to m/s
        #update x and y force attributes:
        self.forceX = 0
        self.forceY = 0
        #use function to get gradient and intercept
        self.massMultiplier, self. massAdder = computeMassToSizeFunction(30, 15, 200, 1, 24)
        #get body radius in pixels using function
        self.bodyRadius = (inputMass * self.massMultiplier) + self.massAdder
        #set random colour of planet
        self.colourCode = random.choice(list(planetColours.values()))
        self.colourName = self.removeColour()
        #set trail attributes
        self.trailFlag = False
        self.previousCoOrds = []
        #force vector atributes
        self.force = 0
        self.fVectorFlag = False    
        self.forceScaleMult, self.forceScaleAdd = computeMassToSizeFunction(250, 20, 1.9, 3.5e-3, 24)
        #force vector atributes
        self.vVectorFlag = False
        self.velScaleMult, self.velScaleAdd = computeMassToSizeFunction(150, 5, 60, 5, 3)
        #graph attributes
        self.previousForces = []
        self.previousVelocities = []
        #used to divide force by correct exponent
        self.forceExp = 22
    #update previous velocities list and add current velocity
    def updatePreviousVel(self):
        currentVel = math.sqrt(self.velX**2 + self.velY**2)/1000
        self.previousVelocities.append(currentVel)
        self.previousVelocities = self.previousVelocities[-1000:] #only keep last 1000 items to avoid wasting memory
    #update previousforces list and add current force
    def updatePreviousForces(self):
        self.previousForces.append(self.force*(10 ** -self.forceExp)) #get rid of exponent of force
        self.previousForces = self.previousForces[-1000:] #only keep last 1000 items to avoid wasting memory
    #calculate the coordinates of the end of the velocity arrow
    def computeEndOfVArrow(self):
        #calc magnitude of vector
        vel = math.sqrt(self.velX**2 + self.velY**2)
        #get vel  vector using velocity x and y
        deltaX = self.velX
        deltaY = self.velY
        #find unit vel vector
        unitVectX = (deltaX)/vel
        unitVectY = (deltaY)/vel
        vVectorLength = vel * self.velScaleMult  + self.velScaleAdd
        arrowX = self.xOrd + (unitVectX * vVectorLength)
        arrowY = self.yOrd - (unitVectY * vVectorLength)
        #convert to vector format (this is what draw_arrow takes in)
        endVector = pygame.math.Vector2(arrowX,arrowY)
        return endVector
    #output force vector on screen
    def showVVector(self, screen):
        endCoOrds= self.computeEndOfVArrow()
        #convert to vector format (this is what draw_arrow takes in)
        starCoOrds = pygame.math.Vector2(self.xOrd,self.yOrd)
        draw_arrow(screen,starCoOrds,endCoOrds,(255,77,1))
    #calculate the coordinates of the end of the force arrow in teh same way as velocity
    def computeEndOfFArrow(self):
        #calc magnitude of vector
        force = math.sqrt(self.forceX**2 + self.forceY**2)
        #get force  vector using velocity x and y
        deltaX = self.forceX
        deltaY = self.forceY
        #if force = 0 set vectors to 0 since can't divide by 0
        if force == 0:
            #find unit force vector
            unitVectX = 0
            unitVectY = 0
        else:
            #find unit force vector
            unitVectX = (deltaX)/force
            unitVectY = (deltaY)/force
        fVectorLength = force * self.forceScaleMult  + self.forceScaleAdd
        arrowX = self.xOrd + (unitVectX * fVectorLength)
        arrowY = self.yOrd - (unitVectY * fVectorLength)
        #convert to vector format (this is what draw_arrow takes in)
        endVector = pygame.math.Vector2(arrowX,arrowY)
        return endVector           
    #output force vector on screen
    def showFVector(self, screen):
        endCoOrds= self.computeEndOfFArrow()
        #convert to vector format (this is what draw_arrow takes in)
        starCoOrds = pygame.math.Vector2(self.xOrd,self.yOrd)
        draw_arrow(screen,starCoOrds,endCoOrds,(255,255,255))
    #add current coordinates to list of previous coordinates for trail
    def updateTrail(self):
        self.previousCoOrds.append((self.xOrd,self.yOrd))
    #clear list so teh trail is reset for next time
    def clearTrail(self):
        self.previousCoOrds.clear()
    #output trail on screen by filling previous pixels
    def showTrail(self, screen):
        if len(self.previousCoOrds)>=2:
            pygame.draw.lines(screen,self.colourCode, False, self.previousCoOrds, 2 )

    #removes colour from dict as now in use and adds to used colours dict
    def removeColour(self):
        #get key value for random colour and delete the valuekey pair from dictionary as it is in use
        for colourName, colourCode in planetColours.items():
            if colourCode == self.colourCode:
                del planetColours[colourName]
                return colourName
    #method which adds planet in pygame window
    def addBody(self, screen):
        pygame.draw.circle(screen, self.colourCode,(self.xOrd,self.yOrd), self.bodyRadius)
    #adds image instead of drawing a circle
    def addImage(self, screen):
        screen.blit(self.image, (self.xOrd- self.bodyRadius,self.yOrd- self.bodyRadius))
    #method to get force acting between two bodies and return x and y component.
    def calcForce(self, other):
        xOrd = self.xOrd
        yOrd = self.yOrd
        otherXOrd = other.xOrd
        otherYOrd = other.yOrd
        mass = self.mass
        otherMass = other.mass
        #get the difference in y and x of the two bodies in m.
        changeInY = ((yOrd - otherYOrd)/ simScale)*1000
        changeInX = ((otherXOrd-xOrd) /simScale)*1000
        #calculate r in m
        r = math.sqrt(changeInX**2 + changeInY**2)
        #Get angle using arctan
        angle = math.atan2(changeInY,changeInX)
        #Calculate force using F= GMm/r^2
        force = (G * mass * otherMass)/r**2
        #Get force components:
        forceX = force * math.cos(angle)
        forceY = force * math.sin(angle)
        return [forceX,forceY]
    #method to update planets position using mathematical formula.
    def updatePosition(self):
        #set net force to 0
        netForceX = 0
        netForceY = 0
        #go through each body on the simulation and add the force each one has
        for body in bodyList:
            #only add force if teh other body is not self
            if body.name != self.name:
                forces = self.calcForce(body)
                netForceX +=forces[0]
                netForceY +=forces[1]
        #update x and y force attributes:
        self.forceX = netForceX
        self.forceY = netForceY
        #update attrbite (used for force vector)
        self.force = math.sqrt(netForceX**2 + netForceY**2)
        #Use F = ma for calculating acceleration in m/s^2
        accX = netForceX/self.mass
        accY = netForceY/self.mass
        #Use v= u+at to calculate new velocity
        self.velX += accX * TIME
        self.velY += accY * TIME
        #s=vt using t as 1 day and convert to pixel value
        # t is 1 Earth day, so each step moves the planet the distance it would move in teh time step 
        distanceMovedX = (self.velX*TIME /1000)*simScale
        distanceMovedY = (self.velY*TIME /1000)*simScale
        #update x ordinate
        self.xOrd += distanceMovedX
        #update y ordinate
        self.yOrd -= distanceMovedY
    #method to detect if body has collided with another body
    def detectCollision(self, list):
        for body in list:
            if body.name == self.name: #check if other is self (all bodies wil have unique names)
                pass
            else:
                distance = math.sqrt((self.xOrd-body.xOrd) ** 2 + (self.yOrd-body.yOrd) ** 2)
                if distance <= self.bodyRadius + body.bodyRadius:
                #remove body from list if it is not a star, so no longer output on screen
                    if body.type != "star":
                        body.removeBody(list)
                    #if other body is comet don't remove planet, only remove comet
                    if body.type != "comet" and body.type!="moon":
                        #resize image to match size of body
                        self.removeBody(list)
                        #need to return true since self was removed and return body for explosion animation
                        return body,True
                    return body,False
        return None,False
    #remove body if it fully exits simulation screen
    def checkRemove(self, list):
        # check if body leaves simulation to the left:
        if self.xOrd+self.bodyRadius < 0:
            self.removeBody(list)
            return True
        #check if body leaves simulation to the right
        if self.xOrd - self.bodyRadius > simWidth:
            self.removeBody(list)
            return True
        #check if body leaves from top
        if self.yOrd + self.bodyRadius < 0:
            self.removeBody(list)
            return True
        #checl if body leaves form bottom
        if self.yOrd -self.bodyRadius > simHeight:
            self.removeBody(list)
            return True
        return False
    #remove body and add colour back to dict
    def removeBody(self, list):
        list.remove(self)
        planetColours[self.colourName] = self.colourCode
    



#dict of comet colours
cometColours = {"Lime green": (173, 255, 47),"Aqua": (0, 255, 255),"Pink": (255, 20, 147), "Orange": (139, 69, 0)}
#comet class inherits from planet class as they are very similiar.
class comet(planet):
    def __init__(self, inputName, inputMass, inputRadius, inputVelocity):
        super(comet,self).__init__(inputName,inputMass, inputRadius, inputVelocity)
        #attributes of planet to be overwritten:
        self.type = "comet"
        #use function to get gradient and intercept
        self.massMultiplier, self. massAdder = computeMassToSizeFunction(10, 5, 50, 1, 13)
        #get body radius in pixels using function
        self.bodyRadius = (inputMass * self.massMultiplier) + self.massAdder
        self.colourCode = random.choice(list(cometColours.values()))
        self.colourName = self.removeColour()
        self.forceScaleMult, self.forceScaleAdd = computeMassToSizeFunction(50, 15, 25, 4, 12)
        #overwrite force exponent for comets
        self.forceExp = 13
    #removes colour from dict as now in use and adds to used colours dict
    def removeColour(self):
        #get key value for random colour and delete the valuekey pair from dictionary as it is in use
        for colourName, colourCode in cometColours.items():
            if colourCode == self.colourCode:
                del cometColours[colourName]
                return colourName
    #method to detect if body has collided with another body
    def detectCollision(self, list):
        for body in list:
            if body.name == self.name: #check if other is self (all bodies wil have unique names)
                pass
            else:
                distance = math.sqrt((self.xOrd-body.xOrd) ** 2 + (self.yOrd-body.yOrd) ** 2)
                if distance <= self.bodyRadius + body.bodyRadius:
                #remove body from list if it is not a star or planet, so no longer output on screen
                    if body.type != "star" and body.type != "planet":
                        body.removeBody(list)
                    self.removeBody(list)
                    return body, True
        return None,False
    #removes body and adds colour back to available colours dict
    def removeBody(self, list):
        list.remove(self)
        cometColours[self.colourName] = self.colourCode
    #output trail on screen by filling previous pixels
    def showTrail(self, screen):
        if len(self.previousCoOrds)>=2:
            pygame.draw.lines(screen,self.colourCode, False, self.previousCoOrds[-50:], 2 )
                
#dict of greys for moon
moonColours = {"Grey": (173, 173, 173), "Light Grey": (217, 217, 217), "Dark Grey": (112, 112, 112), "Silver": (238, 232, 205)}
#moon inherits from comet as they basically do the same thing but around different bodies and the size should be similiar.
class moon(comet):
    def __init__(self, inputName, inputMass, inputRadius, inputVelocity, centralBody):
        super(moon, self).__init__(inputName, inputMass, inputRadius, inputVelocity)
        self.type = "moon" 
        self.centralBody = centralBody
        #use function to get gradient and intercept
        self.massMultiplier, self. massAdder = computeMassToSizeFunction(15, 10, 0.2, 0.01, 24)
        #get body radius in pixels using function
        self.bodyRadius = (inputMass * self.massMultiplier) + self.massAdder
        #overwrite x and y ord to be relative to chosen planet rather than star and scale up so can be seen
        self.xOrd = centralBody.xOrd - self.screenRadius*80
        self.yOrd = centralBody.yOrd
        #make moon rotate opposite direction to planet
        self.velY = -self.velY*math.sqrt(80)
        self.colourCode = random.choice(list(moonColours.values()))
        self.colourName = self.removeColour()
        self.velScaleMult, self.velScaleAdd = computeMassToSizeFunction(40, 15, 5, 1, 3)
     #removes colour from dict as now in use and adds to used colours dict
    def removeColour(self):
        #get key value for random colour and delete the valuekey pair from dictionary as it is in use
        for colourName, colourCode in moonColours.items():
            if colourCode == self.colourCode:
                del moonColours[colourName]
                return colourName
    #methdo which updates position of moon with each iteration
    def updatePosition(self):
        xOrd = self.xOrd
        yOrd = self.yOrd
        other = self.centralBody
        otherXOrd = other.xOrd
        otherYOrd = other.yOrd
        mass = self.mass
        otherMass = other.mass
        #get the difference in y and x of the two bodies in m.
        changeInY = ((yOrd - otherYOrd)/ simScale)*1000
        changeInX = ((otherXOrd-xOrd) /simScale)*1000
        #calculate r in m
        r = math.sqrt(changeInX**2 + changeInY**2)
        #Get angle using arctan
        angle = math.atan2(changeInY,changeInX)
        #Calculate force using F= GMm/r^2
        force = (G * mass * otherMass*6400)/r**2
        #Get force components:
        forceX = force * math.cos(angle)
        forceY = force * math.sin(angle)
        #get force for vector
        self.force = math.sqrt(forceX**2 + forceY**2)
        #Use F = ma for calculating acceleration in m/s^2
        accX = forceX/mass
        accY = forceY/mass
        #Use v= u+at to calculate new velocity
        self.velX += accX * TIME
        self.velY += accY * TIME 
        #s=vt using t as 1 day and convert to pixel value
        # t is 1 Earth day, so each step moves the planet the distance it would move in 1 day 
        distanceMovedX = (self.velX*TIME /1000)*simScale*math.sqrt(80)
        distanceMovedY = (self.velY*TIME /1000)*simScale*math.sqrt(80)
        #update scaled up x ordinate
        self.xOrd += distanceMovedX
        #update scaled up y ordinate
        self.yOrd -= distanceMovedY
    #remove body and add colour back to dict
    def removeBody(self, list):
        list.remove(self)
        moonColours[self.colourName] = self.colourCode
    #output trail on screen by filling previous pixels
    def showTrail(self, screen):
        if len(self.previousCoOrds)>=2:
            pygame.draw.lines(screen,self.colourCode, False, self.previousCoOrds, 2 )

        
##################################
### SIMULATION FUNCTIONS #########
##################################


#function which displays xplosion on the screen
def showExplosion(body1,body2, explosionImage, simScreen):
    # get middle x and y coords of two bodies
    distance = body1.bodyRadius+body2.bodyRadius
    xOrd = (body1.xOrd + (body1.bodyRadius/distance)*(body2.xOrd-body1.xOrd)) -25
    yOrd = (body1.yOrd + (body1.bodyRadius/distance)*(body2.yOrd-body1.yOrd)) - 25
    #output explosion
    simScreen.blit(explosionImage, (xOrd,yOrd))
    pygame.display.update()

#formats and sets the events loop for the simulation window
def learnSimWindow(window,frame, scenarioName, scenarioType, bgCanvas, exitFlag):
    global bodyList,currentMassUnits, currentRadiusUnits, currentVelocityUnits, currentBody, currentGraph, planetColours, moonColours,cometColours
    bodyList = []
    #instantiate indexes as planet unit indexes as this is default type
    currentMassUnits = 24
    currentRadiusUnits = 6
    currentVelocityUnits = 0
    planetCounter = 0
    cometCounter = 0
    moonCounter = 0
    currentBody = None
    currentGraph = "vel"
    #create dictionary of colours to randomly pick thorugh when adding bodies
    planetColours = {"Red":(255,0,0), "Green":(0,255,0), "Blue":(0,0,255),"Yellow": (255,255,0), "Brown": (139, 115, 85), "Aqua": (127, 255, 212),"Violet": (138, 43, 226),"Dark Green": (0, 100, 0), "Coral": (139, 62, 47)}
    moonColours = {"Grey": (173, 173, 173), "Light Grey": (217, 217, 217), "Dark Grey": (112, 112, 112), "Silver": (238, 232, 205)}
    cometColours = {"Lime green": (173, 255, 47),"Aqua": (0, 255, 255),"Pink": (255, 20, 147), "Orange": (139, 69, 0)}

    #delete frame
    frame.destroy()

    #Getting height of screen
    monitor_info = GetMonitorInfo(MonitorFromPoint((0,0)))
    work_area = monitor_info.get("Work")
    workHeight = work_area[3]
    titleBarHeight = getTitleBarHeight() 
    screenHeight =  workHeight-titleBarHeight
    #using bar screenshot in canvas.
    global sideBarWidth
    sideBarWidth = math.ceil(window.winfo_screenwidth()*29/120)
    sideBar = tk.Canvas(bgCanvas, highlightthickness=0, width = sideBarWidth, height = screenHeight)
    barBg = (Image.open("Images/sideBar.png"))
    resized_barBg= ImageTk.PhotoImage(barBg.resize((sideBarWidth,screenHeight)), master = window)
    sideBar.create_image(0,0, image = resized_barBg, anchor= "nw")
    sideBar.grid(row = 0, rowspan = 15, column = 1)

    ####################################
    #       FORMATTING SIDEBAR         #
    ####################################

    #function that: adds label, store x,y coords, delete widgets, optional parameters for different size text
    def labelXY(col, ro, side, inputText = "Add Body: ", size = 15):
        newLabel = tk.Label(bgCanvas, text = inputText, font = ("Microsoft YaHei UI Light",size,"bold"))
        newLabel.grid(column = col, row = ro, sticky = side, padx = (1/12)*sideBarWidth)
        window.update()
        labelX, labelY =newLabel.winfo_rootx(),newLabel.winfo_rooty()
        newLabel.destroy()    
        #return x and y coordinates of label to be added using canvas instead of grid
        return (labelX, labelY)
            
    #y value and height for rectangle in side bar
    barHeight = math.ceil(0.90 * (window.winfo_screenheight()))
    #pixels below rectangle in side bar
    embedY = math.ceil((84*screenHeight)/1001)
    #create tkinter frame for the pygame window to be embedded in
    embed = tk.Frame(bgCanvas,  width = window.winfo_screenwidth()-sideBarWidth, height = screenHeight-embedY) #creates embed frame for pygame window
    embed.grid(row = 1, column = 0, rowspan = 14)

    #filler frame to  take up space in row above py game frame.
    fillerFrame = tk.Frame(bgCanvas, height = embedY)
    fillerFrame.grid(column = 0,row = 0)
    #add savae button to filler frame
    title = tk.Label(fillerFrame, text = scenarioName, bg = "black", fg = "yellow", font = ("Microsoft YaHei UI Light",18,"bold"))
    title.pack()


    #button command for when pause is clicked.
    def pauseClick(button, pauseImage, playImage, runSim):
        #change pause button to play and change command
        bgCanvas.itemconfigure(button, image = playImage)
        bgCanvas.tag_bind(button, "<Button-1>", lambda e: [runSim.set(True),playClick(playButton, pauseImage, playImage, runSim)])

    #button command for when play is clicked.
    def playClick(button, pauseImage, playImage, runSim):
        #change play button to pause and change command
        bgCanvas.itemconfigure(button, image = pauseImage)
        bgCanvas.tag_bind(button, "<Button-1>", lambda e: [runSim.set(False),pauseClick(playButton, pauseImage, playImage, runSim)])

    #boolean var to check if simulation should be ran.
    runSim = tk.BooleanVar()
    runSim.set(False)
    #add play button 
    pauseImage = ImageTk.PhotoImage(Image.open("Images/pauseImage.png").resize((embedY,embedY)), master = window)
    playImage = ImageTk.PhotoImage(Image.open("Images/playImage.png").resize((embedY,embedY)), master = window)
    playButton = bgCanvas.create_image(window.winfo_screenwidth()-sideBarWidth- embedY,0,image=playImage, anchor = "nw")
    #bind image to a button command
    bgCanvas.tag_bind(playButton, "<Button-1>", lambda e: [runSim.set(True),playClick(playButton, pauseImage, playImage,runSim)]) 

    #embed pygame into tkinter frame
    os.environ['SDL_WINDOWID'] = str(embed.winfo_id())
    if pl.system == "Windows":
        os.environ['SDL_VIDEODRIVER'] = 'windib'
    window.update_idletasks()

    ######################################
    #   SIMULATION FRAME USING PYGAME    #
    ######################################

    simScreen = pygame.display.set_mode((0,0))
    #pygame bg
    simBgImage = pygame.image.load('Images/simBg.png')
    simBgImage = pygame.transform.scale(simBgImage,(window.winfo_screenwidth()-sideBarWidth, screenHeight-embedY))
    simScreen.fill(pygame.Color(0,0,0))
    simScreen.blit(simBgImage, (0, 0))
    pygame.display.flip()
    #store image in variable and conserve transparency using conver_alpha
    explosionImage = pygame.image.load('Images/explosionImage.png').convert_alpha()
    explosionImage = pygame.transform.scale(explosionImage,(50,50))

    global simWidth, simHeight, simScale
    simWidth, simHeight = pygame.display.get_surface().get_size()
    #7/8 ths of the frame height corresponds to the maximum orbital radius available x 2.
    #multiply by sim scale to convert to pixel value
    simScale = (7/8 *simHeight)/(400*10**6)
    

                                   
    #prompt user to select a body
    topLabelXY = labelXY(1, 0, "w")
    clearList = []
    #get coordinates here so don't need to do it every time the side bar is refreshed
    infoBoxXY = labelXY(1,1, "w")
    #get information file path/name from db
    scenarioInfoFile = scenarioType + "ScenarioInfo/" + cur.execute('''SELECT information FROM learnModeScenarios WHERE scenarioName = "''' + scenarioName + '''"''').fetchone()[0]
    
    #clear the top of teh side bar by iterating thorugh items in remove list
    def clearTopSidebar():
        #get all canvas items in sidebar
        for item in clearList:
            #check if item is part of canvas or a widget
            if item in sideBar.find_all():
                sideBar.delete(item)
            else:
                item.destroy()
        clearList.clear()
  
    #function for when a body has been selected
    def fillTopSidebar():
        clearTopSidebar()
        #add title to show current body
        title = currentBody.name
        currentBodyTitle = sideBar.create_text(topLabelXY[0] - (window.winfo_screenwidth() -sideBarWidth), topLabelXY[1], text = title, fill= "Yellow", anchor = "nw", font = ("Microsoft YaHei UI Light",30,"bold"))
        #add the information text box
        infoBox = tk.Text(bgCanvas, font=("Microsoft YaHei UI Light",15,"bold"), bg = "#222222", fg= "yellow", insertbackground="Yellow", wrap = "word")
        infoBox.place(x = infoBoxXY[0], y = infoBoxXY[1],height = int((8.5/10) * barHeight), width = int((10/12) * sideBarWidth))
        #get data from file
        with open(currentBody.informationFile,"r") as infoFile:
            info = infoFile.readlines()
            #add each row of information
            for row in info:
                infoBox.insert(tk.END, row)
            
        #set texbox state to disabled so user can't input information
        infoBox.config(state=tk.DISABLED)
        #add widgets to list
        clearList.append(currentBodyTitle)
        clearList.append(infoBox)

    #fill top of sidebar with initial text
    def revertTopSidebar():
        global currentBody
        currentBody = None
        clearTopSidebar()
        #reset sideBar to show information about simulation
        #add title to show current body
        title = scenarioName + " Sim"
        currentScenarioTitle = sideBar.create_text(topLabelXY[0] - (window.winfo_screenwidth() -sideBarWidth), topLabelXY[1], text = title, fill= "Yellow", anchor = "nw", font = ("Microsoft YaHei UI Light",30,"bold"))
        #add the information text box
        infoBox = tk.Text(bgCanvas, font=("Microsoft YaHei UI Light",15,"bold"), bg = "#222222", fg= "yellow", insertbackground="Yellow", wrap = "word")
        infoBox.place(x = infoBoxXY[0], y = infoBoxXY[1],height = int((8.5/10) * barHeight), width = int((10/12) * sideBarWidth))
        #get data from file
        with open(scenarioInfoFile,"r") as infoFile:
            info = infoFile.readlines()
            #add each row of information
            for row in info:
                infoBox.insert(tk.END, row)
        #set texbox state to disabled so user can't input information
        infoBox.config(state=tk.DISABLED)
        #add widgets to list
        clearList.append(currentScenarioTitle)
        clearList.append(infoBox)
    
    
    #set initial state of side bar to simulation info
    revertTopSidebar()



 
    #add bodies from scenario:
    rows = (cur.execute('''
                            SELECT 
                            learnScenarioBodyLink.bodyName,
                            learnModeBodies.velocity, 
                            learnModeBodies.mass,  
                            learnModeBodies.radius,  
                            learnModeBodies.information,
                            learnModeBodies.colour,
                            learnModeBodies.type
                            FROM learnScenarioBodyLink
                            INNER JOIN learnModeBodies ON learnModeBodies.bodyName = learnScenarioBodyLink.bodyName WHERE scenarioName = "''' + scenarioName + '''"
                            ORDER BY learnModeBodies.type DESC''')).fetchall()
    for row in rows:
        #ccreate different object depending on type
        if row[6] == "star":
            newBody = star(row[0],row[2])
        elif row[6] == "planet":
            newBody = planet(row[0], row[2], row[3], row[1]*10**-3)
            newBody.trailFlag = True
        elif row[6] == "moon":
            newBody = moon(row[0], row[2], row[3], row[1]*10**-3)
            newBody.trailFlag = True
        elif row[6] == "comet":
            newBody = comet(row[0], row[2], row[3], row[1]*10**-3)
            newBody.trailFlag = True
        #set vectors to be shown if theory mode
        if scenarioType == "Theory":
            if newBody.type != "star":
                newBody.vVectorFlag=True
                newBody.fVectorFlag = True
        #set other attributes such as image/colour
        newBody.informationFile = scenarioType + "ScenarioInfo/" + row[4]
        if scenarioType == "Existing":
            image = pygame.image.load("ExistingScenarioBodies/"+row[5]).convert_alpha()
            image = pygame.transform.scale(image,(newBody.bodyRadius*2, newBody.bodyRadius*2))
            newBody.image = image 
            #change colour to blue if earth for the trail
            if newBody.name == "Earth":
                newBody.colourCode = (0,0,255)
        else:
            #if theory mode set colour to colour from db
            newBody.colourCode = eval(row[5])
        bodyList.append(newBody)










    #event loop to update tkinter and pygame as long as exit button not pressed
    while exitFlag.get() == False:
        #the number in the after method can be used to control the speed of orbits on the screen as it controls the sleep time between each refresh
        window.after(1,pygame.display.update())
        #only update positions if play has been clicked.
        if runSim.get() == True:
            #clear pygame window to update all positions
            simScreen.blit(simBgImage, (0, 0))
            #reset collisions that need to be shown list
            collisionsToOutput = []
            #update position of all bodies
            for body in bodyList:
                #set removed flags to false
                collidedBody = None
                bodyRemoved = False
                bodyOutOfScreen = False
                #update position of body with eac iteration
                if body.type != "star" and body.type != "moon":
                    body.updatePosition()
                    #update velocity and force for graph
                    body.updatePreviousVel()
                    body.updatePreviousForces()
                elif body.type == "moon":
                    body.updatePosition()
                    #update velocity and force for graph
                    body.updatePreviousVel()
                    body.updatePreviousForces()
                #update and output trail and vector if flag is set to true
                if body.type !="star":
                    if body.trailFlag == True:
                        body.updateTrail()
                        body.showTrail(simScreen)
                    if body.fVectorFlag == True:
                        body.showFVector(simScreen)
                    if body.vVectorFlag == True:
                        body.showVVector(simScreen)
                if scenarioType == "Existing":
                    body.addImage(simScreen)
                else:
                    body.addBody(simScreen)
                #check if the body was removed
                collidedBody, bodyRemoved = body.detectCollision(bodyList)
                if body.type != "star":
                #check if the body was removed
                    bodyOutOfScreen = body.checkRemove(bodyList)
                #output explosion if collision occured:
                if collidedBody != None:
                    collisionsToOutput.append([body,collidedBody])
                #check if we need to revert sidebar 
                if currentBody !=None:
                    #if the body has been removed and was the current body, update side bar
                    if currentBody.name == body.name:
                        if bodyRemoved or bodyOutOfScreen:
                            revertTopSidebar()
                    #if the body that the body collided with, was current body and removed, revert side bar
                    elif collidedBody != None:
                        if currentBody.name == collidedBody.name and not(collidedBody in bodyList):
                            revertTopSidebar()
            #show collision outside loop
            for collision in collisionsToOutput:
                showExplosion(collision[0],collision[1], explosionImage, simScreen)
                #sleep after outputting all collision so can be seen by user
                time.sleep(0.2)

        #pause events loop
        else:
            #reset background to add all bodies
            simScreen.blit(simBgImage, (0, 0))
            #check for right click on a planet if simulation is paused
            for body in bodyList:
                #re adds all trails, vectors, 
                if body.type !="star":
                    if body.trailFlag == True:
                        body.showTrail(simScreen)
                    if body.fVectorFlag == True:
                        body.showFVector(simScreen)
                    if body.vVectorFlag == True:
                        body.showVVector(simScreen)
                #readds all bodies in case any have been removed
                if scenarioType == "Existing":
                    body.addImage(simScreen)
                else:
                    body.addBody(simScreen)
        # check if a planet has been selected
        for event in pygame.event.get():
            if event.type==pygame.MOUSEBUTTONDOWN:
                #this check that it was a left click not a right click
                if pygame.mouse.get_pressed()[0]:
                    clickX,clickY = pygame.mouse.get_pos()
                    #flag for successful click
                    clickedBody = False
                    for body in bodyList:
                        bodyRangeX, bodyRangeY = body.getClickRange()
                        #if a click has occured check if the click was on a planet or not
                        if clickX > bodyRangeX[0] and clickX< bodyRangeX[1] and clickY>bodyRangeY[0] and clickY<bodyRangeY[1]:
                            clickedBody = True
                            #don't need to update side bar if selected body is the same
                            if currentBody ==None:
                                currentBody = body
                                fillTopSidebar()
                            elif currentBody.name !=body.name:
                                currentBody = body
                                fillTopSidebar()
                    #if no body is clicked (but click occurs) , reset side bar
                    if clickedBody == False:
                        revertTopSidebar()
        try:
            window.update_idletasks()
            window.update()
        except:
            pass


