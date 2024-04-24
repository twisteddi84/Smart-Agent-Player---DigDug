import math
import heapq


class Position:
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def __str__(self):
        return "(" + str(self.x) + "," + str(self.y) + ")"

    def __repr__(self):
        return str(self)

    def get_best_neighbor(self, map_size, end):
        x, y = self.x, self.y
        neighbors = []
        for dx, dy in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
            new_x, new_y = x + dx, y + dy
            new_node = Position(new_x, new_y)
            # ingona os "vizinhos" que têm uma distância maior para o destino final
            if 0 <= new_x <= map_size[0] and 0 <= new_y <= map_size[1]:
                if new_node.distance_from(end) < self.distance_from(end):
                    neighbors.append(Position(new_x, new_y))

        return neighbors

    def shortest_path(self, end, forbidden_positions):
            path = []
            current = Position(self.x, self.y)

            while current.x != end.x or current.y != end.y:
                if current.x < end.x and (current.x + 1, current.y) not in forbidden_positions:  # move right
                    current.x += 1
                    path.append(Position(current.x, current.y))
                elif current.y < end.y and (current.x, current.y + 1) not in forbidden_positions:  # move down
                    current.y += 1
                    path.append(Position(current.x, current.y))
                elif current.x > end.x and (current.x - 1, current.y) not in forbidden_positions:  # move left
                    current.x -= 1
                    path.append(Position(current.x, current.y))
                elif current.y > end.y and (current.x, current.y - 1) not in forbidden_positions:  # move up
                    current.y -= 1
                    path.append(Position(current.x, current.y))
                else:
                    # If the path is blocked in both directions, try alternative diagonal directions.
                    if current.x < end.x and current.y < end.y and (current.x + 1, current.y + 1) not in forbidden_positions:
                        current.x += 1
                        current.y += 1
                        path.append(Position(current.x, current.y))
                    elif current.x < end.x and current.y > end.y and (current.x + 1, current.y - 1) not in forbidden_positions:
                        current.x += 1
                        current.y -= 1
                        path.append(Position(current.x, current.y))
                    elif current.x > end.x and current.y < end.y and (current.x - 1, current.y + 1) not in forbidden_positions:
                        current.x -= 1
                        current.y += 1
                        path.append(Position(current.x, current.y))
                    elif current.x > end.x and current.y > end.y and (current.x - 1, current.y - 1) not in forbidden_positions:
                        current.x -= 1
                        current.y -= 1
                        path.append(Position(current.x, current.y))
                    else:
                        # If no available directions, you can handle this situation as needed.
                        # For example, break out of the loop or return an empty path.
                        break

            return path


    def distance_from(self, node):
        dx = node.x - self.x
        dy = node.y - self.y
        distance_squared = dx**2 + dy**2
        return math.sqrt(distance_squared)

    def getDirection(self, past_move):
        if self.x - past_move.x == 1:
            dig_dir = 1

        elif past_move.x - self.x == 1:
            dig_dir = 3

        elif self.y - past_move.y == 1:
            dig_dir = 2

        elif past_move.y - self.y == 1:
            dig_dir = 0

        else:
            dig_dir = 404

        return dig_dir

    def escapeRock(self, rock):
        digdug = self
        key = "w"

        if digdug.x < rock.x:
            key ="w"
        else:
            key = "s"
        if digdug.y < rock.y:
            key = "a"
        else:
            key = "d"
        return key


    def can_shoot_right(self, digdug, danger_zone, to_enemy, dig_dir):
        enemy = self
        if (  ## consegue disparar para a direita
            digdug.x < enemy.x
            and digdug.y == enemy.y
            and dig_dir == 1
            and (enemy.x, enemy.y) in danger_zone
            and all(
                (digdug.x + i, digdug.y) in danger_zone for i in range(0, len(to_enemy))
            )
        ):
            return True
        return False

    def can_shoot_left(self, digdug, danger_zone, to_enemy, dig_dir):
        enemy = self
        if (
            digdug.x > enemy.x
            and digdug.y == enemy.y
            and dig_dir == 3
            and (enemy.x, enemy.y) in danger_zone
            and all(
                (digdug.x - i, digdug.y) in danger_zone for i in range(0, len(to_enemy))
            )
        ):
            return True
        return False

    def can_shoot_up(self, digdug, danger_zone, to_enemy, dig_dir):
        enemy = self
        if (
            digdug.y > enemy.y
            and digdug.x == enemy.x
            and dig_dir == 0
            and (enemy.x, enemy.y) in danger_zone
            and all(
                (digdug.x, digdug.y - i) in danger_zone for i in range(0, len(to_enemy))
            )
        ):
            return True
        return False

    def can_shoot_down(self, digdug, danger_zone, to_enemy, dig_dir):
        enemy = self
        if (
            digdug.y < enemy.y
            and digdug.x == enemy.x
            and dig_dir == 2
            and (enemy.x, enemy.y) in danger_zone
            and all(
                (digdug.x, digdug.y + i) in danger_zone for i in range(0, len(to_enemy))
            )
        ):
            return True
        return False

    def equal(self, posi):
        print(self.x, self.y, posi.x, posi.y)
        print(self.x == posi.x, self.y == posi.y)
        if self.x == posi.x and self.y == posi.y:
            return True
        return False


# Testar Breath First Search

# grid = [48, 24]

# start = Position(0, 0)
# end = Position(5, 5)

# path = start.find_shortest_path(end, grid)
# print(path)
