import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk
import math
from win32api import GetMonitorInfo, MonitorFromPoint
import platform as pl
import os
import pygame
import customtkinter
import random
import time
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.animation import FuncAnimation
from simFuncsTables import *


def saveScenario(scenarioName, currentUser):
    #check if name already in use
    if cur.execute("""SELECT sScenarioName FROM savedScenarios WHERE sScenarioName = '""" + scenarioName + """' AND userName = '""" + currentUser + """'""").fetchone() == None:
        #saves scenario name in savedScenaios table with name and username
        cur.execute("""INSERT INTO savedScenarios VALUES(?,?)""",(scenarioName,currentUser))
        conn.commit()
        #save all bodies in saved bodies table
        for body in bodyList:
            #don't need to add star as this is same for all experiment mode simulations
            if body.type != "star":
                cur.execute("""INSERT INTO savedBodies(type, velX, velY, ordX, ordY ,mass) VALUES(?,?,?,?,?,?)""",(body.type, body.velX,body.velY,body.xOrd, body.yOrd, body.mass))
                conn.commit()
                #get id (primary key) of body that was just added
                bodyID = cur.execute("""SELECT seq FROM sqlite_sequence WHERE name='savedBodies'""")
                bodyID = bodyID.fetchone()[0]
                #create scenario and body link in db for each body
                cur.execute("""INSERT INTO savedScenarioBodyLink VALUES(?,?,?)""",(scenarioName,currentUser,bodyID))
                conn.commit()
    else:
        messagebox.showerror("Name error ", "There is already a saved simulation with this name")

def saveScenarioPopUp(currentUser):
    #create new window and set colour
    saveScenarioWin = tk.Tk()
    saveScenarioWin.configure(bg = "black")
    saveScenarioWin.geometry("700x400")
    tk.Label(saveScenarioWin,text = "Save Scenario", bg = "black", fg = "#FBDF0F",  font = ("Microsoft YaHei UI Light",35,"bold")).grid(row = 0, column = 0, pady =20)
    #create scenario name entry
    nameEntry = tk.Entry(saveScenarioWin, bg = "black", fg = "#FBDF0F", border = 0, font = ("Microsoft YaHei UI Light",20,"bold"))
    nameEntry.configure(insertbackground="#FBDF0F")
    nameEntry.insert(0,"Scenario Name")
    nameEntry.grid(column = 0, row = 1, sticky = "SW", padx=30)
    #create underline
    tk.Frame(saveScenarioWin,width = 600, height = 2, bg = "#FBDF0F").grid(column = 0, row = 2, sticky = "N",padx=30)
    #create button with command for saving scenario
    button = tk.Button(saveScenarioWin, text = "SAVE", font = ("Microsoft YaHei UI Light",15,"bold"), bg = "#FBDF0F", fg = "black", command = lambda:[saveScenario(nameEntry.get(),currentUser), saveScenarioWin.destroy()])
    button.grid(row = 9, column = 0, sticky = "S", pady = 200)
    #create custom main loop
    closeWin = tk.BooleanVar() #set variable to true if window is closed so main loop stops
    closeWin.set(False)
    #stop loop when window is closed
    while closeWin.get():
        saveScenarioWin.update_idletasks()
        saveScenarioWin.update()
        saveScenarioWin.protocol("WM_DELETE_WINDOW",closeWin.set(True) )

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
        #2*10**30 kg is 50 pixel(radius).
        self.massToSizeFactor = 50/(2*10**30)
        self.bodyRadius = inputMass*self.massToSizeFactor
        self.mass = inputMass
        self.xOrd = 0
        self.yOrd = 0


