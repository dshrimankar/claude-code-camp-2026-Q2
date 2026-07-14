#!/usr/bin/env python3
"""
Combat session script for MUD game
Carefully fights mobs while managing health and tracking progress
"""

import sys
import os
import time
import re

# Add the mud-player scripts directory to path
sys.path.insert(0, '/Users/dshri/code/claude-code-camp-2026-Q2/week0_explore/explore_architecture/02_agent_skills/mud-player/scripts')

from mud_client import MUDClient


class CombatTracker:
    """Track combat statistics and outcomes"""

    def __init__(self):
        self.mobs_killed = 0
        self.xp_gained = 0
        self.loot_obtained = []
        self.damage_taken = 0
        self.damage_dealt = 0
        self.healing_sessions = 0
        self.combat_log = []

    def parse_combat_output(self, text):
        """Parse combat text to extract statistics"""
        clean_text = re.sub(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])', '', text)

        # Check for mob death
        if 'is DEAD!' in clean_text or 'is dead!' in clean_text:
            self.mobs_killed += 1
            self.combat_log.append(f"[KILL] Mob defeated!")

        # Check for XP gain
        xp_match = re.search(r'You receive (\d+) experience points', clean_text)
        if xp_match:
            xp = int(xp_match.group(1))
            self.xp_gained += xp
            self.combat_log.append(f"[XP] Gained {xp} experience")

        # Track loot
        if 'You get' in clean_text:
            items = re.findall(r'You get ([^.]+)', clean_text)
            for item in items:
                self.loot_obtained.append(item.strip())
                self.combat_log.append(f"[LOOT] Obtained: {item.strip()}")

    def generate_report(self):
        """Generate summary report"""
        report = []
        report.append("=" * 60)
        report.append("COMBAT SESSION SUMMARY")
        report.append("=" * 60)
        report.append(f"Mobs Killed: {self.mobs_killed}")
        report.append(f"Total XP Gained: {self.xp_gained}")
        report.append(f"Healing Sessions: {self.healing_sessions}")
        report.append(f"\nLoot Obtained ({len(self.loot_obtained)} items):")
        if self.loot_obtained:
            for item in self.loot_obtained:
                report.append(f"  - {item}")
        else:
            report.append("  (none)")
        report.append(f"\nCombat Log:")
        for entry in self.combat_log:
            report.append(f"  {entry}")
        report.append("=" * 60)
        return "\n".join(report)


def safe_send_receive(client, command, delay=0.8):
    """Send command and receive response with error handling"""
    try:
        client.send(command)
        time.sleep(delay)
        response = client.receive(timeout=1.5)
        return response
    except Exception as e:
        print(f"Error with command '{command}': {e}")
        return ""


