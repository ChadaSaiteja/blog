import os
import sys
import re
import glob
from datetime import datetime
from flask import Flask, request, jsonify, send_from_directory, Response
from html import escape
import markdown
import yaml

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from quality import BlogQualityAnalyzer
from liquid_render import LiquidRenderer, render_layout

app = Flask(__name__)
WORKSPACE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
POSTS_DIR = os.path.join(WORKSPACE_DIR, "_posts")

# Extensions applied to a post body. Deliberately excludes `codehilite`:
# it discards the fence's language, so render_post_markdown does the
# highlighting itself to match kramdown + rouge output exactly.
# `toc` is included so the preview produces the same heading ids the real
# build does, which is what the table of contents in assets/js/main.js reads.
MARKDOWN_EXTENSIONS = [
    "fenced_code",
    "tables",
    "sane_lists",
    "attr_list",
    "toc",
]

os.makedirs(POSTS_DIR, exist_ok=True)

def parse_markdown_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
        
    fm_match = re.match(r'^---\r?\n(.*?)\r?\n---\r?\n(.*)$', content, re.DOTALL)
    if not fm_match:
        return {}, content
        
    fm_text = fm_match.group(1)
    body = fm_match.group(2)
    
    metadata = {}
    for line in fm_text.splitlines():
        if ':' in line:
            k, v = line.split(':', 1)
            k = k.strip()
            v = v.strip().strip('"').strip("'")
            if v.lower() == 'true':
                v = True
            elif v.lower() == 'false':
                v = False
            metadata[k] = v
            
    categories = re.findall(r'categories:\s*\n((?:\s*-\s*[^\n]+\n?)+)', fm_text)
    if categories:
        metadata["categories"] = [item.replace("-", "").strip() for item in categories[0].strip().splitlines()]
    elif "categories" in metadata and isinstance(metadata["categories"], str):
        metadata["categories"] = [c.strip() for c in metadata["categories"].split(",")]
        
    tags = re.findall(r'tags:\s*\n((?:\s*-\s*[^\n]+\n?)+)', fm_text)
    if tags:
        metadata["tags"] = [item.replace("-", "").strip() for item in tags[0].strip().splitlines()]
    elif "tags" in metadata and isinstance(metadata["tags"], str):
        metadata["tags"] = [t.strip() for t in metadata["tags"].split(",")]

    return metadata, body

def write_markdown_file(filepath, metadata, body):
    fm_lines = ["---"]
    for k, v in metadata.items():
        if k in ["categories", "tags"] and isinstance(v, list):
            fm_lines.append(f"{k}:")
            for item in v:
                fm_lines.append(f"  - {item}")
        else:
            if isinstance(v, bool):
                fm_lines.append(f"{k}: {str(v).lower()}")
            else:
                fm_lines.append(f"{k}: {v}")
    fm_lines.append("---")
    
    full_content = "\n".join(fm_lines) + "\n" + body
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(full_content)

def get_all_posts(include_drafts=False):
    posts = []
    files = glob.glob(os.path.join(POSTS_DIR, "*.md"))
    for fpath in files:
        filename = os.path.basename(fpath)
        try:
            meta, body = parse_markdown_file(fpath)
            # Generate URL slug
            slug_match = re.search(r'\d{4}-\d{2}-\d{2}-(.*)\.md$', filename)
            slug = slug_match.group(1) if slug_match else filename.replace(".md", "")
            url = f"/blog/{slug}"
            
            # Simple word count read time calculation
            words = len(body.strip().split())
            reading_time = f"{max(1, round(words / 200))} min read"
            
            is_draft = meta.get("draft", False)
            if not is_draft or include_drafts:
                posts.append({
                    "filename": filename,
                    "slug": slug,
                    "url": url,
                    "title": meta.get("title", filename),
                    "description": meta.get("description", ""),
                    "date": meta.get("date", ""),
                    "author": meta.get("author", "Saiteja"),
                    "draft": is_draft,
                    "categories": meta.get("categories", []),
                    "tags": meta.get("tags", []),
                    "reading_time": reading_time,
                    "body": body
                })
        except Exception as e:
            print(f"Error parsing {filename}: {e}")
            
    posts.sort(key=lambda x: str(x["date"]), reverse=True)
    return posts

def strip_jekyll_frontmatter(content):
    """Strip Jekyll YAML frontmatter (--- ... ---) from HTML/markdown files."""
    fm_match = re.match(r'^---\r?\n.*?\r?\n---\r?\n', content, re.DOTALL)
    if fm_match:
        return content[fm_match.end():]
    return content

