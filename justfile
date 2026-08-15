# Default recipe - lists all available recipes
@_default:
    just --list

# Run alex linter on README.md to find inconsiderate writing
@alex:
	bunx alex README.md

# Install and update dependencies
@bootstrap:
    python -m pip install --upgrade pip uv
    uv pip install --upgrade --requirement pyproject.toml

# Generate table of contents and build the Zensical site
@build:
    just doctoc
    uv run zensical build --clean
    uv run python scripts/gen_llms.py site

# Generate table of contents for README.md
@doctoc:
    bunx doctoc README.md

# Serve the site with live reload on port 8000
@serve:
    uv run zensical serve --dev-addr localhost:8000

# Run linting on all files
@lint *ARGS:
    # -uv --quiet tool run curlylint _layouts/
    # -bunx awesome-lint README.md
    uv tool run --with pre-commit-uv pre-commit run {{ ARGS }} --all-files

# Remove the generated site
@clean:
    rm -rf site
