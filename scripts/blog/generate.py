import os
import re
from datetime import datetime
from ai_provider import AIProvider
from research import ResearchAssistant
from quality import load_config
from new_post import build_front_matter, validate_categories

def generate_article_from_notes(topic, title=None, notes="", tech_details="", examples="", tags=None, categories=None, references=None):
    tags = tags or []
    categories = categories or []
    references = references or []

    config = load_config()
    structure = config["structure"]
    rules = structure.get("rules", {})
    defaults = structure.get("defaults", {})
    min_level = rules.get("min_heading_level", 2)
    max_level = rules.get("max_heading_level", 3)

    ai = AIProvider()
    researcher = ResearchAssistant()
    
    print(f"Pipeline started for topic: '{topic}'")
    
    research_log = researcher.research_topic(topic, notes, references)
    facts_str = "\n".join([f"- {fact}" for fact in research_log.get("facts", [])])
    
    ref_list = []
    for ref in research_log.get("references", []):
        ref_list.append(f"1. [{ref.get('title')}]({ref.get('url')}) - {ref.get('notes')}")
    for ref_url in references:
        if ref_url.startswith("http") and not any(ref_url in r for r in ref_list):
            ref_list.append(f"1. [Reference Source]({ref_url})")
            
    references_str = "\n".join(ref_list)
    
    outline_system = (
        "You are an expert technical outline editor. Create a structured outline for a developer blog post.\n"
        "The outline should follow a logical flow (e.g. Introduction, The Problem, Architecture/Concept, Implementation/Code, Summary/Takeaways, References).\n"
        "Output the outline in plain markdown format."
    )
    
    outline_user = (
        f"Topic: {topic}\n"
        f"Research facts gathered:\n{facts_str}\n\n"
        f"User Notes:\n{notes}\n\n"
        f"Technical details to include:\n{tech_details}\n\n"
        "Draft a structured markdown outline."
    )
    
    print("Generating post outline...")
    outline = ai.generate(outline_system, outline_user, temperature=0.5)
    
    writer_system = (
        "You are a Senior Software Engineer and Technical Blogger. Write a polished, detailed, and clear developer-focused article.\n"
        "Guidelines:\n"
        "- Adopt a content-first, technical tone.\n"
        "- Do not use overly marketing or buzzwordy phrases.\n"
        "- Focus on explanation of concepts, architectures, and practical code.\n"
        "- Keep paragraphs readable, short, and to the point.\n"
        f"- Structure using headers (h{min_level} and h{max_level}). Do NOT use H1 (#) headers in the body; "
        "the page layout owns the single h1.\n"
        "- Include code blocks showing correct syntax and implementations, and always tag the language.\n"
        f"- Use {rules.get('callout_syntax', '> [!NOTE]')} callouts for critical architecture tips.\n"
        "```mermaid is the diagram language for architecture and flow.\n"
        f"- Incorporate references at the end of the post under a '## {rules.get('required_trailing_section', 'References')}' heading."
    )
    
    writer_user = (
        f"Topic: {topic}\n"
        f"Title: {title or topic}\n"
        f"Outline:\n{outline}\n\n"
        f"User Notes:\n{notes}\n\n"
        f"Technical Details:\n{tech_details}\n\n"
        f"Code Example to Include:\n{examples}\n\n"
        f"References:\n{references_str}\n\n"
        "Write the full article. Do not include frontmatter blocks yet—just write the main text body."
    )
    
    print("Drafting article body...")
    draft = ai.generate(writer_system, writer_user, temperature=0.7)
    
    reviewer_system = (
        "You are an expert Technical Editor. Review the technical draft, check for accuracy, and refine the text for clarity, "
        "readability, and active voice. Ensure that code blocks are clean, explanations are solid, and there are no placeholder links."
        "Return the refined article in markdown."
    )
    
    reviewer_user = (
        f"Draft to review:\n{draft}\n\n"
        f"Key technical details that should be accurate:\n{tech_details}\n\n"
        "Please provide the final, polished version of the article markdown."
    )
    
    print("Performing technical review and formatting...")
    final_body = ai.generate(reviewer_system, reviewer_user, temperature=0.3)
    
    today_str = datetime.today().strftime('%Y-%m-%d')
    slug = (title or topic).lower()
    slug = re.sub(r'[^\w\s-]', '', slug)
    slug = re.sub(r'[\s_]+', '-', slug).strip("-")
    if not slug:
        slug = "blog-post"
    filename = f"{today_str}-{slug}.md"

    # Categories must be inside structure.category_enum or both checkers
    # reject the post, so fall back to the first enum entry rather than
    # inventing a category.
    if not categories:
        categories = [structure.get("category_enum", ["Backend"])[0]]
    validate_categories(categories, config)

    min_desc = rules.get("min_description_chars", 50)
    max_desc = rules.get("max_description_chars", 160)
    description = notes.replace("\n", " ").strip() or f"Technical article explaining {topic}."
    if not min_desc <= len(description) <= max_desc:
        description = description[:max_desc].rstrip() + "..."

    # Front matter is emitted through the shared builder, so a generated post
    # is shaped exactly like a hand-written one.
    metadata = {
        "layout": defaults.get("layout", "post"),
        "title": title or topic,
        "description": description,
        "date": today_str,
        "updated": today_str,
        "categories": categories,
        "tags": tags or ["tech"],
        "author": defaults.get("author", "Saiteja Chada"),
        "reading_time": defaults.get("reading_time", "5 min read"),
        "draft": True,
    }
    metadata = {k: v for k, v in metadata.items() if v not in (None, [], "")}

    workspace_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    posts_dir = os.path.join(workspace_dir, "_posts")
    fpath = os.path.join(posts_dir, filename)

    trailing = rules.get("required_trailing_section", "References")
    if f"## {trailing}" not in final_body and references_str:
        final_body += f"\n\n## {trailing}\n\n{references_str}"

    full_content = build_front_matter(metadata, config) + "\n\n" + final_body

    with open(fpath, 'w', encoding='utf-8') as f:
        f.write(full_content)
        
    print(f"Success! Generated blog post saved to {fpath}")
    print("Front matter and style rules came from _data/blog_style.yml")
    return True, filename, None
