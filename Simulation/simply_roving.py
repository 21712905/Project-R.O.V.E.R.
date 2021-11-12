import math
import enum
import csv
import datetime
import pygame
import os

from pygame import image

WHITE = (255, 255, 255)
RED = (255, 0, 0)
BLUE = ( 0, 0, 255)
GREEN = ( 0, 255, 0)
BLACK = (0, 0, 0)
DARK_GREEN    = (0, 128, 0)
WIDTH, HEIGHT = 900, 500
ROVER_WIDTH, ROVER_HEIGHT = 30, 30
ROVER_START_X, ROVER_START_Y = 400, 200
WAYPOINT_PROXIMITY = 20
FPS = 60
WIN = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Simply Roving")
pygame.font.init()



current_dir = os.path.dirname(os.path.abspath(__file__))
image_path = os.path.join(current_dir, "rover_image.png")
original_rover = pygame.image.load(image_path)
original_rover = pygame.transform.scale(original_rover, (ROVER_WIDTH,ROVER_HEIGHT))
image_path = os.path.join(current_dir, "battery_life.png")
battery_life_text_image = pygame.image.load(image_path)
font = pygame.font.Font("C:\Windows\Fonts\ARIALN.TTF", 20)
time_text = font.render("", True, BLACK, WHITE)
textRect = time_text.get_rect()

class direction (enum.Enum):
    forward = 1
    backward = 2
    left = 3
    right = 4

class turn (enum.Enum):
    turn_left = 1
    turn_right = 2

def rotate_rover_image(angle, rover_image):
    test = pygame.transform.rotate(pygame.transform.scale(rover_image, (ROVER_WIDTH,ROVER_HEIGHT)), angle)
    return test

def draw_window(rover_information, waypoints, position_history, obstacles):        
    WIN.fill(WHITE)
    
    barSize     = (200, 20)
    barPos      = ((WIDTH-barSize[0] - 10), (barSize[1]*2))
    textPos     = (barPos[0], barPos[1] - 15)
    timePos     = (barPos[0], barPos[1]*2)
    charge_pos  = (10, 5)

    for obstacle in obstacles:
        pygame.draw.circle(WIN, BLACK, (obstacle[0], obstacle[1]), obstacle[2], 0)

    for waypoint in waypoints:
        pygame.draw.circle(WIN, BLUE, waypoint, 2, 0)
        pygame.draw.circle(WIN, BLUE, waypoint, WAYPOINT_PROXIMITY, 1)
    for position in position_history:
        pygame.draw.circle(WIN, RED, position, 1, 0)
    WIN.blit(rover_information["rover_image"], (rover_information["x_position"] - ROVER_WIDTH/2, rover_information["y_position"] - ROVER_HEIGHT/2))

    pygame.draw.rect(WIN, BLACK, (barPos, barSize), 1)
    innerPos  = (barPos[0]+3, barPos[1]+3)
    innerSize = ((barSize[0]-6) * rover_information["current_battery_life"]/rover_information["full_battery_life"], barSize[1]-6)
    pygame.draw.rect(WIN, DARK_GREEN, (innerPos, innerSize))
    WIN.blit(battery_life_text_image, textPos)

    
    textRect.center = timePos
    time_text = font.render("Days: " + str(rover_information["mission_days_elapsed"]) + " Time: " + str(rover_information["hours"]) + ":" + str(rover_information["minutes"]) + ":" + str(rover_information["seconds"]), True, BLACK, WHITE)
    WIN.blit(time_text, textRect)

    if(rover_information["charging"]):
        charging_text = font.render("Charging, I will resume mission when fully charged.", True, BLACK, WHITE)
        WIN.blit(charging_text, charge_pos)
        recharge_text = font.render("Press spacebar to automatically recharge.", True, BLACK, WHITE)
        WIN.blit(recharge_text, (charge_pos[0], charge_pos[1]+  23))

    pygame.display.update()


