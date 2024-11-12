import tkinter as tk
from PIL import Image, ImageTk
import tkinter as tk
from CreateLearnModeTables import *
import customtkinter
from LearnModeSim import *
from ExperimentModeSim import *
import pygame


#define how many columns I want to use in formatting scenarios
COLUMNS = 4

def restartProgram():
    #this shoudl restart the program, import within function to avoid circular import
    from SignUpLogin import main
    main()

def profileWindow(bgCanvas,currentUser, profileButton,profileImage, masterWindow):
    #dim profile image replace old one and disable button
    dimProfileImage = ImageTk.PhotoImage(Image.open("Images/profile_dim.png").resize((80,80)), master = masterWindow)
    bgCanvas.itemconfigure(profileButton, image = dimProfileImage, state = "disabled")
    profileWindow = tk.Tk()
    width = 700 # Width 
    height = 1000 # Height
    screenWidth = profileWindow.winfo_screenwidth()  # Width of the screen
    screenHeight = profileWindow.winfo_screenheight() # Height of the screen
    # Calculate Starting X and Y coordinates for Window
    x = (screenWidth/2) - (width/2)
    y = (screenHeight/2) - (height/2)
    profileWindow.geometry('%dx%d+%d+%d' % (width, height, x, y))
    profileWindow.configure(bg = "black")
    #add username heading
    heading = tk.Label(profileWindow, text = currentUser, font = ("Microsoft YaHei UI Light",40,"bold"), fg = "#FBDF0F", bg = "black" )
    heading.pack()
    #add line for organisation
    tk.Frame(profileWindow, width = width-10, height = 2, bg = "#FBDF0F").pack(pady = 20)
    #add existing label
    existingLabel = tk.Label(profileWindow, text = "Completed Existing Scenarios:", font = ("Microsoft YaHei UI Light",25,"bold"), fg = "#FBDF0F", bg = "black" )
    existingLabel.pack(anchor = "w")
    #get completed scenarios from database that are of type existing
    completedExisting = (cur.execute('''SELECT completedScenarios.scenarioName FROM completedScenarios 
                            INNER JOIN learnModeScenarios ON completedScenarios.scenarioName = learnModeScenarios.scenarioName
                            WHERE completedScenarios.userName = "''' + currentUser +'''" AND learnModeScenarios.mode = "''' + "Existing" + '''"''')).fetchall()
    #limit number of scenarios displayed due to space
    if len(completedExisting) > 3:
        completedExisting = completedExisting[0:3]
        completedExisting.append(("...",))
    for row in completedExisting:
        tk.Label(profileWindow,text = "-" + row[0],font = ("Microsoft YaHei UI Light",20,"bold"), fg = "#FBDF0F", bg = "black").pack(anchor = "w")
    #if no rows are returned tell user there are no scenarios of this type
    if len(completedExisting) == 0:
        tk.Label(profileWindow,text = "-No completed existing scenarios...",font = ("Microsoft YaHei UI Light",20,"bold"), fg = "#FBDF0F", bg = "black").pack(anchor = "w")
    #add line for organisation
    tk.Frame(profileWindow, width = width-10, height = 2, bg = "#FBDF0F").pack(pady = 20)

    #repeat for theory scenarios that are completes
    theoryLabel = tk.Label(profileWindow, text = "Completed Theory Scenarios:", font = ("Microsoft YaHei UI Light",25,"bold"), fg = "#FBDF0F", bg = "black" )
    theoryLabel.pack(anchor = "w")
    #get completed scenarios from database that are of type thoery
    theoryCompleted = (cur.execute('''SELECT completedScenarios.scenarioName FROM completedScenarios 
                            INNER JOIN learnModeScenarios ON completedScenarios.scenarioName = learnModeScenarios.scenarioName
                            WHERE completedScenarios.userName = "''' + currentUser +'''" AND learnModeScenarios.mode = "''' + "Theory" + '''"''')).fetchall()
    #limit number of scenarios displayed due to space
    if len(theoryCompleted) > 3:
        theoryCompleted = theoryCompleted[0:3]
        theoryCompleted.append(("...",))
    for row in theoryCompleted:
        tk.Label(profileWindow,text = "-" +  row[0],font = ("Microsoft YaHei UI Light",20,"bold"), fg = "#FBDF0F", bg = "black").pack(anchor = "w")
    #if no rows are returned tell user there are no scenarios of this type
    if len(theoryCompleted) == 0:
        tk.Label(profileWindow,text = "-No completed theory scenarios...",font = ("Microsoft YaHei UI Light",20,"bold"), fg = "#FBDF0F", bg = "black").pack(anchor = "w")
    #add line for organisation
    tk.Frame(profileWindow, width = width-10, height = 2, bg = "#FBDF0F").pack(pady = 20)

    #repeat for saved scenarios
    savedLabel = tk.Label(profileWindow, text = "Saved Scenarios:", font = ("Microsoft YaHei UI Light",25,"bold"), fg = "#FBDF0F", bg = "black" )
    savedLabel.pack(anchor = "w")
    #get compleetd scenarios from database that are of type existing
    savedScenarios = (cur.execute('''SELECT sScenarioName FROM savedScenarios WHERE userName = "''' + currentUser + '''"''')).fetchall()
    if len(savedScenarios) > 3:
        savedScenarios = savedScenarios[0:3]
        savedScenarios.append(("...",))
    for row in savedScenarios:
        tk.Label(profileWindow,text = "-" + row[0],font = ("Microsoft YaHei UI Light",20,"bold"), fg = "#FBDF0F", bg = "black").pack(anchor = "w")
    #if no rows are returned tell user there are no scenarios of this type
    if len(savedScenarios) == 0:
        tk.Label(profileWindow,text = "-No saved scenarios on this account...",font = ("Microsoft YaHei UI Light",20,"bold"), fg = "#FBDF0F", bg = "black").pack(anchor = "w")
    #add line for organisation
    tk.Frame(profileWindow, width = width-10, height = 2, bg = "#FBDF0F").pack(pady = 20)
    

    #add sign out button
    signOutButton = tk.Button(profileWindow, text = "SIGN OUT", font = ("Microsoft YaHei UI Light",20,"bold"),bg = "#FBDF0F", fg = "black", command = lambda: [profileWindow.destroy(),masterWindow.destroy(), restartProgram()])
    signOutButton.pack()

    #If master window closes, close profile window.
    masterWindow.protocol('WM_DELETE_WINDOW', lambda: [profileWindow.destroy(),masterWindow.destroy()])
    #Enable profile button if window is closed
    profileWindow.protocol('WM_DELETE_WINDOW', lambda: [bgCanvas.itemconfigure(profileButton, image = profileImage, state = "normal"), profileWindow.destroy()])
    profileWindow.mainloop()

