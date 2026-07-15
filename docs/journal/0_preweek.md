# Preweek Technical Documentation

## Technical Goal
The technical goal of Preweek (Explore) is to determine how well do Agent Architectures fit our business use-case.

[Ref 1] Examples of Agent Architectures That Scale With Effort:
- An agent file with referenced files eg. AGENT.md,  @~/docs/*.MD
- Agent Skills driven by main agent eg. ~/.skills
- Filesystem Subagent driven by a coding harness or Coding Agent SDK eg. ~/subagents
- AI workflow automation platform eg. n8n
- Use a generic AI Agent SDK that leverages plug and plays generic AI packages.
- Use low level first-party LLM SDKs and write our own agentic loop
- Use REST APIs directly, write our own agentic loop
  - The agentic loop is model-driven orchestration  with middleware programmatic guidance
  - The agentic loop is code-driven orchestration

## Technical Uncertainty
- I'm uncertain if an coding harnesses agentic loop is effective/productive enough to drive a non-coding workload.
- I'm uncertain if LLMs model's thinking mode and other intelligent parameters is sufficent enough to hold memory and drive decisions for work specific use-case.
- I'm uncertain that coding harnesses can interact with a MUD without an interface or SDK or manage the telnet session.

## ## Technical Hypotheses
- Based on our [Ref 1] I think that we will have issues with the coding harness driving the MUD without an interface because we don't a defined API, we are driving commands over a protocol that we need to live-monitor. Telnet communication seems like it would be a sticking point.

- I think we will need an interface because mangaging a long-lived telnet session may prove difficult.

- I think that models memory will not be able to remember and navigate the complex world of MUD.

- I think that we need our own agent.

## Technical Observerations
- An Agent.md could connect to the MUD via nc, it produced scripts to connect to the MUD, however it had challenges to understand the MUD login flow.
- Skills and Subagents preformed accompanied with a script to manage the nc session. They were able to play the MUD, but maybe not efficiently

## Technical Conclusions
- Skills and Subagents are capable of driving the MUD.
- We need specialized memory for map navigation and world data
- We could not explore n8n completely due to technical restraints executing external scripts.
- Implementing our own specialized loops remain technically uncertain and will need to be explored in depth in Week 2.
- Without a customized agentic loop the agents could not preform goals efficently. And did not have any key meta strategies or journey player strategies.

## Key Takeaway
When we have a specialized use-case like a playing MUD, we likely cannot leverage generic SDKs for Agents because we need specialized tooling and agentic loops.