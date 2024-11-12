import socket
import sys
import time

def handle_agent_interaction(agent_id, agent_port):
    agent_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # Retry logic
    max_attempts = 5
    for attempt in range(max_attempts):
        try:
            agent_socket.connect(('localhost', agent_port))
            print(f"[*] Connected to Agent {agent_id} on port {agent_port}. You can now send commands.")
            break  # Break on successful connection
        except ConnectionRefusedError:
            if attempt < max_attempts - 1:
                print(f"[*] Connection refused. Retrying in 5 seconds... (Attempt {attempt + 1}/{max_attempts})")
                time.sleep(5)  # Wait before retrying
            else:
                print("[*] Failed to connect after multiple attempts.")
                return
        except Exception as e:
            print(f"[*] Unexpected error while connecting: {e}")
            return

    try:
        while True:
            command = input(f"Agent {agent_id} ~ ")
            if command.lower() == "exit":
                print("[*] Closing connection with the agent.")
                break
            if not command:
                command = "pwd"

            # Send command to the server
            agent_socket.send(command.encode('utf-8'))
            response = agent_socket.recv(32768).decode('utf-8')
            print(f"{response}\n")

    except Exception as e:
        print(f"Error during agent interaction: {e}")
    finally:
        agent_socket.close()

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python agent_listener.py <agent_id> <agent_port>")
        sys.exit(1)

    agent_id = sys.argv[1]
    agent_port = int(sys.argv[2])
    handle_agent_interaction(agent_id, agent_port)
