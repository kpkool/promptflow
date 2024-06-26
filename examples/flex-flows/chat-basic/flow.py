from dataclasses import dataclass
from pathlib import Path

from jinja2 import Template

from promptflow.tracing import trace
from promptflow.connections import AzureOpenAIConnection
from promptflow.tools.aoai import chat

BASE_DIR = Path(__file__).absolute().parent


@trace
def load_prompt(jinja2_template: str, question: str, chat_history: list) -> str:
    """Load prompt function."""
    with open(BASE_DIR / jinja2_template, "r", encoding="utf-8") as f:
        tmpl = Template(f.read(), trim_blocks=True, keep_trailing_newline=True)
        prompt = tmpl.render(question=question, chat_history=chat_history)
        return prompt


@dataclass
class Result:
    answer: str


class ChatFlow:
    def __init__(self, connection: AzureOpenAIConnection):
        self.connection = connection

    def __call__(
        self, question: str = "What is ChatGPT?", chat_history: list = None
    ) -> Result:
        """Flow entry function."""

        chat_history = chat_history or []

        prompt = load_prompt("chat.jinja2", question, chat_history)

        output = chat(
            connection=self.connection,
            prompt=prompt,
            deployment_name="gpt-35-turbo",
            max_tokens=256,
            temperature=0.7,
        )
        return Result(answer=output)


if __name__ == "__main__":
    from promptflow.tracing import start_trace
    from promptflow.client import PFClient

    start_trace()
    pf = PFClient()
    connection = pf.connections.get("open_ai_connection", with_secrets=True)
    flow = ChatFlow(connection=connection)
    result = flow("What's Azure Machine Learning?", [])
    print(result)