# Liquid rendering lives in scripts/blog/liquid_render.py, which parses the
# real _layouts/ and _includes/ templates against the real _data/blog_style.yml
# instead of pattern-matching them. The previous regex emulator here silently
# dropped markup as soon as a layout used {% assign %}, a nested {% for %} or
# {% include %} with arguments.


# --- PUBLIC ROUTE SERVINGS ---

def build_site_context():
    """The Jekyll `site` object, built from _config.yml and _data/*.yml.

    Reads the same style config the real build reads, so the dev preview and
    the deployed site cannot disagree about tokens, categories or navigation.
    """
    config = {}
    config_path = os.path.join(WORKSPACE_DIR, "_config.yml")
    if os.path.exists(config_path):
        with open(config_path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f) or {}

    data = {}
    data_dir = os.path.join(WORKSPACE_DIR, "_data")
    if os.path.isdir(data_dir):
        for name in sorted(os.listdir(data_dir)):
            if name.endswith((".yml", ".yaml")):
                with open(os.path.join(data_dir, name), "r", encoding="utf-8") as f:
                    data[os.path.splitext(name)[0]] = yaml.safe_load(f) or {}

    posts = get_all_posts(include_drafts=True)
    posts = sorted(
        posts,
        key=lambda p: (str(p.get("date") or ""), p.get("slug", "")),
        reverse=True,
    )

    return {
        "title": config.get("title", ""),
        "description": config.get("description", ""),
        "url": config.get("url", ""),
        "baseurl": config.get("baseurl", ""),
        "time": datetime.now(),
        "data": data,
        "posts": posts,
    }


def build_post_context(post_dict, site):
    """A Jekyll `page` object for one post, with previous/next resolved."""
    posts = site["posts"]
    slugs = [p.get("slug") for p in posts]
    try:
        position = slugs.index(post_dict.get("slug"))
    except ValueError:
        position = 0

    page = dict(post_dict)
    page["layout"] = "post"
    page["date"] = post_dict.get("date")
    # Jekyll's `previous` is the older post, `next` the newer one.
    page["previous"] = posts[position + 1] if position + 1 < len(posts) else None
    page["next"] = posts[position - 1] if position > 0 else None
    return page


FENCE_HTML_RE = re.compile(
    r'<pre><code(?: class="language-([^"]+)")?>(.*?)</code></pre>',
    re.DOTALL,
)


def _highlight_code(source, language):
    """Syntax-highlight one block, or return it escaped when Pygments is absent.

    Pygments token class names do not match Rouge's one for one, so preview
    colours are close to but not identical with the deployed site. The
    surrounding markup is identical, which is what the .code-box chrome, the
    language label and the copy button actually depend on.
    """
    if not language:
        return escape(source)
    try:
        from pygments import highlight as pygments_highlight
        from pygments.formatters import HtmlFormatter
        from pygments.lexers import get_lexer_by_name
        from pygments.util import ClassNotFound
    except ImportError:
        return escape(source)
    try:
        lexer = get_lexer_by_name(language, stripall=True)
    except ClassNotFound:
        return escape(source)
    formatter = HtmlFormatter(nowrap=True)
    return pygments_highlight(source, lexer, formatter)


def render_post_markdown(body):
    """Render a post body to the same markup shape kramdown + rouge produce.

    kramdown runs with input: GFM and syntax_highlighter_opts.css_class set to
    'highlight', so a fenced block comes out as

        <div class="language-bash highlighter-rouge"><div class="highlight">
        <pre class="highlight"><code class="language-bash" data-lang="bash">...</code>
        </pre></div></div>

    The old call used codehilite, which swallows the fence's language entirely,
    so the preview lost both the .highlight wrapper and the class the code box
    header reads its language label from.
    """
    html = markdown.markdown(
        body,
        extensions=MARKDOWN_EXTENSIONS,
        output_format="html",
    )

    def wrap(match):
        language = (match.group(1) or "").strip()
        source = match.group(2)
        source = (
            source.replace("&lt;", "<")
            .replace("&gt;", ">")
            .replace("&quot;", '"')
            .replace("&#39;", "'")
            .replace("&amp;", "&")
        )
        inner = _highlight_code(source, language)
        return (
            '<div class="language-{lang} highlighter-rouge"><div class="highlight">'
            '<pre class="highlight"><code class="language-{lang}" data-lang="{lang}">'
            "{inner}</code></pre></div></div>"
        ).format(lang=language or "text", inner=inner)

    return FENCE_HTML_RE.sub(wrap, html)


def render_page_file(path, site, page):
    with open(path, "r", encoding="utf-8") as f:
        source = strip_jekyll_frontmatter(f.read())
    renderer = LiquidRenderer(WORKSPACE_DIR)
    return renderer.render(source, [{"site": site, "page": page}])


