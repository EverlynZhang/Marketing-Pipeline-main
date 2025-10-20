#!/usr/bin/env python3
"""
NovaMind AI-Powered Marketing Content Pipeline
Main execution script
"""

import sys
from datetime import datetime
from config import Config
from src.content_generator import ContentGenerator
from src.crm_integration import CRMIntegration
from src.performance_analyzer import PerformanceAnalyzer
from src.utils import save_json, generate_campaign_id, logger, sanitize_filename

def run_pipeline(topic: str, use_mock_contacts: bool = True, generate_variations: bool = False):
    """Run the complete marketing content pipeline"""
    
    print("\n" + "="*70)
    print("🚀 NovaMind AI Marketing Content Pipeline")
    print("="*70 + "\n")
    
    # Initialize components
    config = Config()
    config.setup_directories()
    
    generator = ContentGenerator()
    crm = CRMIntegration()
    analyzer = PerformanceAnalyzer()
    
    # Show setup status
    if crm.mock_mode:
        print("⚙️  Running in MOCK MODE (no real HubSpot API calls)")
        print("💡 To enable HubSpot integration, add HUBSPOT_API_KEY to .env\n")
    
    # Generate campaign ID
    campaign_id = generate_campaign_id()
    print(f"📋 Campaign ID: {campaign_id}\n")
    
    # Step 1: Generate Blog Content
    print("📝 Step 1: Generating blog content...")
    blog_data = generator.generate_blog_post(topic)
    print(f"   ✓ Blog Title: {blog_data['title']}")
    print(f"   ✓ Word Count: {len(blog_data['content'].split())} words\n")
    
    # Optional: Generate content variations
    variations = []
    if generate_variations:
        print("🔄 Generating content variations...")
        variations = generator.generate_variations(blog_data['content'], num_variations=2)
        print(f"   ✓ Generated {len(variations)} variations\n")
    
    # Step 2: Generate Persona Newsletters
    print("📧 Step 2: Generating personalized newsletters...")
    newsletters = generator.generate_persona_newsletters(blog_data)
    for persona, newsletter in newsletters.items():
        print(f"   ✓ {persona}: {newsletter['subject_line']}")
    print()
    
    # Save content
    content_filename = f"{config.CONTENT_DIR}/{sanitize_filename(blog_data['title'])}_{campaign_id}.json"
    save_json({
        'campaign_id': campaign_id,
        'topic': topic,
        'blog': blog_data,
        'newsletters': newsletters,
        'variations': variations,
        'created_at': datetime.now().isoformat()
    }, content_filename)
    print(f"💾 Content saved: {content_filename}\n")
    
    # Step 3: CRM Integration
    print("👥 Step 3: Managing CRM contacts...")
    if use_mock_contacts:
        contacts = crm.create_mock_contacts(count_per_persona=10)
        print(f"   ✓ Created {len(contacts)} mock contacts")
    else:
        contacts = []
    
    # Segment contacts
    segmented_contacts = crm.segment_contacts(contacts)
    for persona, persona_contacts in segmented_contacts.items():
        print(f"   ✓ {persona}: {len(persona_contacts)} contacts")
    print()
    
    # Step 4: Campaign Distribution
    print("📤 Step 4: Distributing campaign...")
    campaign_data = {
        'campaign_id': campaign_id,
        'blog_title': blog_data['title'],
        'newsletters': newsletters
    }

    # Check if we're using real HubSpot contacts
    if not crm.mock_mode:
        print("   ℹ️  Using real HubSpot contacts")
        
    distribution_results = crm.send_campaign(campaign_data)

    # Show distribution summary
    if crm.mock_mode or not crm._check_marketing_access():
        mode_msg = "simulated (no Marketing Hub)" if not crm.mock_mode else "simulated (mock mode)"
        print(f"   ✓ Campaign distribution {mode_msg}")
        total_recipients = sum(
            r.get('recipients', 0) for r in distribution_results.values()
        )
        print(f"   ✓ Total simulated recipients: {total_recipients}")
    else:
        print(f"   ✓ Campaign sent via HubSpot Marketing Hub")
        print(f"   ✓ Distributed to {len(distribution_results)} segments")

    print()
    
    # Log campaign
    campaign_log = crm.log_campaign(campaign_data)
    campaign_log['distribution_results'] = distribution_results
    campaign_filename = f"{config.CAMPAIGNS_DIR}/{campaign_id}_log.json"
    save_json(campaign_log, campaign_filename)
    
    # Step 5: Performance Analysis
    print("📊 Step 5: Analyzing performance...")
    performance_data = analyzer.simulate_performance_data(
        campaign_id, 
        list(config.PERSONAS.keys())
    )
    
    # Display performance metrics
    print("\n   Performance Metrics:")
    for persona, metrics in performance_data.items():
        print(f"\n   {persona.upper()}:")
        print(f"     • Delivered: {metrics['delivered']}/{metrics['sent']}")
        print(f"     • Open Rate: {metrics['opened']*100:.1f}%")
        print(f"     • Click Rate: {metrics['clicked']*100:.1f}%")
        print(f"     • Unsubscribe: {metrics['unsubscribed']*100:.2f}%")
    
    # Store performance data
    analyzer.store_performance_data(campaign_id, performance_data)
    
    # Generate AI-powered summary
    print("\n🤖 Generating AI-powered insights...")
    summary = analyzer.generate_performance_summary(performance_data, blog_data['title'])
    
    print(f"\n   📈 Highlights:\n      {summary['highlights']}")
    print(f"\n   🎯 Comparison:\n      {summary['persona_comparison']}")
    print(f"\n   💡 Recommendations:")
    for i, rec in enumerate(summary['recommendations'], 1):
        print(f"      {i}. {rec}")
    print(f"\n   📝 Suggested Next Topics:")
    for i, topic in enumerate(summary['next_topics'], 1):
        print(f"      {i}. {topic}")
    
    # Save summary
    summary_filename = f"{config.ANALYTICS_DIR}/{campaign_id}_summary.json"
    save_json(summary, summary_filename)
    print(f"\n💾 Analysis saved: {summary_filename}\n")
    
    # Optional: Generate content improvements
    if generate_variations:
        print("✨ Generating content improvement suggestions...")
        improvements = generator.suggest_improvements(
            blog_data['content'], 
            performance_data
        )
        improvement_filename = f"{config.ANALYTICS_DIR}/{campaign_id}_improvements.json"
        save_json(improvements, improvement_filename)
        print(f"   ✓ Headline alternatives: {len(improvements['headline_suggestions'])}")
        print(f"   ✓ Engagement tactics: {len(improvements['engagement_tactics'])}")
        print(f"   💾 Saved to: {improvement_filename}\n")
    
    print("="*70)
    print("✅ Pipeline execution complete!")
    print("="*70 + "\n")
    
    # Show HubSpot setup info if in mock mode
    if crm.mock_mode:
        print("💡 TIP: To enable real HubSpot integration, run:")
        print("   python setup_hubspot.py\n")
    
    return {
        'campaign_id': campaign_id,
        'blog_data': blog_data,
        'newsletters': newsletters,
        'performance': performance_data,
        'summary': summary,
        'mock_mode': crm.mock_mode
    }

