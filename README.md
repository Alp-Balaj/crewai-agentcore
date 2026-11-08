# crewai-agentcore

Day 3: CrewAI quickstart, plus an Amazon Bedrock AgentCore entrypoint.

**JobFit**, a two-agent crew running on Claude. Give it a job posting and a short profile of yourself; a *requirements analyst* pulls out what the role really needs, then a *career coach* compares that with your background and writes a day-by-day prep plan. The same crew is wrapped as an AgentCore Runtime agent so it can be deployed to AWS.

```
posting ─► requirements_analyst ─► analysis ─┐
                                              ├─► career_coach ─► gap analysis + N-day plan
profile, days ────────────────────────────────┘
```

## Run it locally

```sh
export ANTHROPIC_API_KEY=...
uv sync
uv run jobfit examples/posting.md examples/profile.md --days 14 -o report.md
```

Edit `examples/profile.md` to describe yourself and drop in a real posting. `JOBFIT_MODEL` overrides the model (default `claude-opus-5-5`).

## CrewAI concepts in this repo

| Concept | Where |
|---|---|
| **Agent** (role, goal, backstory, llm) | `src/crewai_agentcore/config/agents.yaml`, built in `crew.py` |
| **Task** (description with `{placeholders}`, expected output, agent) | `config/tasks.yaml` |
| **Context** between tasks | `plan_study.context: [analyze_posting]` feeds the analysis into the coach's prompt |
| **Crew + Process** | `JobFitCrew.crew()`: `Process.sequential` runs tasks in order (`Process.hierarchical` would add a manager agent that delegates) |
| **@CrewBase** | collects every `@agent` / `@task` method into `self.agents` / `self.tasks` |
| **Kickoff** | `crew.kickoff(inputs={...})` fills the `{posting}`, `{profile}`, `{days}` placeholders |
| **LLM** | `LLM(model="anthropic/claude-opus-5-5")` uses CrewAI's native Anthropic provider |

## AgentCore overview

Amazon Bedrock AgentCore is AWS's set of managed services for running agents built with any framework (CrewAI, LangGraph, Strands, plain code) and any model:

| Service | What it gives you |
|---|---|
| **Runtime** | Serverless hosting for an agent container, isolated per session, long-running (up to 8 h) |
| **Memory** | Short-term (session) and long-term (extracted facts, preferences) memory |
| **Gateway** | Turns APIs and Lambda functions into MCP tools for agents |
| **Identity** | Inbound auth for callers, outbound OAuth/API-key credentials for tools |
| **Code Interpreter / Browser** | Sandboxed code execution and a managed headless browser |
| **Observability** | OpenTelemetry traces, logs and metrics in CloudWatch |
| **Policy / Evaluations** | Guardrails on tool calls; quality scoring of agent runs |

This project uses **Runtime**. The contract is small: an HTTP server on port 8080 with `POST /invocations` and `GET /ping`. `bedrock_agentcore.runtime.BedrockAgentCoreApp` provides it; `agent.py` registers the crew as the `@app.entrypoint`.

### Try the runtime contract locally (no AWS needed)

```sh
uv run python agent.py
# in another terminal
curl -X POST localhost:8080/invocations -H 'content-type: application/json' \
     -d "$(jq -n --rawfile p examples/posting.md --rawfile q examples/profile.md '{posting:$p, profile:$q, days:7}')"
```

### Deploy to AWS (needs an AWS account and credentials)

The starter toolkit (`agentcore` CLI, installed as a dev dependency) builds the container in CodeBuild, pushes it to ECR and creates the runtime:

```sh
uv export --no-dev --no-hashes -o requirements.txt   # refresh after changing deps
uv run agentcore configure -e agent.py -rf requirements.txt -r us-east-1
uv run agentcore deploy --env ANTHROPIC_API_KEY=$ANTHROPIC_API_KEY
uv run agentcore invoke '{"posting": "...", "profile": "...", "days": 7}'
uv run agentcore destroy                              # tear it down when finished
```

Notes:
- Passing the key with `--env` is fine for a tutorial. For anything real, store it in AWS Secrets Manager or AgentCore Identity and read it at startup.
- To keep everything inside AWS, call Claude through Amazon Bedrock instead: `LLM(model="bedrock/<bedrock model id>")` and give the runtime's execution role Bedrock invoke permissions.
- I haven't run the AWS deploy steps from this machine (no AWS credentials here). The local runtime contract is tested.

## Tests

```sh
uv run pytest
```

A scripted fake LLM checks that the tasks run in order, that the analyst's output reaches the coach, and that the AgentCore entrypoint validates its payload. No API key needed.

## Things to try

- Give the analyst a tool (`crewai_tools.ScrapeWebsiteTool`) so it can take a posting URL.
- Switch to `Process.hierarchical` with a manager LLM and watch it delegate.
- Add `output_pydantic=` to `analyze_posting` to get typed JSON instead of Markdown.
- Enable AgentCore Memory so the coach remembers your profile between sessions.
