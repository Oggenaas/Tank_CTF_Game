import pygame
from pygame.locals import *
from pygame.color import *
import pymunk
import sound

#----- Initialisation -----#


#-- Initialise the display
pygame.init()
pygame.display.set_mode()
pygame.mixer.init()

#-- Initialise the clock
clock = pygame.time.Clock()


#-- Initialise the physics engine
space = pymunk.Space()
space.gravity = (0.0,  0.0)
space.damping = 0.1 # Adds friction to the ground for all objects


#-- Import from the ctf framework
import ai
import images
import gameobjects
import maps


#-- Constants
FRAMERATE = 50


#-- Background music
#sound.background_music()


#--   Define the current level
current_map         = maps.map0


# --  List of all game objects
game_objects_list   = []
tanks_list          = []
ai_list             = []
explosion_group = pygame.sprite.Group()


# -- GAMEPLAY MODS
unfair_ai = False
multiplayer = False
fog_of_war = False
win_condition_options = ["score_limit", "time_limit", "round_limit"]
win_condition = win_condition_options[1]


#-- Resize the screen to the size of the current level
screen = pygame.display.set_mode(current_map.rect().size)


def generate_the_background():
    """
    This function generate the background for the diffrent maps and will Copy 
    the grass title all over the level area. The call to the function "blit will 
    copy the image, contained in "images.grass" into the "background
    image at the coordinates given as the seconde argument
    """

    background = pygame.Surface(screen.get_size())

    for x in range(0, current_map.width):
        for y in range(0, current_map.height):
            background.blit(images.grass, (x*images.TILE_SIZE, y*images.TILE_SIZE))
   
    return background


def create_walls():
    """
    The function creates four statics body to act as borders around 
    the map, so you can get out of bounds when playing. segments added
    to the space
    """
    
    wall_north = pymunk.Segment(space.static_body, (0,0), (current_map.width,0),0.0)
    wall_east = pymunk.Segment(space.static_body, (current_map.width,0),(current_map.width,current_map.height),0.0)
    wall_south = pymunk.Segment(space.static_body, (current_map.width,current_map.height),(0, current_map.height),0.0)
    wall_west = pymunk.Segment(space.static_body, (0, current_map.height), (0,0),0.0)

    space.add(wall_north,wall_east,wall_south,wall_west)
    
    wall_north.collision_type = 4
    wall_east.collision_type = 4
    wall_south.collision_type = 4
    wall_west.collision_type = 4


def bullet_hits_wall(arb, space, data):
    """
    This function handles collisions between the two bodies bullet and walls 
    and remove the game object bullets when collision happens
    """

    if arb.shapes[0].parent in game_objects_list:
        game_objects_list.remove(arb.shapes[0].parent)
        space.remove(arb.shapes[0], arb.shapes[0].body)
    
    return False

Bullet_wall = space.add_collision_handler(1, 4)
Bullet_wall.begin = bullet_hits_wall
   

def collision_bullet_boxes(arb,space,data):
    """
    This function handles collisions between the two bodies bullet and boxes 
    and remove the game object bullet and the box if it's a wooden box
    when collision happens
    """

    bullet = arb.shapes[0].parent
    box = arb.shapes[1].parent
    
    
    if arb.shapes[0].parent in game_objects_list:
        game_objects_list.remove(arb.shapes[0].parent)
        space.remove(arb.shapes[0], arb.shapes[0].body)
        
    if arb.shapes[1].parent.destructable:
        explosion = gameobjects.Explosion(box.body.position[0] * 40, box.body.position[1] * 40, 1)
        explosion_group.add(explosion)
        
        game_objects_list.remove(arb.shapes[1].parent)
        space.remove(arb.shapes[1],arb.shapes[1].body)
    
    
    return True

bullet_box = space.add_collision_handler(1,3)
bullet_box.pre_solve = collision_bullet_boxes