def infoWindow(type,button, masterWindow):
    infoWin = tk.Tk()
    width = 700 # Width 
    #Height depending on type
    if type == "Modes":
        height = 600 # Height
    elif type == "Learn":
        height = 400
    screenWidth = infoWin.winfo_screenwidth()  # Width of the screen
    screenHeight = infoWin.winfo_screenheight() # Height of the screen
    # Calculate Starting X and Y coordinates for Window (centre of screen)
    x = (screenWidth/2) - (width/2)
    y = (screenHeight/2) - (height/2)
    infoWin.geometry('%dx%d+%d+%d' % (width, height, x, y))
    infoWin.configure(bg = "black")
    heading = tk.Label(infoWin, text = "INFORMATION", font = ("Microsoft YaHei UI Light",40,"bold"), fg = "#FBDF0F", bg = "black" )
    heading.pack()
    if type == "Modes":
        #Learn mode text
        learnHeading = tk.Label(infoWin, text = "Learn Mode:", font = ("Microsoft YaHei UI Light",30,"bold"), fg = "#FBDF0F", bg = "black" )
        learnHeading.pack()
        learnInfo = tk.Label(infoWin, text = "Learn mode consists of scenarios that can teach physics theory as well as facts about real life orbits such as the Earth and moon.", font = ("Microsoft YaHei UI Light",20), fg = "#FBDF0F", bg = "black" )
        learnInfo.pack()
        learnInfo.configure(wraplength=700)
        #Experiment mode text
        experimentHeading = tk.Label(infoWin, text = "Experiment Mode:", font = ("Microsoft YaHei UI Light",30,"bold"), fg = "#FBDF0F", bg = "black" )
        experimentHeading.pack()
        experimentInfo = tk.Label(infoWin, text = "Experiment mode is a fun labratory which allows you to make your own orbital system which you can save to your account.", font = ("Microsoft YaHei UI Light",20), fg = "#FBDF0F", bg = "black" )
        experimentInfo.pack()
        experimentInfo.configure(wraplength=700)
        #Saved scenarios text
        savedHeading = tk.Label(infoWin, text = "Saved Scenarios:", font = ("Microsoft YaHei UI Light",30,"bold"), fg = "#FBDF0F", bg = "black" )
        savedHeading.pack()
        savedInfo = tk.Label(infoWin, text = "Access scenarios you have saved from learn and experiment mode to continue where you left off!", font = ("Microsoft YaHei UI Light",20), fg = "#FBDF0F", bg = "black" )
        savedInfo.pack()
        savedInfo.configure(wraplength=700)
    elif type == "Learn":
        #Theory scenarios text
        theoryHeading = tk.Label(infoWin, text = "Theory Scenarios:", font = ("Microsoft YaHei UI Light",30,"bold"), fg = "#FBDF0F", bg = "black" )
        theoryHeading.pack()
        theoryInfo = tk.Label(infoWin, text = "Learn about physics formulas and how they work along with other bits of theory diagramatically.", font = ("Microsoft YaHei UI Light",20), fg = "#FBDF0F", bg = "black" )
        theoryInfo.pack()
        theoryInfo.configure(wraplength=700)
        #Existing scenarios text
        existingtHeading = tk.Label(infoWin, text = "Existing Scenarios:", font = ("Microsoft YaHei UI Light",30,"bold"), fg = "#FBDF0F", bg = "black" )
        existingtHeading.pack()
        existingInfo = tk.Label(infoWin, text = "Learn about current orbits and fun facts with preset scenarios.", font = ("Microsoft YaHei UI Light",20), fg = "#FBDF0F", bg = "black" )
        existingInfo.pack()
        existingInfo.configure(wraplength=700)

    #If master window closes, close profile window.
    masterWindow.protocol('WM_DELETE_WINDOW', lambda: [profileWindow.destroy(),masterWindow.destroy()])
    #Enable info button if window is closed
    infoWin.protocol('WM_DELETE_WINDOW', lambda: [button.config(state = "normal"), infoWin.destroy()])
    infoWin.mainloop()

