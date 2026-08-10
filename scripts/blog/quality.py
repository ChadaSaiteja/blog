import os
import sys
import re

class BlogQualityAnalyzer:
    def __init__(self, filepath):
        self.filepath = filepath
        self.raw_content = ""
        self.frontmatter = {}
        self.content = ""
        self.warnings = []
        
        self.scores = {
            "content_quality": 30,
            "technical_accuracy": 20,
            "structure": 15,
            "examples": 10,
            "readability": 10,
            "references": 10,
            "seo": 5
        }

    def load_file(self):
        if not os.path.exists(self.filepath):
            raise FileNotFoundError(f"File not found: {self.filepath}")
        
        with open(self.filepath, 'r', encoding='utf-8') as f:
            self.raw_content = f.read()
            
        fm_match = re.match(r'^---\r?\n(.*?)\r?\n---\r?\n(.*)$', self.raw_content, re.DOTALL)
        if not fm_match:
            self.warnings.append("Invalid or missing frontmatter blocks (---)")
            self.content = self.raw_content
            return False
            
        fm_text = fm_match.group(1)
        self.content = fm_match.group(2)
        
        for line in fm_text.splitlines():
            if ':' in line:
                key, val = line.split(':', 1)
                key = key.strip()
                val = val.strip().strip('"').strip("'")
                if val == "" or val.startswith("-"):
                    continue
                if val == "[]":
                    self.frontmatter[key] = []
                else:
                    self.frontmatter[key] = val
                
        categories = re.findall(r'categories:\s*\n((?:\s*-\s*[^\n]+\n?)+)', fm_text)
        if categories:
            self.frontmatter["categories"] = [item.replace("-", "").strip() for item in categories[0].strip().splitlines()]
            
        tags = re.findall(r'tags:\s*\n((?:\s*-\s*[^\n]+\n?)+)', fm_text)
        if tags:
            self.frontmatter["tags"] = [item.replace("-", "").strip() for item in tags[0].strip().splitlines()]
            
        return True

    def analyze(self):
        self.load_file()
        
        seo_deduction = 0
        if not self.frontmatter.get("title"):
            seo_deduction += 2
            self.warnings.append("SEO: Missing title in frontmatter")
        elif len(self.frontmatter.get("title", "")) < 10:
            seo_deduction += 1
            self.warnings.append("SEO: Title is too short (less than 10 characters)")
            
        desc = self.frontmatter.get("description", "")
        if not desc:
            seo_deduction += 2
            self.warnings.append("SEO: Missing description in frontmatter")
        elif len(desc) < 50 or len(desc) > 160:
            seo_deduction += 1
            self.warnings.append(f"SEO: Description length is {len(desc)} characters. Recommended is 50-160 characters for search listings.")
            
        images = re.findall(r'!\[(.*?)\]\((.*?)\)', self.content)
        for alt, src in images:
            if not alt.strip():
                seo_deduction += 1
                self.warnings.append(f"SEO: Image with source '{src}' is missing an alt text description.")
        
        self.scores["seo"] = max(0, self.scores["seo"] - seo_deduction)

        struct_deduction = 0
        first_heading = re.search(r'^#+\s+', self.content, re.MULTILINE)
        if first_heading:
            intro_text = self.content[:first_heading.start()].strip()
            if len(intro_text.split()) < 30:
                struct_deduction += 3
                self.warnings.append("Structure: Missing or very short introduction before first heading")
        else:
            struct_deduction += 5
            self.warnings.append("Structure: No headings found in post content")
            
        h1s = re.findall(r'^#\s+.*$', self.content, re.MULTILINE)
        if h1s:
            struct_deduction += 2
            self.warnings.append("Structure: Found H1 (#) headings in content. Jekyll uses H1 for page titles; use H2 (##) or H3 (###) in the post body.")

        headings = [h.strip() for h in re.findall(r'^##+\s+(.*)$', self.content, re.MULTILINE)]
        if len(headings) != len(set(headings)):
            struct_deduction += 2
            self.warnings.append("Structure: Duplicate subheadings found in the content body.")
            
        heading_matches = list(re.finditer(r'^##+\s+(.*)$', self.content, re.MULTILINE))
        for idx, match in enumerate(heading_matches):
            heading_title = match.group(1).lower()
            if "reference" in heading_title or "source" in heading_title:
                continue
                
            start = match.end()
            end = heading_matches[idx+1].start() if idx+1 < len(heading_matches) else len(self.content)
            section_content = self.content[start:end].strip()
            word_count = len(section_content.split())
            if word_count > 0 and word_count < 30:
                struct_deduction += 2
                self.warnings.append(f"Structure: Section '{match.group(1)}' is very short ({word_count} words). Elaborate or combine sections.")
                
        has_takeaway = any(re.search(term, self.content, re.IGNORECASE) for term in [r'takeaway', r'conclusion', r'summary', r'key takeaways'])
        if not has_takeaway:
            struct_deduction += 2
            self.warnings.append("Structure: No summary, takeaways, or conclusion heading identified.")
            
        self.scores["structure"] = max(0, self.scores["structure"] - struct_deduction)

        readability_deduction = 0
        paragraphs = [p.strip() for p in self.content.split('\n\n') if p.strip()]
        
        long_paras = 0
        for p in paragraphs:
            if p.startswith('```') or p.startswith('>'):
                continue
            words = len(p.split())
            if words > 150:
                long_paras += 1
                
        if long_paras > 0:
            readability_deduction += min(4, long_paras)
            self.warnings.append(f"Readability: Found {long_paras} excessively long paragraphs (>150 words). Break them up.")
            
        passive_words = re.findall(r'\b(?:is|was|were|be|been|being)\s+\w+ed\b', self.content, re.IGNORECASE)
        if len(passive_words) > 15:
            readability_deduction += 2
            self.warnings.append("Readability: Frequent use of passive writing detected. Prefer active voice where possible.")
            
        self.scores["readability"] = max(0, self.scores["readability"] - readability_deduction)

        examples_deduction = 0
        code_blocks = re.findall(r'```', self.content)
        num_code_blocks = len(code_blocks) // 2
        
        if num_code_blocks == 0:
            coding_tags = ['go', 'golang', 'typescript', 'javascript', 'python', 'code', 'sql', 'bash']
            has_coding_tag = any(t in self.frontmatter.get("tags", []) or t in self.frontmatter.get("categories", []) for t in coding_tags)
            if has_coding_tag:
                examples_deduction += 5
                self.warnings.append("Examples: Coding topic tag active, but no code blocks found in content.")
            else:
                examples_deduction += 2
                self.warnings.append("Examples: No practical code blocks/examples found in the article.")
        
        self.scores["examples"] = max(0, self.scores["examples"] - examples_deduction)

        ref_deduction = 0
        has_ref_section = any(re.search(r'##\s+References', line, re.IGNORECASE) for line in self.content.splitlines())
        links = re.findall(r'\[.*?\]\((.*?)\)', self.content)
        
        if not has_ref_section:
            ref_deduction += 5
            self.warnings.append("References: Missing dedicated 'References' heading at the end of the post.")
            
        external_links = [l for l in links if l.startswith('http') and 'github.io' not in l]
        if not external_links:
            ref_deduction += 4
            self.warnings.append("References: No external source citations or documentation links found in post.")
            
        for link in links:
            if 'example.com' in link or 'todo' in link.lower() or not link.strip():
                ref_deduction += 2
                self.warnings.append(f"References: Found unresolved placeholder link '{link}'")

        self.scores["references"] = max(0, self.scores["references"] - ref_deduction)

        tech_deduction = 0
        if not self.frontmatter.get("author"):
            tech_deduction += 2
            self.warnings.append("Accuracy: Author is missing from frontmatter metadata.")
            
        if self.frontmatter.get("layout") != "post":
            tech_deduction += 3
            self.warnings.append("Accuracy: Layout must be set to 'post' in frontmatter.")
            
        total_words = len(self.content.split())
        if total_words < 300:
            tech_deduction += 8
            self.warnings.append(f"Accuracy: Post is very short ({total_words} words). Detailed developer articles should be at least 300 words.")
        elif total_words < 500:
            tech_deduction += 3
            self.warnings.append(f"Accuracy: Post is somewhat short ({total_words} words). Consider adding more details or context.")

        self.scores["technical_accuracy"] = max(0, self.scores["technical_accuracy"] - tech_deduction)

        quality_deduction = 0
        if not self.frontmatter.get("categories") or len(self.frontmatter.get("categories")) == 0:
            quality_deduction += 5
            self.warnings.append("Quality: Categories are missing in frontmatter. Add at least 1 category.")
        if not self.frontmatter.get("tags") or len(self.frontmatter.get("tags")) == 0:
            quality_deduction += 5
            self.warnings.append("Quality: Tags are missing in frontmatter. Add at least 1 tag.")
            
        self.scores["content_quality"] = max(0, self.scores["content_quality"] - quality_deduction)

    def get_total_score(self):
        return sum(self.scores.values())

    def print_report(self):
        total = self.get_total_score()
        print("\nBLOG QUALITY REPORT")
        print("=" * 40)
        print(f"{'Content quality':<22} {self.scores['content_quality']}/30")
        print(f"{'Technical accuracy':<22} {self.scores['technical_accuracy']}/20")
        print(f"{'Structure':<22} {self.scores['structure']}/15")
        print(f"{'Examples':<22} {self.scores['examples']}/10")
        print(f"{'Readability':<22} {self.scores['readability']}/10")
        print(f"{'References':<22} {self.scores['references']}/10")
        print(f"{'SEO':<22} {self.scores['seo']}/5")
        print("-" * 40)
        print(f"{'TOTAL SCORE':<22} {total}/100")
        print("=" * 40)
        
        if self.warnings:
            print("\nWarnings:")
            for w in self.warnings:
                print(f"- {w}")
        else:
            print("\nNo warnings! Excellent job.")
        print()
        return total

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python quality.py <path_to_markdown_file> [threshold_score]")
        sys.exit(1)
        
    filepath = sys.argv[1]
    threshold = int(sys.argv[2]) if len(sys.argv) > 2 else 80
    
    analyzer = BlogQualityAnalyzer(filepath)
    try:
        analyzer.analyze()
        score = analyzer.print_report()
        if score < threshold:
            print(f"FAILED: Score {score} is below threshold of {threshold}.")
            sys.exit(1)
        else:
            print(f"PASSED: Score {score} meets threshold of {threshold}.")
            sys.exit(0)
    except Exception as e:
        print(f"Error executing quality checker: {e}", file=sys.stderr)
        sys.exit(1)
