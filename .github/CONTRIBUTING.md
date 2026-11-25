# How to contribute to steam.py

This file should outline how to contribute to steam.py.  
There are a couple of aspects when it comes to contributing to the library which are as follows:

- [Bug reporting](#bug-reports)
- [Feature requests](#feature-requests)
- [Creating a PR (Pull Request)](#pull-requests)

## Bug reports

A bug report should include a full traceback, python/system version information to describe the issue as best as you
can and how you produced it. If possible logs would be useful with any API keys or other sensitive information removed.

## Feature requests

A feature request should as good of an explanation of what the feature would do, why this feature might be useful and
any relevant links to further reading (if applicable).

## Pull requests

Submitting a pull request is fairly simple. It is best to keep commits focused on one aspect of the library. It would
be better if the style is consistent with that found in the project. This project is formatted and linted with
[ruff](https://docs.astral.sh/ruff/) with a column limit of 120. But don't worry too much about meeting this, pre-commit
will fix anything before it is merged.

**Development setup**

The project is managed with [uv](https://docs.astral.sh/uv/).

- Install the dev tools and optional speedups: `uv sync --group speedups --group examples`
- Run the unit tests: `uv run pytest tests/unit`
- Format and lint: `uv run ruff format` and `uv run ruff check --fix`
- Build the docs (needs Python 3.12 or older): `uv run --python 3.12 --group docs sphinx-build -b html -T -W --keep-going docs/ docs/_build`
- Decode a Steam WS message: `uv run python -m scripts.decode <base64 message>`

### Git Commit Guidelines

- Use present tense (e.g. "Add feature" not "Added feature")
- Limit commit messages to 79 characters or less.
- Reference issues or pull requests outside of the first line.
  - Please use the shorthand for the issue (#123) and not the full URL.

Thank you for taking any time to perform any of these actions they help to make the library better for everyone.
