# InboxAI - AI-Powered Email Automation Platform

An intelligent email automation platform inspired by Lindy AI. InboxAI automatically triages your emails, drafts responses in your voice, researches senders, and schedules smart follow-ups. Save 10+ hours per week with AI-powered email intelligence.

## Features

- **Smart Email Triaging**: Automatically classify emails as Urgent, FYI, or Archive
- **AI Response Drafting**: Generate personalized email responses matching your writing style
- **Sender Research**: Deep research on email senders using web scraping and enrichment APIs
- **Smart Follow-ups**: Intelligent follow-up scheduling with Celery background tasks
- **Credit-Based Billing**: Flexible usage-based pricing (Free, Pro, Business tiers)
- **Multi-tenant Architecture**: Complete data isolation between organizations
- **Gmail Integration**: Seamless OAuth 2.0 integration with Gmail API
- **No-Code Workflow Builder**: Create custom email automation workflows
- **Modern UI**: Clean, responsive design with TailwindCSS and Google Material Icons

## Tech Stack

- **Backend**: Flask 3.0, Python 3.14
- **Database**: Supabase (PostgreSQL + GoTrue Auth)
- **AI**: OpenAI GPT-4 for classification and drafting
- **Background Tasks**: Celery + Redis
- **Email**: Gmail API with OAuth 2.0
- **Frontend**: Jinja2 + TailwindCSS + Alpine.js
- **Security**: Row Level Security (RLS), CSRF protection
- **Testing**: Pytest with >80% coverage target

## Quick Start

### 1. Clone and Setup

```bash
git clone https://github.com/chatgptnotes/AgentSDR_3.git
cd AgentSDR_3
make setup
```

This will:
- Create a Python virtual environment
- Copy `.env.example` to `.env`
- Install all dependencies
- Create necessary directories

### 2. Configure Environment

Update `.env` with your credentials:

```env
# Supabase Configuration
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key

# Flask Configuration
FLASK_SECRET_KEY=your-super-secret-key
PORT=5001

# OpenAI Configuration
OPENAI_API_KEY=sk-your-openai-api-key
OPENAI_MODEL=gpt-4
OPENAI_TEMPERATURE=0.7
OPENAI_MAX_TOKENS=2000

# Redis Configuration
REDIS_URL=redis://localhost:6379/0

# Celery Configuration
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# Gmail API Configuration
GMAIL_CREDENTIALS_FILE=credentials/gmail_credentials.json
GMAIL_TOKEN_FILE=credentials/gmail_token.json

# Email Automation Configuration
EMAIL_FETCH_INTERVAL_MINUTES=5
EMAIL_CLASSIFICATION_ENABLED=true
EMAIL_AUTO_DRAFT_ENABLED=false

# Credit System Configuration
FREE_TIER_MONTHLY_CREDITS=400
PRO_TIER_MONTHLY_CREDITS=5000
BUSINESS_TIER_MONTHLY_CREDITS=30000
```

### 3. Setup Supabase Database

1. Create a new Supabase project at https://supabase.com
2. Run the migration in the SQL editor:

```bash
# Copy contents of supabase/migrations/001_email_automation.sql
# Paste and execute in Supabase SQL editor
```

### 4. Install Redis

```bash
# macOS
brew install redis

# Ubuntu/Debian
sudo apt-get install redis-server

# Start Redis
redis-server
```

### 5. Start All Services

```bash
# Option 1: Start everything at once
make all

# Option 2: Start services individually
make redis        # Start Redis server
make dev          # Start Flask app (http://localhost:5001)
make celery       # Start Celery worker + beat
```

Visit **http://localhost:5001** to see the application!

## Configuration

### Environment Variables

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `SUPABASE_URL` | Supabase project URL | Yes | - |
| `SUPABASE_ANON_KEY` | Supabase anonymous key | Yes | - |
| `SUPABASE_SERVICE_ROLE_KEY` | Supabase service role key | Yes | - |
| `FLASK_SECRET_KEY` | Flask secret key for sessions | Yes | - |
| `OPENAI_API_KEY` | OpenAI API key for GPT-4 | Yes | - |
| `OPENAI_MODEL` | OpenAI model to use | No | `gpt-4` |
| `OPENAI_TEMPERATURE` | AI creativity (0.0-1.0) | No | `0.7` |
| `OPENAI_MAX_TOKENS` | Max tokens per response | No | `2000` |
| `REDIS_URL` | Redis connection URL | Yes | `redis://localhost:6379/0` |
| `CELERY_BROKER_URL` | Celery broker URL | Yes | `redis://localhost:6379/0` |
| `PORT` | Flask app port | No | `5001` |
| `EMAIL_FETCH_INTERVAL_MINUTES` | Email fetch interval | No | `5` |
| `FREE_TIER_MONTHLY_CREDITS` | Free tier credits | No | `400` |
| `PRO_TIER_MONTHLY_CREDITS` | Pro tier credits | No | `5000` |
| `BUSINESS_TIER_MONTHLY_CREDITS` | Business tier credits | No | `30000` |

