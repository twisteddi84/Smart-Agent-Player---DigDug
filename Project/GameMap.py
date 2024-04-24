import math

import heapq

# distance between two points
def distance_from(start,end):
    dx = end[0]- start[0]
    dy = end[1] - start[1]
    distance_squared = dx**2 + dy**2
    return int(math.sqrt(distance_squared))

# distance between two points but as sum of x and y differences
def distance_from2(start,end):
    return abs(start[0] - end[0]) + abs(start[1] - end[1])

# given the last and current position of the player, returns the direction
def get_direction(last_pos,current_pos):
    
    dig_dir = 404
    if current_pos[0] - last_pos[0] == 1: # direita
        dig_dir = 1
    elif current_pos[0] - last_pos[0] == -1: # esquerda
        dig_dir = 3  
    elif current_pos[1] - last_pos[1] == 1: # baixo
        dig_dir = 2  
    elif current_pos[1] - last_pos[1] == -1: # cima
        dig_dir = 0

    return dig_dir

# given the current position and direction, returns the next position
def getNextFramePos(actual_pos,dir):
    
    (x,y) = actual_pos
    
    if dir == 0:
        next_pos = (x,y-1)
    elif dir == 1:
        next_pos = (x+1,y)
    elif dir == 2:
        next_pos = (x,y+1)
    elif dir == 3:
        next_pos = (x-1,y)
        
    return next_pos
        
                
# Class used for the A* algorithm, it represents the map of the game as a graph ( python dictionary )   
class GameMap:
    def __init__(self, width, height, costs):
        self.width = width
        self.height = height
        self.costs = costs
        self.graph = self.build_graph()

    def build_graph(self):
        graph = {}

        # Build the initial graph with starting costs for each node
        for x in range(self.width):
            for y in range(self.height):
                node = (x, y)
                graph[node] = []
                for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
                    nx_, ny_ = x + dx, y + dy
                    if 0 <= nx_ < self.width and 0 <= ny_ < self.height:
                        neighbor = (nx_, ny_)
                        cost = self.costs[nx_][ny_]
                        graph[node].append((neighbor, cost))
        return graph
    
    # Heuristic function used for the A* algorithm
    def heuristic(self, node, goal):
        return self.costs[node[0]][node[1]] + self.costs[goal[0]][goal[1]]
           
    # Update the cost of moving to a node
    def update_cost(self, node, new_cost):
        x, y = node
        self.costs[x][y] = new_cost

    # Perform the A* search algorithm on the graph
    def a_star_search(self, start, goal):
        priority_queue = [(0, start, [])]
        visited = set()

        while priority_queue:
            current_cost, current_node, path = heapq.heappop(priority_queue)

            if current_node in visited:
                continue

            visited.add(current_node)
            path = path + [current_node]

            if current_node == goal:
                return path

            for neighbor, cost in self.graph[current_node]:
                if neighbor not in visited:
                    total_cost = current_cost + cost + self.heuristic(neighbor, goal)
                    heapq.heappush(priority_queue, (total_cost, neighbor, path))

        return []


        