def delScenario(scenarioName, currentUser):
    #deleet scneario..this should cascade throughout db
    cur.execute("""DELETE FROM savedScenarios WHERE sScenarioName = '""" + scenarioName + """' AND userName = '""" + currentUser + """'""")
    conn.commit()
    


#create scenario object to store name of scenario and display in correct position.
class scenarioObject:
    def __init__(self, scenarioName, scenarioRow, scenarioColumn, completeValue, frame, currentUser, bgCanvas, exitButton, window, mode):
        self.name = scenarioName
        self.row = scenarioRow
        self.column = scenarioColumn
        #create button object for scenario
        exitPress = tk.BooleanVar(window,False)
        #button command depends on whether mode is saved or not since it will lead to different window
        if mode == "Saved":
            self.button=tk.Button(frame, text = self.name, font = ("Microsoft YaHei UI Light",20,"bold"),bg = "#FBDF0F", fg = "black", command = lambda: [bgCanvas.tag_bind(exitButton, "<Button-1>", lambda e: [exitPress.set(True), pygame.display.quit(), scenarioSelectionWindow(window,frame,mode, currentUser, bgCanvas,exitButton, True)]),experimentSimWindow(window,frame,mode,bgCanvas, exitPress, currentUser, scenarioName)])
        else:
            self.button = tk.Button(frame, text = self.name, font = ("Microsoft YaHei UI Light",20,"bold"),bg = "#FBDF0F", fg = "black", command = lambda: [bgCanvas.tag_bind(exitButton, "<Button-1>", lambda e: [exitPress.set(True), pygame.display.quit(), scenarioSelectionWindow(window,frame,mode, currentUser, bgCanvas,exitButton, True)]),learnSimWindow(window,frame, self.name, mode, bgCanvas, exitPress)])
        #create check box objects for learn mode scenarios
        self.complete = customtkinter.BooleanVar(value = completeValue)
        self.checkBox = customtkinter.CTkCheckBox(frame, variable = self.complete, onvalue= True, offvalue = False, bg_color="black", fg_color = "black", checkbox_height=50, checkbox_width=50, checkmark_color="yellow", width = 50, height = 50, text = None, border_color="yellow", hover_color="#3b3b3b", command = lambda: [self.changeCompletionState(self.complete, currentUser)] )
        #create delete button for saved scenarios
        #Bin button
        self.binImage = ImageTk.PhotoImage(Image.open("Images/bin.jpg").resize((50,65)), master = window)
        self.binButton = tk.Button(frame,height = 65, width = 50, highlightthickness = 0, bd = 0, highlightbackground = "black",image = self.binImage, command = lambda: [delScenario(self.name, currentUser), scenarioSelectionWindow(window,frame,mode, currentUser, bgCanvas,exitButton, False)])
    #method to update db depending on check box    
    def changeCompletionState(self, boxState, currentUser):
        #if the state was checked then add scenario to table with username otherwise delete record
        if boxState.get() == True:
            cur.execute("""INSERT INTO completedScenarios VALUES(?,?)""",(currentUser, self.name))
        else:
            cur.execute("""DELETE FROM completedScenarios WHERE scenarioName = '""" + self.name + """'""")
        conn.commit()
            