def main():
    print("Starting MUD Combat Session")
    print("=" * 60)

    tracker = CombatTracker()

    # Create client
    client = MUDClient(
        host='localhost',
        port=4000,
        username='dummy',
        password='helloworld',
        auto_heal=False,  # We'll manage healing manually
        heal_threshold=40
    )

    if not client.connect():
        print("Failed to connect!")
        return

    try:
        # Login
        client.auto_login()

        # Enter game if at menu
        time.sleep(1)
        response = safe_send_receive(client, "1")
        if "Huh!?!" in response:
            print("Already in game, continuing...")

        # Initial assessment
        print("\n--- Initial Status Check ---")
        response = safe_send_receive(client, "score")
        print(response)

        response = safe_send_receive(client, "look")
        print(response)
        tracker.combat_log.append("Session started")

        # Check where we can go to find easier mobs
        print("\n--- Exploring for easier hunting grounds ---")

        # First, let's try to find a safer area
        # The goblin is too hard, let's explore
        directions_to_try = ['north', 'south', 'east', 'west']

        for direction in directions_to_try:
            print(f"\n--- Trying {direction} ---")
            response = safe_send_receive(client, direction)
            print(response)

            # Look around
            response = safe_send_receive(client, "look")
            print(response)

            # Check for mobs
            if 'rat' in response.lower() or 'bug' in response.lower() or 'newbie' in response.lower():
                print(f"Found potentially easier area to the {direction}!")
                tracker.combat_log.append(f"Moved {direction} to find easier mobs")
                break

            # Go back if nothing interesting
            opposite = {'north': 'south', 'south': 'north', 'east': 'west', 'west': 'east'}
            if direction in opposite:
                safe_send_receive(client, opposite[direction])

        # Combat loop - try to fight 3-5 mobs carefully
        max_kills = 5
        attempts = 0
        max_attempts = 10

        while tracker.mobs_killed < max_kills and attempts < max_attempts:
            attempts += 1

            print(f"\n--- Combat Attempt {attempts} ---")

            # Check current status
            response = safe_send_receive(client, "score")
            print(response)

            # Parse HP
            hp_match = re.search(r'You have (\d+)\((\d+)\) hit', response)
            if hp_match:
                current_hp = int(hp_match.group(1))
                max_hp = int(hp_match.group(2))
                hp_percent = (current_hp / max_hp) * 100

                print(f"HP: {current_hp}/{max_hp} ({hp_percent:.0f}%)")

                # Rest if HP is low
                if hp_percent < 60:
                    print("HP low, resting to recover...")
                    tracker.healing_sessions += 1
                    tracker.combat_log.append(f"Resting to recover HP ({current_hp}/{max_hp})")

                    safe_send_receive(client, "rest")
                    time.sleep(4)  # Wait for some recovery
                    safe_send_receive(client, "stand")

                    # Check HP after rest
                    response = safe_send_receive(client, "score")
                    print(response)

            # Look for targets
            response = safe_send_receive(client, "look")
            print(response)
            tracker.parse_combat_output(response)

            # Try to find an easy target
            # Look for keywords that indicate easy mobs
            easy_targets = ['rat', 'bug', 'rabbit', 'squirrel', 'cat']
            target_found = None

            for target in easy_targets:
                if target in response.lower():
                    target_found = target
                    break

            if not target_found:
                # No easy target, check what's available
                if 'goblin' in response.lower():
                    # Goblins are hard, let's move
                    print("Only hard mobs here, exploring...")
                    safe_send_receive(client, "north")
                    continue
                else:
                    print("No mobs found, moving to find some...")
                    safe_send_receive(client, "south")
                    continue

            print(f"Engaging {target_found}...")

            # Consider the mob first
            response = safe_send_receive(client, f"consider {target_found}")
            print(response)
            tracker.combat_log.append(f"Considering {target_found}")

            if "perfect match" in response.lower() or "easy" in response.lower():
                print("Good match, engaging!")
            elif "luck" in response.lower():
                print("Too hard, skipping...")
                continue

            # Initiate combat
            response = safe_send_receive(client, f"kill {target_found}", delay=1.0)
            print(response)
            tracker.parse_combat_output(response)
            tracker.combat_log.append(f"Attacked {target_found}")

            # Combat rounds - wait for combat to complete
            in_combat = True
            combat_rounds = 0
            max_rounds = 15

            while in_combat and combat_rounds < max_rounds:
                combat_rounds += 1
                time.sleep(1.2)

                # Just receive output without sending commands
                response = client.receive(timeout=1.0)
                if response:
                    print(response)
                    tracker.parse_combat_output(response)

                    # Check if combat ended
                    if 'is DEAD!' in response or 'is dead!' in response:
                        in_combat = False
                        print("Victory!")

                        # Loot the corpse
                        time.sleep(0.5)
                        response = safe_send_receive(client, "get all corpse")
                        print(response)
                        tracker.parse_combat_output(response)

                        # Brief rest
                        safe_send_receive(client, "rest")
                        time.sleep(2)
                        safe_send_receive(client, "stand")

                    elif 'You flee' in response or 'PANIC' in response:
                        in_combat = False
                        print("Fled from combat!")
                        tracker.combat_log.append("Fled from dangerous combat")

            # Small break between fights
            time.sleep(1)

        # Final status
        print("\n--- Final Status ---")
        response = safe_send_receive(client, "score")
        print(response)

        response = safe_send_receive(client, "inventory")
        print(response)

        # Generate report
        print("\n")
        report = tracker.generate_report()
        print(report)

        # Save report
        report_path = "/Users/dshri/code/claude-code-camp-2026-Q2/week0_explore/explore_architecture/02_agent_skills/mud-player-workspace/iteration-1/combat-test/with_skill/outputs/combat_results.txt"
        with open(report_path, 'w') as f:
            f.write(report)
        print(f"\nReport saved to: {report_path}")

        # Graceful logout
        print("\n--- Logging out ---")
        safe_send_receive(client, "quit")

    except KeyboardInterrupt:
        print("\n\nInterrupted by user!")
    except Exception as e:
        print(f"\nError during session: {e}")
        import traceback
        traceback.print_exc()
    finally:
        client.disconnect()
        print(f"\nSession log saved to: {client.log_file}")


if __name__ == '__main__':
    main()
