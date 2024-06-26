import json
import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv
from jinja2 import Template

from promptflow.tracing import trace
from promptflow.connections import AzureOpenAIConnection
from promptflow.tools.aoai import AzureOpenAI

BASE_DIR = Path(__file__).absolute().parent


@trace
def load_prompt(jinja2_template: str, code: str, examples: list) -> str:
    """Load prompt function."""
    with open(BASE_DIR / jinja2_template, "r", encoding="utf-8") as f:
        tmpl = Template(f.read(), trim_blocks=True, keep_trailing_newline=True)
        prompt = tmpl.render(code=code, examples=examples)
        return prompt


@dataclass
class Result:
    correctness: float
    readability: float
    explanation: str


@trace
def eval_code(code: str) -> Result:
    """Evaluate the code based on correctness, readability."""
    examples = [
        {
            "code": 'print("Hello, world!")',
            "correctness": 5,
            "readability": 5,
            "explanation": "The code is correct as it is a simple question and answer format. "
            "The readability is also good as the code is short and easy to understand.",
        }
    ]

    prompt = load_prompt("prompt.md", code, examples)

    if "AZURE_OPENAI_API_KEY" not in os.environ:
        # load environment variables from .env file
        load_dotenv()

    if "AZURE_OPENAI_API_KEY" not in os.environ:
        raise Exception("Please specify environment variables: AZURE_OPENAI_API_KEY")

    connection = AzureOpenAIConnection.from_env()

    output = AzureOpenAI(connection).chat(
        prompt=prompt,
        deployment_name="gpt-35-turbo",
        max_tokens=256,
        temperature=0.7,
    )
    output = Result(**json.loads(output))
    return output


if __name__ == "__main__":
    from promptflow.tracing import start_trace

    start_trace()

    result = eval_code('print("Hello, world!")')
    print(result)
