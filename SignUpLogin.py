import tkinter as tk
from PIL import Image, ImageTk
import hashlib
import random
import sqlite3
from time import sleep
from CreateLearnModeTables import *
from PreSimWindows import homePageWindow

#create tables 
conn = sqlite3.connect('NEA_database.db')
cur = conn.cursor() 
cur.execute('''CREATE TABLE if not exists 
          credentials ( 
   username text PRIMARY KEY, 
   password  text
)''') 
conn.commit()

#only create and populate tables in db if tables don't exist i.e. nothing returned when querying for table
if (cur.execute('SELECT name FROM sqlite_master WHERE type = "table" AND name = "learnModeScenarios"')).fetchone() == None:
    createPopulateLearnModeTables()
conn.execute("PRAGMA foreign_keys = ON")#allow foreign keys
conn.commit()


class credentials: #an object is created to be used for different user credentials i.e. username and password
    def __init__(self, userName,passWord): #def __innit__ used for privatised attributes 
        self.__userName = userName
        self.__passWord = passWord
    def __eq__(self, other): #def __eq__ used to refer to what attributes needs to be compared when comparisons between this object occur
        if self.userName == other.userName and self.passWord == other.passWord:
            return True
        return False
    #getter methods for username and password
    def getUsername(self):
        return self.__userName
    def getPassword(self):
        return self.__passWord

def convertToHash(string): #a function to convert password to a hash value
    hashfunc = hashlib.sha1()
    encodedString=string.encode()
    # Passing the string into update()
    hashfunc.update(encodedString)
    # Saving the new string using hexdigest()
    return(hashfunc.hexdigest())

#check if username is correct
def checkUsername(c,userDetails):
    found = False
    for row in (c.execute('SELECT username FROM credentials WHERE username = "' + userDetails.getUsername() +'"')):
        if userDetails.getUsername() in row:
            found = True
    return found

#check if password is correct
def checkPassword(c,userDetails):
    found = False
    for row in (c.execute('SELECT password FROM credentials WHERE username = "' + userDetails.getUsername() +'"')):
        if userDetails.getPassword() in row:
            found = True
    return found

def checkSignUp(signupLoginWindow, userNameEntry, passwordEntry, error, invalid ):
    invalid.config(fg="red")
    specialchar="$@_"
    lower, upper, digit, special = 0, 0, 0, 0
    userName = userNameEntry.get()
    passWord = (passwordEntry.get())
    userDetails = credentials(userName, passWord)
    if checkUsername(cur,userDetails):
        #if username in use update error
        error.set("Username already in use")
    elif userDetails.getUsername() == "" or userDetails.getPassword() == "":
        #if either field empty update error
        error.set("Field can't be empty...")
    else:
        if len(userDetails.getPassword()) > 5:
            for char in userDetails.getPassword():
                # counting lowercase alphabets
                if (char.islower()):
                    lower+=1           
                # counting uppercase alphabets
                if (char.isupper()):
                    upper+=1           
                # counting digits
                if (char.isdigit()):
                    digit+=1           
                # counting the mentioned special characters
                if(char in specialchar):
                    special+=1          
            if (lower>=1 and upper>=1 and digit>=1 and special>=1):
                #if sign up successful insert credentials into db
                cur.execute('INSERT INTO credentials VALUES (?,?)', (userDetails.getUsername(),convertToHash(userDetails.getPassword()))) 
                conn.commit() 
                #if sign up successful set invalid font colour to green to output success message
                invalid.config(fg="green")
                error.set("Sign up successful")
                userNameEntry.delete(0,tk.END)
                passwordEntry.delete(0,tk.END)
            else:
                #update error message accordingly
                error.set("Password too weak...must contain an uppercase, lowercase, number and special character")
        else:
            #update error message accordingly
            error.set("Password too short...must be at least 6 characters long")   
    #update error to output appropriate error message
    signupLoginWindow.update_idletasks()

