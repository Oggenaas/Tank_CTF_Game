import math
import pymunk
from pymunk import Vec2d
import gameobjects
from collections import defaultdict, deque


MIN_ANGLE_DIF = math.radians(3) # 3 degrees, a bit more than we can turn each tick


def angle_between_vectors(vec1, vec2):
    """ 
    Since Vec2d operates in a cartesian coordinate space we have to
    convert the resulting vector to get the correct angle for our space.
    """

    vec = vec1 - vec2 
    vec = vec.perpendicular()
    return vec.angle


def periodic_difference_of_angles(angle1, angle2): 
    """
    Function calc the diffrences of two angles and take away extra rotations
    """

    return (angle1 - angle2) % (2*math.pi) 


class Ai:
    """ 
    A simple ai that finds the shortest path to the target using
    a breadth first search. Also capable of shooting other tanks and or wooden
    boxes. 
    """
    
    def __init__(self, tank,  game_objects_list, tanks_list, space, currentmap):
        self.tank               = tank
        self.game_objects_list  = game_objects_list
        self.tanks_list         = tanks_list
        self.space              = space
        self.currentmap         = currentmap
        self.flag = None
        self.MAX_X = currentmap.width - 1 
        self.MAX_Y = currentmap.height - 1


        self.path = deque()
        self.move_cycle = self.move_cycle_gen()
        self.update_grid_pos()


    def update_grid_pos(self):
        """ 
        This should only be called in the beginning, or at the end of a move_cycle. 
        """

        self.grid_pos = self.get_tile_of_position(self.tank.body.position)


    def decide(self):
        """ 
        Main decision function that gets called on every tick of the game. 
        """

        self.maybe_shoot()
        next(self.move_cycle)
        
        
    def maybe_shoot(self):
        """ 
        Makes a raycast query in front of the tank. If another tank
        or a wooden box is found, then we shoot.
        """
         
        start = (self.tank.body.position[0] - math.sin(self.tank.body.angle) * 0.4, self.tank.body.position[1] + math.cos(self.tank.body.angle) * 0.4)
        end = (self.tank.body.position[0] - math.sin(self.tank.body.angle) * 10, self.tank.body.position[1] + math.cos(self.tank.body.angle) * 10)
        beam = self.space.segment_query_first(start, end, 0, pymunk.ShapeFilter(),)

        if hasattr(beam,'shape'):
            if hasattr(beam.shape, 'parent'):             
                result = beam.shape.parent
                      
                if isinstance(result, gameobjects.Tank): # kollar om den tillhör klassen tank
                                
                        bullet = self.tank.shoot(self.space)
                        if bullet != None:
                            self.game_objects_list.append(bullet)   
                    
                if isinstance(result, gameobjects.Box): # kollar om den tillhör klassen box           
                        if result.destructable: # kollar om den är destructable
                           
                            bullet = self.tank.shoot(self.space)
                            if bullet != None:
                                self.game_objects_list.append(bullet)

                else:
                    pass
    

    def move_cycle_gen(self):
        """ 
        A generator that iteratively goes through all the required steps
        to move to our goal.
        """ 
       
        def correct_angle(next_cord):
            """
            Calculate the correct angle with a 3 precent deviation
            """

            angle_diffrence = get_angle_diffrence(next_cord)
            return (abs(angle_diffrence) < math.radians(3))

        
        def get_angle_diffrence(next_cord):
            """
            The function calculate the angle between tanks body position and the next coordinate and 
            the periodic angle calc the diffrences between the angles and remove the excess rotataion
            """

            self_grid_cord = Vec2d(self.tank.body.position)
            return periodic_difference_of_angles(self.tank.body.angle, angle_between_vectors(self_grid_cord, next_cord))

        
        def correct_position():
            """
            correct position if last distance is smaller then current distance or 
            current distance is smaller then 0.1
            """

            correct_position = last_distance < current_distance or current_distance < 0.1
            return correct_position

        
        
        while True:
            
            if not self.path:
                self.path = self.find_shortest_path()
                
                yield
                continue
            
            next_cord = self.path.popleft() + Vec2d(0.5,0.5)
           
            yield
            
            while not correct_angle(next_cord): 
                angle_diffrence = get_angle_diffrence(next_cord)
                self.tank.stop_moving()

                if (0 <= angle_diffrence < math.pi):
                    self.tank.turn_left()
                    
                if (math.pi <= angle_diffrence < 2 * math.pi):
                    self.tank.turn_right()
                
                else: 
                    self.tank.turn_left()
               
                yield

            self.tank.stop_turning()
            
            yield
            
            distance = (self.tank.body.position).get_distance(next_cord)    
            current_distance = distance     
            last_distance = distance        
            
            while not correct_position():
                self.tank.accelerate()
                last_distance = current_distance 
                current_distance = (self.tank.body.position).get_distance(next_cord)

                if current_distance > 2:
                    break
                yield

            self.update_grid_pos()
            self.move_cycle


    def find_shortest_path(self, metal_box = False):
        """ A simple Breadth First Search using integer coordinates as our nodes.
            Edges are calculated as we go, using an external function.
        """
        
        visisted = set()
        queue = deque()
        parent = {}
        shortest_path = deque()
        queue.append(self.grid_pos)
        visisted.add(tuple(self.grid_pos))
         
        while queue:
            node = queue.popleft()
            
            if node == self.get_target_tile():
                
                if parent == {}:          
                    return deque()
                
                shortest_path.append(node)
                element = parent[tuple(node)]
                while element != self.grid_pos:                 
                    shortest_path.appendleft(Vec2d(element))            
                    element = parent[element]         
                break
           
            for neighbour in self.get_tile_neighbors(node, metal_box):
                if tuple(neighbour) not in visisted:
                    visisted.add(tuple(node))
                    queue.append(neighbour)
                    parent[tuple(neighbour)] = tuple(node)        
       
        if not shortest_path:
            return self.find_shortest_path(metal_box = True)
                 
        return shortest_path


    def get_target_tile(self):
        """ Returns position of the flag if we don't have it. If we do have the flag,
            return the position of our home base.
        """

        if self.tank.flag != None:
            x, y = self.tank.start_position
        
        else:
            self.get_flag() # Ensure that we have initialized it.
            x, y = self.flag.x, self.flag.y
        
        return Vec2d(int(x), int(y))


    def get_flag(self):
        """ This has to be called to get the flag, since we don't know
            where it is when the Ai object is initialized.
        """

        if self.flag == None:
        
        # Find the flag in the game objects list
            for obj in self.game_objects_list:
                if isinstance(obj, gameobjects.Flag):
                    self.flag = obj
                    break
        
        return self.flag


    def get_tile_of_position(self, position_vector):
        """ 
        Converts and returns the float position of our tank to an integer position. 
        """

        x, y = position_vector
        return Vec2d(int(x), int(y))


    def get_tile_neighbors(self, coord_vec, metal_box):
        """ 
        Returns all bordering grid squares of the input coordinate.
        A bordering square is only considered accessible if it is grass
        or a wooden box.
        """
        
        north_tile  = coord_vec + Vec2d(0,-1)
        west_tile   = coord_vec + Vec2d(-1,0)
        east_tile   = coord_vec + Vec2d(1,0)
        south_tile  = coord_vec + Vec2d(0,1)
       
        neighbors = [north_tile, west_tile, east_tile, south_tile] 
        
        acceptable_coords = []
        for coord in neighbors:
            if self.filter_tile_neighbors(coord, metal_box) == True:
                acceptable_coords.append(coord)

        return acceptable_coords

    def filter_tile_neighbors (self, coord, metal_box):
        """
        Checks if the tile is within the border of the map, if no path is found 
        it will return and accept metal boxes for shortest path
        """

        if  0 <= coord[0] <= self.MAX_X and 0 <= coord[1] <= self.MAX_Y:           
            box_type = self.currentmap.boxAt(int(coord[0]), int(coord[1]))
            
            if box_type == 0:
                return True

            elif box_type == 2:
                return True
            
            elif metal_box:
                if box_type == 3:
                    return True
            
            else:
                return False


SimpleAi = Ai # Legacy

