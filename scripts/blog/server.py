import os
import sys
import re
import glob
from datetime import datetime
from flask import Flask, request, jsonify, send_from_directory, Response
import markdown

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from quality import BlogQualityAnalyzer

app = Flask(__name__)
WORKSPACE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
POSTS_DIR = os.path.join(WORKSPACE_DIR, "_posts")

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

# --- LIQUID LAYOUT EMULATOR RENDERING ---
def resolve_includes(html_text):
    includes_dir = os.path.join(WORKSPACE_DIR, "_includes")
    include_tags = re.findall(r'\{?\%\s*include\s+(.*?)\s*\%\}', html_text)
    for tag in include_tags:
        inc_path = os.path.join(includes_dir, tag)
        if os.path.exists(inc_path):
            with open(inc_path, 'r', encoding='utf-8') as inf:
                inc_content = inf.read()
            html_text = html_text.replace(f"{{% include {tag} %}}", inc_content)
        else:
            html_text = html_text.replace(f"{{% include {tag} %}}", f"<!-- Include {tag} not found -->")
    return html_text

def emulate_liquid_render(html_text, page_metadata=None, content_body=""):
    page_metadata = page_metadata or {}
    
    # 1. Inject content block
    html_text = html_text.replace("{{ content }}", content_body)
    
    # 2. Handle {% if page.X %} ... {% endif %} blocks
    def resolve_if_page(match):
        key = match.group(1).strip()
        val = page_metadata.get(key)
        inner = match.group(2)
        # Handle {% if %} ... {% else %} ... {% endif %}
        else_match = re.search(r'(.*?)\{%\s*else\s*%\}(.*)', inner, re.DOTALL)
        if else_match:
            if_part = else_match.group(1)
            else_part = else_match.group(2)
            return if_part if val else else_part
        return inner if val else ''
    html_text = re.sub(r'\{%\s*if page\.(\w+)\s*%\}(.*?)\{%\s*endif\s*%\}',
                       resolve_if_page, html_text, flags=re.DOTALL)
    
    # 3. Resolve for loops over page.categories and page.tags
    def resolve_for_cats(match):
        items = page_metadata.get("categories", [])
        template = match.group(1)
        result = ""
        for item in items:
            result += template.replace("{{ cat }}", item)
        return result
    html_text = re.sub(r'\{%\s*for cat in page\.categories[^%]*%\}(.*?)\{%\s*endfor\s*%\}',
                       resolve_for_cats, html_text, flags=re.DOTALL)
    
    def resolve_for_tags(match):
        items = page_metadata.get("tags", [])
        template = match.group(1)
        result = ""
        for item in items:
            result += template.replace("{{ tag }}", item)
        return result
    html_text = re.sub(r'\{%\s*for tag in page\.tags[^%]*%\}(.*?)\{%\s*endfor\s*%\}',
                       resolve_for_tags, html_text, flags=re.DOTALL)
    
    # 4. Resolve relative_urls
    html_text = re.sub(r"\{\{\s*'(.*?)'\s*\|\s*relative_url\s*\}\}", r'\1', html_text)
    html_text = re.sub(r'\{\{\s*"(.*?)"\s*\|\s*relative_url\s*\}\}', r'\1', html_text)
    
    # 5. Resolve page variables
    html_text = html_text.replace("{{ page.title }}", str(page_metadata.get("title", "")))
    html_text = html_text.replace("{{ page.description }}", str(page_metadata.get("description", "")))
    html_text = html_text.replace("{{ page.author }}", str(page_metadata.get("author", "Saiteja")))
    html_text = html_text.replace("{{ page.reading_time }}", str(page_metadata.get("reading_time", "5 min read")))
    
    pdate = page_metadata.get("date", "")
    formatted_date = ""
    if pdate:
        if isinstance(pdate, str):
            try:
                pdate = datetime.strptime(pdate, "%Y-%m-%d")
            except:
                pass
        if isinstance(pdate, datetime):
            formatted_date = pdate.strftime("%B %d, %Y")
        else:
            formatted_date = str(pdate)
    html_text = html_text.replace('{{ page.date | date: "%B %d, %Y" }}', formatted_date)
    
    # 6. Resolve includes
    html_text = resolve_includes(html_text)
    
    # 7. Site config variables
    html_text = html_text.replace("{{ site.title }}", "Saiteja's Dev Blog")
    html_text = html_text.replace("{{ site.description }}", "Backend engineering blog by Saiteja Chada.")
    html_text = html_text.replace('{{ site.time | date: "%Y" }}', str(datetime.today().year))
    
    # 8. Remove any remaining Liquid tags/variables
    html_text = re.sub(r'\{%.*?%\}', '', html_text, flags=re.DOTALL)
    html_text = re.sub(r'\{\{.*?\}\}', '', html_text, flags=re.DOTALL)
    return html_text


