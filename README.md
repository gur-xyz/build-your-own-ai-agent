# Build Your Own AI Agent

A small Python starter project that demonstrates the core AI agent pattern:

```text
profile + memory + tools + loop
```

This repository is intentionally simple:

- no framework
- no external Python dependencies
- supports OpenAI or OpenRouter through the standard library
- includes an offline mock mode for tests

## What This Shows

An agent is software that can:

1. receive a user request
2. load relevant context
3. ask a model what to do next
4. run a tool if the model asks for one
5. feed the tool result back to the model
6. answer or continue the loop

```text
User request
      ↓
Load profile/context
      ↓
Model decides: answer or use a tool
      ↓
Tool runs
      ↓
Tool result returns
      ↓
Answer or loop again
```

## Setup

Use Python 3.10 or newer.

No Python packages are required.

### OpenRouter

```bash
export OPENROUTER_API_KEY="your_key_here"
export AGENT_MODEL="openai/gpt-4o-mini"
python3 main.py product "How do refunds work?"
```

### OpenAI

```bash
export OPENAI_API_KEY="your_key_here"
export AGENT_MODEL="gpt-4o-mini"
python3 main.py product "How do refunds work?"
```

### Offline mock mode

```bash
python3 main.py --brain mock personal "What should I focus on today?"
python3 main.py --brain mock product "How do refunds work?"
python3 main.py --brain mock product "My payment failed and I need a human"
```

## Demo Modes

### Personal companion

Loads a profile and searches local notes.

```bash
python3 main.py personal "What should I focus on today?"
```

### Product copilot

Searches product documentation and answers from the matched content.

```bash
python3 main.py product "How do refunds work?"
```

### Human handoff

Creates a fake support ticket when the request should be escalated.

```bash
python3 main.py product "My payment failed and I need a human"
```

## Quick Start

```bash
git clone https://github.com/gur-xyz/build-your-own-ai-agent.git
cd build-your-own-ai-agent
python3 -m unittest discover -s tests -v
python3 main.py --brain mock product "How do refunds work?"
```

Then add an API key and run the real model path.

## Project Structure

```text
build-your-own-ai-agent/
├── main.py                         # CLI entry point
├── agent.py                        # agent loop + real/mocked brain
├── tools/                          # tools the agent can use
│   ├── notes.py                    # searches local notes
│   ├── product_docs.py             # searches product docs
│   ├── calculator.py               # safe tiny calculator
│   └── tickets.py                  # fake human escalation
├── profiles/                       # agent profiles
│   ├── personal_companion.json
│   └── product_copilot.json
├── data/                           # local memory / knowledge base
│   ├── personal_notes.txt
│   └── product_docs.txt
├── tests/
│   └── test_agent.py
└── requirements.txt
```

## How It Maps To Real Agents

| Starter kit idea | Real-world version |
|---|---|
| `OpenAICompatibleBrain` | GPT, Claude-through-OpenRouter, DeepSeek, Llama, or another compatible model |
| `profile.json` | system prompt and user/product preferences |
| text files in `data/` | memory store, database, or vector index |
| `tools/*.py` | APIs, browser, terminal, CRM, database, ticketing tools |
| ticket tool | Zendesk, Intercom, Linear, Jira, or another workflow system |
| loop in `agent.py` | agent runtime |

## Safety Note

Start with read-only tools. Add write actions only after you understand approvals, logs, and permissions.