def health_bar():
    """
    This function create a surface acting as a Hp-bar over the 
    players tank, that changes colours depening on your hp
    """

    health_bar = pygame.Surface((20,5)) # creates the surface
    for tank in tanks_list:
           
        
        
            if tank.player_health >= 3:
                health_bar.fill('green')
                
            if tank.player_health == 2:
                health_bar.fill('orange')
                
            if tank.player_health == 1:
                health_bar.fill('red')
                
            screen.blit(health_bar,(tank.body.position.x * images.TILE_SIZE, tank.body.position.y * images.TILE_SIZE))


def collision_bullet_tank(arb, space, data):
    """
    This function handles collisions between the two bodies bullet and tanks 
    and remove the game objects when destroyed, it also handel the reset of the tank
    when your hp reaches 0.
    """
    
    bullet = arb.shapes[0].parent
    tank = arb.shapes[1].parent
    explosion = gameobjects.Explosion(tank.body.position[0] * 40, tank.body.position[1] * 40, 2)
    explosion_group.add(explosion)
    
   
    if bullet in game_objects_list:
        game_objects_list.remove(bullet)
        space.remove(arb.shapes[0], arb.shapes[0].body)
        sound.shoot_sound()

        
       
        tank.player_health -= 1
      
        if tank.player_health <= 0: #Activates when tanks get destroyed
            sound.explosion_sound()
            explosion = gameobjects.Explosion(tank.body.position[0] * 40, tank.body.position[1] * 40, 3)
            explosion_group.add(explosion)

            tank.player_health = 3


            if tank.flag != None:
                flag.is_on_tank = False
                tank.flag = None
                       
            tank.spawn_reset()        
        space.remove(arb.shapes[0], arb.shapes[0].body)
        
    return False

bullet_tank = space.add_collision_handler(1,2)
bullet_tank.pre_solve = collision_bullet_tank


def create_boxes():
    """
    This function loops throught the map grid to check where 
    and what kind of box to create on specific coordinates
    """
    for x in range(0, current_map.width):
        for y in range(0, current_map.height): 
            box_type = current_map.boxAt(x,y) 
    
            if(box_type != 0 ):
                box = gameobjects.get_box_with_type(x, y, box_type, space)
                game_objects_list.append(box)


def create_bases():
    """
    This function loops throught current_map to get the starting positions for the 
    bases, and adds the pictures of the base from images.bases into gameobjects.gamevisbleobject
    """
   
    for i in range(0, len(current_map.start_positions)):   
        base_position = current_map.start_positions[i]    
        base = gameobjects.GameVisibleObject(base_position[0],base_position[1], images.bases[i])
        game_objects_list.append(base)

      
def create_tanks():
    """
    This function loops throught current map to get tanks starting position,
    and add them into there respective list for tanks and ai. 
    """

    for i in range(0, len(current_map.start_positions)):
        pos = current_map.start_positions[i]
        tank = gameobjects.Tank(pos[0], pos[1], pos[2], images.tanks[i], space)
        tanks_list.append(tank)
        game_objects_list.append(tank)

            
            
            
        if not multiplayer:

            if i != 0: # To control if the ai is buffed or not

                if unfair_ai == True:

                    tank.unfair_ai_stats()

                    ai_instance = ai.Ai(tank,  game_objects_list, tanks_list, space, current_map)

                    ai_list.append(ai_instance)

                else:

                    #Else create normal ai:s

                    ai_instance = ai.Ai(tank,  game_objects_list, tanks_list, space, current_map)

                    ai_list.append(ai_instance)

        if multiplayer:

                if i > 1:

                    if unfair_ai == True and i != 0 and i!= 1:

                        tank.unfair_ai_stats()

                        ai_instance = ai.Ai(tank, game_objects_list, tanks_list, space, current_map)

                        ai_list.append(ai_instance)

                    else:

                        ai_instance = ai.Ai(tank, game_objects_list, tanks_list, space, current_map)

                        ai_list.append(ai_instance)


