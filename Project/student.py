"""Example client."""
import asyncio
import getpass
import json
import os
import random
import time

import websockets

from GameMap import *


async def agent_loop(server_address="localhost:8000", agent_name="student"):
    """Example client loop."""
    async with websockets.connect(f"ws://{server_address}/player") as websocket:
        # Receive information about static game properties
        await websocket.send(json.dumps({"cmd": "join", "name": agent_name}))
        last_dir = 1  # initial direction of digdug ( right )

        i = 0
        while True:
            try:
                state = json.loads(
                    await websocket.recv()
                )  # receive game update, this must be called timely or your game will get out of sync with the server

                key = ""

                ###### Loading a new level ######

                if "digdug" not in state:
                    size = (state["size"][0], state["size"][1])

                    danger_zone = []  # digged blocks
                    rocks = []  # empty list of rocks on new level
                    last_pos = (
                        1,
                        1,
                    )  # initial digdug position for direction calculation
                    costs = [
                        [3 for y_ in range(size[1])] for x_ in range(size[0])
                    ]  # default cost of 3 for all blocks
                    mapa = GameMap(size[0], size[1], costs)  # create a map for search

                    # add all digged blocks at the start to danger zone
                    for i in range(0, size[0]):
                        for j in range(0, size[1]):
                            if state["map"][i][j] == 0:
                                danger_zone.append((i, j))

                    continue

                if not state["enemies"]:  # bugs on level start
                    continue

                digdug_pos = (int(state["digdug"][0]), int(state["digdug"][1]))

                # add digdug position to danger zone if not there already
                danger_zone.append(
                    digdug_pos
                ) if digdug_pos not in danger_zone else None

                # position and direction of all fygars
                fygars = [
                    (enemy["pos"][0], enemy["pos"][1], enemy["dir"])
                    for enemy in state["enemies"]
                    if enemy["name"] == "Fygar"
                ]
                # position and direction of all pookas
                pookas = [
                    (enemy["pos"][0], enemy["pos"][1], enemy["dir"])
                    for enemy in state["enemies"]
                    if enemy["name"] == "Pooka"
                ]
                # position of all rocks
                rocks = [(rock["pos"][0], rock["pos"][1]) for rock in state["rocks"]]

                ##### Update the costs of the map #####

                for position in danger_zone:
                    mapa.update_cost(position, 1)  # cost 1 for all digged blocks

                for rock in rocks:
                    mapa.update_cost(
                        rock, 1000000000
                    )  # very big cost for rocks to not run into them

                for fygar in fygars:
                    mapa.update_cost((fygar[0], fygar[1]), 10000)
                    for pos in range(1, 5):
                        if (
                            (fygar[2] == 1)
                            or ((fygar[0] - 1, fygar[1]) not in danger_zone)
                        ) and (fygar[0] + pos < size[0]):
                            mapa.update_cost(
                                (fygar[0] + pos, fygar[1]), 10000
                            )  # big cost of running to possible fire positions
                        if (
                            (fygar[2] == 3)
                            or ((fygar[0] + 1, fygar[1]) not in danger_zone)
                        ) and (fygar[0] - pos >= 0):
                            mapa.update_cost(
                                (fygar[0] - pos, fygar[1]), 10000
                            )  # big cost of running to possible fire positions

                for pooka in pookas:
                    mapa.update_cost((pooka[0], pooka[1]), 10000)

                #### Calculate digdug actual direction ####
                dig_dir = 404
                if digdug_pos != last_pos:
                    dig_dir = get_direction(last_pos, digdug_pos)
                    last_dir = dig_dir
                    last_pos = digdug_pos

                if dig_dir == 404:
                    dig_dir = last_dir

                # Choose next enemy to kill (closest one)
                next_to_kill = sorted(
                    state["enemies"], key=lambda k: distance_from2(k["pos"], digdug_pos)
                )[0]

                next_to_kill_pos = (next_to_kill["pos"][0], next_to_kill["pos"][1])

                if next_to_kill["name"] == "Fygar":
                    # If its a fygar, go to either up or down of it ( to avoid fire )
                    if checkinbounds((next_to_kill_pos[0] + 1, next_to_kill_pos[1])):
                        go_to = (next_to_kill_pos[0] + 1, next_to_kill_pos[1])
                    else:
                        go_to = (next_to_kill_pos[0] - 1, next_to_kill_pos[1])
                else:
                    # If its a pooka, just go towards it
                    go_to = next_to_kill_pos

                # Get all enemies close to digdug for running and safety purposes
                close_enemies = [
                    (enemy["pos"][0], enemy["pos"][1], enemy["name"], enemy["dir"])
                    for enemy in state["enemies"]
                    if distance_from2(enemy["pos"], digdug_pos) <= 10
                ]

                shoot = False  # By default, dont shoot

                distance_to_enemy = distance_from2(
                    next_to_kill_pos, digdug_pos
                )  # distance to next enemy to kill ( sum of x and y differences in this case )

                if safe_to_shoot(
                    distance_to_enemy
                ):  # decide if its safe to shoot or not
                    if can_shoot(
                        digdug_pos, next_to_kill_pos, dig_dir, danger_zone, rocks
                    ):
                        shoot = True  # if can shoot and hit the enemy, shoot

                if not shoot:
                    # if cant shoot, check if digdug should run from the enemy
                    if should_run(
                        go_to, close_enemies, next_to_kill, digdug_pos, danger_zone
                    ):
                        # if should run, find a safe block to run to
                        go_to = find_closest_safe_block(
                            digdug_pos, close_enemies, rocks
                        )

                    ### If digdug can turn around and shoot the enemy , do it ###

                    if distance_from(digdug_pos, next_to_kill_pos) == 3:
                        possible_pos = (
                            digdug_pos[0] + 1,
                            digdug_pos[1],
                        )  # turn right and shoot
                        if (
                            can_shoot(
                                possible_pos, next_to_kill_pos, 1, danger_zone, rocks
                            )
                            and next_to_kill["dir"] == 3
                        ):
                            go_to = possible_pos

                        possible_pos = (
                            digdug_pos[0] - 1,
                            digdug_pos[1],
                        )  # turn left and shoot
                        if (
                            can_shoot(
                                possible_pos, next_to_kill_pos, 3, danger_zone, rocks
                            )
                            and next_to_kill["dir"] == 1
                        ):
                            go_to = possible_pos

                        possible_pos = (
                            digdug_pos[0],
                            digdug_pos[1] - 1,
                        )  # turn down and shoot
                        if (
                            can_shoot(
                                possible_pos, next_to_kill_pos, 0, danger_zone, rocks
                            )
                            and next_to_kill["dir"] == 2
                        ):
                            go_to = possible_pos

                        possible_pos = (
                            digdug_pos[0],
                            digdug_pos[1] + 1,
                        )  # turn up and shoot
                        if (
                            can_shoot(
                                possible_pos, next_to_kill_pos, 2, danger_zone, rocks
                            )
                            and next_to_kill["dir"] == 0
                        ):
                            go_to = possible_pos

                        #########################################################

                path = mapa.a_star_search(
                    digdug_pos, go_to
                )  # find the shortest path to the next block to go to

                if path == [] or len(path) == 1:  # dont crash if there's no path
                    continue

                next_move = path[1]  # go to the first block of the path

                ### Move digdug to the next block ###

                if next_move[0] > digdug_pos[0]:
                    key = "d"
                elif next_move[0] < digdug_pos[0]:
                    key = "a"
                elif next_move[1] > digdug_pos[1]:
                    key = "s"
                elif next_move[1] < digdug_pos[1]:
                    key = "w"

                ### Shoot if possible ###
                if shoot == True:
                    key = "A"

                await websocket.send(json.dumps({"cmd": "key", "key": key}))
                # send key command to server - you must implement this send in the AI agent

            except websockets.exceptions.ConnectionClosedOK:
                print("Server has cleanly disconnected us")
                return


