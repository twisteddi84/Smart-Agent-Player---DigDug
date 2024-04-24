import os

# Comandos a serem executados em cada painel do tmux
commands = [
    "python3 server.py",
    "python3 viewer.py",
    "python3 student.py"
]

# Iniciar o tmux
os.system("tmux new-session -d -s mysession")

# Abrir painéis e executar comandos
for command in commands:
    os.system(f"tmux split-window -t mysession:0 -h '{command}'")

# Anexar-se à sessão do tmux
os.system("tmux attach-session -t mysession")