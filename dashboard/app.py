#!/usr/bin/env python3
"""
Simple Flask Dashboard for NovaMind Pipeline
"""

import sys
import os

# Add parent directory to Python path so we can import from root
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from flask import Flask, render_template, request, jsonify, redirect, url_for
import json
from datetime import datetime
from config import Config
from src.content_generator import ContentGenerator
from src.crm_integration import CRMIntegration
from src.performance_analyzer import PerformanceAnalyzer
from src.utils import generate_campaign_id, sanitize_filename, save_json, logger
import threading
import traceback

app = Flask(__name__)
config = Config()
config.setup_directories()

# Store running pipelines
running_pipelines = {}

@app.route('/')
def index():
    """Main dashboard page"""
    # Get all campaigns
    campaigns = []
    campaigns_dir = os.path.abspath(config.CAMPAIGNS_DIR)
    
    if os.path.exists(campaigns_dir):
        for file in os.listdir(campaigns_dir):
            if file.endswith('_log.json'):
                filepath = os.path.join(campaigns_dir, file)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        campaigns.append(json.load(f))
                except Exception as e:
                    logger.error(f"Error loading {file}: {e}")
    
    campaigns.sort(key=lambda x: x.get('send_date', ''), reverse=True)
    
    return render_template('index.html', campaigns=campaigns[:10])

@app.route('/create', methods=['GET', 'POST'])
def create_campaign():
    """Create new campaign form"""
    if request.method == 'POST':
        topic = request.form.get('topic')
        generate_variations = request.form.get('variations') == 'on'
        
        if not topic or not topic.strip():
            return render_template('create.html', error="Please enter a topic")
        
        # Start pipeline in background
        campaign_id = generate_campaign_id()
        
        # Initialize status
        running_pipelines[campaign_id] = {
            'status': 'starting',
            'topic': topic,
            'started_at': datetime.now().isoformat()
        }
        
        thread = threading.Thread(
            target=run_pipeline_async,
            args=(campaign_id, topic, generate_variations),
            name=f"Pipeline-{campaign_id}"
        )
        thread.daemon = True
        thread.start()
        
        logger.info(f"Started pipeline thread for campaign {campaign_id}")
        
        return redirect(url_for('campaign_status', campaign_id=campaign_id))
    
    return render_template('create.html')

@app.route('/campaign/<campaign_id>')
def campaign_detail(campaign_id):
    """View campaign details"""
    # Load campaign data
    campaign_file = os.path.join(config.CAMPAIGNS_DIR, f'{campaign_id}_log.json')
    performance_file = os.path.join(config.ANALYTICS_DIR, f'{campaign_id}_performance.json')
    summary_file = os.path.join(config.ANALYTICS_DIR, f'{campaign_id}_summary.json')
    
    if not os.path.exists(campaign_file):
        return "Campaign not found", 404
    
    with open(campaign_file, 'r', encoding='utf-8') as f:
        campaign = json.load(f)
    
    performance = None
    if os.path.exists(performance_file):
        with open(performance_file, 'r', encoding='utf-8') as f:
            performance = json.load(f)
    
    summary = None
    if os.path.exists(summary_file):
        with open(summary_file, 'r', encoding='utf-8') as f:
            summary = json.load(f)
    
    return render_template('campaign.html', 
                         campaign=campaign, 
                         performance=performance,
                         summary=summary)

@app.route('/status/<campaign_id>')
def campaign_status(campaign_id):
    """Check campaign status"""
    # First check if it's in running_pipelines
    if campaign_id in running_pipelines:
        status = running_pipelines[campaign_id]
        
        # If completed, redirect to campaign detail
        if status.get('status') == 'completed':
            campaign_file = os.path.join(config.CAMPAIGNS_DIR, f"{campaign_id}_log.json")
            if os.path.exists(campaign_file):
                return redirect(url_for('campaign_detail', campaign_id=campaign_id))
        
        return render_template('status.html', 
                             campaign_id=campaign_id,
                             status=status)
    
    # Check if campaign exists in files (completed before server restart)
    campaign_file = os.path.join(config.CAMPAIGNS_DIR, f'{campaign_id}_log.json')
    if os.path.exists(campaign_file):
        return redirect(url_for('campaign_detail', campaign_id=campaign_id))
    
    # Campaign not found
    return render_template('status.html',
                         campaign_id=campaign_id,
                         status={'status': 'not_found', 'topic': 'Unknown'})

@app.route('/api/campaigns')
def api_campaigns():
    """API endpoint for campaigns list"""
    campaigns = []
    if os.path.exists(config.CAMPAIGNS_DIR):
        for file in os.listdir(config.CAMPAIGNS_DIR):
            if file.endswith('_log.json'):
                try:
                    with open(os.path.join(config.CAMPAIGNS_DIR, file), 'r', encoding='utf-8') as f:
                        campaigns.append(json.load(f))
                except Exception as e:
                    logger.error(f"Error loading {file}: {e}")
    
    return jsonify(campaigns)

