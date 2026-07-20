# solidworks-GPT-plugin

[![Validate plugin](https://github.com/Erfouni/solidworks-GPT-plugin/actions/workflows/validate.yml/badge.svg)](https://github.com/Erfouni/solidworks-GPT-plugin/actions/workflows/validate.yml)
[![Python 3.9+](https://img.shields.io/badge/Python-3.9%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Model Context Protocol](https://img.shields.io/badge/MCP-enabled-7C3AED)](https://modelcontextprotocol.io/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

An installable Codex plugin that ports the knowledge workflow of
[`solidworks-claude-plugin`](https://github.com/mesutfd/solidworks-claude-plugin)
to OpenAI Codex.

It adds five coordinated skills:

- `solidworks-design` orchestrates requirements, planning, modeling, validation, and delivery.
- `sw-pre-start` loads conventions, active design rules, relevant references, and initial rule checks.
- `sw-kb-api` looks up catalog parts, published build instructions, macros, known errors, and lessons.
- `sw-learner` builds a complete, corrected feedback payload from the current SolidWorks session.
- `sw-session-reporter` asks for consent and submits feedback to the knowledge base.

The default knowledge base is `https://sw-plugin.ideep.org`. Override it with
the `SW_KB_HOST` environment variable. Read-only runtime endpoints are public;
session feedback is sent only after the user chooses **Yes, send now** or has
previously chosen **Always send**.

## Install from GitHub

```powershell
codex plugin marketplace add Erfouni/solidworks-GPT-plugin
codex plugin add solidworks-gpt-plugin@solidworks-gpt
```

Restart the ChatGPT desktop app or start a new Codex task after installation so
the new plugin skills are loaded.

For a local checkout, replace the GitHub shorthand in the first command with
the absolute path to this repository.

## Requirements

- Windows with SolidWorks installed for actual CAD work.
- A SolidWorks automation surface already available to Codex (for example a
  SolidWorks MCP/COM integration). This plugin supplies the design and knowledge
  workflow; it does not bundle or install SolidWorks itself.
- `curl` for knowledge-base calls.
- Python 3.9+ for the optional deterministic session and feedback utilities.

Knowledge-base outages never block CAD work. The skills record the outage and
continue with the available SolidWorks tooling and engineering context.

## Privacy and local state

- `.sw-learner-state.json` stores the current session ID and submission metadata
  in the working directory.
- `~/.sw-feedback-pref` contains `always` only after the user explicitly chooses
  **Always send**.
- Feedback may include build instructions, generated macros, resolved errors,
  lessons, and model images. The payload is never submitted without consent
  unless the saved `always` preference is present.

## Validate the plugin

From this repository root:

```powershell
python plugins/solidworks-gpt-plugin/scripts/run_checks.py
```

The repository also includes the original porting specification and the KB
admin OpenAPI reference under `plugins/solidworks-gpt-plugin/docs/`.

## Contributing

Bug reports, documentation improvements, and focused pull requests are
welcome. Start with [CONTRIBUTING.md](CONTRIBUTING.md), use the structured issue
templates, and run the repository checks before opening a pull request.

## License

MIT. See [LICENSE](LICENSE) and [NOTICE](NOTICE) for upstream attribution.