def render_blog_card(post_dict):
    includes_dir = os.path.join(WORKSPACE_DIR, "_includes")
    with open(os.path.join(includes_dir, "blog-card.html"), 'r', encoding='utf-8') as f:
        card_layout = f.read()
        
    # Inject variables
    card_layout = card_layout.replace("{{ post.url | relative_url }}", post_dict["url"])
    card_layout = card_layout.replace("{{ post.title }}", post_dict["title"])
    card_layout = card_layout.replace("{{ post.description | default: post.excerpt | strip_html | truncatewords: 25 }}", post_dict["description"])
    
    pdate = post_dict.get("date", "")
    if isinstance(pdate, str):
        try:
            pdate = datetime.strptime(pdate, "%Y-%m-%d")
        except:
            pass
    formatted_date = pdate.strftime("%B %d, %Y") if isinstance(pdate, datetime) else str(pdate)
    card_layout = card_layout.replace('{{ post.date | date: "%B %d, %Y" }}', formatted_date)
    
    read_time = post_dict.get("reading_time", "5 min read")
    # Replace the {% if post.reading_time %}{{ post.reading_time }}{% else %}5 min read{% endif %} block
    card_layout = re.sub(
        r'\{%\s*if post\.reading_time\s*%\}.*?\{%\s*else\s*%\}.*?\{%\s*endif\s*%\}',
        read_time,
        card_layout,
        flags=re.DOTALL
    )
    
    # Resolve loops
    cats_html = "".join([f'<span class="badge category-badge">{c}</span>' for c in post_dict.get("categories", [])])
    tags_html = "".join([f'<span class="badge tag-badge">#{t}</span>' for t in post_dict.get("tags", [])])
    card_layout = re.sub(r'\{%\s*for cat in post\.categories[^%]*%\}.*?\{%\s*endfor\s*%\}', cats_html, card_layout, flags=re.DOTALL)
    card_layout = re.sub(r'\{%\s*for tag in post\.tags[^%]*%\}.*?\{%\s*endfor\s*%\}', tags_html, card_layout, flags=re.DOTALL)
    
    card_layout = re.sub(r'\{%.*?\%}', '', card_layout)
    card_layout = re.sub(r'\{\{.*?\}\}', '', card_layout)
    return card_layout

# --- PUBLIC ROUTE SERVINGS ---