def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='NovaMind AI Marketing Content Pipeline')
    parser.add_argument('topic', type=str, nargs='?', help='Blog topic to generate content about')
    parser.add_argument('--variations', action='store_true', help='Generate content variations')
    parser.add_argument('--no-mock', action='store_true', help='Disable mock contacts')
    parser.add_argument('--setup-hubspot', action='store_true', help='Show HubSpot setup instructions')
    
    args = parser.parse_args()
    
    if args.setup_hubspot:
        crm = CRMIntegration()
        print(crm.get_hubspot_setup_instructions())
        return
    
    if not args.topic:
        # Interactive mode
        print("\n🚀 NovaMind AI Marketing Content Pipeline")
        print("=" * 50)
        topic = input("\nEnter a blog topic: ")
        variations = input("Generate variations? (y/n): ").lower() == 'y'
        
        run_pipeline(topic, use_mock_contacts=True, generate_variations=variations)
        return
    
    try:
        result = run_pipeline(
            topic=args.topic,
            use_mock_contacts=not args.no_mock,
            generate_variations=args.variations
        )
        
        print(f"\n📦 Pipeline Summary:")
        print(f"   Campaign ID: {result['campaign_id']}")
        print(f"   Blog Title: {result['blog_data']['title']}")
        print(f"   Newsletters: {len(result['newsletters'])}")
        print(f"   Best Performing: {max(result['performance'].items(), key=lambda x: x[1]['clicked'])[0]}")
        print(f"   Mode: {'MOCK' if result['mock_mode'] else 'PRODUCTION'}")
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Pipeline interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Pipeline failed: {e}", exc_info=True)
        print(f"\n❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()