#a star class is created which inherits the methods and attributes of the star class.
class star(body):
    def __init__(self, inputName, inputMass):
        super(star,self).__init__(inputName,inputMass)
        self.type ="star"
        self.colour = (255,88,0) #orange
        self.xOrd = simWidth/2
        self.yOrd = simHeight/2
    #method which draws star in centre of frame
    def addBody(self, screen):
        pygame.draw.circle(screen, self.colour,(self.xOrd,self.yOrd), self.bodyRadius)
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
        self.forceX = 0
        self.forceY = 0
        #use function to get gradient and intercept
        self.massMultiplier, self. massAdder = computeMassToSizeFunction(23, 15, 200, 1, 24)
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
    #return range of coordinates where the user should click to select body
    def getClickRange(self):
        xMin = self.xOrd - self.bodyRadius
        xMax = self.xOrd + self.bodyRadius
        yMin = self.yOrd - self.bodyRadius
        yMax = self.yOrd + self.bodyRadius
        return [xMin,xMax], [yMin, yMax]



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
        #get force multiple for force vector
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
    def __init__(self, inputName, inputMass, inputRadius, inputVelocity, centralBody = None):
        super(moon, self).__init__(inputName, inputMass, inputRadius, inputVelocity)
        self.type = "moon" 
        #use function to get gradient and intercept
        self.massMultiplier, self. massAdder = computeMassToSizeFunction(7, 5, 0.2, 0.01, 24)
        #get body radius in pixels using function
        self.bodyRadius = (inputMass * self.massMultiplier) + self.massAdder
        if centralBody != None: #i.e. if not in saved mode
            #overwrite x and y ord to be relative to chosen planet rather than star 
            self.xOrd = centralBody.xOrd - self.screenRadius
            self.yOrd = centralBody.yOrd
        else:
            self.xOrd = 0
            self.yOrd = 0
        #make moon rotate opposite direction to planet
        self.velY = -self.velY
        self.colourCode = random.choice(list(moonColours.values()))
        self.colourName = self.removeColour()
        self.velScaleMult, self.velScaleAdd = computeMassToSizeFunction(40, 15, 5, 1, 3)
        #get force multiple for force vector
        self.forceScaleMult, self.forceScaleAdd = computeMassToSizeFunction(20, 10, 3, 0.9, 18)
     #removes colour from dict as now in use and adds to used colours dict
    def removeColour(self):
        #get key value for random colour and delete the valuekey pair from dictionary as it is in use
        for colourName, colourCode in moonColours.items():
            if colourCode == self.colourCode:
                del moonColours[colourName]
                return colourName
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
        if other.type == "star":
            return [0,0]
        return [forceX*65**2,forceY*65**2]
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
        distanceMovedX = (self.velX*TIME /1000)*simScale*math.sqrt(65)
        distanceMovedY = (self.velY*TIME /1000)*simScale*math.sqrt(65)
        #update x ordinate
        self.xOrd += distanceMovedX
        #update y ordinate
        self.yOrd -= distanceMovedY
    #remove body and add colour back to dict
    def removeBody(self, list):
        list.remove(self)
        moonColours[self.colourName] = self.colourCode
    #output trail on screen by filling previous pixels
    def showTrail(self, screen):
        if len(self.previousCoOrds)>=2:
            pygame.draw.lines(screen,self.colourCode, False, self.previousCoOrds, 2 )
     #calculate the coordinates of the end of the force arrow in teh same way as velocity
    def computeEndOfFArrow(self):
        #calc magnitude of vector
        force = math.sqrt(self.forceX**2 + self.forceY**2)/(65**2)
        #get force  vector using velocity x and y
        deltaX = self.forceX/(65**2)
        deltaY = self.forceY/(65**2)
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

                

        


#instantiate indexes as planet unit indexes as this is default type
currentMassUnits = 24
currentRadiusUnits = 6
currentVelocityUnits = 0
#create list of body objects
bodyList = []  
planetCounter = 0
cometCounter = 0
moonCounter = 0

##################################
### SIMULATION FUNCTIONS #########
##################################

#command for the add body button which adds the body at the correct position
def addBodyToScreen(type, mass, velocity, radius, screen):
    global planetCounter
    global cometCounter
    global moonCounter
    global currentBody
    #put parameters in correct powers
    mass = mass* 10 **currentMassUnits
    radius = radius * 10 **currentRadiusUnits
    velocity = velocity * 10 **currentVelocityUnits
    #check what type the body is and add corresponding object
    if type == "Planet":
        name = "Planet" + str(planetCounter)
        newBody = planet(name, mass, radius, velocity)
        bodyList.append(newBody)
        newBody.addBody(screen)
        planetCounter = planetCounter + 1
    if type == "Comet":
        name = "Comet" + str(cometCounter)
        newBody = comet(name, mass, radius, velocity)
        bodyList.append(newBody)
        newBody.addBody(screen)
        cometCounter = cometCounter +1
    if type == "Moon":
        if currentBody in bodyList:
            if currentBody.type == "planet":
                name = "Moon" + str(moonCounter)
                newBody = moon(name, mass, radius*65, velocity*math.sqrt(65), currentBody)
                bodyList.append(newBody)
                newBody.addBody(screen)
                moonCounter = moonCounter +1
            else:
                messagebox.showerror("Moon error ", "Please pause the simulation and select a planet first")
        else:
            messagebox.showerror("Moon error ", "Please pause the simulation and select a planet first")
    
#command for remove button: removes selected body from screen  
def removeBodyFromScreen():
    global currentBody
    currentBody.removeBody(bodyList)
    currentBody = None

