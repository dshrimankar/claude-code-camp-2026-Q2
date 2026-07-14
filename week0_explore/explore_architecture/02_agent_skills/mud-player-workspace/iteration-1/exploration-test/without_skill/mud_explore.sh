#!/bin/bash

# MUD exploration script
OUTPUT_DIR="/Users/dshri/code/claude-code-camp-2026-Q2/week0_explore/explore_architecture/02_agent_skills/mud-player-workspace/iteration-1/exploration-test/without_skill/outputs"

# Commands to send to the MUD
{
    sleep 2
    echo "dummy"
    sleep 2
    echo "helloworld"
    sleep 2
    echo ""
    sleep 2
    echo "1"
    sleep 3
    echo "look"
    sleep 2
    echo "north"
    sleep 2
    echo "look"
    sleep 2
    echo "south"
    sleep 2
    echo "look"
    sleep 2
    echo "east"
    sleep 2
    echo "look"
    sleep 2
    echo "west"
    sleep 2
    echo "look"
    sleep 2
    echo "south"
    sleep 2
    echo "look"
    sleep 2
    echo "north"
    sleep 2
    echo "west"
    sleep 2
    echo "look"
    sleep 2
    echo "east"
    sleep 2
    echo "inventory"
    sleep 2
    echo "score"
    sleep 2
    echo "who"
    sleep 2
    echo "quit"
    sleep 1
} | nc localhost 4000 | tee "$OUTPUT_DIR/mud_session_full.log"