@app.route('/api/performance/<campaign_id>')
def api_performance(campaign_id):
    """API endpoint for campaign performance"""
    performance_file = os.path.join(config.ANALYTICS_DIR, f'{campaign_id}_performance.json')
    
    if not os.path.exists(performance_file):
        return jsonify({'error': 'Performance data not found'}), 404
    
    with open(performance_file, 'r', encoding='utf-8') as f:
        return jsonify(json.load(f))

@app.route('/api/status/<campaign_id>')
def api_status(campaign_id):
    """API endpoint to check campaign status"""
    if campaign_id in running_pipelines:
        return jsonify(running_pipelines[campaign_id])
    
    campaign_file = os.path.join(config.CAMPAIGNS_DIR, f'{campaign_id}_log.json')
    if os.path.exists(campaign_file):
        return jsonify({'status': 'completed', 'campaign_id': campaign_id})
    
    return jsonify({'status': 'not_found'}), 404

def run_pipeline_async(campaign_id, topic, generate_variations):
    """Run pipeline asynchronously"""
    try:
        logger.info(f"Pipeline thread starting for {campaign_id}")
        
        # Update status
        running_pipelines[campaign_id]['status'] = 'running'
        
        # Import main here to avoid issues
        sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
        
        # Import the function components instead of running full pipeline
        from src.content_generator import ContentGenerator
        from src.crm_integration import CRMIntegration
        from src.performance_analyzer import PerformanceAnalyzer
        from src.utils import save_json, sanitize_filename
        
        logger.info(f"Generating content for: {topic}")
        
        # Initialize components
        generator = ContentGenerator()
        crm = CRMIntegration()
        analyzer = PerformanceAnalyzer()
        
        # Generate blog post
        blog_data = generator.generate_blog_post(topic)
        logger.info(f"Blog generated: {blog_data['title']}")
        
        # Generate newsletters
        newsletters = generator.generate_persona_newsletters(blog_data)
        logger.info(f"Newsletters generated for {len(newsletters)} personas")
        
        # Generate variations if requested
        variations = []
        if generate_variations:
            variations = generator.generate_variations(blog_data['content'], num_variations=2)
            logger.info(f"Generated {len(variations)} variations")
        
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
        
        # Create contacts
        contacts = crm.create_mock_contacts(count_per_persona=10)
        segmented_contacts = crm.segment_contacts(contacts)
        
        # Distribute campaign
        campaign_data = {
            'campaign_id': campaign_id,
            'blog_title': blog_data['title'],
            'newsletters': newsletters
        }
        distribution_results = crm.send_campaign(campaign_data)
        
        # Log campaign
        campaign_log = crm.log_campaign(campaign_data)
        campaign_log['distribution_results'] = distribution_results
        campaign_filename = f"{config.CAMPAIGNS_DIR}/{campaign_id}_log.json"
        save_json(campaign_log, campaign_filename)
        
        # Generate performance data
        performance_data = analyzer.simulate_performance_data(
            campaign_id, 
            list(config.PERSONAS.keys())
        )
        analyzer.store_performance_data(campaign_id, performance_data)
        
        # Generate summary
        summary = analyzer.generate_performance_summary(performance_data, blog_data['title'])
        summary_filename = f"{config.ANALYTICS_DIR}/{campaign_id}_summary.json"
        save_json(summary, summary_filename)
        
        # Generate improvements if variations requested
        if generate_variations:
            improvements = generator.suggest_improvements(blog_data['content'], performance_data)
            improvement_filename = f"{config.ANALYTICS_DIR}/{campaign_id}_improvements.json"
            save_json(improvements, improvement_filename)
        
        # Update status to completed
        running_pipelines[campaign_id] = {
            'status': 'completed',
            'topic': topic,
            'campaign_id': campaign_id,
            'completed_at': datetime.now().isoformat()
        }
        
        logger.info(f"Pipeline completed successfully for {campaign_id}")
        
    except Exception as e:
        error_msg = str(e)
        error_trace = traceback.format_exc()
        
        logger.error(f"Pipeline failed for {campaign_id}: {error_msg}")
        logger.error(f"Traceback: {error_trace}")
        
        running_pipelines[campaign_id] = {
            'status': 'failed',
            'topic': topic,
            'error': error_msg,
            'trace': error_trace,
            'failed_at': datetime.now().isoformat()
        }
        
        print(f"Pipeline error details: {error_trace}")

if __name__ == '__main__':
    print("\n" + "="*70)
    print("🚀 NovaMind Marketing Pipeline Dashboard")
    print("="*70)
    print(f"\n📊 Dashboard URL: http://localhost:5000")
    print(f"📁 Data Directory: {os.path.abspath(config.DATA_DIR)}")
    print(f"\n💡 Press CTRL+C to stop the server\n")
    
    app.run(debug=True, port=5000, use_reloader=False, threaded=True)
