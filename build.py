#!/usr/bin/env python3
"""Minimal markdown blog generator."""

import os
import re
import shutil
from datetime import datetime

import mistune
import yaml
from jinja2 import Environment, FileSystemLoader
from pygments import highlight
from pygments.formatters import HtmlFormatter
from pygments.lexers import get_lexer_by_name, guess_lexer
from pygments.styles import get_style_by_name


# --- Config ---

def load_config(path="config.yaml"):
    with open(path) as f:
        return yaml.safe_load(f)


# --- Markdown parsing ---

def parse_front_matter(text):
    """Extract YAML front matter and body from markdown text."""
    match = re.match(r"^---\s*\n(.*?)\n---\s*\n(.*)", text, re.DOTALL)
    if match:
        meta = yaml.safe_load(match.group(1))
        body = match.group(2)
    else:
        meta = {}
        body = text
    return meta, body


def make_markdown_renderer(code_theme):
    """Create a mistune renderer with Pygments syntax highlighting."""
    formatter = HtmlFormatter(style=code_theme, cssclass="highlight")

    class HighlightRenderer(mistune.HTMLRenderer):
        def block_code(self, code, info=None):
            if info:
                try:
                    lexer = get_lexer_by_name(info)
                except Exception:
                    lexer = guess_lexer(code)
            else:
                try:
                    lexer = guess_lexer(code)
                except Exception:
                    lexer = get_lexer_by_name("text")
            return highlight(code, lexer, formatter)

    return mistune.Markdown(renderer=HighlightRenderer())


# --- File scanning ---

def scan_content(directory):
    """Scan a directory for .md files and return parsed content."""
    items = []
    if not os.path.isdir(directory):
        return items
    for filename in sorted(os.listdir(directory)):
        if not filename.endswith(".md"):
            continue
        filepath = os.path.join(directory, filename)
        with open(filepath) as f:
            text = f.read()
        meta, body = parse_front_matter(text)
        slug = meta.get("slug", filename.removesuffix(".md"))
        items.append({
            "meta": meta,
            "body": body,
            "slug": slug,
            "title": meta.get("title", slug.replace("-", " ").title()),
            "date": meta.get("date"),
        })
    return items


# --- Build ---

def build():
    config = load_config()
    md = make_markdown_renderer(config["style"]["code_theme"])

    # Clean and create output directory
    if os.path.exists("output"):
        shutil.rmtree("output")
    os.makedirs("output")

    # Generate Pygments CSS
    formatter = HtmlFormatter(
        style=config["style"]["code_theme"],
        cssclass="highlight",
    )
    pygments_css = formatter.get_style_defs()

    # Build style.css
    style = config["style"]
    css = f"""\
:root {{
  --font-family: {style['font_family']};
  --font-size: {style['font_size']};
  --line-height: {style['line_height']};
  --max-width: {style['max_width']};
  --bg: {style['background']};
  --text: {style['text_color']};
  --link: {style['link_color']};
}}

*, *::before, *::after {{
  box-sizing: border-box;
}}

body {{
  font-family: var(--font-family);
  font-size: var(--font-size);
  line-height: var(--line-height);
  color: var(--text);
  background: var(--bg);
  margin: 0;
  padding: 0;
}}

header {{
  border-bottom: 1px solid #eee;
  padding: 1rem 0;
}}

nav {{
  max-width: var(--max-width);
  margin: 0 auto;
  padding: 0 1rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
}}

.site-title {{
  font-weight: 700;
  font-size: 1.2rem;
  text-decoration: none;
  color: var(--text);
}}

.nav-links a {{
  margin-left: 1.5rem;
  text-decoration: none;
  color: var(--link);
}}

.nav-links a:hover {{
  text-decoration: underline;
}}

main {{
  max-width: var(--max-width);
  margin: 2rem auto;
  padding: 0 1rem;
}}

a {{
  color: var(--link);
}}

h1, h2, h3 {{
  margin-top: 2em;
  margin-bottom: 0.5em;
}}

pre {{
  position: relative;
  background: #282a36;
  border-radius: 6px;
  padding: 1rem;
  overflow-x: auto;
}}

pre code {{
  font-size: 0.9em;
  line-height: 1.5;
}}

code {{
  font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
}}

:not(pre) > code {{
  background: #f0f0f0;
  padding: 0.15em 0.4em;
  border-radius: 3px;
  font-size: 0.9em;
}}

.copy-btn {{
  position: absolute;
  top: 0.5rem;
  right: 0.5rem;
  background: rgba(255, 255, 255, 0.1);
  color: #ccc;
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 4px;
  padding: 0.25rem 0.5rem;
  font-size: 0.75rem;
  cursor: pointer;
  font-family: var(--font-family);
}}

.copy-btn:hover {{
  background: rgba(255, 255, 255, 0.2);
  color: #fff;
}}

blockquote {{
  border-left: 3px solid var(--link);
  margin: 1.5em 0;
  padding: 0.5em 1em;
  color: #666;
}}

.post-list {{
  list-style: none;
  padding: 0;
}}

.post-list li {{
  margin-bottom: 1.5rem;
}}

.post-list a {{
  text-decoration: none;
  font-weight: 600;
  font-size: 1.1rem;
}}

.post-list a:hover {{
  text-decoration: underline;
}}

.post-list .date {{
  color: #999;
  font-size: 0.85rem;
  margin-left: 0.5rem;
}}

.post-meta {{
  color: #999;
  font-size: 0.85rem;
  margin-bottom: 2rem;
}}

/* Pygments syntax highlighting */
{pygments_css}
"""
    with open(os.path.join("output", "style.css"), "w") as f:
        f.write(css)

    # Scan content
    posts = scan_content("posts")
    pages = scan_content("pages")

    # Convert markdown to HTML
    for post in posts:
        post["html"] = md(post["body"])
    for page in pages:
        page["html"] = md(page["body"])

    # Sort posts by date (newest first)
    posts.sort(key=lambda p: str(p.get("date", "")), reverse=True)

    # Set up Jinja2
    env = Environment(loader=FileSystemLoader("templates"))
    layout = env.get_template("layout.html")

    # Prepare page list for nav
    page_list = [{"slug": p["slug"], "title": p["title"]} for p in pages]

    # Render posts
    for post in posts:
        output = layout.render(
            config=config,
            title=post["title"],
            pages=page_list,
            content=f'<div class="post-meta">{post["date"]}</div>\n{post["html"]}',
        )
        with open(os.path.join("output", f"{post['slug']}.html"), "w") as f:
            f.write(output)

    # Render pages
    for page in pages:
        output = layout.render(
            config=config,
            title=page["title"],
            pages=page_list,
            content=page["html"],
        )
        with open(os.path.join("output", f"{page['slug']}.html"), "w") as f:
            f.write(output)

    # Render index
    post_list_html = '<ul class="post-list">\n'
    for post in posts:
        date_str = f'<span class="date">{post["date"]}</span>' if post.get("date") else ""
        post_list_html += f'  <li><a href="{post["slug"]}.html">{post["title"]}</a>{date_str}</li>\n'
    post_list_html += '</ul>'

    output = layout.render(
        config=config,
        title=None,
        pages=page_list,
        content=post_list_html,
    )
    with open(os.path.join("output", "index.html"), "w") as f:
        f.write(output)

    print(f"Built {len(posts)} post(s) and {len(pages)} page(s) → output/")


if __name__ == "__main__":
    build()