def create_flag():
    """
    The function create the flag and places it on its starting position
    depending on current map and adds it too the game_objects_list
    """
    
    flag = gameobjects.Flag(current_map.flag_position[0], current_map.flag_position[1])
    game_objects_list.append(flag)
    return flag 

flag = create_flag()
  

def flag_function(flag):
    """
    The function handles diffrent flag functions like try_grab_flag and has_won
    """
  
    for tank in tanks_list:
        tank.try_grab_flag(flag)

        if tank.has_won():
            sound.victory_sound()
            tank.show_score = 0
            tank.score += 1
            print_score_board(tank)
            flag.is_on_tank = False
            tank.flag = None
            flag.x, flag.y = current_map.flag_position[0], current_map.flag_position[1]
            
    return True


def print_score_board(tank):
    """
    Prints the scoreboard on the screen
    """

    print("\n")
    for tank in range(len(tanks_list)):
        print(f"Player {tank+1}: {tanks_list[tank].score}")


def print_score_on_screen():
    """
    This function handles the settings for the score, e.g how many players, (2 as default) up to +6 players
    """

    score_font = pygame.font.Font(None,50) #font, size
    playerscore_list = []
    num_of_tanks = len(tanks_list)
    tank_name = 1
    
    for tank in tanks_list:
        playerscore_list.append(score_font.render(f'Player{tank_name}: {tank.score}', False, 'White'))
        tank_name += 1
        
    screen.blit(playerscore_list[0],(100,20))
    screen.blit(playerscore_list[1],(100,20*4))
    
    if num_of_tanks >= 4:
        screen.blit(playerscore_list[2],(100,20*8))
        screen.blit(playerscore_list[3],(100,20*12))
    
    if num_of_tanks >= 6:
        screen.blit(playerscore_list[4],(100,20*16))
        screen.blit(playerscore_list[5],(100,20*20))


def display_round_or_time(win_condition):
    """
    The function handles the settings to display ither round or time 
    on screen, depending on what win conditions that are choosen
    """

    test_font = pygame.font.Font(None,50) #font, size
    round = 0
    
    for tank in tanks_list:
        round += tank.score 
    
    if win_condition == "round_limit":
        round_surface = test_font.render(f'{round} / {5}', False, 'White')
        screen.blit(round_surface,(280,20)) # x,y coords
    
    if win_condition == "time_limit":
        time_surface = test_font.render(f'{tanks_list[0].time_limit}', False, 'White')
        screen.blit(time_surface,(280,20))


def winner():
    """
    The function handles the setting for for diffrent win_conditions 
    e.g score_limit, time_limit and round_limit.
    """

    if win_condition == "score_limit": #first to 5 points win
        for tank in tanks_list:
            if tank.score == 5:
                print(f'Player {tanks_list.index(tank)+1} won!')
                return False
        return True

    if win_condition == "time_limit": #player with most points when time runns out win 
        if tanks_list[0].time_limit < 0:
            
            top_scorer = tanks_list[1]
            for tank in tanks_list:
                if tank.score > top_scorer.score:
                    top_scorer = tank
            
                print(f'Player {tanks_list.index(top_scorer)+1} won!')
                return False
        return True

    if win_condition == "round_limit": # player with most points after 5 rounds win 
       
        top_scorer = tanks_list[1]
        res = []
    
        for tank in tanks_list:
            res.append(tank.score)
                       
            if tank.score > top_scorer.score:
                top_scorer = tank
                
            if sum(res) == 5:
                print(f'Player {tanks_list.index(top_scorer)+1} won!')
                return False
            
        return True