def checkLogin(signupLoginWindow, userNameEntry, passwordEntry, error, invalid, frame, bgCanvas):
    #set font colour of invalid label to red
    invalid.config(fg="red")
    #gets username and hashed password
    userName = userNameEntry.get()
    passWord = convertToHash(passwordEntry.get())
    userDetails = credentials(userName, passWord)
    if userDetails.getUsername() == "" or userDetails.getPassword() == "":
        #if either field empty update error
        error.set("Field can't be empty...")
    else:
       if not checkUsername(cur, userDetails):
            #if username not correct update error message
            error.set("Username doesn't exist")
            #update window to output error
            signupLoginWindow.update_idletasks()
       elif not checkPassword(cur,userDetails):
            #if password not correct update error message
            error.set("Invalid Password")
            signupLoginWindow.update_idletasks()
       else:
            #if login successful destroy window
            homePageWindow(signupLoginWindow,frame,bgCanvas,userDetails.getUsername())
    conn.commit() 

#function to generate username
def generateUsername(usernameGenWin, fNameEntry, lNameEntry, nameGenLbl,userNameEntry,genUnameButton):
    #get text from first and last name entry fields
    fName = fNameEntry.get()
    lName = lNameEntry.get()
    userNamegen = ""
    tempUName = fName[0:len(fName)//2].lower() + lName[0:len(lName)//2+1].lower()
    #create random username
    for i in range(0,len(tempUName)-1):
        if i % 2== 0:
            userNamegen += tempUName[i].upper()
        else:
            userNamegen += tempUName[i].lower()
    userNamegen += str(ord(lName[-1:]))
    userNamegen += chr(random.randint(33,64))
    nameGenLbl.config(text = "Suggested username: " + userNamegen)
    #add buttons to allow user to use, not use user name
    useBtn = tk.Button(usernameGenWin,font =("Microsoft YaHei UI Light",15,"bold"), bg = "#FBDF0F", fg = "black",text = "Use now", command = lambda: [userNameEntry.delete(0,tk.END),sleep(0.1),genUnameButton.config(state = "normal"),userNameEntry.insert(0,userNamegen),usernameGenWin.destroy()]).grid(row = 13, column = 0)
    dontUseBtn = tk.Button(usernameGenWin, font =("Microsoft YaHei UI Light",15,"bold"), bg = "#FBDF0F", fg = "black",text = "Don't use", command = lambda:[genUnameButton.config(state = "normal"),usernameGenWin.destroy()]).grid(row = 15, column = 0)

def userNameGeneratorWindow(userNameEntry,genUnameButton, masterWindow):
    #create new window and set colour
    usernameGenWin = tk.Tk()
    usernameGenWin.configure(bg = "black")
    usernameGenWin.geometry("700x400")
    tk.Label(usernameGenWin,text = "Username Generator", bg = "black", fg = "#FBDF0F",  font = ("Microsoft YaHei UI Light",35,"bold")).grid(row = 0, column = 0, pady =20)
    #create firstname and last name entry the same way as username and password entries
    firstNameEntry = tk.Entry(usernameGenWin, bg = "black", fg = "#FBDF0F", border = 0, font = ("Microsoft YaHei UI Light",20,"bold"))
    firstNameEntry.configure(insertbackground="#FBDF0F")
    firstNameEntry.insert(0,"First Name")
    firstNameEntry.grid(column = 0, row = 1, sticky = "SW", padx=30)
    tk.Frame(usernameGenWin,width = 600, height = 2, bg = "#FBDF0F").grid(column = 0, row = 2, sticky = "N",padx=30)
    lastNameEntry = tk.Entry(usernameGenWin, bg = "black", fg = "#FBDF0F", border = 0, font = ("Microsoft YaHei UI Light",20,"bold"))
    lastNameEntry.configure(insertbackground="#FBDF0F")
    lastNameEntry.insert(0,"Last Name")
    lastNameEntry.grid(column = 0, row = 6, sticky = "SW", padx=30)
    tk.Frame(usernameGenWin,width = 600, height = 2, bg = "#FBDF0F").grid(column = 0, row = 7, sticky = "N",padx=30)
    #create button with command for username generation
    button = tk.Button(usernameGenWin, text = "Generate", font = ("Microsoft YaHei UI Light",15,"bold"), bg = "#FBDF0F", fg = "black", command = lambda:generateUsername(usernameGenWin,firstNameEntry,lastNameEntry, nameGenLbl,userNameEntry,genUnameButton))
    button.grid(row = 9, column = 0)
    #create empty label to be filled with generated username
    nameGenLbl = tk.Label(usernameGenWin, text = "", fg = "#FBDF0F", font = ("Microsoft YaHei UI Light",20,"bold"), bg = "black")
    nameGenLbl.grid(row = 10, column = 0)

    #If master window closes, close usernamegen window.
    masterWindow.protocol('WM_DELETE_WINDOW', lambda: [usernameGenWin.destroy(),masterWindow.destroy()])
    #Enable usernamegen button if window is closed
    usernameGenWin.protocol('WM_DELETE_WINDOW', lambda: [genUnameButton.config(state = "normal"), usernameGenWin.destroy()])


    usernameGenWin.mainloop()

def loginSignUpWindow(type):
    for widgets in window.winfo_children():
        #remove previous widgets on window (as the type may be different now)
        widgets.destroy()
    #full screen window
    window.state("zoomed")
    #create canvas
    bgCanvas = tk.Canvas(window, highlightthickness=0)
    bgCanvas.pack(fill=tk.BOTH, expand=True)
    #add bg image to canvas
    bg = (Image.open('Images/bg.webp'))
    resizedBg= ImageTk.PhotoImage(bg.resize((1920,1200)), master = window)
    bgCanvas.create_image(window.winfo_screenwidth()/2,window.winfo_screenheight()/2,image = resizedBg)
    #add central frame
    frame = tk.Frame(bgCanvas, bg = "black", height = 800, width = 1500)
    frame.place(relx=0.5, rely=0.5,anchor = tk.CENTER)
    frame.grid_propagate(False)
    #add welcome heading
    heading = tk.Label(frame, text = "WELCOME", font = ("Microsoft YaHei UI Light",50,"bold"), fg = "#FBDF0F", bg = "black" )
    heading.grid(row = 0, column = 0, pady = 40, sticky = "N")
    #add image
    img = (Image.open("Images/bg5.jpg"))
    resizedImg= ImageTk.PhotoImage(img.resize((800,642)))
    leftimg = tk.Label(frame, image = resizedImg, bg = "black")
    leftimg.grid(row = 1, column = 0,rowspan = 15, sticky = "N")
    #add login/signup heading depending on type
    loginSignupHeading = tk.Label(frame, text = type, bg = "black", fg = "#FBDF0F", font = ("Microsoft YaHei UI Light",40,"bold"))
    loginSignupHeading.grid(row=0, column = 1, sticky = "S")
    #add username entry field
    userNameEntry = tk.Entry(frame, bg = "black", fg = "#FBDF0F", border = 0, font = ("Microsoft YaHei UI Light",20,"bold"),width=28)
    userNameEntry.configure(insertbackground="#FBDF0F") #typing cursor
    userNameEntry.grid(row = 3, column = 1, sticky = "SW", padx=30 )
    #add line for username field and pre-enter username in field
    tk.Frame(frame, width = 600, height = 2, bg = "#FBDF0F").grid(row = 4, column = 1,sticky = "N", padx = 30)
    userNameEntry.insert(0, "Username")
    #add password entry field
    passwordEntry = tk.Entry(frame, bg = "black", fg = "#FBDF0F", border = 0, font = ("Microsoft YaHei UI Light",20,"bold"), width = 28)
    passwordEntry.configure(insertbackground="#FBDF0F")#typing cursor
    passwordEntry.grid(row = 5, column = 1, sticky = "SW", padx=30 )
    #add line for password field and pre-enter password in field
    tk.Frame(frame, width = 600, height = 2, bg = "#FBDF0F").grid(row = 6, column = 1,sticky = "N", padx = 30)
    passwordEntry.insert(0, "Password")
    #button to hide password
    hideImage = ImageTk.PhotoImage(Image.open('Images/hidePassword.png').resize((46,35)))
    hideButton = tk.Button(frame, bg = "black",highlightthickness = 0, bd = 0, highlightbackground = "black",image = hideImage, command = lambda: hideButtonPress(passwordEntry, frame))
    hideButton.grid(row =5, column = 1, sticky = "SE", padx = 30)
    #different errors depending on the username and password inputted.
    error = tk.StringVar()
    invalid = tk.Label(frame,font = ("Microsoft YaHei UI Light",10,"bold"), textvariable = error, bg = "black", fg = "red")
    invalid.grid(row = 6, column = 1,sticky = "WE")
    #submit button will have different commands depending on whether they are signing up or logging in.
    if type == "Log-in":
        opposite = "Sign-up"
        preword = "Don't"
        button = tk.Button(frame, text = "SUBMIT", font = ("Microsoft YaHei UI Light",15,"bold"), bg = "#FBDF0F", fg = "black", command = lambda: checkLogin(window, userNameEntry, passwordEntry, error, invalid,frame,bgCanvas))
    else:
        opposite = "Log-in"
        preword = "Already"
        button = tk.Button(frame, text = "SUBMIT", font = ("Microsoft YaHei UI Light",15,"bold"), bg = "#FBDF0F", fg = "black", command = lambda: checkSignUp(window, userNameEntry, passwordEntry, error, invalid))
        #need to show the generate username button if the user is signing up
        genUnameButton = tk.Button(frame, text = "GENERATE", font = ("Microsoft YaHei UI Light",15,"bold"),bg = "#FBDF0F", fg = "black", command = lambda: [genUnameButton.config(state = "disabled"),userNameGeneratorWindow(userNameEntry, genUnameButton,window )])
        genUnameButton.grid(row=3,column=1, sticky = "SE", padx=30)
    #place submit button
    button.grid(row = 7, column = 1)
    tk.Label(frame, text = "----------------------OR----------------------", font = ("Microsoft YaHei UI Light",20,"bold"), bg = "black", fg = "#FBDF0F" ).grid(row = 8, column = 1)
    tk.Label(frame, text = preword + " have an account?", font = ("Microsoft YaHei UI Light",15,"bold"), bg = "black", fg = "#FBDF0F").grid(row = 9, column = 1)
    #give user the option to do the opposite action i.e. sign up or login
    tk.Button(frame, text = opposite, font = ("Microsoft YaHei UI Light",15,"bold"), bg = "#FBDF0F", fg = "black", command = lambda:[loginSignUpWindow(opposite)]).grid(row = 10, column = 1)

    window.mainloop()


#function for showing the password and changing button to hide password
def showButtonPress(pWordEntry,frame):
    hideImage = ImageTk.PhotoImage(Image.open('Images/hidePassword.png').resize((46,35)))
    pWordEntry.config(show="")
    hideButton = tk.Button(frame, bg = "black",highlightthickness = 0, bd = 0, highlightbackground = "black",image = hideImage, command = lambda: hideButtonPress(pWordEntry, frame))
    hideButton.image = hideImage
    hideButton.grid(row =5, column = 1, sticky = "SE", padx = 30)

#function for hiding the password with asterisks and changing button to show password
def hideButtonPress(pWordEntry,frame):
    showImage = ImageTk.PhotoImage(Image.open('Images/showPassword.png').resize((46,35)))
    pWordEntry.config(show="*")
    showButton = tk.Button(frame, bg = "black",highlightthickness = 0, bd = 0, highlightbackground = "black",image = showImage, command = lambda: showButtonPress(pWordEntry, frame))
    showButton.image = showImage
    showButton.grid(row =5, column = 1, sticky = "SE", padx = 30)

def main():
    global window
    window = tk.Tk()
    loginSignUpWindow("Log-in")

if __name__ == "__main__":
    main()