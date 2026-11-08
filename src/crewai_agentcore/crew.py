"""A two-agent crew: a requirements analyst, then a career coach.

CrewAI vocabulary:
  Agent    a role + goal + backstory, backed by an LLM (config/agents.yaml)
  Task     a description + expected output, assigned to one agent (config/tasks.yaml)
  Crew     agents + tasks + a process. Process.sequential runs tasks in order and
           passes earlier outputs forward (see `context:` in tasks.yaml).
"""

import os

from crewai import LLM, Agent, Crew, Process, Task
from crewai.llms.base_llm import BaseLLM
from crewai.project import CrewBase, agent, crew, task


def claude_llm() -> LLM:
    # "anthropic/..." routes to CrewAI's native Anthropic provider; it reads
    # ANTHROPIC_API_KEY. Opus 5.5 thinks adaptively by default, so no thinking config.
    return LLM(model=f"anthropic/{os.environ.get('JOBFIT_MODEL', 'claude-opus-5-5')}", max_tokens=16000)


@CrewBase
class JobFitCrew:
    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"

    def __init__(self, llm: BaseLLM | None = None):
        self.llm = llm or claude_llm()

    @agent
    def requirements_analyst(self) -> Agent:
        return Agent(config=self.agents_config["requirements_analyst"], llm=self.llm, verbose=False)

    @agent
    def career_coach(self) -> Agent:
        return Agent(config=self.agents_config["career_coach"], llm=self.llm, verbose=False)

    @task
    def analyze_posting(self) -> Task:
        return Task(config=self.tasks_config["analyze_posting"])

    @task
    def plan_study(self) -> Task:
        return Task(config=self.tasks_config["plan_study"])

    @crew
    def crew(self) -> Crew:
        # self.agents / self.tasks are collected from the decorated methods above.
        return Crew(agents=self.agents, tasks=self.tasks, process=Process.sequential, verbose=False)


def run(posting: str, profile: str, days: int = 14, llm: BaseLLM | None = None) -> dict:
    result = JobFitCrew(llm).crew().kickoff(inputs={"posting": posting, "profile": profile, "days": days})
    analysis, plan = (t.raw for t in result.tasks_output)
    return {"analysis": analysis, "plan": plan}
