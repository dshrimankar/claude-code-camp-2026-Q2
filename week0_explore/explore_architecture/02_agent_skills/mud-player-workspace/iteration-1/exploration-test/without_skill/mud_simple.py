#!/usr/bin/env python3

import socket
import time
import sys
import select

def send_command(sock, command):
    """Send a command to the MUD"""
    sock.sendall((command + '\r\n').encode('utf-8'))

def receive_data(sock, timeout=2.0):
    """Receive data from the MUD with timeout"""
    sock.setblocking(0)
    data = b''
    start_time = time.time()

    while time.time() - start_time < timeout:
        try:
            chunk = sock.recv(4096)
            if chunk:
                data += chunk
            else:
                break
        except BlockingIOError:
            time.sleep(0.1)
        except Exception as e:
            break

    sock.setblocking(1)
    return data.decode('utf-8', errors='replace')

def main():
    output_dir = "/Users/dshri/code/claude-code-camp-2026-Q2/week0_explore/explore_architecture/02_agent_skills/mud-player-workspace/iteration-1/exploration-test/without_skill/outputs"

    print("Connecting to localhost:4000...")
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        sock.connect(('localhost', 4000))

        full_log = []

        # Initial connection
        print("\n=== Waiting for initial prompt ===")
        time.sleep(2)
        response = receive_data(sock, 3)
        full_log.append("=== INITIAL CONNECTION ===\n" + response)
        print(response)

        # Send username
        print("\n=== Sending username: dummy ===")
        send_command(sock, 'dummy')
        time.sleep(1)
        response = receive_data(sock, 2)
        full_log.append("\n=== USERNAME SENT ===\n" + response)
        print(response)

        # Send password
        print("\n=== Sending password ===")
        send_command(sock, 'helloworld')
        time.sleep(2)
        response = receive_data(sock, 3)
        full_log.append("\n=== PASSWORD SENT ===\n" + response)
        print(response)

        # Check if we need to press return
        if "PRESS RETURN" in response:
            print("\n=== Pressing return ===")
            send_command(sock, '')
            time.sleep(1)
            response = receive_data(sock, 2)
            full_log.append("\n=== RETURN PRESSED ===\n" + response)
            print(response)

        # Check if we need to enter the game
        if "Make your choice" in response or "make your choice" in response.lower():
            print("\n=== Entering game (option 1) ===")
            send_command(sock, '1')
            time.sleep(2)
            response = receive_data(sock, 3)
            full_log.append("\n=== GAME ENTERED ===\n" + response)
            print(response)

        # If in combat, try to flee
        if "goblin" in response.lower() or "combat" in response.lower():
            print("\n=== Fleeing from combat ===")
            send_command(sock, 'flee')
            time.sleep(1)
            response = receive_data(sock, 2)
            full_log.append("\n=== FLEE ===\n" + response)
            print(response)

        # Exploration commands
        commands = [
            'look',
            'score',
            'inventory',
            'north',
            'look',
            'south',
            'look',
            'east',
            'look',
            'west',
            'look',
        ]

        for cmd in commands:
            print(f"\n=== Executing: {cmd} ===")
            send_command(sock, cmd)
            time.sleep(1.5)
            response = receive_data(sock, 2)
            full_log.append(f"\n=== {cmd.upper()} ===\n{response}")
            print(response)

            # If we can't move that way, try another direction
            if "Alas, you cannot go that way" in response or "You can't go there" in response:
                print(f"Cannot go {cmd}, trying alternatives...")

        # Get who's online
        print("\n=== Executing: who ===")
        send_command(sock, 'who')
        time.sleep(1)
        response = receive_data(sock, 2)
        full_log.append(f"\n=== WHO ===\n{response}")
        print(response)

        # Save and quit
        print("\n=== Saving and quitting ===")
        send_command(sock, 'quit')
        time.sleep(1)
        response = receive_data(sock, 2)
        full_log.append(f"\n=== QUIT ===\n{response}")
        print(response)

        # Save full log
        log_path = f"{output_dir}/mud_session_full.log"
        with open(log_path, 'w') as f:
            f.write('\n'.join(full_log))
        print(f"\n=== Session log saved to {log_path} ===")

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        sock.close()
        print("\n=== Connection closed ===")

if __name__ == '__main__':
    main()
