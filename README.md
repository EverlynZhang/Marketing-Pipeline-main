# Marketing-Pipeline-main
# 🚀 NovaMind AI Marketing Content Pipeline

An automated AI-powered marketing pipeline that generates, distributes, and optimizes blog and newsletter content using OpenAI and CRM integrations.

## 🌟 Features

- **AI Content Generation**: Automatically generates blog posts and persona-specific newsletters
- **CRM Integration**: Works with HubSpot API (with mock mode fallback)
- **Performance Analytics**: Tracks engagement metrics and generates AI-powered insights
- **Content Variations**: Generate multiple versions with improvement suggestions
- **Web Dashboard**: Simple Flask-based UI for managing campaigns
- **Automated Segmentation**: Targets content by persona (Founders, Creatives, Operations)

## 📋 Prerequisites

- Python 3.8+
- OpenAI API key
- HubSpot API key (optional - works in mock mode without it)

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure Environment

Create a `.env` file:
```bash
OPENAI_API_KEY=sk-your-openai-key-here
HUBSPOT_API_KEY=your-hubspot-key-here  # Optional
HUBSPOT_ACCOUNT_ID=your-account-id      # Optional
```

### 3. Run Your First Campaign
```bash
# Command line
python main.py "AI workflow automation"

# With variations
python main.py "AI workflow automation" --variations

# Interactive mode
python main.py
```

### 4. Launch Dashboard
```bash
python dashboard/app.py
```

Visit http://localhost:5000

## 📁 Project Structure
```
novamind-content-pipeline/
├── config.py              
├── main.py               
├── run_dashboard.py   
├── requirements.txt
├── .env
├── src/
│   ├── content_generator.py   
│   ├── crm_integration.py      
│   ├── performance_analyzer.py 
│   └── utils.py                
├── dashboard/
│   ├── app.py                  
│   └── templates/              
└── data/
    ├── generated_content/      
    ├── campaigns/             
    └── analytics/           
```

## 💡 Usage Examples

### Generate Campaign with All Features
```bash
python run_dashboard.py
```


### API Usage
```python
from main import run_pipeline

result = run_pipeline(
    topic="AI in creative automation",
    use_mock_contacts=True,
    generate_variations=True
)

print(f"Campaign ID: {result['campaign_id']}")
print(f"Best Performer: {max(result['performance'].items(), key=lambda x: x[1]['clicked'])[0]}")
```

## 📊 Output Files

Each campaign generates:

- **Content**: `data/generated_content/[title]_[campaign_id].json`
- **Campaign Log**: `data/campaigns/[campaign_id]_log.json`
- **Performance Data**: `data/analytics/[campaign_id]_performance.json`
- **AI Summary**: `data/analytics/[campaign_id]_summary.json`
- **Improvements** (if variations enabled): `data/analytics/[campaign_id]_improvements.json`

## 🎯 Personas

The system generates targeted content for three personas:

1. **Founders / Decision-Makers**: Focus on ROI, growth, efficiency
2. **Creative Professionals**: Focus on inspiration, tools, creativity
3. **Operations Managers**: Focus on workflows, integrations, reliability

## 🔧 Configuration

Edit `config.py` to customize:

- AI model settings
- Content length parameters
- Data storage paths
- Persona definitions

## 📈 Performance Metrics

Tracked metrics include:
- Delivery rate
- Open rate
- Click-through rate
- Unsubscribe rate
- Bounce rate

## 🤖 AI-Powered Features

- Blog post generation (400-600 words)
- Persona-specific newsletters (150-250 words)
- Content variations
- Performance insights
- Topic suggestions
- Improvement recommendations

## 🛠️ Development

### Add New Persona

Edit `config.py`:
```python
PERSONAS = {
    'new_persona': {
        'name': 'New Persona Name',
        'focus': ['focus1', 'focus2'],
        'tone': 'professional, friendly'
    }
}
```

## 🤝 Contributing

Contributions welcome! Please open an issue or PR.

## 📞 Support

For issues or questions:
- Open a GitHub issue
- Check documentation at `/docs`

## 🎉 Acknowledgments

Built with:
- OpenAI GPT-4o
- HubSpot CRM API
- Flask
- Python

---
