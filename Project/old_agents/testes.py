def can_shoot(digdug_pos, enemy_pos, dig_dir, danger_zone):
    
    if (
        (digdug_pos[1] == enemy_pos[1])  # mesmo y
        and (digdug_pos[0] < enemy_pos[0])  # distancia de 3 ou menos
        and (dig_dir == 1)  # ta virado para a direita
        and ((enemy_pos[0], enemy_pos[1]) in danger_zone)  # inimigo ta num sitio cavado
        and all(
            (digdug_pos[0] + i, digdug_pos[1]) in danger_zone
            for i in range(1, enemy_pos[0] - digdug_pos[0])
        )  # todos os buracos à frente tao cavados
    ):
        return True  # consegue disparar para a direita

    if (
        (digdug_pos[1] == enemy_pos[1])
        and (digdug_pos[0] > enemy_pos[0])
        and (dig_dir == 3)  # esquerda
        and ((enemy_pos[0], enemy_pos[1]) in danger_zone)
        and all(
            (digdug_pos[0] - i, digdug_pos[1]) in danger_zone
            for i in range(enemy_pos[0] - digdug_pos[0], -1)
        )
    ):
        return True

    if (
        (digdug_pos[0] == enemy_pos[0])
        and (digdug_pos[1] < enemy_pos[1])
        and (dig_dir == 2)  # baixo
        and ((enemy_pos[0], enemy_pos[1]) in danger_zone)
        and all(
            (digdug_pos[0], digdug_pos[1] + i) in danger_zone
            for i in range(1, enemy_pos[1] - digdug_pos[1])
        )
    ):
        return True

    if (
        (digdug_pos[0] == enemy_pos[0])
        and (digdug_pos[1] > enemy_pos[1])
        and (dig_dir == 0)  # cima
        and ((enemy_pos[0], enemy_pos[1]) in danger_zone)
        and all(
            (digdug_pos[0], digdug_pos[1] - i) in danger_zone
            for i in range(1, digdug_pos[1] - enemy_pos[1])
        )
    ):
        return True
    return False


print(can_shoot((1, 6), (1, 9), 2, [(1, 6), (1, 7),(1,8),(1,9)]))