@app.route('/')
def home_page():
    posts = get_all_posts(include_drafts=False)
    
    # Load index file (strip Jekyll frontmatter)
    with open(os.path.join(WORKSPACE_DIR, "index.html"), 'r', encoding='utf-8') as f:
        home_content = strip_jekyll_frontmatter(f.read())
        
    # Render loop in home content
    loop_regex = r'\{%.*?for post in posts limit: 3.*?%\}(.*?)\{%.*?endfor.*?%\}'
    loop_match = re.search(loop_regex, home_content, re.DOTALL)
    
    cards_html = ""
    if loop_match and len(posts) > 0:
        for post in posts[:3]:
            cards_html += render_blog_card(post)
    else:
        cards_html = '<p style="color: var(--text-secondary);">No articles published yet.</p>'
        
    home_content = re.sub(loop_regex, cards_html, home_content, flags=re.DOTALL)
    
    # Categories listing emulation
    cats = set()
    for post in posts:
        for c in post.get("categories", []):
            cats.add(c)
            
    cats_html = ""
    for c in sorted(list(cats)):
        cats_html += f'<span class="badge category-badge" style="font-size: 0.85rem; padding: 0.3rem 0.7rem; cursor: pointer;" onclick="location.href=\'/blog?category={c.lower()}\'">{c}</span>\n'
    if not cats_html:
        cats_html = '<p style="color: var(--text-muted); font-size: 0.9rem;">Categories will show up here.</p>'
        
    cats_regex = r'\{%.*?for cat in site\.categories.*?%\}.*?\{%.*?endfor.*?%\}'
    home_content = re.sub(cats_regex, cats_html, home_content, flags=re.DOTALL)
    
    # Wrap in default layout
    with open(os.path.join(WORKSPACE_DIR, "_layouts", "default.html"), 'r', encoding='utf-8') as f:
        default_layout = strip_jekyll_frontmatter(f.read())
        
    final_html = emulate_liquid_render(default_layout, {"title": "Home"}, home_content)
    return final_html

@app.route('/blog')
@app.route('/blog/')
def blog_list_page():
    posts = get_all_posts(include_drafts=False)
    
    with open(os.path.join(WORKSPACE_DIR, "blog", "index.html"), 'r', encoding='utf-8') as f:
        blog_content = strip_jekyll_frontmatter(f.read())
        
    loop_regex = r'\{%.*?for post in sorted_posts.*?%\}(.*?)\{%.*?endfor.*?%\}'
    loop_match = re.search(loop_regex, blog_content, re.DOTALL)
    
    grid_html = ""
    if loop_match and len(posts) > 0:
        for post in posts:
            cats_data = " ".join(post["categories"]).lower()
            tags_data = " ".join(post["tags"]).lower()
            title_data = post["title"].lower()
            desc_data = post["description"].lower()
            grid_html += f'<div class="filterable-post" data-title="{title_data}" data-description="{desc_data}" data-categories="{cats_data}" data-tags="{tags_data}">'
            grid_html += render_blog_card(post)
            grid_html += '</div>'
    else:
        grid_html = '<p>No articles published yet.</p>'
        
    blog_content = re.sub(loop_regex, grid_html, blog_content, flags=re.DOTALL)
    
    # Wrap in default layout
    with open(os.path.join(WORKSPACE_DIR, "_layouts", "default.html"), 'r', encoding='utf-8') as f:
        default_layout = strip_jekyll_frontmatter(f.read())
        
    final_html = emulate_liquid_render(default_layout, {"title": "Blog"}, blog_content)
    return final_html

@app.route('/blog/<slug>')
@app.route('/blog/<slug>/')
def public_blog_post(slug):
    posts = get_all_posts(include_drafts=True)
    post_dict = None
    for post in posts:
        if post["slug"] == slug:
            post_dict = post
            break
            
    if not post_dict:
        return f"Article '{slug}' not found", 404
        
    # Parse markdown body
    post_html = markdown.markdown(post_dict["body"], extensions=['fenced_code', 'codehilite', 'tables'])
    
    # Load post layout
    with open(os.path.join(WORKSPACE_DIR, "_layouts", "post.html"), 'r', encoding='utf-8') as f:
        post_layout = strip_jekyll_frontmatter(f.read())
        
    rendered_post = emulate_liquid_render(post_layout, post_dict, post_html)
    
    # Wrap in default layout
    with open(os.path.join(WORKSPACE_DIR, "_layouts", "default.html"), 'r', encoding='utf-8') as f:
        default_layout = strip_jekyll_frontmatter(f.read())
        
    final_html = emulate_liquid_render(default_layout, post_dict, rendered_post)
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