def render_layout_file(name, site, page, content=""):
    path = os.path.join(WORKSPACE_DIR, "_layouts", name + ".html")
    output, unsupported = render_layout(WORKSPACE_DIR, name, {"site": site, "page": page}, content)
    return output, unsupported


def preview_banner(unsupported):
    """Dev-only notice when the preview could not resolve every construct."""
    if not unsupported:
        return ""
    items = "".join("<li>{}</li>".format(escape(u)) for u in sorted(set(unsupported)))
    return (
        '<div style="background:#fffbeb;border:1px solid #b45309;color:#92400e;'
        'padding:12px 16px;margin:0 0 24px;font:13px/1.6 monospace;border-radius:6px">'
        "<strong>Dev preview is not faithful.</strong> These Liquid constructs are "
        "not supported by scripts/blog/liquid_render.py, so the page below differs "
        "from the Jekyll build:<ul>{}</ul></div>"
    ).format(items)


@app.route('/')
@app.route('/blog')
@app.route('/blog/')
def blog_list_page():
    site = build_site_context()
    page = {"title": "Blog", "description": site.get("description", "")}

    content = render_page_file(
        os.path.join(WORKSPACE_DIR, "index.html"), site, page
    )
    body, unsupported = render_layout_file("default", site, page, content)
    body = body.replace("<main class=\"main-content\">",
                        "<main class=\"main-content\">" + preview_banner(unsupported), 1)
    return body

@app.route('/blog/<slug>')
@app.route('/blog/<slug>/')
def public_blog_post(slug):
    site = build_site_context()

    post_dict = None
    for post in site["posts"]:
        if post["slug"] == slug:
            post_dict = post
            break

    if not post_dict:
        return f"Article '{slug}' not found", 404

    post_html = render_post_markdown(post_dict.get("body", ""))
    page = build_post_context(post_dict, site)

    rendered_post, unsupported_post = render_layout_file("post", site, page, post_html)
    final_html, unsupported_default = render_layout_file("default", site, page, rendered_post)

    banner = preview_banner(unsupported_post + unsupported_default)
    if banner:
        final_html = final_html.replace(
            '<main class="main-content">', '<main class="main-content">' + banner, 1
        )
    return final_html

# API JSON Search Index endpoint
@app.route('/search.json')
def search_json_index():
    posts = get_all_posts(include_drafts=False)
    index_list = []
    for post in posts:
        index_list.append({
            "title": post["title"],
            "url": post["url"],
            "description": post["description"],
            "categories": ", ".join(post["categories"]).lower(),
            "tags": ", ".join(post["tags"]).lower(),
            "date": post["date"]
        })
    return jsonify(index_list)

# --- BACKEND REST API ENDPOINTS ---

@app.route('/api/posts', methods=['GET'])
def list_posts():
    posts = []
    files = glob.glob(os.path.join(POSTS_DIR, "*.md"))
    for fpath in files:
        filename = os.path.basename(fpath)
        try:
            meta, body = parse_markdown_file(fpath)
            posts.append({
                "filename": filename,
                "title": meta.get("title", filename),
                "description": meta.get("description", ""),
                "date": meta.get("date", ""),
                "author": meta.get("author", "Saiteja"),
                "draft": meta.get("draft", False),
                "categories": meta.get("categories", []),
                "tags": meta.get("tags", [])
            })
        except Exception as e:
            print(f"Error parsing {filename}: {e}")
    posts.sort(key=lambda x: str(x["date"]), reverse=True)
    return jsonify(posts)

@app.route('/api/posts/<filename>', methods=['GET'])
def get_post(filename):
    fpath = os.path.join(POSTS_DIR, filename)
    if not os.path.exists(fpath):
        return jsonify({"error": "Post not found"}), 404
    try:
        meta, body = parse_markdown_file(fpath)
        return jsonify({"filename": filename, "metadata": meta, "body": body})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/posts', methods=['POST'])
def save_post():
    data = request.json
    filename = data.get("filename")
    metadata = data.get("metadata", {})
    body = data.get("body", "")
    
    if not filename:
        slug = metadata.get("title", "untitled").lower()
        slug = re.sub(r'[^\w\s-]', '', slug)
        slug = re.sub(r'[\s_]+', '-', slug).strip("-")
        date_str = metadata.get("date") or datetime.today().strftime('%Y-%m-%d')
        metadata["date"] = date_str
        filename = f"{date_str}-{slug}.md"
        
    metadata["layout"] = "post"
    metadata["draft"] = metadata.get("draft", True)
    metadata["author"] = metadata.get("author", "Saiteja")
        
    fpath = os.path.join(POSTS_DIR, filename)
    try:
        write_markdown_file(fpath, metadata, body)
        return jsonify({"success": True, "filename": filename, "metadata": metadata})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/posts/<filename>', methods=['DELETE'])
