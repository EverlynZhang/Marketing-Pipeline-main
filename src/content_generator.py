from openai import OpenAI
from typing import Dict, List
import json
from config import Config
from src.utils import logger

class ContentGenerator:
    def __init__(self):
        self.config = Config()
        self.client = OpenAI(api_key=self.config.OPENAI_API_KEY)
        self.model = "gpt-4o" 
    
    @staticmethod
    def clean_response(raw_text):
        if raw_text.startswith("```json"):
            raw_text = raw_text[len("```json"):]
        if raw_text.endswith("```"):
            raw_text = raw_text[:-len("```")]
        return raw_text


    def generate_blog_post(self, topic: str) -> Dict[str, str]:
        """Generate a blog post outline and draft"""
        logger.info(f"Generating blog post for topic: {topic}")
        
        prompt = f"""You are a content writer for NovaMind, an AI startup that helps small creative agencies automate their daily workflows (think Notion + Zapier + ChatGPT combined).

                    Write a blog post about: {topic}

                    Requirements:
                    - Length: 400-600 words
                    - Target audience: Small creative agencies and automation enthusiasts
                    - Tone: Professional yet approachable, innovative
                    - Include: Introduction, 2-3 main sections, conclusion with CTA
                    - Focus on practical value and real-world applications

                    Please provide ONLY a valid JSON response with no additional text, using this exact format:
                    {{
                    "title": "Your compelling title here",
                    "outline": ["Point 1", "Point 2", "Point 3", "Point 4"],
                    "content": "Full blog post content in markdown format here"
                    }}"""
        
        try:
            response = self.client.responses.create(
                model=self.model,
                instructions="You are a content writer for NovaMind, an AI startup that helps small creative agencies automate their daily workflows (think Notion + Zapier + ChatGPT combined).",
                input = prompt
            )
            raw_content = response.output[0].content[0].text
            content = ContentGenerator.clean_response(raw_content)
            blog_data = json.loads(content)
            
            logger.info(f"Blog post generated: {blog_data['title']}")
            return blog_data
            
        except Exception as e:
            logger.error(f"Error generating blog post: {e}")
            # Fallback response
            return {
                "title": f"How {topic} is Transforming Creative Workflows",
                "outline": ["Introduction to automation", "Key benefits", "Implementation strategies", "Conclusion"],
                "content": f"# How {topic} is Transforming Creative Workflows\n\nAutomation is revolutionizing how creative agencies work..."
            }
    
    def generate_persona_newsletters(self, blog_data: Dict[str, str]) -> Dict[str, Dict[str, str]]:
        """Generate personalized newsletters for each persona"""
        logger.info("Generating persona-specific newsletters")
        
        newsletters = {}
        
        for persona_key, persona_info in self.config.PERSONAS.items():
            prompt = f"""You are writing a newsletter for NovaMind targeting {persona_info['name']}.

                            Original Blog Post Title: {blog_data['title']}
                            Blog Content Summary: {blog_data['content'][:800]}...

                            Target Persona: {persona_info['name']}
                            Focus Areas: {', '.join(persona_info['focus'])}
                            Tone: {persona_info['tone']}

                            Create a personalized newsletter version (150-250 words) that:
                            - Highlights aspects most relevant to this persona
                            - Uses language and examples that resonate with them
                            - Includes a clear CTA to read the full blog post
                            - Has an engaging subject line

                            Respond with ONLY valid JSON using this exact format:
                            {{
                            "subject_line": "Your subject line here",
                            "preview_text": "Preview text (50-80 chars)",
                            "content": "Full newsletter content here"
                            }}"""
            
            try:
                response = self.client.responses.create(
                model=self.model,
                instructions="You are a content writer for NovaMind, an AI startup that helps small creative agencies automate their daily workflows (think Notion + Zapier + ChatGPT combined).",
                input = prompt
                )
                raw_content = response.output[0].content[0].text
                content = ContentGenerator.clean_response(raw_content)
                newsletter_data = json.loads(content)
                
            except Exception as e:
                logger.error(f"Error generating newsletter for {persona_key}: {e}")
                newsletter_data = {
                    "subject_line": f"New: {blog_data['title']} for {persona_info['name']}",
                    "preview_text": f"Discover how this impacts your work",
                    "content": f"Hi there,\n\nWe've just published a new article that's perfect for {persona_info['name']}..."
                }
            
            newsletters[persona_key] = newsletter_data
            logger.info(f"Newsletter generated for {persona_key}")
        
        return newsletters
    
    def generate_variations(self, content: str, num_variations: int = 2) -> List[str]:
        """Generate alternative versions of content"""
        logger.info(f"Generating {num_variations} content variations")
        
        prompt = f"""Create {num_variations} alternative versions of the following content. 
                    Make each version distinct in style and approach while maintaining the core message.

                    Original Content:
                    {content[:500]}

                    Provide ONLY a JSON array of strings. Example format: ["variation 1 text here", "variation 2 text here"]"""
        
        try:
            response = self.client.responses.create(
                model=self.model,
                instructions="You are a content writer for NovaMind, an AI startup that helps small creative agencies automate their daily workflows (think Notion + Zapier + ChatGPT combined).",
                input = prompt
                )
            raw_content = response.output[0].content[0].text
            content = ContentGenerator.clean_response(raw_content)
            result = json.loads(content)
            
            # Handle different JSON formats
            if isinstance(result, dict) and 'variations' in result:
                variations = result['variations']
            elif isinstance(result, list):
                variations = result
            else:
                variations = list(result.values())
            
            return variations
            
        except Exception as e:
            logger.error(f"Error generating variations: {e}")
            return [content]
    
    def suggest_improvements(self, content: str, performance_data: Dict = None) -> Dict[str, any]:
        """Suggest content improvements based on performance"""
        logger.info("Generating content improvement suggestions")
        
        performance_context = ""
        if performance_data:
            performance_context = f"\n\nPerformance Context:\n{json.dumps(performance_data, indent=2)}"
        
        prompt = f"""Analyze the following content and suggest improvements.
                        {performance_context}

                        Content:
                        {content[:600]}

                        Provide specific suggestions for:
                        1. Headlines (2-3 alternatives)
                        2. Opening hook improvements
                        3. CTA optimization
                        4. Engagement tactics

                        Respond with ONLY valid JSON using this format:
                        {{
                        "headline_suggestions": ["headline 1", "headline 2"],
                        "hook_improvements": "suggestion text",
                        "cta_optimization": "suggestion text",
                        "engagement_tactics": ["tactic 1", "tactic 2", "tactic 3"]
                        }}"""
        
        try:
            response = self.client.responses.create(
                model=self.model,
                instructions="You are a content writer for NovaMind, an AI startup that helps small creative agencies automate their daily workflows (think Notion + Zapier + ChatGPT combined).",
                input = prompt
                )
            raw_content = response.output[0].content[0].text
            content = ContentGenerator.clean_response(raw_content)
            return json.loads(content)
            
        except Exception as e:
            logger.error(f"Error generating improvements: {e}")
            return {
                "headline_suggestions": ["Consider more specific headlines", "Add numbers or data"],
                "hook_improvements": "Start with a compelling question or stat",
                "cta_optimization": "Make CTAs more action-oriented",
                "engagement_tactics": ["Add case studies", "Include visuals", "Use storytelling"]
            }