#creates scenario selection window dpendent on mode 
def scenarioSelectionWindow(window,frame,mode, currentUser, bgCanvas, exitButton, fromSim = False):
    #create list of scenario objects
    scenarioList = []
    if not fromSim:
        #if called from learn page just clear frame
        for widgets in frame.winfo_children():
            widgets.destroy()
        #if called from home page also add exit button (so if saved scenarios pressed)
        if mode == "Saved":
            #add exit image to canvas
            exitImage = ImageTk.PhotoImage(Image.open("Images/exit.png").resize((80,80)), master = window)
            exitButton = bgCanvas.create_image(40, 40,image=exitImage)
            bgCanvas.tag_bind(exitButton, "<Button-1>", lambda e: [bgCanvas.delete(exitButton), homePageWindow(window,frame,bgCanvas, currentUser)])
    #if called from simulation clear contents of page and re-add frame, exit button, profile button
    else:
        #destroy all widgets
        for widget in bgCanvas.winfo_children():
            widget.destroy()
        #destroy all canvas objects
        for item in bgCanvas.find_all():
                bgCanvas.delete(item)
        #readd backgroundimg
        bg = (Image.open("Images/bg.webp"))
        resizedBg= ImageTk.PhotoImage(bg.resize((1920,1200)), master = window)
        bgCanvas.create_image(window.winfo_screenwidth()/2,window.winfo_screenheight()/2,image = resizedBg)
        #re add exit button and profile buttons
        #add exit image to canvas
        exitImage = ImageTk.PhotoImage(Image.open("Images/exit.png").resize((80,80)), master = window)
        exitButton = bgCanvas.create_image(40, 40,image=exitImage)
        # if mode is saved update exit button command accoringly to return to correct window
        if mode == "Saved":
            bgCanvas.tag_bind(exitButton, "<Button-1>", lambda e: [bgCanvas.delete(exitButton), homePageWindow(window,frame,bgCanvas, currentUser)])
        else:
            bgCanvas.tag_bind(exitButton, "<Button-1>", lambda e: [bgCanvas.delete(exitButton), learnPageWindow(window,frame,bgCanvas,homePageWindow,currentUser)])
        profileImage = ImageTk.PhotoImage(Image.open("Images/profile.png").resize((80,80)), master = window)
        profileButton = bgCanvas.create_image(window.winfo_screenwidth() - 40,40,image=profileImage)
        bgCanvas.tag_bind(profileButton, "<Button-1>", lambda e: profileWindow(bgCanvas,currentUser, profileButton,profileImage, window)) 
        #re add frame to window
        frame = tk.Frame(bgCanvas, bg = "black", height = 800, width = 1500)
        frame.place(relx=0.5, rely=0.5,anchor = tk.CENTER)
    #make all columns equally weighted
    frame.grid_columnconfigure(0, weight=1, uniform="scenario")
    frame.grid_columnconfigure(1, weight=1, uniform="scenario")
    frame.grid_columnconfigure(2, weight=1, uniform="scenario")
    frame.grid_columnconfigure(3, weight=1, uniform="scenario")
    frame.grid_rowconfigure(0, weight=1, uniform = "scenario1")
    frame.grid_rowconfigure(1, weight=1, uniform = "scenario1")
    frame.grid_rowconfigure(2, weight=1, uniform = "scenario1")
    frame.grid_rowconfigure(3, weight=1, uniform = "scenario1")
    heading = tk.Label(frame, text = mode+ " Scenarios", font = ("Microsoft YaHei UI Light",50,"bold"), fg = "#FBDF0F", bg = "black")
    heading.grid(row = 0,columnspan  = COLUMNS, pady = 40)
    currentColumn = -1
    currentRow = 0
    #if learn mode scenario selection do the below
    if mode != "Saved":
        #use the database to fetch scenarios and format correctly
        for row in (cur.execute('SELECT scenarioName FROM learnModeScenarios WHERE mode = "' + mode +'"')).fetchall():
            completedFlag = False
            #format rows and columns so they are output in correct format
            currentColumn +=1
            #if last column reached, update row and reset column
            if (currentColumn+1) % COLUMNS == 1:
                currentRow +=1
                currentColumn = 0
            #if scenario is present in the completed table with current user then set the completed flag to true, 
            for returnScenario in (cur.execute('SELECT scenarioName FROM completedScenarios WHERE userName = "' + currentUser + '"')).fetchall():
                if row[0] in returnScenario:
                    completedFlag = True
            scenarioList.append(scenarioObject(row[0],currentRow,currentColumn, completedFlag, frame, currentUser, bgCanvas, exitButton, window, mode))
    #if saved scenario scenario selection do the below    
    else:
        rows = (cur.execute('SELECT sScenarioName FROM savedScenarios WHERE userName = "' + currentUser +'"')).fetchall()
        #check if user has any saved scenarios
        if len(rows) == 0:
            noneSavedLabel = tk.Label(frame, text = "NO SAVED SCENARIOS...", font = ("Microsoft YaHei UI Light",30,"bold"),fg = "#FBDF0F", bg = "black")
            noneSavedLabel.grid(columnspan = 4, row = 1, padx = 400)
        else:
            #use the database to fetch scenarios and format correctly
            for row in rows:
                #format rows and columns so they are output in correct format
                currentColumn +=1
                #if last column reached, update row and reset column
                if (currentColumn+1) % COLUMNS == 1:
                    currentRow +=1
                    currentColumn = 0
                #create scenario object
                scenarioList.append(scenarioObject(row[0],currentRow,currentColumn, False, frame, currentUser, bgCanvas, exitButton, window, mode))
    #add buttons for each scenario
    for scenario in scenarioList:
        (scenario.button).grid(row =scenario.row, column = scenario.column, pady = 50)
        window.update()
        if mode !="Saved":
            (scenario.checkBox).grid(row =scenario.row, column = scenario.column,sticky = "E", padx = (scenario.button.winfo_width()+80,0))
        else:
            (scenario.binButton).grid(row =scenario.row, column = scenario.column,sticky = "E", padx = (scenario.button.winfo_width()+80,0))
    window.mainloop()

        