#Constricts rover to only be able to turn (maximum_heading_adjustment) at a time
#Also turns the rover in the direction which requires the shortest turn
def dampen_turn(rover_information):
    if(abs(rover_information["current_heading"] - rover_information["previous_heading"]) > rover_information["maximum_heading_adjustment"]):
        if(rover_information["current_heading"] >= 0 and rover_information["previous_heading"] >= 0):
            if((rover_information["current_heading"] - rover_information["previous_heading"]) > rover_information["maximum_heading_adjustment"]):
                rover_information["current_heading"] = rover_information["previous_heading"] + rover_information["maximum_heading_adjustment"]
            elif((rover_information["previous_heading"] - rover_information["current_heading"]) > rover_information["maximum_heading_adjustment"]):
                rover_information["current_heading"] = rover_information["previous_heading"] - rover_information["maximum_heading_adjustment"]

        elif(rover_information["current_heading"] <= 0 and rover_information["previous_heading"] <= 0):
            if((rover_information["current_heading"] - rover_information["previous_heading"]) < -rover_information["maximum_heading_adjustment"]):
                rover_information["current_heading"] = rover_information["previous_heading"] - rover_information["maximum_heading_adjustment"]
            elif((rover_information["previous_heading"] - rover_information["current_heading"]) < -rover_information["maximum_heading_adjustment"]):
                rover_information["current_heading"] = rover_information["previous_heading"] + rover_information["maximum_heading_adjustment"]

        elif(rover_information["current_heading"] >= 0 and rover_information["previous_heading"] <= 0):
            theta = rover_information["current_heading"] - rover_information["previous_heading"]
            if(theta > math.pi):
                if((2*math.pi - theta) > rover_information["maximum_heading_adjustment"]):
                    rover_information["current_heading"] = rover_information["previous_heading"] - rover_information["maximum_heading_adjustment"]
            elif(theta > rover_information["maximum_heading_adjustment"]):
                rover_information["current_heading"] = rover_information["previous_heading"] + rover_information["maximum_heading_adjustment"]

        elif(rover_information["current_heading"] <= 0 and rover_information["previous_heading"] >= 0):
            theta = rover_information["previous_heading"] - rover_information["current_heading"]
            if(theta > math.pi):
                if((2*math.pi - theta) > rover_information["maximum_heading_adjustment"]):
                    rover_information["current_heading"] = rover_information["previous_heading"] + rover_information["maximum_heading_adjustment"]
            elif(theta > rover_information["maximum_heading_adjustment"]):
                rover_information["current_heading"] = rover_information["previous_heading"] - rover_information["maximum_heading_adjustment"]
    rover_information["current_heading"] = normalise_heading(rover_information["current_heading"])
    return rover_information

#Moves rover a distance of (rover_speed*time) in the direction of (rover_heading)
def move_rover (rover_information, dt):
    if(rover_information["current_heading"] > 0 and rover_information["current_heading"] <= math.pi/2):
        rover_information["x_position"] = rover_information["x_position"] + math.sin(rover_information["current_heading"])*rover_information["speed"]*dt
        rover_information["y_position"] = rover_information["y_position"] - math.cos(rover_information["current_heading"])*rover_information["speed"]*dt

    elif(rover_information["current_heading"] > math.pi/2 and rover_information["current_heading"] <= math.pi):
        rover_information["x_position"] = rover_information["x_position"] + math.cos(rover_information["current_heading"] - math.pi/2)*rover_information["speed"]*dt
        rover_information["y_position"] = rover_information["y_position"] + math.sin(rover_information["current_heading"] - math.pi/2)*rover_information["speed"]*dt

    elif(rover_information["current_heading"] <= 0 and rover_information["current_heading"] > -math.pi/2 ):
        rover_information["x_position"] = rover_information["x_position"] + math.sin(rover_information["current_heading"])*rover_information["speed"]*dt
        rover_information["y_position"] = rover_information["y_position"] - math.cos(rover_information["current_heading"])*rover_information["speed"]*dt

    elif(rover_information["current_heading"] <= -math.pi/2 and rover_information["current_heading"] > -math.pi):
        rover_information["x_position"] = rover_information["x_position"] - math.cos(rover_information["current_heading"] + math.pi/2)*rover_information["speed"]*dt
        rover_information["y_position"] = rover_information["y_position"] - math.sin(rover_information["current_heading"] + math.pi/2)*rover_information["speed"]*dt

    rover_information["x_position"] = truncate4(rover_information["x_position"])
    rover_information["y_position"] = truncate4(rover_information["y_position"])
    return rover_information
    
