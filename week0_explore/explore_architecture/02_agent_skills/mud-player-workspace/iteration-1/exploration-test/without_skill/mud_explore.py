#!/usr/bin/env python3

import socket
import time
import sys

def send_and_receive(sock, command, wait_time=1.5):
    """Send a command and wait for response"""
    if command is not None:
        sock.sendall((command + '\r\n').encode('utf-8'))
    time.sleep(wait_time)

    # Receive data
    data = b''
    sock.setblocking(0)
    try:
        start_time = time.time()
        while time.time() - start_time < 0.5:
            try:
                chunk = sock.recv(4096)
                if not chunk:
                    break
                data += chunk
            except BlockingIOError:
                time.sleep(0.1)
                continue
    except Exception as e:
        print(f"Error receiving: {e}", file=sys.stderr)
    sock.setblocking(1)

    return data.decode('utf-8', errors='replace')

def main():
    output_dir = "/Users/dshri/code/claude-code-camp-2026-Q2/week0_explore/explore_architecture/02_agent_skills/mud-player-workspace/iteration-1/exploration-test/without_skill/outputs"

    # Connect to MUD
    print("Connecting to localhost:4000...")
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect(('localhost', 4000))

    full_log = []

    try:
        # Initial connection
        response = send_and_receive(sock, None, 3)
        full_log.append(response)
        print(response)

        # Send username
        print("Sending username: dummy")
        response = send_and_receive(sock, 'dummy', 2)
        full_log.append(response)
        print(response)

        # Send password
        print("Sending password...")
        response = send_and_receive(sock, 'helloworld', 2)
        full_log.append(response)
        print(response)

        # Check if we're already in game or at menu
        if "(news) (motd)" in response:
            print("Already in game! Starting exploration...")
        elif "PRESS RETURN" in response:
            # Press return
            print("Pressing return...")
            response = send_and_receive(sock, '', 2)
            full_log.append(response)
            print(response)

            # Should now be at menu
            if "Make your choice" in response or "make your choice" in response.lower():
                print("Entering game (option 1)...")
                response = send_and_receive(sock, '1', 3)
                full_log.append(response)
                print(response)
        else:
            print("Unexpected state, trying to continue...")

        # Wait a moment to stabilize
        time.sleep(2)

        # Exploration commands
        commands = [
            'look',
            'north',
            'look',
            'south',
            'look',
            'east',
            'look',
            'west',
            'look',
            'south',
            'look',
            'north',
            'look',
            'west',
            'look',
            'east',
            'look',
            'inventory',
            'score',
            'who'
        ]

        for cmd in commands:
            print(f"\nExecuting: {cmd}")
            response = send_and_receive(sock, cmd, 2)
            full_log.append(f"\n>>> {cmd}\n{response}")
            print(response)

            # Check if we're still connected
            if not response:
                print("Connection appears to be lost")
                break

        # Quit
        print("\nQuitting...")
        response = send_and_receive(sock, 'quit', 1)
        full_log.append(response)
        print(response)

    except Exception as e:
        print(f"Error during session: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
    finally:
        sock.close()

        # Save full log
        with open(f"{output_dir}/mud_session_full.log", 'w') as f:
            f.write('\n'.join(full_log))

        print(f"\nSession log saved to {output_dir}/mud_session_full.log")

if __name__ == '__main__':
    main()