def can_shoot(digdug_pos, enemy_pos, dig_dir, danger_zone, rocks):
    """
    The agent decides if it can shoot based on the following criteria:
    - They are on the same axis (x or y)
    - Digdug is facing the enemy
    - The enemy is in the danger zone (digged blocks)
    - There are no rocks between them
    """

    if (  # shoot to the right
        (digdug_pos[1] == enemy_pos[1])
        and (digdug_pos[0] < enemy_pos[0])
        and (dig_dir == 1)
        and ((enemy_pos[0], enemy_pos[1]) in danger_zone)
        and all(
            (digdug_pos[0] + i, digdug_pos[1]) in danger_zone
            for i in range(1, enemy_pos[0] - digdug_pos[0])
        )
        and all(
            (digdug_pos[0] + i, digdug_pos[1]) not in rocks
            for i in range(1, enemy_pos[0] - digdug_pos[0])
        )
    ):
        return True

    if (  # shoot to the left
        (digdug_pos[1] == enemy_pos[1])
        and (digdug_pos[0] > enemy_pos[0])
        and (dig_dir == 3)
        and ((enemy_pos[0], enemy_pos[1]) in danger_zone)
        and all(
            (digdug_pos[0] - i, digdug_pos[1]) in danger_zone
            for i in range(enemy_pos[0] - digdug_pos[0], -1)
        )
        and all(
            (digdug_pos[0] - i, digdug_pos[1]) not in rocks
            for i in range(enemy_pos[0] - digdug_pos[0], -1)
        )
    ):
        return True

    if (  # shoot up
        (digdug_pos[0] == enemy_pos[0])
        and (digdug_pos[1] < enemy_pos[1])
        and (dig_dir == 2)
        and ((enemy_pos[0], enemy_pos[1]) in danger_zone)
        and all(
            (digdug_pos[0], digdug_pos[1] + i) in danger_zone
            for i in range(1, enemy_pos[1] - digdug_pos[1])
        )
        and all(
            (digdug_pos[0], digdug_pos[1] + i) not in rocks
            for i in range(1, enemy_pos[1] - digdug_pos[1])
        )
    ):
        return True

    if (  # shoot down
        (digdug_pos[0] == enemy_pos[0])
        and (digdug_pos[1] > enemy_pos[1])
        and (dig_dir == 0)
        and ((enemy_pos[0], enemy_pos[1]) in danger_zone)
        and all(
            (digdug_pos[0], digdug_pos[1] - i) in danger_zone
            for i in range(1, digdug_pos[1] - enemy_pos[1])
        )
        and all(
            (digdug_pos[0], digdug_pos[1] - i) not in rocks
            for i in range(1, digdug_pos[1] - enemy_pos[1])
        )
    ):
        return True
    return False


