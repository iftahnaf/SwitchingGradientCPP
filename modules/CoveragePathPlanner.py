from multiprocessing.dummy import freeze_support
import numpy as np
from scipy.spatial import distance

class SwitchingGradientPathPlanning():

    def __init__(self, map):
        self.map = map
        self.tmp_map = map
        self.width = self.map.shape[0]
        self.height = self.map.shape[1]
        initial_pose = np.where(self.map == 2)
        self.initial_pose = [initial_pose[0][0], initial_pose[1][0]]
    
    def check_obstacle(self, pose):
        # Description: checks if pose is on obstacle
        # Inputs: pose - the next robot position.
        # Outputs: return 1 if pose is an obstacle.
        return self.map[pose[0]][pose[1]]

    def check_bounderies(self, pose):
        # Description: if pose is in the given map. return True if it is outside of the map.
        # Inputs: pose - the next robot position.
        # Outputs: return 1 if pose is out of bounds.
        x_bound = False
        y_bound = False
        if pose[0] > self.width-1 or pose[0] < 0 :
            x_bound = True

        if pose[1] > self.height-1 or pose[1] < 0:
            y_bound = True

        return x_bound or y_bound

    def check_visits(self, pose, route):
        # Description: count how many times the robot visited in pose.
        # Inputs: pose - the next robot position.
        #         route - the x,y coordinate list of the robots passed positions.
        # Outputs: counter - how many times the robot visited in the pose.
        counter = 0
        for i in range(len(route[0])):
            if route[1][i] == pose[1] and route[0][i] == pose[0]:
                counter +=  1    
        return counter

    def check_neighbors(self, pose, route, repeat_num=0, dist_map=None):
        # Description: check allowed movments and distances of the next step
        # Inputs: pose - the current robot position.
        #         route - the x,y coordinate list of the robots passed positions.
        #         repeat_num(0 default) - the number of allowed visits per coordinate
        #         dist_map(None default) - the distances map
        # Outputs: movments - 1d array, order: right, left, up down. 1 is allowed movment.
        #          distances - 1d array, same order as movement, represents the distance number of each position.
        right = [pose[0] + 0, pose[1] + 1]
        left = [pose[0] + 0, pose[1] - 1]
        up = [pose[0] - 1, pose[1] + 0]
        down = [pose[0] + 1, pose[1] + 0]

        neighbors = [right, left, up, down]

        movements = []
        distances = []

        for neighbor in neighbors:
            if self.check_bounderies(neighbor):
                movements.append(0)
                distances.append(0)
                continue
            if self.check_obstacle(neighbor):
                movements.append(0)
                distances.append(0)
                continue
            if self.check_visits(neighbor, route) > repeat_num:
                movements.append(0)
                distances.append(0)
                continue

            movements.append(1)
            distances.append(dist_map[neighbor[0], neighbor[1]])  

        return movements, distances
    
    def calculate_distance_map(self, current_pose=[0, 0], method="round"):
        # Description: create a distance 2d map, round the norm of the distance.
        # Outputs: map - 2d array, each element is some distance from the starting point.
        map = np.ones([self.width, self.height])
        for i in range(self.width):
            for j in range(self.height):
                if self.tmp_map[i][j] != 1:
                    distance = [current_pose[0] - i, current_pose[1] -j]
                    if method in "round":
                        map[i][j] = np.round(np.linalg.norm(distance)) + 2
                    else:
                        map[i][j] = np.linalg.norm(distance) + 2
        self.max_dist = np.max(map)
        return map
    
    # def direct_backtracking(self, current_pose, visit_map, dist_map, x, y):
    #     done = False
    #     min_value = 10000
    #     free_squares = np.where(visit_map == 0)
    #     new_dist_map = dist_map(current_pose=current_pose)
    #     for free_square in free_squares:
    #         if new_dist_map[free_square] < min_value:
    #             min_value = new_dist_map[free_squares]
    #             dest = free_square
    #     x_moves = dest[0] - current_pose[0]
    #     y_moves = dest[1] - current_pose[1]
    #     for i in range(x_moves):
    #         if not self.check_bounderies():
    #             x.append(x+i)
            




    def iftach_switching_gradient(self, movement, distances, dir="up"):
        # Description: decide what the next move should be, I call it iftach switching gradient method.
        # we move along the gradient of the distances map, when we reach the end of the map start move along the negative gradient of the distances map.
        # also, if two direction has the same values, we check which has most visited and take the other one(in the path_planning function). inspired by the wavefront CPP method.
        # Inputs: movement - 1d array with the allowed direction of movment.
        #         distances - 1d array with the distances of each movement. 0 for prohibited movement.
        # Outputs: indx - the index number of the choosen movement.
        indx = 0
        if dir in "up":
            max_distance = 0
            for counter, move in enumerate(movement):
                if move:
                    if distances[counter] > max_distance:
                        max_distance = distances[counter]
                        indx = counter
            return indx
        else:
            min_distance = 10000
            for counter, move in enumerate(movement):
                if move:
                    if distances[counter] <= min_distance:
                        min_distance = distances[counter]
                        indx = counter
            return indx  

    def path_planning(self,max_repeat=10, gradient_dir=0, switch_dir="randomly", method="round"):
        # Description: iteratively calls iftach switching gradient and updates the route accordingly. allowed repeated
        # visiting is reseting every time there is a new movement allowed.
        # Inputs:  max_repeat(default 10) - the maximum allowed of repeats per square.
        #          gradient_dir (default 0) - gradient direction, 0 - up, 1 - down.
        #          switch_dir (default "randomly") - how to change the gradient dir when stuck.
        # Outputs: x,y - list of the coordinates during the lawn mowing.
        #           steps - the number of steps to fully cover the map.
        #           unnecessary_steps - the number of steps the robot did on an visited coordinate.
        #           grad_dir_along_path - a list of the gradient direction along the path.
        #           1/0 - 1 if the robot successfully covered the map.
        visit_map = np.zeros([self.width, self.height])
        visit_map = np.where(self.map == 1, 1, 0)
        visit_map[self.initial_pose[0]][self.initial_pose[1]] = 1
        dist_map = self.calculate_distance_map(current_pose=self.initial_pose, method=method)
        x = []
        y = []
        grad_dir_along_path = []
        x.append(self.initial_pose[1])
        y.append(self.initial_pose[0])

        unnecessary_steps  = 0
        steps = 0
        done = 0

        movement, distances = self.check_neighbors(self.initial_pose, [y, x], dist_map=dist_map)

        while not done:
            repeat_num = 0
            grad_dir_along_path.append(np.float(gradient_dir))
            if not gradient_dir:
                indx = self.iftach_switching_gradient(movement, distances, "up")
            else:
                indx = self.iftach_switching_gradient(movement, distances, "down")

            if indx == 0:              
                x.append(x[-1] + 1)
                y.append(y[-1] + 0)
            if indx == 1:
                x.append(x[-1] - 1)
                y.append(y[-1] - 0)
            if indx == 2:
                x.append(x[-1] + 0)
                y.append(y[-1] - 1)
            if indx == 3:
                x.append(x[-1] - 0)
                y.append(y[-1] + 1)

            visit_map[y[-1]][x[-1]] = visit_map[y[-1]][x[-1]] +1 
            if visit_map[y[-1]][x[-1]] > 1:
                unnecessary_steps += +1
            steps +=  1
            movement, distances  = self.check_neighbors([y[-1], x[-1]], [y, x], repeat_num, dist_map=dist_map)

            if ( visit_map != 0 ).all(): # stopping condition
                done = True 

            if switch_dir not in "randomly":
                not gradient_dir if all(dir == 0 for dir in movement) else gradient_dir 

            while all(dir == 0 for dir in movement): # stucking condition
                repeat_num += 1
                if switch_dir in "randomly":
                    gradient_dir = not gradient_dir
                movement, distances  = self.check_neighbors([y[-1], x[-1]], [y, x], repeat_num, dist_map=dist_map)

            if repeat_num > max_repeat:
                break

        return x, y, steps, unnecessary_steps, grad_dir_along_path, done

    def switching_gradient_planning(self):
        # Description: calles path_planning method with different hyper-parameters for the same map. 
        # return the shortest solution. 
        # Outputs: x,y - list of the coordinates during the lawn mowing.
        #           steps - the number of steps to fully cover the map.
        #           unnecessary_steps - the number of steps the robot did on an visited coordinate.
        #           1/0 - 1 if the robot successfully covered the map.
        gradient_dir = [0, 1]
        switch_dir = ["randomly", "one_per_stuck"]
        dist_method = ["round", "direct"]
        steps_shortest = 10000
        for i in gradient_dir:
            for j in switch_dir:
                for k in dist_method:
                    x, y, steps, unnecessary_steps, grad_dir_along_path, done = self.path_planning(gradient_dir=i, switch_dir=j, method=k)
                    if done:
                        if steps_shortest > steps:
                            steps_shortest = steps
                            unnecessary_steps_shortest = unnecessary_steps
                            x_shortest = x
                            y_shortest = y
                            hyper_parameters = {i, j, k}
                            grad_dir_along_path_shortest = grad_dir_along_path
                    self.__init__(self.map)
        return x_shortest, y_shortest, steps_shortest, unnecessary_steps_shortest, grad_dir_along_path_shortest, hyper_parameters, done


    def online_planning(self):
        # ********** EXPERIMENTAL FOR DEVELOPERS ONLY ;) **********
        # Description: an online option when the map is not given.
        # Outputs: x,y - list of the coordinates during the lawn mowing.
        #           steps - the number of steps to fully cover the map.
        dist_map = np.zeros([self.width, self.height])
        x = []
        y = []
        x.append(self.initial_pose[1])
        y.append(self.initial_pose[0])
        movement, _ = self.check_neighbors(self.initial_pose, [y, x], dist_map=dist_map)
        repeat_num = 0
        steps = 0
        while not self.done:
            
            while movement[0] and not movement[1]:
                steps = steps + 1
                x.append(x[-1] + 1)
                y.append(y[-1] + 0)
                movement, _  = self.check_neighbors([y[-1], x[-1]], [y, x], repeat_num, dist_map=dist_map)

            while movement[2]:
                steps = steps + 1
                x.append(x[-1] + 0)
                y.append(y[-1] - 1)
                movement, _  = self.check_neighbors([y[-1], x[-1]], [y, x], repeat_num, dist_map=dist_map)

            while movement[1]:
                steps = steps + 1
                x.append(x[-1] - 1)
                y.append(y[-1] - 0)
                movement, _  = self.check_neighbors([y[-1], x[-1]], [y, x], repeat_num, dist_map=dist_map)

            while movement[3]:
                steps = steps + 1
                x.append(x[-1] - 0)
                y.append(y[-1] + 1)
                movement, _  = self.check_neighbors([y[-1], x[-1]], [y, x], repeat_num, dist_map=dist_map)
                if movement[1]:
                    break

            if all(dir == 0 for dir in movement):
                repeat_num = repeat_num + 1
                movement, _  = self.check_neighbors([y[-1], x[-1]], [y, x], repeat_num, dist_map=dist_map)

            if not np.where(self.map == 0) or repeat_num > 2:
                return x, y, steps,_, 0