### Credit Costs

| Action | Credits | Description |
|--------|---------|-------------|
| Email Classification | 1 | AI-powered Urgent/FYI/Archive classification |
| Short Email Draft | 3 | Response draft (< 200 words) |
| Long Email Draft | 7 | Response draft (> 200 words) |
| Basic Sender Research | 2 | Company info, social profiles |
| Deep Sender Research | 5 | Detailed profile with enrichment APIs |
| Workflow Execution | 2 | Per workflow run |

### Subscription Tiers

| Tier | Monthly Credits | Price | Best For |
|------|----------------|-------|----------|
| **Free** | 400 | $0 | Personal use, testing |
| **Pro** | 5,000 | $49.99 | Professionals, small teams |
| **Business** | 30,000 | $299.99 | Large teams, enterprises |

## Usage

### Email Classification

```python
from agentsdr.email.ai_service import AIService

ai_service = AIService()

classification = ai_service.classify_email(
    subject="Urgent: Q4 Revenue Report Needed",
    body="Can you send the Q4 revenue report by EOD?",
    from_email="boss@company.com",
    user_id="user-123"
)

print(classification)
# {
#     "category": "urgent",
#     "confidence_score": 0.95,
#     "reasoning": "Time-sensitive request from manager",
#     "priority_score": 90,
#     "keywords": ["urgent", "revenue report", "EOD"],
#     "sentiment": "neutral",
#     "action_required": True,
#     "estimated_response_time": "24 hours"
# }
```

### Draft Email Response

```python
from agentsdr.email.ai_service import AIService

ai_service = AIService()

draft = ai_service.draft_response(
    subject="Re: Partnership Opportunity",
    body="I'd love to discuss a potential partnership...",
    from_email="partner@startup.com",
    user_id="user-123",
    tone="professional",
    key_points=["Express interest", "Suggest meeting time"]
)

print(draft["draft_body"])
# "Hi [Name],
#  Thank you for reaching out about the partnership opportunity...
#  I'd be happy to discuss this further. Would next Tuesday at 2pm work?
#  Best regards, [Your name]"
```

### Research Email Sender

```python
from agentsdr.email.research_service import ResearchService

research_service = ResearchService()

research = research_service.research_sender(
    email_address="john@acmecorp.com",
    deep_research=True
)

print(research)
# {
#     "email_address": "john@acmecorp.com",
#     "full_name": "John Smith",
#     "company": "Acme Corporation",
#     "job_title": "VP of Sales",
#     "linkedin_url": "https://linkedin.com/in/johnsmith",
#     "bio": "15 years in enterprise sales...",
#     "location": "San Francisco, CA"
# }
```

### Create Automated Workflow

```python
from agentsdr.email.tasks import fetch_user_emails, classify_email

# Emails are automatically fetched every 5 minutes
# and classified using Celery background tasks

# You can also trigger manually:
fetch_user_emails.delay(
    user_id="user-123",
    org_id="org-456",
    credentials={"access_token": "..."}
)
```

## Architecture

### Project Structure

```
AgentSDR_3/
├── agentsdr/                    # Main application package
│   ├── __init__.py             # Flask app factory with version injection
│   ├── auth/                   # Authentication & user management
│   ├── core/                   # Core utilities & Supabase client
│   ├── email/                  # Email automation module
│   │   ├── models.py           # Pydantic models for email entities
│   │   ├── gmail_service.py    # Gmail API integration
│   │   ├── ai_service.py       # OpenAI GPT-4 integration
│   │   ├── research_service.py # Sender research & enrichment
│   │   └── tasks.py            # Celery background tasks
│   ├── orgs/                   # Organization management
│   ├── admin/                  # Super admin functionality
│   ├── utils/                  # Utilities
│   │   └── version.py          # Version management
│   ├── templates/              # Jinja2 templates
│   │   ├── layout.html         # Base layout with version footer
│   │   └── main/
│   │       └── index.html      # SEO-optimized landing page
│   └── static/                 # CSS, JS, assets
├── supabase/                   # Database schema & migrations
│   └── migrations/
│       └── 001_email_automation.sql  # Email automation schema
├── scripts/                    # Utility scripts
│   ├── increment_version.py    # Version increment script
│   ├── install_git_hooks.sh    # Git hooks installer
│   └── seed.py                 # Database seeding
├── tests/                      # Test suite
├── version.json                # Version tracking file
├── Makefile                    # Development commands
├── requirements.txt            # Python dependencies
└── app.py                      # Application entry point
```

