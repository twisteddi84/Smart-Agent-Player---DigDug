"""Example client."""
import asyncio
import getpass
import json
from math import sqrt
import os

# Next 4 lines are not needed for AI agents, please remove them from your code!
import pygame
import websockets
import time

from Position import *

pygame.init()
program_icon = pygame.image.load("data/icon2.png")
pygame.display.set_icon(program_icon)


async def agent_loop(server_address="localhost:8000", agent_name="student"):
    """Example client loop."""
    async with websockets.connect(f"ws://{server_address}/player") as websocket:
        # Receive information about static game properties
        await websocket.send(json.dumps({"cmd": "join", "name": agent_name}))

        # Next 3 lines are not needed for AI agent
        SCREEN = pygame.display.set_mode((299, 123))
        SPRITES = pygame.image.load("data/pad.png").convert_alpha()
        SCREEN.blit(SPRITES, (0, 0))

        digdug_recorder = []
        while True:
            try:
                state = json.loads(
                    await websocket.recv()
                )  # receive game update, this must be called timely or your game will get out of sync with the server

                key = ""
                
                if "digdug" not in state:
                    size = (state["size"][0], state["size"][1])
                    
                    danger_zone = []
                    digdug_recorder = []
                    # past_move = Position(0, 0)
                    
                    #pontos onde os bixos podem andar
                    for i in range(0, size[0]):
                        for j in range(0, size[1]):
                            # if j == 0 or j == 1:
                            #     continue

                            if state["map"][i][j] == 0:
                                danger_zone.append((i, j))

                
                    continue
                    # load next level


                digdug = Position(int(state["digdug"][0]), int(state["digdug"][1]))

                # ir buscar o inimigo mais proximo --> mudar para ser o que tiver mais no fundo
                smaller_dist = 100000000
                #fygar_number = state["enemies"]["Fygar"]
                fygar_number = 0
                index_fygar = 0
                for element in state["enemies"]:
                    if element["name"] == "Fygar":
                        fygar_number += 1
                        index_fygar = state["enemies"].index(element)

                if fygar_number == 0:
                    for enemi in state["enemies"]:
                        
                        posi_enemi = Position(int(enemi["pos"][0]), int(enemi["pos"][1]))
                        distance = digdug.distance_from(posi_enemi)

                        if distance < smaller_dist:
                            smaller_dist = distance
                            next_to_kill = enemi
                else:
                    next_to_kill = state["enemies"][index_fygar]
                    position_fygar = next_to_kill["pos"]
                    fila_escavada_fygar = encontrar_fila_escavada(position_fygar,danger_zone)
                    fygar = Position(int(position_fygar[0]), int(position_fygar[1]))
                    zona_escavada_mais_longe = None
                    maior_distancia = 0

                    for pos in fila_escavada_fygar:
                        dist = distancia_euclidiana(position_fygar, pos)
                        if dist > maior_distancia:
                            maior_distancia = dist
                            zona_escavada_mais_longe = pos
                    
               

                enemy = Position(
                    int(next_to_kill["pos"][0]), int(next_to_kill["pos"][1])
                )
                
                
                destino = Position(enemy.x, enemy.y) 
                                        
                past_move = digdug
                for dig in digdug_recorder[-1:0:-1]:
                    if dig != (digdug.x, digdug.y):
                        past_move = Position(dig[0], dig[1])
                        break
                
                if digdug.x - past_move.x == 1 :
                    dig_dir = 1
                    
                elif past_move.x - digdug.x == 1 :
                    dig_dir = 3
                    
                elif digdug.y - past_move.y == 1 :
                    dig_dir = 2
                    
                elif past_move.y - digdug.y == 1 :
                    dig_dir = 0
                
                else:
                    dig_dir = 404
                
                to_enemy = digdug.shortest_path(enemy, size)
                    
                if next_to_kill["name"] == "Fygar":
                    
                    if next_to_kill["dir"] == 1:
                        destino = Position(enemy.x - 5, enemy.y)
                    elif next_to_kill["dir"] == 3:
                        destino = Position(enemy.x + 5, enemy.y)
                    elif next_to_kill["dir"] == 0:
                        destino = Position(enemy.x, enemy.y - 5)
                    elif next_to_kill["dir"] == 2:
                        destino = Position(enemy.x, enemy.y + 5)
                
                else:
                    for posi in danger_zone:
                        
                        position = Position(posi[0], posi[1])
                        
                        if posi[1] == enemy.y and abs(posi[0] - enemy.x) == 5 :
                            destino = position
                            break
                        
                        
                        elif posi[0] == enemy.x and abs(posi[1] - enemy.y) == 5:
                            destino = position
                            break
                        
                        
                        elif len(position.shortest_path(enemy, size)) == 5:
                            destino = position
                        

            
                #distancia de segurança   
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
                        destino = Position(digdug.x + 1, digdug.y)
                          
                    elif enemy.x < digdug.x and digdug.y == enemy.y:
                        destino = Position(digdug.x - 1, digdug.y)
                            
                    elif digdug.y > enemy.y and digdug.x == enemy.x:
                        destino = Position(digdug.x, digdug.y - 1)
                       
                    elif digdug.y < enemy.y and digdug.x == enemy.x:
                        destino = Position(digdug.x, digdug.y + 1)
                 
                    
                shoot = False
                
                if len(to_enemy) <= 3:
                    
                    if enemy.x > digdug.x and digdug.y == enemy.y and dig_dir == 1 and (enemy.x, enemy.y) in danger_zone:
                        shoot = True
                        
                        for loc in to_enemy:
                            if (loc.x, loc.y) not in danger_zone:
                                shoot = False
                                break
                                
                    elif enemy.x < digdug.x and digdug.y == enemy.y and dig_dir == 3 and (enemy.x, enemy.y) in danger_zone:
    
                        shoot = True
                        for loc in to_enemy:
                             
                            if (loc.x, loc.y) not in danger_zone:
                      
                                shoot = False
                                break
                        
                    elif digdug.y > enemy.y and digdug.x == enemy.x and dig_dir == 0 and (enemy.x, enemy.y) in danger_zone:
                
                        shoot = True
                        for loc in to_enemy:
                             
                            if (loc.x, loc.y) not in danger_zone:
                               
                                shoot = False
                                break
                                
                    elif digdug.y < enemy.y and digdug.x == enemy.x and dig_dir == 2 and (enemy.x, enemy.y) in danger_zone: 
                      
                        shoot = True  
                        for loc in to_enemy:
                             
                            if (loc.x, loc.y) not in danger_zone:
                               
                                shoot = False
                                break
                            
                    else:
                        shoot = False
                   
                        rock = Position(state["rocks"][0]["pos"][0], state["rocks"][0]["pos"][1])
                       
                            
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
                
                destino = Position(zona_escavada_mais_longe[0],zona_escavada_mais_longe[1])
                print(destino)

                path = digdug.shortest_path(destino, size)
                
                if len(path) == 1 :
                    nex_move = path[0]
                elif len(path) == 0:
                    nex_move = digdug
                else:
                    nex_move = path[1]
                    
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
                    danger_zone.append((nex_move.x, nex_move.y))
                    danger_zone = set(danger_zone)
                    danger_zone = list(danger_zone)
               
                
                # Next lines are only for the Human Agent, the key values are nonetheless the correct ones!
                    
                await websocket.send(json.dumps({"cmd": "key", "key": key}))
                # send key command to server - you must implement this send in the AI agent

            except websockets.exceptions.ConnectionClosedOK:
                print("Server has cleanly disconnected us")
                return

            # Next line is not needed for AI agent
            pygame.display.flip()

