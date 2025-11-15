# 🤖 Complete Autonomous AI Social Media System

## Overview

This is a **fully autonomous AI system** that acts as a complete social media team - automatically finding viral topics, creating professional videos, and managing entire YouTube & Instagram channels with **zero daily human input**.

## 🏗️ System Architecture

The system consists of **6 Core Modules** that work together seamlessly:

### 1. 🧠 AI Content Brain
**Location:** `agent/services/ai_content_brain.py`

**Components:**
- **TrendDetector**: Scans YouTube/Instagram/Twitter for trending Malayalam topics
- **IdeaGenerator**: Creates viral content concepts based on trends
- **ScriptWriter**: Writes complete video scripts with scenes and dialogue
- **ContentPlanner**: Creates 7-day content calendar automatically

**Key Features:**
- Multi-platform trend scanning (YouTube, Instagram, Twitter)
- Malayalam content detection and filtering
- Viral potential scoring
- Automated content calendar generation

### 2. 🎬 AI Video Factory
**Location:** `agent/services/ai_video_factory.py`

**Components:**
- **SceneGenerator**: Creates video scenes from text using AI models (Stable Video Diffusion)
- **VoiceStudio**: Generates natural Malayalam voiceovers with emotions
- **VideoEditor**: Automatically edits scenes, adds transitions, effects
- **SubtitleEngine**: Creates perfect Malayalam/English subtitles with timing
- **ThumbnailDesigner**: Designs thumbnails using AI

**Key Features:**
- AI-powered scene generation
- Multi-voice synthesis (Voice Engine, ElevenLabs, Google TTS)
- Automated video composition with FFmpeg
- Multi-language subtitle generation

### 3. 📡 Smart Publisher
**Location:** `agent/services/smart_publisher.py`

**Components:**
- **PlatformManager**: Handles YouTube & Instagram APIs
- **SchedulingEngine**: Finds perfect posting times for maximum views
- **CaptionGenerator**: Writes engaging captions in Malayalam + English
- **HashtagOptimizer**: Creates trending hashtag combinations

**Key Features:**
- Multi-platform publishing (YouTube, Instagram)
- AI-optimized scheduling
- Bilingual caption generation
- Hashtag optimization

### 4. 📊 Performance Optimizer
**Location:** `agent/services/performance_optimizer.py`

**Components:**
- **AnalyticsTracker**: Monitors views, likes, comments, engagement
- **MLLearningEngine**: Learns what content performs best
- **ABTesting**: Tests different thumbnails, titles, captions
- **ImprovementSuggester**: Recommends content strategy changes

**Key Features:**
- Real-time performance tracking
- Machine learning-based optimization
- Automated A/B testing
- Data-driven improvement suggestions

### 5. 🚀 Automation Orchestrator
**Location:** `agent/services/automation_orchestrator.py`

**Components:**
- **WorkflowManager**: Coordinates all modules seamlessly
- **ErrorHandler**: Automatically retries failed operations
- **QualityChecker**: Ensures all content meets standards
- **BackupSystems**: Prevents any single point of failure

**Key Features:**
- End-to-end workflow automation
- Automatic error recovery
- Quality assurance
- Backup and restore capabilities

### 6. 📱 Management Dashboard
**Location:** `frontend/app/automation/page.tsx`

**Features:**
- Real-time monitoring of all automated activities
- Content calendar visualization
- Performance analytics and insights
- Manual override capabilities
- System status and health monitoring

## 🔄 Complete Automation Workflow

### Phase 1: CONTENT DISCOVERY
```
AI scans trends → Analyzes competitor content → Predicts viral topics → 
Generates content ideas → Creates content calendar
```

### Phase 2: VIDEO CREATION
```
AI writes script → Generates video scenes → Adds Malayalam voiceover → 
Creates subtitles → Designs thumbnail → Adds background music
```

