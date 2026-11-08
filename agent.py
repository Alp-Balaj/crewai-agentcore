"""Amazon Bedrock AgentCore Runtime entrypoint.

BedrockAgentCoreApp is a small HTTP server with the contract AgentCore expects:
  POST /invocations   JSON payload in, JSON out (our @app.entrypoint)
  GET  /ping          health check
It listens on port 8080. Locally: `uv run python agent.py`, then

  curl -X POST localhost:8080/invocations -H 'content-type: application/json' \
       -d '{"posting": "...", "profile": "...", "days": 7}'
"""

from bedrock_agentcore.runtime import BedrockAgentCoreApp

from crewai_agentcore.crew import run

app = BedrockAgentCoreApp()


@app.entrypoint
def invoke(payload: dict) -> dict:
    missing = [k for k in ("posting", "profile") if not payload.get(k)]
    if missing:
        return {"error": f"missing field(s): {', '.join(missing)}"}
    return run(payload["posting"], payload["profile"], int(payload.get("days", 14)))


if __name__ == "__main__":
    app.run()
