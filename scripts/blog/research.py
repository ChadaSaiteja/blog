import os
import requests
import re
import json
from ai_provider import AIProvider

class ResearchAssistant:
    def __init__(self):
        self.ai = AIProvider()

    def fetch_url_content(self, url):
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
            response = requests.get(url, headers=headers, timeout=15)
            if response.status_code == 200:
                html = response.text
                text = re.sub(r'<script.*?</script>', '', html, flags=re.DOTALL)
                text = re.sub(r'<style.*?</style>', '', text, flags=re.DOTALL)
                text = re.sub(r'<[^>]+>', ' ', text)
                text = re.sub(r'\s+', ' ', text).strip()
                return text[:8000]
        except Exception as e:
            print(f"Research: Failed to fetch context from URL {url}: {e}")
        return ""

    def research_topic(self, topic, raw_notes="", user_urls=None):
        user_urls = user_urls or []
        fetched_contexts = []
        
        for url in user_urls:
            if url.startswith("http"):
                print(f"Researching user provided reference: {url}...")
                content = self.fetch_url_content(url)
                if content:
                    fetched_contexts.append(f"Source: {url}\nContent Summary: {content[:3000]}")

        fetched_text = "\n\n".join(fetched_contexts)
        
        system_prompt = (
            "You are an expert technical Research Assistant. Your goal is to gather verified facts, "
            "synthesize official documentation details, and identify official reference citations for a blog topic.\n"
            "Produce output in JSON format with two keys:\n"
            "1. 'facts': A list of key technical facts, constraints, and architectures related to the topic.\n"
            "2. 'references': A list of objects containing 'title', 'url', and 'notes' explaining what documentation is referenced."
        )
        
        user_prompt = f"Topic: {topic}\n\nUser Notes:\n{raw_notes}\n\n"
        if fetched_text:
            user_prompt += f"Fetched Web Content Context:\n{fetched_text}\n\n"
            
        user_prompt += (
            "Please compile the research synthesis. Ensure the URLs listed in references are official documentation links "
            "(e.g., go.dev, kafka.apache.org, react.dev, learn.microsoft.com) and match the topic perfectly."
        )

        try:
            raw_response = self.ai.generate(system_prompt, user_prompt, temperature=0.2)
            json_match = re.search(r'(\{.*\})', raw_response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group(1))
            else:
                return {
                    "facts": [f"Research fact about {topic}"],
                    "references": [{"title": "Official Docs", "url": "https://google.com", "notes": "General lookup"}]
                }
        except Exception as e:
            print(f"Error during AI topic research: {e}")
            return {
                "error": str(e),
                "facts": [f"Error occurred during research step: {e}"],
                "references": []
            }
