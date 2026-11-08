"""Offline tests: a scripted fake LLM stands in for Claude."""

import os

os.environ.setdefault("CREWAI_TRACING_ENABLED", "false")
os.environ.setdefault("OTEL_SDK_DISABLED", "true")

from crewai.llms.base_llm import BaseLLM  # noqa: E402

from crewai_agentcore.crew import run  # noqa: E402


class ScriptedLLM(BaseLLM):
    """Returns canned answers in order and records every prompt it was sent."""

    replies: list[str] = []
    prompts: list[str] = []

    def call(self, messages, tools=None, callbacks=None, available_functions=None,
             from_task=None, from_agent=None, response_model=None):
        text = messages if isinstance(messages, str) else "\n".join(str(m.get("content", "")) for m in messages)
        self.prompts.append(text)
        return f"Thought: I can answer now.\nFinal Answer: {self.replies[len(self.prompts) - 1]}"


def make_llm(*replies):
    return ScriptedLLM(model="scripted", replies=list(replies), prompts=[])


def test_tasks_run_in_order_and_context_flows_forward():
    llm = make_llm("ANALYSIS: must know RAG", "PLAN: day 1 build RAG")
    out = run("Posting text XYZ", "Profile text ABC", days=3, llm=llm)

    assert out == {"analysis": "ANALYSIS: must know RAG", "plan": "PLAN: day 1 build RAG"}
    first, second = llm.prompts
    assert "Posting text XYZ" in first and "Technical Recruiter" in first
    # the coach sees the profile, the day count, and the analyst's output
    assert "Profile text ABC" in second and "3 days" in second
    assert "ANALYSIS: must know RAG" in second


def test_agentcore_entrypoint_validates_payload():
    import agent

    assert agent.invoke({"posting": "x"}) == {"error": "missing field(s): profile"}
