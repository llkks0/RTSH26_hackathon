For this project you need uv installed.

You can get uv from https://docs.astral.sh/uv/getting-started/installation/

To install the dependencies, run:

```
uv sync
```

## Environment Setup

Create a `.env` file in the backend directory with your OpenAI API key:

```
OPENAI_API_KEY=your_openai_api_key_here
```

You can copy `.env.example` to `.env` and fill in your API key:

```
cp .env.example .env
```

Get your API key from https://platform.openai.com/api-keys

To run the project, run:

```
uv run main.py
```