def controll_keys(event):
    """
    This function handles the controll_keys for key_down, 
    key_up, shooting and multiplayer 
    """

    if event.type == KEYDOWN:

        if event.key == K_UP:
            tanks_list[0].accelerate()
        if event.key == K_LEFT:
            tanks_list[0].turn_left()
        if event.key == K_RIGHT:
            tanks_list[0].turn_right()
        if event.key == K_DOWN:
            tanks_list[0].decelerate()
        if event.key == K_KP_ENTER:
            bullet = tanks_list[0].shoot(space)
            if bullet != None:
                sound.shoot_second_sound()
                game_objects_list.append(bullet)

        if multiplayer:

            if event.key == K_w:
                tanks_list[1].accelerate()
            if event.key == K_a:
                tanks_list[1].turn_left()
            if event.key == K_d:
                tanks_list[1].turn_right()
            if event.key == K_s:
                tanks_list[1].decelerate()
            if event.key == K_SPACE:
                bullet = tanks_list[1].shoot(space)
                if bullet != None:
                    sound.shoot_second_sound()
                    game_objects_list.append(bullet)


    if event.type == KEYUP:

        if event.key == K_UP:
            tanks_list[0].stop_moving()
        if event.key == K_LEFT:
            tanks_list[0].stop_turning()
        if event.key == K_RIGHT:
            tanks_list[0].stop_turning()
        if event.key == K_DOWN:
            tanks_list[0].stop_moving()

        if multiplayer:
            if event.key == K_w:
                tanks_list[1].stop_moving()
            if event.key == K_a:
                tanks_list[1].stop_turning()
            if event.key == K_d:
                tanks_list[1].stop_turning()
            if event.key == K_s:
                tanks_list[1].stop_moving()


# Calling_functions
create_walls()
create_bases()
create_tanks()
create_boxes()


def create_fog():
    """
    This function create a black mask over the screen and 1 or 2 transparent 
    cirle's depening on soloplayer or multiplayer
    """

    if multiplayer:
        holes_in_fog = [tanks_list[0], tanks_list[1]] 
    
    else: 
        holes_in_fog = [tanks_list[0]]
    
    fog_of_war = pygame.Surface((1000, 1000),SRCALPHA) 
    fog_of_war.fill('black')
    
    for tank in holes_in_fog:
        pygame.draw.circle(fog_of_war, (255 , 255, 255, 0), (tank.body.position.x * images.TILE_SIZE, tank.body.position.y * images.TILE_SIZE),80)
        pygame.draw.circle(fog_of_war, (255 , 255, 255, 20), (tank.body.position.x * images.TILE_SIZE, tank.body.position.y * images.TILE_SIZE),70)
    
    screen.blit(fog_of_war, (0,0))

    
def update_physics(skip_update):  
    """
    This funktions handles all updates for physics-object
    """

    if skip_update == 0:
        
        for obj in game_objects_list:
            obj.update()
        
        skip_update = 2
    
    else:
        skip_update -= 1
  
    #   Check collisions and update the objects position
    space.step(1 / FRAMERATE)

    #   Update object that depends on an other object position (for instance a flag)
    for obj in game_objects_list:
        obj.post_update()
              
    #-- Update Display
    screen.blit(generate_the_background(), (0,0))
    explosion_group.draw(screen)
    explosion_group.update()

    # Update the display of the game objects on the screen
    for obj in game_objects_list:
        obj.update_screen(screen)
        
    for tanks in tanks_list:
        tanks.update_screen(screen)

    health_bar() # must be over fog_of_war

    if fog_of_war:
        create_fog()
    
   

    for tank in tanks_list: # shows the score for ~2 seconds when someone scores
        if tank.show_score < 200:
            print_score_on_screen()
        if win_condition == "round_limit" or win_condition == "time_limit":
            display_round_or_time(win_condition)
    
    #   Redisplay the entire screen (see double buffer technique)
    pygame.display.flip()

    #   Control the game framerate
    clock.tick(FRAMERATE)

  
def main_loop():
    """
    This loop keeps the game running as long as "running" is True
    """

    running = True
    skip_update = 0
    
    while running:
    #-- Handle the events
        update_physics(skip_update)
        
        for ai_instance in ai_list:
            ai.Ai.decide(ai_instance) 
        
        flag_function(flag)
        running = winner()
        for event in pygame.event.get():
            controll_keys(event)
            if event.type == QUIT or (event.type == KEYDOWN and event.key == K_ESCAPE):
                running = False
                   
main_loop()