def learnPageWindow(learnWin,frame,bgCanvas, previousWindow, currentUser):
    #reset columns and rows
    frame.grid_forget()
    frame.grid_columnconfigure(0, weight=0, uniform="learn")
    frame.grid_columnconfigure(1, weight=0, uniform="learn")
    frame.grid_rowconfigure(0, weight=1, uniform = "learnrow")
    frame.grid_rowconfigure(1, weight=4, uniform = "learnrow")
    frame.grid_rowconfigure(2, weight=1, uniform = "learnrow")

    for widgets in frame.winfo_children():
        #remove previous widgets on frame
        widgets.destroy()
    #add exit image to canvas
    exitImage = ImageTk.PhotoImage(Image.open("Images/exit.png").resize((80,80)), master = learnWin)
    exitButton = bgCanvas.create_image(40, 40,image=exitImage)
    #bind image to a button command
    bgCanvas.tag_bind(exitButton, "<Button-1>", lambda e: [bgCanvas.delete(exitButton), previousWindow(learnWin,frame,bgCanvas,currentUser)]) 
    #add learn heading
    heading = tk.Label(frame, text = "LEARN", font = ("Microsoft YaHei UI Light",50,"bold"), fg = "#FBDF0F", bg = "black" )
    heading.grid(row = 0,columnspan  = 2, sticky = "N")
    #Theory Scenarios image
    theoryImg = (Image.open("Images/Theory.png"))
    resizedTheoryImg= ImageTk.PhotoImage(theoryImg.resize((800,500)), master = learnWin)
    leftimg = tk.Label(frame, image = resizedTheoryImg, bg = "black")
    leftimg.grid(row = 1, column = 0, sticky = "S", padx = 50, pady = 25)
    #Existing Scenarios mode image
    existingImg = (Image.open("Images/Existing.jpg"))
    resizedExistingImg= ImageTk.PhotoImage(existingImg.resize((800,500)), master = learnWin)
    rightimg = tk.Label(frame, image = resizedExistingImg, bg = "black")
    rightimg.grid(row = 1, column = 1, sticky = "S", padx = 50, pady = 25)
    #Theory Scenarios button
    #command updates exit button so it will exit to new previous window and creates new window
    theoryButton = tk.Button(frame, text = "THEORY SCENARIOS", font = ("Microsoft YaHei UI Light",20,"bold"),bg = "#FBDF0F", fg = "black", command = lambda: [bgCanvas.tag_bind(exitButton, "<Button-1>", lambda e: [bgCanvas.delete(exitButton), learnPageWindow(learnWin,frame,bgCanvas,homePageWindow,currentUser)]), scenarioSelectionWindow(learnWin, frame, "Theory", currentUser, bgCanvas, exitButton)])
    theoryButton.grid(row=2,column=0, sticky = "S", padx=50, pady =25)
    #Existing Scenarios button
    existingButton = tk.Button(frame, text = "EXISTING SCENARIOS", font = ("Microsoft YaHei UI Light",20,"bold"),bg = "#FBDF0F", fg = "black", command = lambda: [bgCanvas.tag_bind(exitButton, "<Button-1>", lambda e: [bgCanvas.delete(exitButton), learnPageWindow(learnWin,frame,bgCanvas,homePageWindow,currentUser)]), scenarioSelectionWindow(learnWin, frame, "Existing", currentUser, bgCanvas, exitButton)])
    existingButton.grid(row=2,column=1, sticky = "S", padx=50,pady = 25)
    #Info button
    infoImage = ImageTk.PhotoImage(Image.open("Images/info.jpg").resize((60,60)), master = learnWin)
    infoButton = tk.Button(frame, bg = "black",highlightthickness = 0, bd = 0, highlightbackground = "black",image = infoImage, command = lambda: [infoButton.config(state = "disabled"), infoWindow("Learn",infoButton,learnWin)])
    infoButton.grid(row =0, column = 0, sticky = "NW", pady = 10, padx = 10)

    learnWin.mainloop()