#Adjust rover heading 45 degrees in specified direction
def turn_45_degrees (turn_direction, rover_information):

    if(turn_direction == turn.turn_right):
        rover_information["current_heading"] = rover_information["current_heading"] + math.pi/4

    elif(turn_direction == turn.turn_left):
        rover_information["current_heading"] = rover_information["current_heading"] - math.pi/4

    rover_information["current_heading"] = normalise_heading(rover_information['current_heading'])
    return rover_information

#Updates rover's sensor distances if something is detected
def update_sensors(rover_information, obstacles):
    left_sensor_heading = rover_information["current_heading"] - math.pi/6
    left_sensor_heading = normalise_heading(left_sensor_heading)
    right_sensor_heading = rover_information["current_heading"] + math.pi/6
    right_sensor_heading = normalise_heading(right_sensor_heading)
    centre_sensor_heading = rover_information["current_heading"]
    rear_sensor_heading = rover_information["current_heading"] + math.pi
    rear_sensor_heading = normalise_heading(rear_sensor_heading)

    rover_information["previous_left_sensor_distance"] = rover_information["left_sensor_distance"]
    rover_information["previous_right_sensor_distance"] = rover_information["right_sensor_distance"]
    rover_information["previous_centre_sensor_distance"] = rover_information["centre_sensor_distance"]


    for obstacle in obstacles:
        obstacle_heading = calculate_heading(obstacle[0], obstacle[1],rover_information["x_position"], rover_information["y_position"])

        if((obstacle_heading > (left_sensor_heading - math.pi/12)) and (obstacle_heading < (left_sensor_heading + math.pi/12))):
            buff = calculate_distance(obstacle[0], obstacle[1], rover_information["x_position"], rover_information["y_position"]) - obstacle[2]
            if(buff < rover_information["left_sensor_distance"]):
                rover_information["left_sensor_distance"] = buff
        
        if((obstacle_heading > (centre_sensor_heading - math.pi/12)) and (obstacle_heading < (centre_sensor_heading + math.pi/12))):
            buff = calculate_distance(obstacle[0], obstacle[1], rover_information["x_position"], rover_information["y_position"]) - obstacle[2]
            if(buff < rover_information["centre_sensor_distance"]):
                rover_information["centre_sensor_distance"] = buff

        if((obstacle_heading > (right_sensor_heading - math.pi/12)) and (obstacle_heading < (right_sensor_heading + math.pi/12))):
            buff = calculate_distance(obstacle[0], obstacle[1], rover_information["x_position"], rover_information["y_position"]) - obstacle[2]
            if(buff< rover_information["right_sensor_distance"]):
                rover_information["right_sensor_distance"] = buff
    
    if(rover_information["left_sensor_distance"] == rover_information["previous_left_sensor_distance"]):
        rover_information["left_sensor_distance"] = 400

    if(rover_information["right_sensor_distance"] == rover_information["previous_right_sensor_distance"]):
        rover_information["right_sensor_distance"] = 400

    if(rover_information["centre_sensor_distance"] == rover_information["previous_centre_sensor_distance"]):
        rover_information["centre_sensor_distance"] = 400

    return rover_information

#Keeps heading between -pi and pi
def normalise_heading(heading):
        if heading > math.pi:
            heading = - ( 2*math.pi - heading)
        elif heading < -math.pi:
            heading = 2*math.pi + heading
        return heading

def truncate4(n):
    return int(n*10000)/10000

def truncate2(n):
    return int(n*100)/100

