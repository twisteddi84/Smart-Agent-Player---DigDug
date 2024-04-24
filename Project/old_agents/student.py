"""Example client."""
import asyncio
import getpass
import json
import os
import random
import time

import websockets

from Position import *

prioritize = "closest"  # definir qual é o inimigo com + prioridade, lowest ou closest
forbidden = []
# o lowest tá a dar merdice n usem


async def agent_loop(server_address="localhost:8000", agent_name="student"):
    """Example client loop."""
    async with websockets.connect(f"ws://{server_address}/player") as websocket:
        # Receive information about static game properties
        await websocket.send(json.dumps({"cmd": "join", "name": agent_name}))


        digdug_recorder = []
        while True:
            try:
                state = json.loads(
                    await websocket.recv()
                )  # receive game update, this must be called timely or your game will get out of sync with the server

                key = ""

                ###### Loading a new level ######

                if "digdug" not in state:
                    size = (state["size"][0], state["size"][1])

                    danger_zone = []  # espaços escavados
                    digdug_recorder = []  # para definir a direção do digdug
                    rocks = []  # lista de calhaus

                    for i in range(0, size[0]):
                        for j in range(0, size[1]):
                            if (
                                state["map"][i][j] == 0
                            ):  # os que vem no state com 0 são os espaços escavados
                                danger_zone.append((i, j))

                    continue

                ###################################

                
                digdug = Position(
                    int(state["digdug"][0]), int(state["digdug"][1])
                )  # posição do digdug

                rocks = [(int(r["pos"][0]), int(r["pos"][1])) for r in state["rocks"]]
                fygars = [(f["pos"][0], int(f["pos"][1]),f["dir"]) for f in state["enemies"] if f["name"] == "Fygar"]
                forbidden = []
                if fygars:
                    for f in fygars:
                        if f[2] == 1:
                            forbidden.extend([(f[0]+i,f[1]) for i in range(1,3)]) # nao ir pra frente dos fygars
                        elif f[2] == 3:
                            forbidden.extend([(f[0]-i,f[1]) for i in range(1,3)]) # nao ir pra frente dos fygars
                        else:
                            forbidden.extend([(f[0]+i,f[1]) for i in range(1,3)]) # nao ir pra frente nem trás se tao virados pra cima ou baixo
                            forbidden.extend([(f[0]-i,f[1]) for i in range(1,3)])

                #### Definir o próximo inimigo para ir atacar ####

                if state["enemies"]:
                    if prioritize == "lowest":
                        next_to_kill = sorted(
                            state["enemies"], key=lambda k: k["pos"][1]
                        )[
                            -1
                        ]  # ordenar os inimigos por y e ir buscar o ultimo ( mais abaixo)

                    if prioritize == "closest":
                        next_to_kill = sorted(
                            state["enemies"],
                            key=lambda distance: digdug.distance_from(
                                Position(
                                    int(distance["pos"][0]), int(distance["pos"][1])
                                )
                            ),
                        )[
                            0
                        ]  # ordenar os inimigos por distancia e ir buscar o primeiro ( mais perto )
                else:
                    continue

                enemy = Position(
                    int(next_to_kill["pos"][0]), int(next_to_kill["pos"][1])
                )  # criar um objeto position com a posição do inimigo para dar para fazer search

                ###################################

                #### Definir a direção do digdug ####

                past_move = digdug
                for dig in digdug_recorder[-1:0:-1]:
                    if dig != (digdug.x, digdug.y):
                        past_move = Position(dig[0], dig[1])
                        break

                dig_dir = digdug.getDirection(
                    past_move
                )  # ir buscar a direção com base na posição anterior

                ###################################

                to_enemy = digdug.shortest_path(
                    enemy, forbidden
                )  # caminho mais curto para o inimigo através da search

                #### Default behaviour, quando não chegou a pelo menos 5 de distancia do mob ####

                mob = next_to_kill["name"]
                direcao_mob = next_to_kill["dir"]

                if mob == "Fygar":
                    if direcao_mob == 1:  # DIREITA
                        destino = Position(enemy.x - 5, enemy.y)
                    elif direcao_mob == 3:  # ESQUERDA
                        destino = Position(enemy.x + 5, enemy.y)
                    elif direcao_mob == 0:  # CIMA
                        destino = Position(enemy.x, enemy.y - 5)
                    elif direcao_mob == 2:  # BAIXO
                        destino = Position(enemy.x, enemy.y + 5)

                if mob == "Pooka":
                    for posi in danger_zone:  # dar scan nos espaços escavados
                        position = Position(posi[0], posi[1])

                        if posi[1] == enemy.y and abs(posi[0] - enemy.x) == 5:
                            destino = position
                            break

                        elif posi[0] == enemy.x and abs(posi[1] - enemy.y) == 5:
                            destino = position
                            break

                        elif len(position.shortest_path(enemy, forbidden)) == 5:
                            destino = position

                ###################################

                # distancia de segurança
                if 4 <= len(to_enemy) <= 5:
                    if next_to_kill["name"] == "Fygar":
                        if next_to_kill["dir"] == 1:
                            destino = Position(enemy.x - 3, enemy.y)
                        elif next_to_kill["dir"] == 3:
                            destino = Position(enemy.x + 3, enemy.y)
                        elif next_to_kill["dir"] == 0:
                            destino = Position(enemy.x, enemy.y - 3)
                        elif next_to_kill["dir"] == 2:
                            destino = Position(enemy.x, enemy.y + 3)

                    if enemy.x > digdug.x and digdug.y == enemy.y:
                        # print("DIREITA")
                        destino = Position(digdug.x + 1, digdug.y)

                    elif enemy.x < digdug.x and digdug.y == enemy.y:
                        # print("ESQUERDA")
                        destino = Position(digdug.x - 1, digdug.y)

                    elif digdug.y > enemy.y and digdug.x == enemy.x:
                        # print("CIMA")
                        destino = Position(digdug.x, digdug.y - 1)

                    elif digdug.y < enemy.y and digdug.x == enemy.x:
                        # print("BAIXO")
                        destino = Position(digdug.x, digdug.y + 1)

                shoot = False
                reverse_mobdir = (direcao_mob +2)%4

                if len(to_enemy) <= 3:
                    if ( enemy.can_shoot_right(digdug,danger_zone,to_enemy,dig_dir ) # se conseguir disparar para a direita
                    or ( enemy.can_shoot_left(digdug,danger_zone,to_enemy,dig_dir) ) # se conseguir disparar para a esquerda
                    or ( enemy.can_shoot_up(digdug,danger_zone,to_enemy,dig_dir)   ) # se conseguir disparar para cima
                    or ( enemy.can_shoot_down(digdug,danger_zone,to_enemy,dig_dir) ) # se conseguir disparar para baixo
                    ):
                        shoot = True

                    if ( not shoot ):  # não consegue disparar por alguma razão e ta a distancia de 3 ou menos
                        
                        ## default é fugir
                        
                        if digdug.x - 1 == 0 or digdug.x + 1 == size[0]:
                                    if enemy.y > digdug.y:
                                        destino = Position(digdug.x, digdug.y - 1)
                                    else:
                                        destino = Position(digdug.x, digdug.y + 1)

                        elif digdug.y + 1 == size[1] or digdug.y - 1 == 0:
                                    if enemy.x > digdug.x:
                                        destino = Position(digdug.x - 1, digdug.y)
                                    else:
                                        destino = Position(digdug.x + 1, digdug.y)

                        else:
                                    if enemy.x > digdug.x:
                                        destino = Position(digdug.x - 1, digdug.y)
                                    else:
                                        destino = Position(digdug.x + 1, digdug.y)

                                    if enemy.y > digdug.y:
                                        destino = Position(digdug.x, digdug.y - 1)
                                    else:
                                        destino = Position(digdug.x, digdug.y + 1)
                        
                        if digdug.distance_from(enemy)==3 : # só tentar virar e disparar se tiver a 3 de distancia, a menos é arriscado
                            
                            if (enemy.can_shoot_right(Position(digdug.x+1,digdug.y),danger_zone,to_enemy,1) and ((direcao_mob == 3 and mob == "Pooka") or (direcao_mob == 1 and mob == "Fygar"))):
                                print("Turning right to shoot")
                                destino = Position(digdug.x+1,digdug.y)
                                
                            elif (enemy.can_shoot_left(Position(digdug.x-1,digdug.y),danger_zone,to_enemy,3) and ((direcao_mob == 1 and mob == "Pooka") or (direcao_mob == 3 and mob == "Fygar"))):
                                print("Turning left to shoot")
                                destino = Position(digdug.x-1,digdug.y)
                            
                            elif (enemy.can_shoot_up(Position(digdug.x,digdug.y-1),danger_zone,to_enemy,0) and direcao_mob == 2):
                                print("Turning up to shoot")
                                destino = Position(digdug.x,digdug.y-1)
                                
                            elif (enemy.can_shoot_down(Position(digdug.x,digdug.y+1),danger_zone,to_enemy,2) and direcao_mob == 0):
                                print("Turning down to shoot")
                                destino = Position(digdug.x,digdug.y+1)
                            
                    
                    
                                
                                 
                path = digdug.shortest_path(destino,forbidden)
                

                if len(path) == 1:
                    nex_move = path[0]
                elif len(path) == 0:
                    nex_move = digdug
                else:
                    nex_move = path[1]
                    
                
                if (nex_move.x, nex_move.y) in rocks:
                    print("borro")
                    if dig_dir == 1 or dig_dir == 3:
                        next_possible_dir = [2,4]
                        next_dir = random.choice(next_possible_dir)

                    else:
                        next_possible_dir = [1,3]
                        next_dir = random.choice(next_possible_dir)

                    if next_dir == 1:
                        nex_move.x = digdug.x + 1
                        nex_move.y = digdug.y
                    elif next_dir == 3:
                        nex_move.x = digdug.x - 1
                        nex_move.y = digdug.y
                    elif next_dir == 2:
                        nex_move.x = digdug.x
                        nex_move.y = digdug.y + 1
                    elif next_dir == 4:
                        nex_move.x = digdug.x
                        nex_move.y = digdug.y - 1


                # past_move = digdug
                digdug_recorder.append((digdug.x, digdug.y))

                if nex_move.x > digdug.x:
                    key = "d"
                elif nex_move.x < digdug.x:
                    key = "a"
                elif nex_move.y > digdug.y:
                    key = "s"
                elif nex_move.y < digdug.y:
                    key = "w"




                if shoot == True:
                    key = "A"

                else:
                    danger_zone.append((nex_move.x, nex_move.y)) if (
                        nex_move.x,
                        nex_move.y,
                    ) not in danger_zone else None

                # Next lines are only for the Human Agent, the key values are nonetheless the correct ones!

                await websocket.send(json.dumps({"cmd": "key", "key": key}))
                # send key command to server - you must implement this send in the AI agent

            except websockets.exceptions.ConnectionClosedOK:
                print("Server has cleanly disconnected us")
                return

            # Next line is not needed for AI agent
            # pygame.display.flip()


# DO NOT CHANGE THE LINES BELLOW
# You can change the default values using the command line, example:
# $ NAME='arrumador' python3 client.py
loop = asyncio.get_event_loop()
SERVER = os.environ.get("SERVER", "localhost")
PORT = os.environ.get("PORT", "8000")
NAME = os.environ.get("NAME", getpass.getuser())
loop.run_until_complete(agent_loop(f"{SERVER}:{PORT}", NAME))

