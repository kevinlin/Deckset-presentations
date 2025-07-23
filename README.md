# Deckset Presentations

A Python tool for generating presentations using Markdown and Jinja2 templates.

## Features

- Convert Markdown files to presentation formats
- Use Jinja2 templates for customizable presentation layouts
- Simple and extensible architecture

## Installation

This project uses [uv](https://docs.astral.sh/uv/) as the package manager.

```bash
# Clone the repository
git clone <repository-url>
cd deckset-presentations

# Install dependencies
uv sync
```

## Usage

```bash
# Activate the virtual environment
source .venv/bin/activate

# Run the main script
python main.py
```

## Development

```bash
# Add new dependencies
uv add <package-name>

# Add development dependencies
uv add --dev <package-name>

# Run in development mode
uv run python main.py
```

## Dependencies

- **markdown**: For parsing Markdown files
- **jinja2**: For template rendering

## License

MIT License