#Returns distancee between two points
def calculate_distance(x1, y1, x2, y2):
    x_distance = abs(x1 - x2)
    y_distance = abs(y1 - y2)
    distance = math.sqrt(x_distance**2 + y_distance**2)
    return distance

#Returns heading FROM (x2;y2) TO (x1;y1)
def calculate_heading(x1, y1, x2, y2):

    x_distance = abs(x1 - x2)
    y_distance = abs(y1 - y2)
    heading = 0

    if ((x1 > x2) & (y1 > y2)):
        # heading = math.atan(x_distance/y_distance)
        heading = math.atan(y_distance/x_distance) + math.pi/2

    elif ((x1 < x2) & (y1 > y2)):
        # heading = -math.atan(x_distance/y_distance)
        heading = -(math.atan(y_distance/x_distance) + math.pi/2)

    elif ((x1 < x2) & (y1 < y2)):
        # heading = -(math.atan(y_distance/x_distance) + math.pi/2)
        heading = -math.atan(x_distance/y_distance)

    elif ((x1 > x2) & (y1 < y2)):
        # heading = math.atan(y_distance/x_distance) + math.pi/2
        heading = math.atan(x_distance/y_distance)

    return heading

def adjust_heading_for_collisions(rover_information):

    max_heading_adjustment = math.pi/4

    if(rover_information["direction"] == direction.forward):
        if(rover_information["centre_sensor_distance"] < rover_information["rover_proximity"] ):
            adjustment = max_heading_adjustment*(1/rover_information["rover_proximity"])*(rover_information["rover_proximity"] - rover_information["centre_sensor_distance"])
            if(rover_information["right_sensor_distance"] > rover_information["left_sensor_distance"]):
                rover_information["current_heading"] = rover_information["current_heading"] + adjustment
            else:
                rover_information["current_heading"] = rover_information["current_heading"] - adjustment

        if(rover_information["left_sensor_distance"] < rover_information["rover_proximity"]):
            adjustment = max_heading_adjustment*(1/rover_information["rover_proximity"])*(rover_information["rover_proximity"] - rover_information["left_sensor_distance"])
            rover_information["current_heading"] = rover_information["current_heading"] + adjustment

        if(rover_information["right_sensor_distance"] < rover_information["rover_proximity"]):
            adjustment = max_heading_adjustment*(1/rover_information["rover_proximity"])*(rover_information["rover_proximity"] - rover_information["right_sensor_distance"])
            rover_information["current_heading"] = rover_information["current_heading"] - adjustment

        rover_information["current_heading"] = normalise_heading(rover_information["current_heading"])

    elif(rover_information["direction"] == direction.backward):
        if(rover_information["rear_sensor_distance"] < rover_information["rover_proximity"] ):
            pass

    return rover_information

#Calculates current usage
#The motors of the rover draw less current to turn because the motors will be slowed down to turn the rover
#The 'if' statements are to adress edge cases that are caused by the heading plane
def calculate_current_usage(rover_information):

    if( -rover_information["maximum_heading_adjustment"] <= rover_information["previous_heading"] <= 0 and rover_information["current_heading"] >= 0):
        rover_information["total_current_drawn"] = ((rover_information["maximum_heading_adjustment"] - abs(rover_information["current_heading"]) - abs(rover_information["previous_heading"]) )/rover_information["maximum_heading_adjustment"])*rover_information["maximum_motor_current"]*3
    elif( 0 <= rover_information["previous_heading"] <= rover_information["maximum_heading_adjustment"] and rover_information["current_heading"] <= 0):
        rover_information["total_current_drawn"] = ((rover_information["maximum_heading_adjustment"] - abs(rover_information["current_heading"]) - abs(rover_information["previous_heading"]) )/rover_information["maximum_heading_adjustment"])*rover_information["maximum_motor_current"]*3
    elif( -math.pi <= rover_information["previous_heading"] <= -(math.pi - rover_information["maximum_heading_adjustment"]) and rover_information["current_heading"] >= 0):
        rover_information["total_current_drawn"] = ((rover_information["maximum_heading_adjustment"] - ( 2*math.pi - abs(rover_information["current_heading"]) - abs(rover_information["previous_heading"])) )/rover_information["maximum_heading_adjustment"])*rover_information["maximum_motor_current"]*3
    elif(math.pi - rover_information["maximum_heading_adjustment"] <= rover_information["previous_heading"] <= math.pi and rover_information["current_heading"] <= 0):
        rover_information["total_current_drawn"] = ((rover_information["maximum_heading_adjustment"] - ( 2*math.pi - abs(rover_information["current_heading"]) - abs(rover_information["previous_heading"])) )/rover_information["maximum_heading_adjustment"])*rover_information["maximum_motor_current"]*3
    else:
        rover_information["total_current_drawn"] = ((rover_information["maximum_heading_adjustment"] - abs((rover_information["current_heading"] - rover_information["previous_heading"])))/rover_information["maximum_heading_adjustment"])*rover_information["maximum_motor_current"]*3

    rover_information["total_current_drawn"] += rover_information["maximum_motor_current"]*3 + rover_information["microcontroller_current_drawn"]
    return rover_information

