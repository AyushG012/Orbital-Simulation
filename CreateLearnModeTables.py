import sqlite3

def createPopulateLearnModeTables():
    #create connection to database
    conn = sqlite3.connect("NEA_database.db")
    #get cursor to use db
    cur = conn.cursor()
    #create relevant tables for learn mode
    cur.execute("""
                CREATE TABLE if not exists learnModeScenarios
                (
                    scenarioName     text,
                    information        text,
                    mode              text
                )
            """)
    cur.execute("""
                CREATE TABLE if not exists learnScenarioBodyLink
                (
                    scenarioName     text,
                    bodyName       integer
                    
                )
            """)
    cur.execute("""
                CREATE TABLE if not exists learnModeBodies
                (
                    bodyName        text,
                    velocity       float,
                    mass           float,
                    radius          float,
                    information    text,
                    colour          text,
                    type        text 
                )
            """)
    conn.commit()

    #ADDING ACTUAL EXISTING SCENARIO DATA TO DATABASE:

    #add scenario to table:
    cur.execute("""INSERT INTO learnModeScenarios VALUES(?,?,?)""",("Earth-Sun","earthSunInfo.txt", "Existing"))
    #add bodies earth and sun
    cur.execute("""INSERT INTO learnModeBodies VALUES(?,?,?,?,?,?,?)""",("Earth",3e4, 5.97e24, 1.5e8, "earthInfo.txt", "Earth.png", "planet"))
    cur.execute("""INSERT INTO learnModeBodies VALUES(?,?,?,?,?,?,?)""",("Sun",0, 1.99e30, 0, "sunInfo.txt", "sun.png", "star"))
    #create link between scenario and body
    cur.execute("""INSERT INTO learnScenarioBodyLink VALUES(?,?)""",("Earth-Sun", "Sun"))
    cur.execute("""INSERT INTO learnScenarioBodyLink VALUES(?,?)""",("Earth-Sun", "Earth"))

    # ADDING ACTUAL DATA FOR THEORETICAL SCENARIO:

    #add scenario to table:
    cur.execute("""INSERT INTO learnModeScenarios VALUES(?,?,?)""",("Circular Motion","circularMotion.txt", "Theory"))
    #add bodies earth and sun
    cur.execute("""INSERT INTO learnModeBodies VALUES(?,?,?,?,?,?,?)""",("Planet - Circular",2.6e4, 101e24, 2e8, "circMotionPlanet.txt", "(0,0,255)", "planet"))
    cur.execute("""INSERT INTO learnModeBodies VALUES(?,?,?,?,?,?,?)""",("Star",0, 1.99e30, 0, "circMotionSun.txt", "(255,88,0)", "star"))
    #create link between scenario and body
    cur.execute("""INSERT INTO learnScenarioBodyLink VALUES(?,?)""",("Circular Motion", "Planet - Circular"))
    cur.execute("""INSERT INTO learnScenarioBodyLink VALUES(?,?)""",("Circular Motion", "Star - Circular"))

    conn.commit()

    cur.execute("""
                CREATE TABLE if not exists completedScenarios 
                (
                    userName       text,
                    scenarioName     text 
                )
            """)
    
    conn.commit()

    #add dummy scenarios
    cur.execute("""INSERT INTO learnModeScenarios VALUES(?,?,?)""",("Test1","test1.txt", "Existing"))
    cur.execute("""INSERT INTO learnModeScenarios VALUES(?,?,?)""",("Test2","test2.txt", "Existing"))
    cur.execute("""INSERT INTO learnModeScenarios VALUES(?,?,?)""",("Test3","test3.txt", "Existing"))
    cur.execute("""INSERT INTO learnModeScenarios VALUES(?,?,?)""",("Test4","test4.txt", "Existing"))
    cur.execute("""INSERT INTO learnModeScenarios VALUES(?,?,?)""",("Test5","test5.txt", "Existing"))
    cur.execute("""INSERT INTO learnModeScenarios VALUES(?,?,?)""",("Test6","test6.txt", "Existing"))
    cur.execute("""INSERT INTO learnModeScenarios VALUES(?,?,?)""",("Test1b","test1.txt", "Theory"))
    cur.execute("""INSERT INTO learnModeScenarios VALUES(?,?,?)""",("Test2b","test2.txt", "Theory"))
    cur.execute("""INSERT INTO learnModeScenarios VALUES(?,?,?)""",("Test3b","test3.txt", "Theory"))
    cur.execute("""INSERT INTO learnModeScenarios VALUES(?,?,?)""",("Test4b","test4.txt", "Theory"))
    cur.execute("""INSERT INTO learnModeScenarios VALUES(?,?,?)""",("Test5b","test5.txt", "Theory"))
    cur.execute("""INSERT INTO learnModeScenarios VALUES(?,?,?)""",("Test6b","test6.txt", "Theory"))
    conn.commit()
    conn.close()




    