def find_closest_safe_block(digdug_pos, enemy_positions, rocks):
    # Define potential moves based on the relative positions of the enemies
    possible_moves = [
        (-1, 0),
        (1, 0),
        (0, -1),
        (0, 1),
    ]

    ### Calculate the potential moves for each enemy ( a + around each enemy, assuming it can move in any direction ) ###
    enemy_moves = []

    for enemy in enemy_positions:
        enemy_moves.append((enemy[0], enemy[1]))
    for enemy_pos in enemy_positions:
        for move in possible_moves:
            move = (move[0] + enemy_pos[0], move[1] + enemy_pos[1])
            enemy_moves.append(move) if checkinbounds(move) else None

        ### Add potential fire positions for fygars ###

        if enemy_pos[2] == "Fygar":
            for pos in range(1, 5):
                enemy_moves.append((enemy_pos[0] + pos, enemy_pos[1])) if checkinbounds(
                    (enemy_pos[0] + pos, enemy_pos[1])
                ) else None
                enemy_moves.append((enemy_pos[0] - pos, enemy_pos[1])) if checkinbounds(
                    (enemy_pos[0] - pos, enemy_pos[1])
                ) else None

    ### Add rock positions ###

    for rock in rocks:
        enemy_moves.append(rock)

    # Filter valid moves within the boundaries ( dont try to run out of the map )
    valid_moves = [
        (digdug_pos[0] + move[0], digdug_pos[1] + move[1])
        for move in possible_moves
        if checkinbounds((digdug_pos[0] + move[0], digdug_pos[1] + move[1]))
    ]

    # Filter possible digdug moves, removing the ones that are not safe
    for move in enemy_moves:
        if move in valid_moves:
            valid_moves.remove(move)

    if valid_moves != []:
        return random.choice(
            valid_moves
        )  # if there are safe moves, choose one randomly
    else:
        """
        If there arent any totally safe moves, go to plan B
        Here we will just try to run from the enemies based on their current direction ( and fygar fire )
        We assume only the next block where the mob will run to ( based on current direction ) is dangerous ( or blocks with possible fire )
        """
        cant_stay = []
        digdug_moves = []
        dir_dict = {0: (0, -1), 1: (1, 0), 2: (0, 1), 3: (-1, 0)}

        for enemy in enemy_positions:
            # add next move enemy positions to cant stay
            cant_stay.append(
                (enemy[0] + dir_dict[enemy[3]][0], enemy[1] + dir_dict[enemy[3]][1])
            )
            # add possible fire positions to cant stay
            if enemy[2] == "Fygar":
                for pos in range(1, 3):
                    cant_stay.append((enemy[0] + pos, enemy[1])) if checkinbounds(
                        (enemy[0] + pos, enemy[1])
                    ) else None
                    cant_stay.append((enemy[0] - pos, enemy[1])) if checkinbounds(
                        (enemy[0] - pos, enemy[1])
                    ) else None

        for move in possible_moves:
            digdug_moves.append((digdug_pos[0], digdug_pos[1])) if checkinbounds(
                (digdug_pos[0] + move[0], digdug_pos[1] + move[1])
            ) else None
            digdug_moves.append(
                (digdug_pos[0] + move[0], digdug_pos[1] + move[1])
            ) if move not in rocks and checkinbounds(
                (digdug_pos[0] + move[0], digdug_pos[1] + move[1])
            ) else None

        # Choose a random one of this "kinda safe" positions to go to
        go_to = random.choice([move for move in digdug_moves if move not in cant_stay])
        return go_to