def reduce_battery(rover_information, dt):
    # buff = rover_information["total_current_drawn"]/(3600*FPS)
    # rover_information["current_battery_life"] = rover_information["current_battery_life"] - buff

    rover_information["current_battery_life"] = rover_information["current_battery_life"] - (rover_information["total_current_drawn"]*dt)
    return rover_information


#Increases battery life with charge relating to time of day
def solar_input(rover_information, dt):
    max_solar_panel_input_current = 1.1
    if(6 <= rover_information["hours"] < 18):
        rover_information["solar_input_current"] = (math.sin(((((rover_information["hours"]-6) + rover_information["minutes"]/60)/12)*180)*math.pi/180)*max_solar_panel_input_current)
        rover_information["current_battery_life"] += rover_information["solar_input_current"]*dt
        return rover_information
    else:
        rover_information["solar_input_current"] = 0
        return rover_information

#Updates the time of the rover
def update_time(rover_information):
    rover_information["hours"] = (int(rover_information["current_time"]/60/60) + rover_information["mission_start_time"]) % 24
    rover_information["minutes"] = int(((rover_information["current_time"]/60/60 - int(rover_information["current_time"]/60/60)))*60)
    rover_information["seconds"] = int((rover_information["current_time"]/60 - int(rover_information["current_time"]/60))*60)

    rover_information["mission_days_elapsed"] = int(((rover_information["current_time"] /60 /60) + rover_information["mission_start_time"]) /24)
    return rover_information

