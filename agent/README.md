# Autonomous AI Social Media Agent

A sophisticated background service that autonomously manages social media content using artificial intelligence. The agent continuously monitors, optimizes, and executes social media strategies for maximum engagement and reach.

## Features

### 🤖 AI Decision Engine
- **Platform Selection**: Automatically chooses between YouTube and Instagram based on content analysis
- **Optimal Timing**: Uses analytics to determine best posting times
- **Caption Optimization**: AI-generated, platform-specific captions for maximum engagement
- **Content Categorization**: Intelligent content analysis with Malayalam language support

### 🎬 Content Repurposing
- **Cross-Platform Content**: Automatically creates Instagram clips from YouTube videos
- **Video Processing**: Intelligent clip extraction and formatting
- **Thumbnail Generation**: AI-optimized thumbnails for each platform

### 📊 Analytics & Learning
- **Performance Analysis**: Comprehensive analytics with engagement tracking
- **Success Prediction**: ML-powered prediction of content success potential
- **Continuous Learning**: Agent learns from performance data to improve decisions

### 💬 Comment Automation
- **AI Responses**: Context-aware replies in Malayalam and English
- **Smart Filtering**: Only responds to meaningful comments
- **Platform Integration**: Works with YouTube and Instagram comments

### 📈 Report Generation
- **Weekly Reports**: Automated performance summaries
- **Email/WhatsApp Notifications**: Configurable report delivery
- **Actionable Insights**: AI-generated recommendations for improvement

## Architecture

```
agent/
├── core/                 # Core orchestration
│   ├── monitoring.py     # Continuous post monitoring
│   └── orchestrator.py   # Main service coordinator
├── services/             # AI services
│   ├── decision_engine.py    # Platform & timing decisions
│   ├── content_repurposer.py # Cross-platform content creation
│   ├── analytics_agent.py    # Performance analysis
│   ├── comment_automation.py # AI comment responses
│   └── report_generator.py   # Automated reporting
├── utils/                # Utilities
│   └── database.py       # Database operations
└── config/               # Configuration
    └── settings.py       # Agent settings
```

## Installation

### Requirements
```bash
pip install -r requirements.txt
pip install -r agent/requirements-agent.txt
```

### Environment Variables
```bash
# Required
OPENAI_API_KEY=your_openai_key
DATABASE_URL=postgresql://user:pass@localhost/db

# Optional
YOUTUBE_API_KEY=your_youtube_key
INSTAGRAM_ACCESS_TOKEN=your_instagram_token
EMAIL_RECIPIENT=your@email.com
WHATSAPP_NUMBER=+1234567890

# Agent Configuration
MONITORING_INTERVAL_HOURS=2
LOG_LEVEL=INFO
```

## Usage

### Running the Agent

```bash
# Start the autonomous agent
python -m agent

# Check agent status
python -m agent status

# Generate manual report
python -m agent report

# Run manual monitoring check
python -m agent check
```

### Docker Deployment

```bash
# Build and run with docker-compose
docker-compose -f infra/docker-compose.yml up agent

# Or build standalone
docker build -f Dockerfile.agent -t social-media-agent .
docker run -e OPENAI_API_KEY=... social-media-agent
```

## Configuration

The agent is highly configurable through environment variables:

- **Monitoring**: `MONITORING_INTERVAL_HOURS`, `MAX_POSTS_PER_CHECK`
- **AI**: `OPENAI_MODEL`, `MAX_TOKENS_DECISION`, `TEMPERATURE_DECISION`
- **Content**: `CLIP_DURATION_SECONDS`, `MALAYALAM_LANGUAGE_CODE`
- **Comments**: `COMMENT_CHECK_INTERVAL_MINUTES`, `MAX_COMMENTS_PER_POST`
- **Reports**: `REPORT_GENERATION_DAY`, `EMAIL_ENABLED`, `WHATSAPP_ENABLED`

## API Integration

The agent integrates seamlessly with the existing FastAPI backend:

- **Database**: Shared PostgreSQL database with the main application
- **Models**: Uses existing Post and Analytics models
- **Services**: Leverages existing AI and platform services
- **Scheduling**: Integrates with APScheduler for post timing

## Monitoring & Logging

- **Comprehensive Logging**: All actions logged with configurable levels
- **Health Checks**: Built-in health monitoring for all services
- **Status API**: Real-time status checking via orchestrator
- **Error Handling**: Graceful error handling with automatic retries

## Safety & Ethics

- **Content Filtering**: Respects platform guidelines and content policies
- **Rate Limiting**: Built-in rate limiting to prevent API abuse
- **Privacy**: No user data collection beyond necessary analytics
- **Transparency**: All AI decisions logged and auditable

## Development

### Testing
```bash
# Run agent tests
pytest agent/tests/

# Test individual services
python -c "from agent.services.decision_engine import DecisionEngine; # test code"
```

### Extending the Agent

The modular architecture makes it easy to add new capabilities:

1. **New Services**: Add to `agent/services/` with consistent interface
2. **New Platforms**: Extend platform integrations in existing services
3. **New AI Features**: Integrate additional OpenAI capabilities
4. **Custom Logic**: Override decision-making logic for specific use cases

## Troubleshooting

### Common Issues

1. **Database Connection**: Ensure DATABASE_URL is correct and database is accessible
2. **OpenAI API**: Verify API key and quota limits
3. **Platform APIs**: Check YouTube/Instagram API credentials
4. **FFmpeg**: Ensure FFmpeg is installed for video processing

### Logs
Check agent logs at the configured `LOG_FILE` location (default: `agent.log`)

### Health Checks
Use `python -m agent status` to check all service health

## License

This project is part of the AI Social Media Manager system.

## Contributing

1. Follow the existing code structure and patterns
2. Add comprehensive logging
3. Include error handling and tests
4. Update documentation for new features
5. Ensure all new code is asynchronous where appropriate
