# About

GATE is a system designed for AI agents to execute actions that require credentials or access to external systems.

Rather than give the AI agent the credentials to perform actions, the AI agent passes off execution to GATE.

GATE uses policies to determine if the action requires approval first, and seeks approval.

GATE then executes the action, passing in credentials as necessary. The AI agent never has access to the credentials.

See [DESIGN.md](DESIGN.md) for design details.