def main():

    position_history = [(ROVER_START_X, ROVER_START_Y)]
    
    #CSV
    #This is to print data to csv file
    # f = open(r'INSERT_CURRENT_DIRECTORY_HERE', 'w', newline='')
    # writer = csv.writer(f)

    rover_information = {
        "full_battery_life":103680,
        "current_battery_life": 103680,
        "x_position" : ROVER_START_X,
        "y_position" : ROVER_START_Y,
        "rover_image": 0,
        "current_heading": 0,
        "previous_heading": 0,
        "maximum_heading_adjustment": math.pi/20,
        "speed": 0.138,
        "friction_coefficient": 0.02,
        "rover_proximity": 100,
        "direction": direction.forward,
        "left_sensor_distance": 400,
        "previous_left_sensor_distance": 400,
        "centre_sensor_distance": 400,
        "previous_centre_sensor_distance": 400,
        "right_sensor_distance": 400,
        "previous_right_sensor_distance": 400,
        "wheel_constants": 0.003216*0.72727272727272, #rolling friction coefficient * torque constant
        "maximum_motor_current": 0.8,
        "total_current_drawn": 0,
        "microcontroller_current_drawn": 0.33,
        "solar_input_current": 0,
        "current_time": 0,
        "hours": 0,
        "minutes": 1,
        "seconds": 0,
        "mission_days_elapsed": 0,
        "mission_start_time": 5,
        "charging": False

    }

    waypoint0 = (600, 400)
    waypoint1 = (400, 200)
    waypoint2 = (300, 300)
    waypoint3 = (200, 100)
    waypoint4 = (800, 200)
    waypoint5 = (200, 420)
    waypoints = [waypoint0, waypoint1, waypoint2, waypoint3, waypoint4, waypoint5]

    obstacle0 = (500, 300, 10)
    obstacle1 = (350, 250, 12)
    obstacle2 = (250, 200, 10)
    obstacle3 = (500, 150, 15)
    obstacle4 = (400, 410, 20)
    obstacle5 = (700, 250, 10)
    obstacles = [obstacle0, obstacle1, obstacle2, obstacle3, obstacle4, obstacle5]

    final_waypoint_reached = False
    waypoint_counter = 0
    waypoint_distance = 1000

    run = True
    clock = pygame.time.Clock()

    while(run):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
        while(final_waypoint_reached == False and run):
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    run = False

            #Waypoint tuple is broken apart for clarity about contents
            waypoint = waypoints[waypoint_counter]
            waypoint_x = waypoint[0]
            waypoint_y = waypoint[1]


            waypoint_distance = math.sqrt((waypoint_x - rover_information["x_position"])**2 + (waypoint_y - rover_information["y_position"])**2)

            while(waypoint_distance > WAYPOINT_PROXIMITY and run):
                clock.tick(FPS)
                dt = clock.get_time() #/1000             #Divide dt by a 1000 to represent real time
                rover_information["current_time"] += dt
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        run = False
                    if event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_SPACE:
                            if(rover_information["charging"] == True):
                                rover_information["current_battery_life"] = rover_information["full_battery_life"]
            
                rover_information = update_time(rover_information)
                rover_information = solar_input(rover_information, dt)

                if(rover_information["current_battery_life"] > 0 and rover_information["charging"] == False):
                    rover_information["previous_heading"] = rover_information["current_heading"]
                    rover_information["current_heading"] = calculate_heading(waypoint[0], waypoint[1], rover_information["x_position"], rover_information["y_position"])
                    rover_information = update_sensors(rover_information, obstacles)
                    rover_information = adjust_heading_for_collisions(rover_information)
                    rover_information = dampen_turn(rover_information)
                    rover_information = calculate_current_usage(rover_information)
                    rover_information = move_rover(rover_information, dt)
                    rover_information = reduce_battery(rover_information, dt)
                else:
                    rover_information["charging"] = True
                    if(rover_information["current_battery_life"] >= rover_information["full_battery_life"] ):
                        rover_information["charging"] = False

                


                position_history.append((rover_information["x_position"], rover_information["y_position"]))
                #############################################################################################################
                #Pygame updates
                rover_information["rover_image"] = rotate_rover_image((-rover_information["current_heading"]*180/math.pi), original_rover)
                draw_window(rover_information, waypoints, position_history, obstacles)
                #############################################################################################################

                waypoint_distance = math.sqrt((waypoint_x - rover_information["x_position"])**2 + (waypoint_y - rover_information["y_position"])**2)
                
                #CSV
                #Prints simulated data to csv file every five in-game minutes
                # if((rover_information["minutes"] % 5) == 0 and 0 < rover_information["seconds"] < 18):
                #     writer.writerow([rover_information["total_current_drawn"], rover_information["total_current_drawn"] - rover_information["microcontroller_current_drawn"], rover_information["microcontroller_current_drawn"], rover_information["solar_input_current"], str(rover_information["hours"]) + ":" + str(rover_information["minutes"])])
                        
            waypoint_counter = waypoint_counter + 1
            if waypoint_counter == len(waypoints):

                #This line creates infinite loop through all waypoints
                waypoint_counter = 0

                #This line creates a single loop through all waypoints
                # final_waypoint_reached = True

        print("I have completed the mission...")
        #CSV
        # f.close()
        run = False
    pygame.quit

if __name__ == "__main__":
    main()