### Database Schema

**Core Tables:**

- `emails` - Email messages with metadata
- `email_classifications` - AI classification results
- `email_drafts` - AI-generated response drafts
- `sender_research` - Sender profile research data
- `follow_up_schedules` - Smart follow-up scheduling
- `user_credits` - Credit balance tracking
- `credit_transactions` - Credit usage history
- `workflow_automations` - No-code workflow definitions
- `workflow_execution_logs` - Workflow execution history

**Row Level Security (RLS):**

All tables have RLS policies ensuring:
- Users can only access data from their organizations
- Super admins can access all data
- Credit deductions are atomic and secure
- Email data is fully isolated per organization

### Background Tasks

Celery tasks run periodically:

- **fetch_all_user_emails** - Every 5 minutes
- **process_follow_ups** - Every hour
- **reset_monthly_credits** - First day of each month

## API Documentation

### Email Classification API

**Endpoint:** `POST /api/emails/classify`

**Request:**
```json
{
  "email_id": "email-123",
  "user_id": "user-456"
}
```

**Response:**
```json
{
  "category": "urgent",
  "confidence_score": 0.95,
  "reasoning": "Time-sensitive request from important contact",
  "priority_score": 90,
  "keywords": ["urgent", "deadline", "report"],
  "sentiment": "neutral",
  "action_required": true,
  "estimated_response_time": "24 hours",
  "credits_used": 1
}
```

### Draft Response API

**Endpoint:** `POST /api/emails/draft`

**Request:**
```json
{
  "email_id": "email-123",
  "user_id": "user-456",
  "tone": "professional",
  "key_points": ["Express gratitude", "Propose meeting"]
}
```

**Response:**
```json
{
  "draft_subject": "Re: Partnership Opportunity",
  "draft_body": "Hi John,\n\nThank you for reaching out...",
  "tone": "professional",
  "style_match_score": 0.85,
  "credits_used": 3
}
```

### Sender Research API

**Endpoint:** `POST /api/senders/research`

**Request:**
```json
{
  "email_address": "john@company.com",
  "deep_research": true
}
```

**Response:**
```json
{
  "email_address": "john@company.com",
  "full_name": "John Smith",
  "company": "Acme Corp",
  "job_title": "VP Sales",
  "linkedin_url": "https://linkedin.com/in/johnsmith",
  "twitter_url": "https://twitter.com/johnsmith",
  "bio": "15 years in enterprise sales...",
  "location": "San Francisco, CA",
  "credits_used": 5
}
```

## Deployment

### Render.com Deployment

1. **Create Web Service**
   - Go to https://render.com and create a new Web Service
   - Connect your GitHub repository

2. **Configure Build Settings**
   ```bash
   # Build Command
   pip install -r requirements.txt && chmod +x tailwindcss-macos-arm64

   # Start Command
   gunicorn app:app --bind 0.0.0.0:$PORT
   ```

3. **Add Environment Variables**
   - Copy all variables from `.env.example`
   - Update with production values
   - Ensure `REDIS_URL` points to a production Redis instance

4. **Create Redis Service**
   - Create a new Redis instance on Render
   - Copy the internal Redis URL to `REDIS_URL` environment variable

5. **Create Worker Service**
   ```bash
   # Start Command for Celery Worker
   celery -A agentsdr.celery_config.celery_app worker --beat --loglevel=info
   ```

6. **Deploy**
   - Push to GitHub
   - Render will automatically deploy

### Environment Variables for Production

Update these in Render dashboard:

```env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-production-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-production-service-key
FLASK_SECRET_KEY=your-super-secret-production-key
OPENAI_API_KEY=sk-your-production-key
REDIS_URL=redis://red-xxxxx:6379
PORT=5001
BASE_URL=https://your-app.onrender.com
```

### Health Check Endpoint

Render will automatically use `GET /` for health checks.

## Testing

### Run All Tests

```bash
# Run tests with coverage
make test

# Run specific test file
./venv/bin/pytest tests/test_email_classification.py -v

# Run with coverage report
./venv/bin/pytest tests/ -v --cov=agentsdr --cov-report=html
```