### Phase 3: OPTIMIZATION & PUBLISHING
```
AI writes captions → Generates hashtags → Finds optimal posting time → 
Auto-posts to platforms → Cross-promotes content
```

### Phase 4: PERFORMANCE & LEARNING
```
Tracks analytics → Learns from engagement → Adjusts strategy → 
Improves future content → Generates weekly reports
```

## 🚀 Getting Started

### Prerequisites

1. **Python 3.9+**
2. **Node.js 18+**
3. **PostgreSQL**
4. **Redis**
5. **FFmpeg** (for video processing)
6. **API Keys:**
   - OpenAI API Key (for GPT-4)
   - YouTube Data API v3
   - Instagram Graph API
   - Twitter API (optional)
   - ElevenLabs API (optional, for voice)
   - Google TTS API (optional, for voice)

### Installation

1. **Clone the repository:**
```bash
git clone <repository-url>
cd web
```

2. **Install Python dependencies:**
```bash
pip install -r requirements.txt
pip install -r agent/requirements-agent.txt
```

3. **Install Node.js dependencies:**
```bash
cd frontend
npm install
```

4. **Set up environment variables:**
```bash
cp env.example .env
# Edit .env with your API keys and configuration
```

**Required Environment Variables:**
```env
# AI Services
OPENAI_API_KEY=your_openai_key
STABLE_VIDEO_API_URL=http://localhost:7860  # Optional
ELEVENLABS_API_KEY=your_key  # Optional
GOOGLE_TTS_API_KEY=your_key  # Optional

# Platform APIs
YOUTUBE_API_KEY=your_youtube_key
YOUTUBE_OAUTH_TOKEN=your_oauth_token
INSTAGRAM_ACCESS_TOKEN=your_instagram_token
INSTAGRAM_ACCOUNT_ID=your_account_id
TWITTER_BEARER_TOKEN=your_twitter_token  # Optional

# Voice Engine
VOICE_ENGINE_URL=http://localhost:8000

# Database
DATABASE_URL=postgresql+asyncpg://user:password@localhost/social_media_manager
REDIS_URL=redis://localhost:6379/0

# Backend
BACKEND_API_URL=http://localhost:8000
```

5. **Initialize database:**
```bash
# Run migrations
alembic upgrade head
```

6. **Start services:**

**Windows (PowerShell):**
```powershell
# Option 1: Use startup scripts (Recommended)
.\scripts\start-backend.ps1    # Terminal 1
.\scripts\start-frontend.ps1   # Terminal 2

# Option 2: Manual commands
.\venv\Scripts\Activate.ps1
cd backend
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**Linux/Mac:**
```bash
# Terminal 1: Backend
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Terminal 2: Frontend
cd frontend
npm run dev

# Terminal 3: Agent Worker (optional, for background tasks)
cd agent
celery -A celery_app worker --loglevel=info
```

**Note:** On Windows, always use `python -m uvicorn` instead of just `uvicorn` to ensure it uses the virtual environment.

## 📖 Usage

### Starting Automation

1. **Via Dashboard:**
   - Navigate to `http://localhost:3000/automation`
   - Click "🚀 Start Automation"
   - Select number of days to plan (default: 7)
   - Monitor progress in real-time

2. **Via API:**
```bash
curl -X POST http://localhost:8000/agent/automation/start \
  -H "Content-Type: application/json" \
  -d '{"days": 7}'
```

3. **Via Python:**
```python
from agent.services.automation_orchestrator import AutomationOrchestrator

orchestrator = AutomationOrchestrator()
result = await orchestrator.start_automation(days=7)
```

### Monitoring

- **Dashboard:** `http://localhost:3000/automation`
- **API Status:** `GET http://localhost:8000/agent/automation/status`
- **Health Check:** `GET http://localhost:8000/health`

### Manual Override

You can manually trigger individual components:

