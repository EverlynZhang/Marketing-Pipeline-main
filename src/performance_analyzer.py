import random
from typing import Dict, List, Any
import pandas as pd
from config import Config
from src.utils import logger, format_timestamp
from openai import OpenAI
import json

class PerformanceAnalyzer:
    def __init__(self):
        self.config = Config()
        self.client = OpenAI(api_key=self.config.OPENAI_API_KEY)
        self.model = "gpt-4o"
    
    @staticmethod
    def clean_response(raw_text):
        """Clean JSON response from markdown code blocks"""
        if raw_text.startswith("```json"):
            raw_text = raw_text[len("```json"):]
        if raw_text.endswith("```"):
            raw_text = raw_text[:-len("```")]
        return raw_text.strip()
    
    def simulate_performance_data(self, campaign_id: str, personas: List[str]) -> Dict[str, Dict[str, float]]:
        """Simulate newsletter performance metrics"""
        logger.info(f"Simulating performance data for campaign: {campaign_id}")
        
        performance = {}
        
        for persona in personas:
            # Generate base metrics
            sent = random.randint(80, 100)
            
            # Delivered should be less than or equal to sent
            delivered = random.randint(int(sent * 0.85), sent)  # 85-100% delivery rate
            
            # Open rate as fraction of delivered
            base_open = random.uniform(0.18, 0.35)
            
            # Click rate as fraction of delivered (always less than open rate)
            base_click = random.uniform(0.05, 0.15)
            
            # Different personas have different engagement patterns
            if persona == 'founders':
                open_rate = base_open * 1.1  # Executives open more
                click_rate = base_click * 0.9  # But click through less
            elif persona == 'creatives':
                open_rate = base_open * 1.2  # Creatives are curious
                click_rate = base_click * 1.3  # And engage more
            else:  # operations
                open_rate = base_open
                click_rate = base_click * 1.1
            
            # Ensure rates don't exceed 100%
            open_rate = min(open_rate, 0.95)
            click_rate = min(click_rate, open_rate * 0.8)  # Clicks can't exceed opens
            
            performance[persona] = {
                'sent': sent,
                'delivered': delivered,
                'opened': round(open_rate, 4),
                'clicked': round(click_rate, 4),
                'unsubscribed': round(random.uniform(0.001, 0.01), 4),
                'bounced': round(random.uniform(0.01, 0.05), 4)
            }
        
        logger.info("Performance data simulated")
        return performance
    
    def fetch_real_performance_data(self, campaign_id: str) -> Dict[str, Any]:
        """Fetch actual performance data from HubSpot (when available)"""
        logger.info("Fetching performance data (mock)")
        return self.simulate_performance_data(campaign_id, list(self.config.PERSONAS.keys()))
    
    def store_performance_data(self, campaign_id: str, performance_data: Dict[str, Any]) -> str:
        """Store performance data for historical tracking"""
        from src.utils import save_json
        
        filepath = f"{self.config.ANALYTICS_DIR}/{campaign_id}_performance.json"
        
        data_to_store = {
            'campaign_id': campaign_id,
            'timestamp': format_timestamp(),
            'performance': performance_data
        }
        
        save_json(data_to_store, filepath)
        logger.info(f"Performance data stored: {filepath}")
        return filepath
    
    def generate_performance_summary(self, performance_data: Dict[str, Dict[str, float]], 
                                    blog_title: str) -> Dict[str, Any]:
        """Generate AI-powered performance analysis and recommendations"""
        logger.info("Generating AI-powered performance summary")
        
        # Format performance data for analysis
        performance_text = self._format_performance_for_analysis(performance_data)
        
        prompt = f"""You are a marketing analyst for NovaMind. Analyze the following email campaign performance data and provide insights.

                    Campaign: {blog_title}

                    Performance Data:
                    {performance_text}

                    Provide a comprehensive analysis with:
                    1. Key Performance Highlights (2-3 sentences about overall performance)
                    2. Persona Comparison (detailed comparison of which segment performed best and why)
                    3. Actionable Recommendations (3-5 specific, data-driven suggestions for improving future campaigns)
                    4. Suggested Next Topics (2-3 blog topic ideas based on engagement patterns)

                    Respond with ONLY valid JSON using this exact format:
                    {{
                    "highlights": "your highlights text here",
                    "persona_comparison": "your comparison text here",
                    "recommendations": ["recommendation 1", "recommendation 2", "recommendation 3"],
                    "next_topics": ["topic 1", "topic 2", "topic 3"]
                    }}"""
        
        try:
            response = self.client.responses.create(
                model=self.model,
                instructions="You are a marketing analytics expert for NovaMind. Always provide data-driven insights and actionable recommendations.",
                input=prompt
            )
            
            raw_content = response.output[0].content[0].text
            content = self.clean_response(raw_content)
            summary = json.loads(content)
            logger.info("Performance summary generated")
            return summary
        
        except Exception as e:
            logger.error(f"Error generating summary: {e}")
            return self._fallback_summary(performance_data)
    
    def _format_performance_for_analysis(self, performance_data: Dict[str, Dict[str, float]]) -> str:
        """Format performance data as readable text"""
        lines = []
        for persona, metrics in performance_data.items():
            lines.append(f"\n{persona.upper()}:")
            lines.append(f"  - Sent: {metrics['sent']}")
            lines.append(f"  - Delivered: {metrics['delivered']}")
            lines.append(f"  - Open Rate: {metrics['opened']*100:.1f}%")
            lines.append(f"  - Click Rate: {metrics['clicked']*100:.1f}%")
            lines.append(f"  - Unsubscribe Rate: {metrics['unsubscribed']*100:.2f}%")
        
        return "\n".join(lines)
    
    def _fallback_summary(self, performance_data: Dict[str, Dict[str, float]]) -> Dict[str, Any]:
        """Generate basic summary if AI fails"""
        best_persona = max(performance_data.items(), key=lambda x: x[1]['clicked'])
        
        return {
            'highlights': f"Campaign delivered to {sum(p['delivered'] for p in performance_data.values())} recipients across 3 segments.",
            'persona_comparison': f"{best_persona[0]} segment had the highest engagement with {best_persona[1]['clicked']*100:.1f}% click rate.",
            'recommendations': [
                "Continue targeting the best-performing segment",
                "A/B test subject lines for lower-performing segments",
                "Increase visual content for creative professionals"
            ],
            'next_topics': [
                "Workflow automation case studies",
                "Integration deep-dives",
                "ROI calculators for automation"
            ]
        }
    
    def compare_campaigns(self, campaign_ids: List[str]) -> pd.DataFrame:
        """Compare performance across multiple campaigns"""
        from src.utils import load_json
        
        all_data = []
        
        for campaign_id in campaign_ids:
            try:
                filepath = f"{self.config.ANALYTICS_DIR}/{campaign_id}_performance.json"
                data = load_json(filepath)
                
                for persona, metrics in data['performance'].items():
                    all_data.append({
                        'campaign_id': campaign_id,
                        'persona': persona,
                        **metrics
                    })
            except FileNotFoundError:
                logger.warning(f"Performance data not found for {campaign_id}")
        
        if all_data:
            df = pd.DataFrame(all_data)
            logger.info(f"Compared {len(campaign_ids)} campaigns")
            return df
        
        return pd.DataFrame()
    
    def generate_topic_suggestions(self, historical_performance: pd.DataFrame = None) -> List[str]:
        """Generate blog topic suggestions based on historical data"""
        logger.info("Generating topic suggestions based on historical performance")
        
        if historical_performance is None or historical_performance.empty:
            prompt = """You are a content strategist for NovaMind (an AI automation platform for creative agencies).

                        Suggest 5 compelling blog topics that would resonate with our audience segments:
                        - Founders/Decision-Makers (focus on ROI, growth)
                        - Creative Professionals (focus on inspiration, tools)
                        - Operations Managers (focus on workflows, integrations)

                        Respond with ONLY valid JSON:
                        {
                        "topics": ["topic 1", "topic 2", "topic 3", "topic 4", "topic 5"]
                        }"""
        else:
            # Analyze best-performing content
            top_performers = historical_performance.nlargest(5, 'clicked')
            
            prompt = f"""Based on the following high-performing campaign data, suggest 5 new blog topics for NovaMind (an AI automation platform for creative agencies).

                        Top Performing Campaigns:
                        {top_performers.to_string()}

                        Suggest topics that would likely resonate with our audience. Respond with ONLY valid JSON:
                        {{
                        "topics": ["topic 1", "topic 2", "topic 3", "topic 4", "topic 5"]
                        }}"""
        
        try:
            response = self.client.responses.create(
                model=self.model,
                instructions="You are a content strategist for NovaMind. Always suggest relevant, engaging topics.",
                input=prompt
            )
            
            raw_content = response.output[0].content[0].text
            content = self.clean_response(raw_content)
            result = json.loads(content)
            return result.get('topics', [])
            
        except Exception as e:
            logger.error(f"Error generating topics: {e}")
            return [
                "10 Automation Workflows Every Creative Agency Needs",
                "How AI is Transforming Project Management in 2025",
                "Integration Strategies for Modern Agencies",
                "Case Study: Saving 20 Hours Per Week with Automation",
                "The ROI of AI-Powered Workflow Tools"
            ]
    
    def analyze_persona_trends(self, campaign_ids: List[str]) -> Dict[str, Any]:
        """Analyze trends across personas over multiple campaigns"""
        logger.info("Analyzing persona trends")
        
        df = self.compare_campaigns(campaign_ids)
        
        if df.empty:
            return {
                'trends': 'Insufficient data for trend analysis',
                'recommendations': []
            }
        
        # Calculate averages by persona
        persona_stats = df.groupby('persona').agg({
            'opened': 'mean',
            'clicked': 'mean',
            'unsubscribed': 'mean'
        }).to_dict()
        
        prompt = f"""Analyze these persona engagement trends for NovaMind's email campaigns:

                    {json.dumps(persona_stats, indent=2)}

                    Provide insights on:
                    1. Which personas are most engaged
                    2. Any concerning trends (e.g., high unsubscribe rates)
                    3. Specific recommendations for each persona

                    Respond with ONLY valid JSON:
                    {{
                    "trends": "overall trends description",
                    "persona_insights": {{
                        "founders": "insights for founders",
                        "creatives": "insights for creatives",
                        "operations": "insights for operations"
                    }},
                    "recommendations": ["rec 1", "rec 2", "rec 3"]
                    }}"""
        
        try:
            response = self.client.responses.create(
                model=self.model,
                instructions="You are a marketing analytics expert. Provide actionable insights based on data.",
                input=prompt
            )
            
            raw_content = response.output[0].content[0].text
            content = self.clean_response(raw_content)
            return json.loads(content)
            
        except Exception as e:
            logger.error(f"Error analyzing trends: {e}")
            return {
                'trends': 'Analysis unavailable',
                'persona_insights': {},
                'recommendations': ['Continue monitoring engagement metrics']
            }