def delete_post(filename):
    fpath = os.path.join(POSTS_DIR, filename)
    if not os.path.exists(fpath):
        return jsonify({"error": "Post not found"}), 404
    try:
        os.remove(fpath)
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/posts/<filename>/quality', methods=['GET'])
def check_quality(filename):
    fpath = os.path.join(POSTS_DIR, filename)
    if not os.path.exists(fpath):
        return jsonify({"error": "Post not found"}), 404
    try:
        analyzer = BlogQualityAnalyzer(fpath)
        analyzer.analyze()
        return jsonify({
            "score": analyzer.get_total_score(),
            "scores": analyzer.scores,
            "warnings": analyzer.warnings
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/assets/css/style.css', methods=['GET'])
def compile_style_scss():
    style_path = os.path.join(WORKSPACE_DIR, "assets", "css", "style.scss")
    if not os.path.exists(style_path):
        return Response("/* style.scss not found */", mimetype="text/css")
    compiled_css = []
    sass_dir = os.path.join(WORKSPACE_DIR, "_sass")
    with open(style_path, 'r', encoding='utf-8') as f:
        content = f.read()
    for line in content.splitlines():
        line = line.strip()
        if line.startswith("@import"):
            import_name = line.replace("@import", "").replace('"', "").replace("'", "").replace(";", "").strip()
            partial_path = os.path.join(sass_dir, f"_{import_name}.scss")
            if os.path.exists(partial_path):
                with open(partial_path, 'r', encoding='utf-8') as pf:
                    compiled_css.append(f"/* @import {import_name} */")
                    compiled_css.append(pf.read())
            else:
                compiled_css.append(f"/* Warning: import {import_name} not found */")
        elif not line.startswith("---"):
            compiled_css.append(line)
    return Response("\n".join(compiled_css), mimetype="text/css")

@app.route('/assets/<path:subpath>')
def serve_assets(subpath):
    return send_from_directory(os.path.join(WORKSPACE_DIR, "assets"), subpath)

@app.route('/preview/<filename>')
def preview_post(filename):
    return public_blog_post(filename.replace(".md", ""))

@app.route('/admin/')
def serve_admin_index():
    return send_from_directory(os.path.join(WORKSPACE_DIR, "admin"), "index.html")

@app.route('/admin/<path:subpath>')
def serve_admin_assets(subpath):
    return send_from_directory(os.path.join(WORKSPACE_DIR, "admin"), subpath)

@app.route('/api/env-check', methods=['GET'])
def env_check():
    return jsonify({
        "openai": bool(os.getenv("OPENAI_API_KEY")),
        "anthropic": bool(os.getenv("ANTHROPIC_API_KEY")),
        "provider": os.getenv("AI_PROVIDER", "openai"),
        "github": bool(os.getenv("GITHUB_API_KEY") or os.getenv("GITHUB_TOKEN"))
    })

@app.route('/api/ai/generate', methods=['POST'])
def trigger_ai_generation():
    try:
        from generate import generate_article_from_notes
        data = request.json
        topic = data.get("topic")
        title = data.get("title")
        notes = data.get("notes")
        tech_details = data.get("tech_details")
        examples = data.get("examples")
        tags = data.get("tags", [])
        categories = data.get("categories", [])
        references = data.get("references", [])
        
        if not topic:
            return jsonify({"error": "Topic is required"}), 400
            
        success, filename, error = generate_article_from_notes(
            topic=topic, title=title, notes=notes, tech_details=tech_details,
            examples=examples, tags=tags, categories=categories, references=references
        )
        if success:
            return jsonify({"success": True, "filename": filename})
        else:
            return jsonify({"error": error}), 500
    except Exception as e:
        import traceback
        return jsonify({"error": str(e), "trace": traceback.format_exc()}), 500

@app.route('/api/posts/<filename>/publish', methods=['POST'])
def trigger_publish(filename):
    try:
        from github_api import create_pull_request_for_blog
        data = request.json or {}
        commit_message = data.get("commit_message")
        success, pr_url, error = create_pull_request_for_blog(filename, commit_message)
        if success:
            return jsonify({"success": True, "pr_url": pr_url})
        else:
            return jsonify({"error": error}), 500
    except Exception as e:
        import traceback
        return jsonify({"error": str(e), "trace": traceback.format_exc()}), 500

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv(os.path.join(WORKSPACE_DIR, ".env"))
    print(f"Starting Dev Blog Admin Server on http://localhost:5000/admin/")
    app.run(host="localhost", port=5000, debug=True)