def is_escavada(pos,danger_zone):
    return pos in danger_zone

def encontrar_fila_escavada(fygar_position,danger_zone):
    fila = [fygar_position]
    visitados = set()
    visitados.add(tuple(fygar_position))

    while fila:
        pos_atual = fila.pop(0)
        x, y = pos_atual

        # Verifique todas as posições vizinhas
        vizinhos = [(x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)]

        for vizinho in vizinhos:
            if is_escavada(vizinho,danger_zone) and tuple(vizinho) not in visitados:
                fila.append(vizinho)
                visitados.add(tuple(vizinho))

    return list(visitados)

# Função para calcular a distância Euclidiana entre duas posições
def distancia_euclidiana(pos1, pos2):
    x1, y1 = pos1
    x2, y2 = pos2
    return sqrt((x1 - x2) ** 2 + (y1 - y2) ** 2)



# DO NOT CHANGE THE LINES BELLOW
# You can change the default values using the command line, example:
# $ NAME='arrumador' python3 client.py
loop = asyncio.get_event_loop()
SERVER = os.environ.get("SERVER", "localhost")
PORT = os.environ.get("PORT", "8000")
NAME = os.environ.get("NAME", getpass.getuser())
loop.run_until_complete(agent_loop(f"{SERVER}:{PORT}", NAME))
