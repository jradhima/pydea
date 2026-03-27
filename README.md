# pydeas

A minimal markdown blog generator. Write posts in Markdown, get a static site with syntax highlighting and copy buttons.

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Usage

```bash
python build.py
```

Open `output/index.html` in your browser.

## Project Structure

```
├── config.yaml       # Site title, fonts, colors, code theme
├── build.py          # Build script
├── templates/        # HTML template
├── posts/            # Blog posts (.md files with front matter)
├── pages/            # Static pages (About, etc.)
└── output/           # Generated site
```

## Adding Posts

Create a `.md` file in `posts/`:

```markdown
---
title: "My Post"
date: 2026-03-27
---

# My Post

Content goes here.
```

## Adding Pages

Create a `.md` file in `pages/`:

```markdown
---
title: About
---

# About

This page is linked in the nav bar.
```

## Configuration

Edit `config.yaml`:

```yaml
site:
  title: "My Blog"
  description: "A simple blog"

style:
  font_family: "system-ui, -apple-system, sans-serif"
  font_size: "18px"
  line_height: "1.7"
  max_width: "720px"
  code_theme: "monokai"   # any Pygments theme
  background: "#ffffff"
  text_color: "#333333"
  link_color: "#0066cc"
```