#depending on whetehr check box was checked or unchecked, update trail
def editTrail(trailState):
    #if it was unchecked, clear trail, set flag to false, so no longer output and reset for future
    if trailState.get() == False:
        currentBody.trailFlag = False
        currentBody.clearTrail()
    #if it was checked, set flag to true, this should cause it to be outptu in the events loop
    else:
        currentBody.trailFlag = True

def editFVector(fVectorState):
    #if it was unchecked, hide vector, set flag to false, so no longer output
    if fVectorState.get() == False:
        currentBody.fVectorFlag = False
    #if it was checked, set flag to true, this should cause it to be outptu in the events loop
    else:
        currentBody.fVectorFlag = True

def editVVector(vVectorState):
    #if it was unchecked, hide vector, set flag to false, so no longer output
    if vVectorState.get() == False:
        currentBody.vVectorFlag = False
    #if it was checked, set flag to true, this should cause it to be outptu in the events loop
    else:
        currentBody.vVectorFlag = True

plt.style.use('dark_background')
figure = plt.Figure(figsize = (1,1), dpi = 100) #so 1 inch is 100 pixels
ax = figure.add_subplot(1,1,1)
ax.set_xticks([])

#animation function called each time the graph needs to be updated
def animateGraph(i):
        global figure, ax, line, currentGraph
        #clear graph for new line
        ax.clear()
        #cahnge axis and data depending on type of graph
        if currentGraph == "vel":
            dataToUse = currentBody.previousVelocities
            ax.set_ylabel("Velocity[km/s]", fontsize = 7)
            ax.set_title("Velocity Graph", fontsize = 15)
            graphColour = "orange"
        else:
            dataToUse = currentBody.previousForces
            ax.set_ylabel("Force[x10^ " + str(currentBody.forceExp) +  "N]", fontsize = 7)
            ax.set_title("Force Graph", fontsize = 15)
            graphColour = "white"
        #if there are less thane 200 velocities recorded set the x to be the length of velocities else plot the last x velocities
        if len(dataToUse)<500:
            timeList = list(range(len(dataToUse)))
        else:   
            timeList = list(range(500))
        #data for graph
        velData = {
            "time":timeList,   #list of consecutive integres of same size as previousVelocities
            "bodyData": dataToUse[-500:],
        }
        #update graph2
        ax.plot(velData["time"], velData["bodyData"], color = graphColour)
        ax.set_xticks([])#get rid of x axis scale as time is arbitrary
        ax.set_xlabel("Time", fontsize = 7)
        ax.tick_params(axis='y', labelsize=6)
        return line,

#draws vel/force graph
def drawCurrentGraph(sideBar,sideBarWidth, xOrd, yOrd):
    global figure, ax, line, currentGraph
    #if graph was velocity siwtch it to now be force and vice versa
    if currentGraph == "vel":
        currentGraph = "force"
    else:
        currentGraph = "vel"
    figureSize = (sideBarWidth *(1/2)) /100
    figure.set_size_inches((figureSize*3/2,figureSize*9/8))
    ax.clear()
    #change axis labels and data being used depending on whther it is force or velocity graph
    if currentGraph == "vel":
        dataToUse = currentBody.previousVelocities
        ax.set_ylabel("Velocity[km/s]", fontsize = 7)
        ax.set_title("Velocity Graph", fontsize = 15)
        graphColour = "orange"
    else:
        dataToUse = currentBody.previousForces
        ax.set_ylabel("Force[x10^ " + str(currentBody.forceExp) +  "N]", fontsize = 7)
        ax.set_title("Force Graph", fontsize = 15)
        graphColour = "white"
    #if there are less thane 200 velocities recorded set the x to be the length of velocities else plot the last x velocities
    if len(dataToUse)<500:
        timeList = list(range(len(dataToUse)))
    else:   
        timeList = list(range(500))
    #data for graph
    velData = {
        "time":timeList,   #list of consecutive integres of same size as previousVelocities
        "bodyData": dataToUse[-500:],
    }
    #draw graph using pandas and matplot lib
    #get require graph size in inches
    lineGraph = FigureCanvasTkAgg(figure,sideBar)
    #convert to tk widget and place on screen
    lineGraph.get_tk_widget().place(x=xOrd-15, y=yOrd)
    #plot data
    line, = ax.plot(velData["time"], velData["bodyData"], color = graphColour)
    ax.set_xlabel("Time", fontsize = 7)
    ax.set_xticks([]) #get rid of x axis scale as time is arbitrary
    ax.tick_params(axis='y', labelsize=6) #make y axis sxale smaller so label can be seen
    #return tkinter graph widget
    return lineGraph.get_tk_widget()

    #function which displays xplosion on the screen