### Test Coverage Goals

- Overall coverage: >80%
- Core modules: >90%
- Email automation: >85%
- API endpoints: >80%

### Writing Tests

```python
# tests/test_email_classification.py
import pytest
from agentsdr.email.ai_service import AIService

def test_classify_urgent_email():
    ai_service = AIService()

    result = ai_service.classify_email(
        subject="URGENT: Server Down",
        body="Production server is down, need immediate help",
        from_email="ops@company.com",
        user_id="test-user"
    )

    assert result["category"] == "urgent"
    assert result["confidence_score"] > 0.8
    assert result["action_required"] == True
```

## Makefile Commands

### Development Commands

```bash
make setup           # Initial project setup
make dev             # Run Flask development server
make install         # Install Python dependencies
make clean           # Clean up generated files
```

### Service Management

```bash
make all             # Start all services (Redis + Flask + Celery)
make redis           # Start Redis server
make redis-stop      # Stop Redis server
make redis-status    # Check Redis status
make worker          # Start Celery worker
make beat            # Start Celery beat scheduler
make celery          # Start Celery worker + beat
make flower          # Start Flower monitoring (http://localhost:5555)
make stop-all        # Stop all background services
```

### Testing & Quality

```bash
make test            # Run tests with coverage
make lint            # Run linting (black, ruff)
make format          # Format code
```

### Version Management

```bash
make version         # Show current version
make version-increment  # Increment version
make version-bump    # Alias for version-increment
```

### Database

```bash
make seed            # Seed database with demo data
```

### Deployment

```bash
make deploy-check    # Check deployment readiness
make build           # Build production assets
```

## Security Features

- **Authentication**: Supabase GoTrue with secure session management
- **Authorization**: Role-based access control (Super Admin, Org Admin, Member)
- **Data Isolation**: Row Level Security (RLS) for multi-tenant data
- **CSRF Protection**: Flask-WTF CSRF tokens
- **Secure Cookies**: HTTP-only, secure, same-site cookies
- **Credit Security**: Atomic credit deductions with transaction logging
- **API Key Security**: Environment variables, never committed to git
- **Gmail OAuth**: Secure OAuth 2.0 flow with token refresh
- **Rate Limiting**: Protection against abuse

## Version Management

InboxAI uses an auto-incrementing version system:

- **Version Format**: `MAJOR.MINOR` (e.g., 1.0, 1.1, 2.0)
- **Auto-Increment**: Version automatically increments on `git push`
- **Version Display**: Footer shows version, date, and repository
- **Version File**: `version.json` tracks current version

### Manual Version Increment

```bash
# Increment version manually
make version-increment

# Show current version
make version
```

### Install Git Hooks

```bash
# Install pre-push hook for auto-increment
bash scripts/install_git_hooks.sh
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Add tests for new functionality
5. Run linting: `make lint`
6. Run tests: `make test`
7. Commit changes (`git commit -m 'Add amazing feature'`)
8. Push to branch (`git push origin feature/amazing-feature`)
9. Open a Pull Request

### Code Style

- **Python**: Follow PEP 8, use Black for formatting
- **Line Length**: 88 characters (Black default)
- **Imports**: Sort with isort
- **Type Hints**: Use type hints for all functions
- **Docstrings**: Google-style docstrings
- **Comments**: Explain why, not what

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support and questions:

- **GitHub Issues**: https://github.com/chatgptnotes/AgentSDR_3/issues
- **Documentation**: Check this README and code comments
- **Email**: support@inboxai.com

## Roadmap

- [x] Email classification (Urgent/FYI/Archive)
- [x] AI response drafting with tone matching
- [x] Sender research and enrichment
- [x] Smart follow-up scheduling
- [x] Credit-based billing system
- [x] Multi-tenant architecture
- [x] Gmail integration
- [ ] No-code workflow builder UI
- [ ] Microsoft Outlook integration
- [ ] Mobile app (iOS/Android)
- [ ] Advanced analytics dashboard
- [ ] Team collaboration features
- [ ] Slack/Teams notifications
- [ ] Custom AI training on user's emails
- [ ] Multi-language support
- [ ] API webhooks
- [ ] Zapier/Make.com integration

## Acknowledgments

- Inspired by [Lindy AI](https://www.lindy.ai)
- Built with Flask, Supabase, OpenAI GPT-4, Celery
- UI powered by TailwindCSS and Google Material Icons

---

**InboxAI** - Save 10+ hours per week with AI-powered email automation

Version: 1.3 | Repository: https://github.com/chatgptnotes/AgentSDR_3