def may_colide(go_to, enemy_pos, danger_zone):
    """
    This function checks if the enemy can collide with digdug in the next move
    """
    danger_zone_copy = (
        danger_zone.copy() + [go_to] if go_to not in danger_zone else danger_zone.copy()
    )

    # Given any possible direction change of the enemy, check if it can collide with digdug ( given digdug next move (go_to) )
    possible_moves_enemy = []
    for pos in enemy_pos:
        for move in [(0, -1), (1, 0), (0, 1), (-1, 0)]:
            new_pos = (pos[0] + move[0], pos[1] + move[1])
            if new_pos in danger_zone_copy:
                possible_moves_enemy.append(move)

    # If they can collide, return True
    if go_to in possible_moves_enemy:
        return True

    return False  # No collision in any direction


def checkinbounds(move):
    # Function to check if a move goes outside of the map
    size = (48, 24)
    x, y = move

    if x >= 0 and x < size[0] and y >= 0 and y < size[1]:
        return True


def safe_to_shoot(distance_to_enemy):
    safe = False
    if (
        distance_to_enemy <= 3 and distance_to_enemy > 1
    ):  # Only allow digdug to shoot if the enemy is close ( <= 3 distance ) and not too close ( > 1 distance )
        safe = True

    return safe


def should_run(go_to, close_enemies, next_to_kill, digdug_pos, danger_zone):
    distance_to_enemy = abs(digdug_pos[0] - next_to_kill["pos"][0]) + abs(
        digdug_pos[1] - next_to_kill["pos"][1]
    )
    # Calculate distance to enemy as sum of x and y differences

    if distance_to_enemy <= 2 or may_colide(go_to, close_enemies, danger_zone):
        return True
    if "traverse" in close_enemies:
        return True

    return False


loop = asyncio.get_event_loop()

SERVER = os.environ.get("SERVER", "localhost")
PORT = os.environ.get("PORT", "8000")
NAME = "108969"
loop.run_until_complete(agent_loop(f"{SERVER}:{PORT}", NAME))