def showExplosion(body1,body2, explosionImage, simScreen):
    # get middle x and y coords of two bodies
    distance = body1.bodyRadius+body2.bodyRadius
    xOrd = (body1.xOrd + (body1.bodyRadius/distance)*(body2.xOrd-body1.xOrd)) -25
    yOrd = (body1.yOrd + (body1.bodyRadius/distance)*(body2.yOrd-body1.yOrd)) - 25
    #output explosion
    simScreen.blit(explosionImage, (xOrd,yOrd))
    pygame.display.update()



#formats and sets the events loop for teh simulation window for experiment adn saved mode
def experimentSimWindow(window,frame,mode,bgCanvas, exitFlag, currentUser, scenarioName):
    #reset global vars
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
    #reset dictionary of colours to randomly pick thorugh when adding bodies
    planetColours = {"Red":(255,0,0), "Green":(0,255,0), "Blue":(0,0,255),"Yellow": (255,255,0), "Brown": (139, 115, 85), "Aqua": (127, 255, 212),"Violet": (138, 43, 226),"Dark Green": (0, 100, 0), "Coral": (139, 62, 47)}
    moonColours = {"Grey": (173, 173, 173), "Light Grey": (217, 217, 217), "Dark Grey": (112, 112, 112), "Silver": (238, 232, 205)}
    cometColours = {"Lime green": (173, 255, 47),"Aqua": (0, 255, 255),"Pink": (255, 20, 147), "Orange": (139, 69, 0)}


    #delete frame
    frame.destroy()

    #if mode is experiment then add exit button:
    if mode == "Experiment":
        from PreSimWindows import homePageWindow
        #add exit image to canvas
        exitImage = ImageTk.PhotoImage(Image.open("Images/exit.png").resize((80,80)), master = window)
        exitButton = bgCanvas.create_image(40, 40,image=exitImage)
        #bind image to a button command
        bgCanvas.tag_bind(exitButton, "<Button-1>", lambda e: [exitFlag.set(True), pygame.display.quit(),bgCanvas.delete(exitButton), homePageWindow(window,frame,bgCanvas,currentUser)]) 


    barHeight = math.ceil(0.90 * (window.winfo_screenheight())) #hieght of bar
    #Getting height of screen
    monitor_info = GetMonitorInfo(MonitorFromPoint((0,0)))
    work_area = monitor_info.get("Work")
    workHeight = work_area[3]
    titleBarHeight = getTitleBarHeight() 
    screenHeight =  workHeight-titleBarHeight
    #using bar screenhsot in canvas.
    global sideBarWidth
    sideBarWidth = math.ceil(window.winfo_screenwidth()*29/120)
    sideBar = tk.Canvas(bgCanvas, highlightthickness=0, width = sideBarWidth, height = screenHeight)
    barBg = (Image.open("Images/sideBar.png"))
    resized_barBg= ImageTk.PhotoImage(barBg.resize((sideBarWidth,screenHeight)), master = window)
    sideBar.create_image(0,0, image = resized_barBg, anchor= "nw")
    sideBar.grid(row = 0, rowspan = 15, column = 1)

    ####################################
    #       FORMATTING SIDEBAR         #
    #####################################

    #function that: adds label, store x,y coords, delete widgets, optiona;l parameters for different size text
    def labelXY(col, ro, side, inputText = "Add Body: ", size = 15):
        newLabel = tk.Label(bgCanvas, text = inputText, font = ("Microsoft YaHei UI Light",size,"bold"))
        newLabel.grid(column = col, row = ro, sticky = side, padx = (1/12)*sideBarWidth)
        window.update()
        labelX, labelY =newLabel.winfo_rootx(),newLabel.winfo_rooty()
        newLabel.destroy()    
        #return x and y coordinates of label to be added using canvas instead of grid
        return (labelX, labelY)
    
    #add sliders/buttons/dropdowns

    bodyType = tk.StringVar(window)
    bodyType.set("None") 
    
    massUnits = tk.StringVar(window)
    massUnits.set("x10\u00b2\u2074 kg")
    radiusUnits = tk.StringVar(window)
    radiusUnits.set("x10\u2076 km")
    velocityUnits = tk.StringVar(window)
    velocityUnits.set("km/s")

    #command for changing dropdown body type
    #need to accordingly update slider ranges and units
    def changeType(value):
        global currentMassUnits
        global currentRadiusUnits
        global currentVelocityUnits
        if value == "Planet":
            massSliderRange = [1, 200]
            massSliderSteps = (massSliderRange[1]-massSliderRange[0])/1
            massUnits.set("x10\u00b2\u2074 kg")
            currentMassUnits = 24
            radiusSliderRange = [50,200]
            radiusSliderSteps = (radiusSliderRange[1]-radiusSliderRange[0])/10
            radiusUnits.set("x10\u2076 km")
            currentRadiusUnits = 6
            velocitySliderRange = [5,50]
            velocitySliderSteps = (velocitySliderRange[1]-velocitySliderRange[0])/1
            velocityUnits.set(" km/s")
            currentVelocityUnits = 0
        elif value == "Moon":
            massSliderRange = [0.01,0.20]
            massSliderSteps = (massSliderRange[1]-massSliderRange[0])/0.01
            massUnits.set("x10\u00b2\u2074 kg")
            currentMassUnits = 24
            radiusSliderRange = [0.20,0.50]
            radiusSliderSteps = (radiusSliderRange[1]-radiusSliderRange[0])/0.01
            radiusUnits.set("x10\u2076 km")
            currentRadiusUnits = 6
            velocitySliderRange = [1,5]
            velocitySliderSteps = (velocitySliderRange[1]-velocitySliderRange[0])/0.25
            velocityUnits.set(" km/s")
            currentVelocityUnits = 0
        else:
            massSliderRange = [1,50]
            massSliderSteps = (massSliderRange[1]-massSliderRange[0])/(1)
            massUnits.set("x10\u00b9\u00b3 kg")
            currentMassUnits = 13
            radiusSliderRange = [7.0,12.0]
            radiusSliderSteps = (radiusSliderRange[1]-radiusSliderRange[0])/0.25
            radiusUnits.set("x10\u2077 km")
            currentRadiusUnits = 7
            velocitySliderRange = [5,30]
            velocitySliderSteps = (velocitySliderRange[1]-velocitySliderRange[0])/0.25
            velocityUnits.set(" km/s")
            currentVelocityUnits = 0
        massSlider.configure(from_ = massSliderRange[0], to = massSliderRange[1], number_of_steps=massSliderSteps)
        massSlider.set(massSliderRange[0])
        massValue.configure(text = str(massSliderRange[0]) + str(massUnits.get()))
        radiusSlider.configure(from_ = radiusSliderRange[0], to = radiusSliderRange[1], number_of_steps=radiusSliderSteps)
        radiusSlider.set(radiusSliderRange[0])
        radiusValue.configure(text = str(radiusSliderRange[0]) + str(radiusUnits.get()))
        velocitySlider.configure(from_ = velocitySliderRange[0], to = velocitySliderRange[1], number_of_steps=velocitySliderSteps)
        velocitySlider.set(velocitySliderRange[0])
        velocityValue.configure(text = str(velocitySliderRange[0]) + str(velocityUnits.get()))

    
    #add drop down
    #create tkinter variable to store value of dropdown
    bodyTypes = ["Planet", "Moon", "Comet"]
    typeDropdown = customtkinter.CTkOptionMenu(bgCanvas, values = bodyTypes, variable = bodyType, bg_color = "black", fg_color="#2b2b2b", text_color="yellow", button_color="#595959", dropdown_text_color="yellow", button_hover_color="#919191", command = changeType)
    typeDropdown.grid(column = 1, row = 10,  sticky = "e", padx = (1/12) * sideBarWidth)
    typeDropdown.set("Planet")

    #masslider

    #slider function for outputing value of mass slider
    def slidingMass(value):
        value = str(value)
        #fix length issue with moon masses
        if len(value)>6:
            value = value[0:4]
        massValue.configure(text = value + str(massUnits.get()))

    #add mass slider using custom tkinter and initialise to 1
    sliderLength = sideBarWidth*(8/12) - 50
    massSlider= customtkinter.CTkSlider(bgCanvas,from_ = 1 , to = 200, number_of_steps=199, command = slidingMass, width=sliderLength, bg_color = "black", button_color = "yellow", button_hover_color="#EFFD5F")
    massSlider.grid(column = 1, row = 11,  sticky = "e", padx = (1/12) * sideBarWidth)
    massSlider.set(1)
    #add mass slider label 
    massValue = customtkinter.CTkLabel(bgCanvas, text = str(massSlider.get()) + str(massUnits.get()), fg_color = ("black", "black"), width = 100, text_color = "yellow")
    massValue.grid(column = 1, row = 11, sticky = "se", padx = ((1/12) * sideBarWidth) + sliderLength/3)

    #radius slider
    
    #slider function for outputting value of radius slider
    def slidingRadius(value):
        value = str(value)
        #fix length issue with moon radii
        if len(value)>6:
            value = value[0:4]
        radiusValue.configure(text = str(value) + str(radiusUnits.get()))

    #add radius slider using custom tkinter 
    radiusSlider= customtkinter.CTkSlider(bgCanvas,from_ = 50, to = 200,number_of_steps=150, command = slidingRadius, width=sliderLength, bg_color = "black", button_color = "yellow", button_hover_color="#EFFD5F")
    radiusSlider.grid(column = 1, row = 12,  sticky = "e", padx = (1/12) * sideBarWidth)
    radiusSlider.set(50)
    #add radius slider label 
    radiusValue = customtkinter.CTkLabel(bgCanvas, text = str(radiusSlider.get()) + str(radiusUnits.get()), fg_color = ("black", "black"), width = 100, text_color = "yellow")
    radiusValue.grid(column = 1, row = 12, sticky = "SE", padx = (1/12) * sideBarWidth + sliderLength/3)

    #slider function for outputting value of radius slider
    def slidingVelocity(value):
        velocityValue.configure(text = str(value) + str(velocityUnits.get()))

    #add velocity slider using custom tkinter 
    velocitySlider= customtkinter.CTkSlider(bgCanvas,from_ = 5, to = 50, number_of_steps=45, command = slidingVelocity, width=sliderLength, bg_color = "black", button_color = "yellow", button_hover_color="#EFFD5F")
    velocitySlider.grid(column = 1, row = 13,  sticky = "e", padx = (1/12) * sideBarWidth)
    velocitySlider.set(5)
    #add velocity slider label 
    velocityValue = customtkinter.CTkLabel(bgCanvas, text = str(velocitySlider.get())  + str(velocityUnits.get()), fg_color = ("black", "black"), width = 100, text_color = "yellow")
    velocityValue.grid(column = 1, row = 13, sticky = "SE", padx = (1/12) * sideBarWidth + sliderLength/3)

    #add labels for sliders/dropdowns/buttons using above function
    addLabelXY = labelXY(1, 9, "w")
    sideBar.create_text(addLabelXY[0], addLabelXY[1], text = "Add Body: ", fill= "Yellow", anchor = "w", font = ("Microsoft YaHei UI Light",17,"bold"))
    typeLabelXY = labelXY(1,10, "w")
    sideBar.create_text(typeLabelXY[0], typeLabelXY[1], text = "Type ", fill= "Yellow", anchor = "w", font = ("Microsoft YaHei UI Light",12))
    massLabelXY = labelXY(1,11, "w")
    sideBar.create_text(massLabelXY[0], massLabelXY[1], text = "Mass", fill= "Yellow", anchor = "w", font = ("Microsoft YaHei UI Light",12))
    orbitRadiusLabelXY = labelXY(1,12, "w")
    sideBar.create_text(orbitRadiusLabelXY[0], orbitRadiusLabelXY[1], text = "Orbital Radius", fill= "Yellow", anchor = "w", font = ("Microsoft YaHei UI Light",12))
    velocityLabelXY = labelXY(1,13, "w")
    sideBar.create_text(velocityLabelXY[0], velocityLabelXY[1], text = "Velocity", fill= "Yellow", anchor = "w", font = ("Microsoft YaHei UI Light",12))
    
    #y value and height for rectangle in side bar
    barY = math.ceil((window.winfo_screenheight()-barHeight)/5)
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
    saveButton = tk.Button(fillerFrame, text = "SAVE", bg = "black", fg = "yellow", font = ("Microsoft YaHei UI Light",18,"bold"), command = lambda:[saveScenarioPopUp(currentUser)])
    saveButton.pack()


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

    #button to add bodies
    addButton = tk.Button(bgCanvas, text = "ADD", bg = "green", font = ("Microsoft YaHei UI Light",12,"bold"), command = lambda: addBodyToScreen(typeDropdown.get(), massSlider.get(), velocitySlider.get(), radiusSlider.get(), simScreen))
    addButton.grid(column = 1, row = 9,  sticky = "e", padx = (1/12) * sideBarWidth)

    #prompt user to select a body
    topLabelXY = labelXY(1, 0, "w")
    clearedTitle = sideBar.create_text(topLabelXY[0] - (window.winfo_screenwidth() -sideBarWidth), topLabelXY[1], text = "Pause the sim and select a body to see information...", fill= "Yellow", anchor = "w", font = ("Microsoft YaHei UI Light",11,"bold"))
    clearList = [clearedTitle]
    #get coordinates here so don't need to do it every time the side bar is refreshed
    trailButtonXY = labelXY(1,1,"ne", "ABCD")
    trailLabelXY = labelXY(1,1, "w")
    fVectorLabelXY = labelXY(1,2, "w")
    fVectorButtonXY = labelXY(1,2,"ne", "ABCD")
    vVectorLabelXY = labelXY(1,3, "w")
    vVectorButtonXY = labelXY(1,3,"ne", "ABCD")
    removeButtonXY = labelXY(1,8,"e","REMOVE", 12)
    velGraphXY = labelXY(1,4,"w")
    switchGraphXY = labelXY(1,5, "e", "SWITCH")
   

    #clear the top of teh side bar by iterating thorugh items in remove list
    def clearTopSidebar():
        #get all canvas items in sidebar
        for item in clearList:
            #check if item is part of canvas or widget
            if item in sideBar.find_all():
                sideBar.delete(item)
            else:
                item.destroy()
        clearList.clear()
  
    #function for when a body has been selected
    def fillTopSidebar():
        clearTopSidebar()
        #add title to show current body
        title = currentBody.colourName + " " + currentBody.type
        currentBodyTitle = sideBar.create_text(topLabelXY[0] - (window.winfo_screenwidth() -sideBarWidth), topLabelXY[1], text = title, fill= "Yellow", anchor = "w", font = ("Microsoft YaHei UI Light",20,"bold"))
        #button and label to toggle trail
        trailBoxState = customtkinter.BooleanVar(value = currentBody.trailFlag)
        trailLabel = sideBar.create_text(trailLabelXY[0] - (window.winfo_screenwidth() -sideBarWidth), trailLabelXY[1], text = "Show trail", fill= "Yellow", anchor = "w", font = ("Microsoft YaHei UI Light",18,"bold"))
        trailButton = customtkinter.CTkCheckBox(bgCanvas,variable = trailBoxState, onvalue = True, text = None, offvalue=False, bg_color="black", fg_color = "black", checkbox_height=50, checkbox_width=50, checkmark_color="yellow", width = 50, height = 50, border_color="yellow", hover_color="#3b3b3b", command = lambda: [editTrail(trailBoxState)] )
        trailButton.place(x = trailButtonXY[0], y = trailButtonXY[1])
        #button and label to toggle fvector
        fVectorBoxState = customtkinter.BooleanVar(value = currentBody.fVectorFlag)
        fVectorLabel = sideBar.create_text(fVectorLabelXY[0] - (window.winfo_screenwidth() -sideBarWidth), fVectorLabelXY[1], text = "Show Force Vector", fill= "White", anchor = "w", font = ("Microsoft YaHei UI Light",18,"bold"))
        fVectorButton = customtkinter.CTkCheckBox(bgCanvas,variable = fVectorBoxState, onvalue = True, text = None, offvalue=False, bg_color="black", fg_color = "black", checkbox_height=50, checkbox_width=50, checkmark_color="white", width = 50, height = 50, border_color="white", hover_color="#3b3b3b", command = lambda: [editFVector(fVectorBoxState)] )
        fVectorButton.place(x = fVectorButtonXY[0], y = fVectorButtonXY[1])
        #button and label to toggle vel vector
        vVectorBoxState = customtkinter.BooleanVar(value = currentBody.vVectorFlag)
        vVectorLabel = sideBar.create_text(vVectorLabelXY[0] - (window.winfo_screenwidth() -sideBarWidth), vVectorLabelXY[1], text = "Show Velocity Vector", fill= "Orange", anchor = "w", font = ("Microsoft YaHei UI Light",18,"bold"))
        vVectorButton = customtkinter.CTkCheckBox(bgCanvas,variable = vVectorBoxState, onvalue = True, text = None, offvalue=False, bg_color="black", fg_color = "black", checkbox_height=50, checkbox_width=50, checkmark_color="orange", width = 50, height = 50, border_color="orange", hover_color="#3b3b3b", command = lambda: [editVVector(vVectorBoxState)] )
        vVectorButton.place(x = vVectorButtonXY[0], y = vVectorButtonXY[1])
        #button to remove bodies
        removeButton = tk.Button(bgCanvas, text = "REMOVE", bg = "red", font = ("Microsoft YaHei UI Light",12,"bold"), command = lambda:[removeBodyFromScreen(), revertTopSidebar()])
        removeButton.place(x = removeButtonXY[0], y = removeButtonXY[1])
        #display vel graph
        velGraph = drawCurrentGraph(sideBar, sideBarWidth, velGraphXY[0]- (window.winfo_screenwidth() -sideBarWidth), velGraphXY[1])
        switchGraphButton = tk.Button(bgCanvas, fg = "yellow",text = "SWITCH", bg = "black", font = ("Microsoft YaHei UI Light",12,"bold"), command = lambda:[clearList.append(drawCurrentGraph(sideBar, sideBarWidth, velGraphXY[0]- (window.winfo_screenwidth() -sideBarWidth), velGraphXY[1]))])
        switchGraphButton.place(x = switchGraphXY[0], y = switchGraphXY[1])
        #add widgets to clear list incase the side bar needs to be reset
        clearList.append(currentBodyTitle)
        clearList.append(removeButton)
        clearList.append(trailLabel)
        clearList.append(trailButton)
        clearList.append(fVectorLabel)
        clearList.append(fVectorButton)
        clearList.append(vVectorLabel)
        clearList.append(vVectorButton)
        clearList.append(velGraph)
        clearList.append(switchGraphButton)

    #fill top of sidebar with initial text
    def revertTopSidebar():
        global currentBody
        currentBody = None
        clearTopSidebar()
        #reset sideBar
        revertTitle = sideBar.create_text(topLabelXY[0] -  (window.winfo_screenwidth() -sideBarWidth), topLabelXY[1], text = "Pause the sim and select a body to see information...", fill= "Yellow", anchor = "w", font = ("Microsoft YaHei UI Light",11,"bold"))
        clearList.append(revertTitle)
        

    sun = star("sun",2*10 **30 )
    bodyList.append(sun)
    sun.addBody(simScreen)

 
    #add bodies if mode is saved
    if mode == "Saved":
        rows = (cur.execute('''
                            SELECT 
                            savedBodies.velX, 
                            savedBodies.velY, 
                            savedBodies.mass,  
                            savedBodies.ordX,  
                            savedBodies.ordY,  
                            savedBodies.type
                            FROM savedBodies
                            INNER JOIN savedScenarioBodyLink ON savedBodies.bodyID = savedScenarioBodyLink.bodyID WHERE sScenarioName = "''' + scenarioName + '''" AND userName = "''' + currentUser + '''"
                            ORDER BY savedBodies.type DESC''')).fetchall()
        #for each body fetched from db add body to body list
        for row in rows:
            #create different object depending on type
            if row[5] == "planet":
                name = "Planet " +  str(planetCounter)
                planetCounter+=1
                newBody = planet(name, row[2], 0, 0)
            elif row[5] == "moon":
                name = "Moon " +  str(moonCounter)
                moonCounter+=1
                newBody = moon(name, row[2], 0, 0)
            elif row[5] == "comet":
                name = "Comet " +  str(cometCounter)
                cometCounter+=1
                newBody = comet(name, row[2], 0, 0)
            #set velocities and coordinates 
            newBody.velX = row[0]
            newBody.velY = row[1]
            newBody.xOrd = row[3]
            newBody.yOrd = row[4]
            bodyList.append(newBody)





    #event loop to update tkinter and pygame as long as exit not pressed
    while exitFlag.get() == False:
        #the number in the after method can be used to control the speed of orbits on the screen as it controls the sleep time between each refresh
        window.after(1,pygame.display.update())
        #only update positions if play has been clicked.
        if runSim.get() == True:
            #clear pygame window to update all positions
            simScreen.blit(simBgImage, (0, 0))
            #reset collisions that need to be shown list
            collisionsToOutput = []
            #if there is a selected body, update its graph
            if currentBody !=None:
                FuncAnimation(figure, animateGraph, interval = 1, blit = True, frames = 1)
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
                #update and output trail and vector if flag is set to true
                if body.type !="star":
                    if body.trailFlag == True:
                        body.updateTrail()
                        body.showTrail(simScreen)
                    if body.fVectorFlag == True:
                        body.showFVector(simScreen)
                    if body.vVectorFlag == True:
                        body.showVVector(simScreen)
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
                #readds all bodies in case any have been removed
                body.addBody(simScreen)
                #re adds all trails, vectors, 
                if body.type !="star":
                    if body.trailFlag == True:
                        body.showTrail(simScreen)
                    if body.fVectorFlag == True:
                        body.showFVector(simScreen)
                    if body.vVectorFlag == True:
                        body.showVVector(simScreen)
                # check if a planet has been selected
                for event in pygame.event.get():
                    if event.type==pygame.MOUSEBUTTONDOWN:
                        #this check that it was a left click not a right click
                        if pygame.mouse.get_pressed()[0]:
                            clickX,clickY = pygame.mouse.get_pos()
                            #flag for successful click
                            clickedBody = False
                            for body in bodyList:
                                if body.type != "star":
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
    

