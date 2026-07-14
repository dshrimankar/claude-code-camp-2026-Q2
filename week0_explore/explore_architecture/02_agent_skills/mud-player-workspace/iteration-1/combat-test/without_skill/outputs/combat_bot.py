#!/usr/bin/env python3
"""
Smart MUD Combat Bot
Connects to a MUD, explores to find easy mobs, fights them safely,
and manages health to avoid death.
"""

import socket
import time
import re
import sys
from datetime import datetime
from pathlib import Path

class CombatBot:
    def __init__(self, host, port, username, password, output_dir):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.output_dir = Path(output_dir)
        self.sock = None

        # State tracking
        self.current_hp = 100
        self.max_hp = 100
        self.current_mana = 100
        self.max_mana = 100
        self.current_moves = 100
        self.max_moves = 100
        self.is_resting = False
        self.is_fighting = False
        self.level = 1
        self.experience = 0

        # Combat tracking
        self.kills = 0
        self.deaths = 0
        self.total_xp_gained = 0
        self.loot_obtained = []
        self.combat_log = []

        # Session logging
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        self.session_log_file = self.output_dir / f'session_{timestamp}.log'
        self.session_log = open(self.session_log_file, 'w')

        print(f"Session log: {self.session_log_file}")

    def connect(self):
        """Connect to MUD server"""
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.settimeout(10.0)
            self.sock.connect((self.host, self.port))
            print(f"Connected to {self.host}:{self.port}")
            return True
        except Exception as e:
            print(f"Connection failed: {e}")
            return False

    def send(self, message):
        """Send command to MUD"""
        try:
            self.sock.sendall((message + '\r\n').encode('utf-8'))
            self.log(f">>> {message}")
            return True
        except Exception as e:
            print(f"Send failed: {e}")
            return False

    def receive(self, timeout=1.0):
        """Receive data from MUD"""
        data = []
        self.sock.settimeout(timeout)
        start_time = time.time()

        while time.time() - start_time < timeout:
            try:
                chunk = self.sock.recv(4096).decode('utf-8', errors='replace')
                if chunk:
                    data.append(chunk)
                    start_time = time.time()  # Reset on new data
            except socket.timeout:
                break
            except Exception as e:
                print(f"Receive error: {e}")
                break

        result = ''.join(data)
        if result:
            self.log(result)
            self.parse_state(result)
        return result

    def log(self, message):
        """Log to session file"""
        self.session_log.write(message)
        if not message.endswith('\n'):
            self.session_log.write('\n')
        self.session_log.flush()

    def strip_ansi(self, text):
        """Remove ANSI color codes"""
        ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
        return ansi_escape.sub('', text)

    def parse_state(self, text):
        """Parse game state from output"""
        clean = self.strip_ansi(text)

        # Parse HP/Mana/Moves from common formats
        # Format examples: "100H 50M 100V >", "HP:100/120 Mana:50/80", "<100hp 50m 100mv>"
        hp_patterns = [
            r'(\d+)H\s+(\d+)M\s+(\d+)V',  # 100H 50M 100V
            r'(\d+)/(\d+)[Hh]',  # 100/120H
            r'<(\d+)hp\s+(\d+)m\s+(\d+)mv>',  # <100hp 50m 100mv>
        ]

        # Try to find HP
        for pattern in hp_patterns:
            match = re.search(pattern, clean)
            if match:
                try:
                    self.current_hp = int(match.group(1))
                    if len(match.groups()) >= 2:
                        if '/' in pattern:
                            self.max_hp = int(match.group(2))
                except:
                    pass

        # Check combat state
        if 'You hit' in clean or 'You miss' in clean or 'You pierce' in clean or 'You slash' in clean:
            self.is_fighting = True
        if 'is DEAD!' in clean or 'is dead!' in clean:
            self.is_fighting = False
            self.kills += 1
            self.combat_log.append(f"Kill #{self.kills} at {datetime.now()}")
        if 'You are dead!' in clean or 'You have been killed' in clean:
            self.deaths += 1
            print("WARNING: Character died!")
        if 'You gain' in clean and 'experience' in clean:
            xp_match = re.search(r'gain\s+(\d+)\s+experience', clean)
            if xp_match:
                xp = int(xp_match.group(1))
                self.total_xp_gained += xp
                self.combat_log.append(f"Gained {xp} XP")

        # Check resting state
        if 'You sit down and rest' in clean or 'You go to sleep' in clean:
            self.is_resting = True
        if 'You wake and stand up' in clean or 'You stop resting' in clean:
            self.is_resting = False

    def login(self):
        """Login to the MUD"""
        print("Logging in...")
        time.sleep(1)
        output = self.receive(timeout=2)
        print(output)

        # Send username
        time.sleep(0.5)
        self.send(self.username)
        output = self.receive(timeout=1)
        print(output)

        # Send password
        time.sleep(0.5)
        self.send(self.password)
        output = self.receive(timeout=2)
        print(output)

        # Press enter to get past MOTD
        time.sleep(0.5)
        self.send('')
        output = self.receive(timeout=2)
        print(output)

        print("Login complete!")
        return True

    def execute_command(self, cmd, wait=0.5):
        """Execute a command and wait for response"""
        print(f"> {cmd}")
        self.send(cmd)
        time.sleep(wait)
        output = self.receive(timeout=1.5)
        print(output)
        return output

    def check_health(self):
        """Check if we need to rest"""
        if self.max_hp == 0:
            return True

        hp_percent = (self.current_hp / self.max_hp) * 100

        if hp_percent < 40 and not self.is_resting:
            print(f"\n[Health low: {self.current_hp}/{self.max_hp} ({hp_percent:.0f}%) - RESTING]")
            self.execute_command('rest')
            # Rest until health is good
            while hp_percent < 80:
                time.sleep(2)
                self.execute_command('score')
                hp_percent = (self.current_hp / self.max_hp) * 100
                print(f"Resting... HP: {hp_percent:.0f}%")
            self.execute_command('stand')
            print("[Health restored, ready to continue]")

        return hp_percent > 20  # Return False if critically low

    def find_and_explore(self):
        """Explore the starting area"""
        print("\n=== EXPLORING ===")

        # Get bearings
        self.execute_command('look')
        self.execute_command('score')

        # Check what's in the room
        output = self.execute_command('look')

        return output

    def find_mobs(self):
        """Look for mobs in current room"""
        output = self.execute_command('look')
        clean = self.strip_ansi(output)

        # Common MUD mob indicators
        mob_keywords = []
        lines = clean.split('\n')

        for line in lines:
            # Look for lines that might indicate mobs
            # Usually they start with "A " or "An " or have "is here" or "standing here"
            if any(indicator in line.lower() for indicator in ['is here', 'standing here', 'lying here']):
                # Extract potential mob name
                words = line.split()
                if words:
                    # Try to find the mob keyword (usually first noun)
                    for word in words:
                        if len(word) > 2 and word.lower() not in ['the', 'is', 'here', 'standing', 'lying']:
                            mob_keywords.append(word.lower().strip('.,!?'))
                            break

        return mob_keywords

    def fight_mob(self, mob_name):
        """Engage in combat with a mob"""
        print(f"\n=== FIGHTING: {mob_name} ===")

        # Check health before fight
        if not self.check_health():
            print("Health too low to fight!")
            return False

        # Initiate combat
        output = self.execute_command(f'kill {mob_name}')

        # Check if combat started
        if 'You do the best you can' in output or 'already fighting' in output:
            print("Already in combat or can't attack")
            return False

        # Combat loop
        max_rounds = 30
        rounds = 0

        while self.is_fighting and rounds < max_rounds:
            time.sleep(1)

            # Get status
            output = self.receive(timeout=0.5)
            if output:
                print(output)

            # Check if we need emergency healing
            hp_percent = (self.current_hp / self.max_hp) * 100 if self.max_hp > 0 else 100
            if hp_percent < 25:
                print(f"[CRITICAL HP: {hp_percent:.0f}% - Attempting to flee!]")
                self.execute_command('flee')
                time.sleep(1)
                break

            rounds += 1

        # Check result
        if not self.is_fighting:
            print(f"[Combat ended - Victory!]")
            # Loot the corpse
            time.sleep(1)
            self.execute_command('get all corpse')
            return True
        else:
            print(f"[Combat timeout or fled]")
            return False

    def explore_direction(self, direction):
        """Try to move in a direction"""
        output = self.execute_command(direction)
        # Check if movement succeeded (usually no "You can't go that way" message)
        if "can't go" in output.lower():
            return False
        return True

    def run_combat_session(self, target_kills=5):
        """Main combat session"""
        print("\n" + "="*50)
        print("STARTING COMBAT SESSION")
        print("="*50 + "\n")

        if not self.connect():
            return

        try:
            # Login
            self.login()
            time.sleep(1)

            # Initial exploration
            self.find_and_explore()

            # Try to find easy starter mobs
            # Most MUDs have areas with names like "newbie", "academy", "school", etc.
            print("\n=== Looking for mobs ===")

            # Common easy mob areas - try different directions
            directions = ['north', 'south', 'east', 'west', 'up', 'down']

            attempt = 0
            while self.kills < target_kills and attempt < 50:
                attempt += 1

                # Check health
                if not self.check_health():
                    print("Health critical, ending session")
                    break

                # Look for mobs in current room
                mobs = self.find_mobs()

                if mobs:
                    print(f"Found potential mobs: {mobs}")
                    # Try to fight the first one
                    for mob in mobs:
                        if self.fight_mob(mob):
                            print(f"Kills: {self.kills}/{target_kills}")
                            break
                        time.sleep(2)
                else:
                    # No mobs here, try moving
                    import random
                    direction = random.choice(directions)
                    print(f"No mobs here, trying {direction}...")
                    if not self.explore_direction(direction):
                        # Can't go that way, try another
                        continue

                time.sleep(1)

            # Final status
            print("\n" + "="*50)
            print("SESSION COMPLETE")
            print("="*50)
            self.execute_command('score')
            self.execute_command('inventory')

            # Quit gracefully
            self.execute_command('quit')

        except KeyboardInterrupt:
            print("\n[Interrupted by user]")
        except Exception as e:
            print(f"Error during session: {e}")
            import traceback
            traceback.print_exc()
        finally:
            self.cleanup()

    def cleanup(self):
        """Cleanup and save results"""
        if self.sock:
            self.sock.close()
        if self.session_log:
            self.session_log.close()

        # Write combat results
        results_file = self.output_dir / 'combat_results.txt'
        with open(results_file, 'w') as f:
            f.write("="*50 + "\n")
            f.write("MUD COMBAT SESSION RESULTS\n")
            f.write("="*50 + "\n\n")
            f.write(f"Date: {datetime.now()}\n")
            f.write(f"Username: {self.username}\n\n")

            f.write("COMBAT STATISTICS:\n")
            f.write(f"  Mobs Killed: {self.kills}\n")
            f.write(f"  Deaths: {self.deaths}\n")
            f.write(f"  Total XP Gained: {self.total_xp_gained}\n")
            f.write(f"  Final HP: {self.current_hp}/{self.max_hp}\n\n")

            f.write("COMBAT LOG:\n")
            for entry in self.combat_log:
                f.write(f"  {entry}\n")

            f.write("\n" + "="*50 + "\n")
            f.write(f"Full session log: {self.session_log_file}\n")

        print(f"\nResults saved to: {results_file}")
        print(f"Session log: {self.session_log_file}")
        print(f"\nFinal stats: {self.kills} kills, {self.deaths} deaths, {self.total_xp_gained} XP gained")

if __name__ == '__main__':
    output_dir = '/Users/dshri/code/claude-code-camp-2026-Q2/week0_explore/explore_architecture/02_agent_skills/mud-player-workspace/iteration-1/combat-test/without_skill/outputs/'

    bot = CombatBot(
        host='localhost',
        port=4000,
        username='dummy',
        password='helloworld',
        output_dir=output_dir
    )

    bot.run_combat_session(target_kills=5)