def homePageWindow(homeWin,frame,bgCanvas,currentUser):
    #destroy all widgets
    for widget in bgCanvas.winfo_children():
        widget.destroy()
    #destroy all canvas objects
    for item in bgCanvas.find_all():
            bgCanvas.delete(item)
    #readd backgroundimg
    bg = (Image.open("Images/bg.webp"))
    resizedBg= ImageTk.PhotoImage(bg.resize((1920,1200)), master = homeWin)
    bgCanvas.create_image(homeWin.winfo_screenwidth()/2,homeWin.winfo_screenheight()/2,image = resizedBg)
    #re add frame to window
    frame = tk.Frame(bgCanvas, bg = "black", height = 800, width = 1500)
    frame.place(relx=0.5, rely=0.5,anchor = tk.CENTER)
    #add home heading
    heading = tk.Label(frame, text = "HOME", font = ("Microsoft YaHei UI Light",50,"bold"), fg = "#FBDF0F", bg = "black" )
    heading.grid(row = 0, column = 1, pady = 40, sticky = "N")
    #add profile image to canvas
    profileImage = ImageTk.PhotoImage(Image.open("Images/profile.png").resize((80,80)), master = homeWin)
    profileButton = bgCanvas.create_image(homeWin.winfo_screenwidth() - 40,40,image=profileImage)
    #bind image to a button command
    bgCanvas.tag_bind(profileButton, "<Button-1>", lambda e: profileWindow(bgCanvas,currentUser, profileButton,profileImage, homeWin)) 
    #Learn Mode image
    learn_img = (Image.open("Images/Learn.png"))
    resizedLearn_img= ImageTk.PhotoImage(learn_img.resize((464,428)), master = homeWin)
    leftimg = tk.Label(frame, image = resizedLearn_img, bg = "black")
    leftimg.grid(row = 1, column = 0, sticky = "S", padx = 50)
    #Experiment mode image
    experiment_img = (Image.open("Images/Experiment.png"))
    resizedExp_img= ImageTk.PhotoImage(experiment_img.resize((464,428)), master = homeWin)
    middleimg = tk.Label(frame, image = resizedExp_img, bg = "black")
    middleimg.grid(row = 1, column = 1, sticky = "S", padx = 50)
    #Experiment mode image
    savedImg = (Image.open("Images/Saved.png"))
    resizedSavedImg= ImageTk.PhotoImage(savedImg.resize((464,428)), master = homeWin)
    middleimg = tk.Label(frame, image = resizedSavedImg, bg = "black")
    middleimg.grid(row = 1, column = 2, sticky = "S", padx = 50)
    #Learn mode button
    learnButton = tk.Button(frame, text = "LEARN MODE", font = ("Microsoft YaHei UI Light",20,"bold"),bg = "#FBDF0F", fg = "black", command = lambda: learnPageWindow(homeWin,frame, bgCanvas, homePageWindow,currentUser))
    learnButton.grid(row=2,column=0, sticky = "S", padx=50, pady = 50)
    #create button object for scenario
    exitPress = tk.BooleanVar(homeWin,False)
    #Experiment mode button
    experimentButton = tk.Button(frame, text = "EXPERIMENT MODE", font = ("Microsoft YaHei UI Light",20,"bold"),bg = "#FBDF0F", fg = "black", command = lambda: [experimentSimWindow(homeWin,frame,"Experiment",bgCanvas, exitPress, currentUser, "")])
    experimentButton.grid(row=2,column=1, sticky = "S", padx=50, pady = 50)
    #Saved mode button
    savedButton = tk.Button(frame, text = "SAVED SCENARIOS", font = ("Microsoft YaHei UI Light",20,"bold"),bg = "#FBDF0F", fg = "black", command = lambda: scenarioSelectionWindow(homeWin, frame, "Saved", currentUser, bgCanvas, None))
    savedButton.grid(row=2,column=2, sticky = "S", padx=50, pady = 50)
    #Info button
    infoImage = ImageTk.PhotoImage(Image.open("Images/info.jpg").resize((60,60)), master = homeWin)
    infoButton = tk.Button(frame, bg = "black",highlightthickness = 0, bd = 0, highlightbackground = "black",image = infoImage, command = lambda: [infoButton.config(state = "disabled"),infoWindow("Modes", infoButton,homeWin)])
    infoButton.grid(row =0, column = 0, sticky = "NW", pady = 10, padx = 10)

    homeWin.mainloop()
