```python
# Generate content for a specific trend
from agent.services.ai_content_brain import AIContentBrain

brain = AIContentBrain()
result = await brain.generate_content_for_trend(trend_data)

# Create a single video
from agent.services.ai_video_factory import AIVideoFactory

factory = AIVideoFactory()
video = await factory.create_complete_video(script)

# Publish content
from agent.services.smart_publisher import SmartPublisher

publisher = SmartPublisher()
result = await publisher.publish_content(video_data, platforms=["youtube", "instagram"])
```

## 🔧 Configuration

### Content Settings

Edit `agent/config/settings.py` to customize:
- Content categories
- Malayalam keywords
- Posting time preferences
- Quality thresholds

### Automation Settings

Configure automation behavior:
- `MAX_CONCURRENT_TASKS`: Number of parallel tasks (default: 3)
- `TIMEOUT_SECONDS`: Task timeout (default: 300)
- `MAX_RETRIES`: Retry attempts (default: 3)

## 📊 API Endpoints

### Automation Endpoints

- `POST /agent/automation/start` - Start automation cycle
- `POST /agent/automation/stop` - Stop automation
- `GET /agent/automation/status` - Get current status
- `POST /agent/automation/single-video` - Execute single video workflow

### Other Endpoints

- `GET /health` - Health check
- `GET /analytics/` - Get analytics data
- `POST /upload/video` - Upload video
- `POST /generate/caption` - Generate caption
- `POST /youtube/upload` - Upload to YouTube
- `POST /instagram/upload` - Upload to Instagram

## 🎯 Success Metrics

The system is designed to achieve:
- ✅ **100% automated content pipeline**
- ✅ **<30 minutes from idea to published video**
- ✅ **95%+ successful automation rate**
- ✅ **Continuous performance improvement**
- ✅ **Multi-platform consistency**

## 🔍 Troubleshooting

### Common Issues

1. **API Key Errors:**
   - Verify all API keys in `.env`
   - Check API quotas and limits

2. **Video Generation Fails:**
   - Ensure FFmpeg is installed: `ffmpeg -version`
   - Check Stable Video Diffusion API is running
   - Verify video storage (S3/MinIO) is accessible

3. **Voice Generation Fails:**
   - Check Voice Engine service is running
   - Verify TTS API keys are valid
   - Check network connectivity

4. **Publishing Fails:**
   - Verify platform API credentials
   - Check OAuth tokens are valid
   - Review platform API rate limits

### Debug Mode

Enable debug logging:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 📝 Development

### Adding New Features

1. **New Module:**
   - Create service in `agent/services/`
   - Add to orchestrator in `automation_orchestrator.py`
   - Create API routes in `backend/routes/`

2. **New Platform:**
   - Add platform manager in `smart_publisher.py`
   - Update trend detector in `ai_content_brain.py`
   - Add platform-specific logic

3. **New AI Model:**
   - Add model integration in respective service
   - Update configuration
   - Add fallback mechanisms

## 🚢 Deployment

### Docker Deployment

```bash
docker-compose up --build
```

### Kubernetes Deployment

See `infra/k8s/` for Kubernetes manifests.

### Production Checklist

- [ ] All API keys configured
- [ ] Database migrations run
- [ ] Redis cache configured
- [ ] Video storage (S3) configured
- [ ] Monitoring (Prometheus/Grafana) set up
- [ ] Backup systems configured
- [ ] Rate limiting configured
- [ ] Security best practices implemented

## 📚 Additional Resources

- **Backend API Docs:** `http://localhost:8000/docs`
- **Orchestrator README:** `orchestrator/README.md`
- **Agent README:** `agent/README.md`
- **Deployment Guide:** `DEPLOYMENT_CHECKLIST.md`

## 🤝 Contributing

1. Follow code formatting guidelines in `CODE_FORMATTING.md`
2. Write tests for new features
3. Update documentation
4. Submit pull requests

## 📄 License

MIT

---

**Built with ❤️ for autonomous social media management**

