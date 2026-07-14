# Exploring Agent Architectures

An agent file with referenced files eg: AGENT.md, @~/docs/*.md

Observations:
 - Claude Code will read local files outside of the 001_playing_agent folder with Haiku and waste tokens
 - Claude Code fails to login and starts exploring other local files
 - The Agent created temp files to create socket connection and execute commands
 - On changing the model to Sonnet, Claude Code will generate python files in the 001_playing_agent directory instead of creating in the tmp folder