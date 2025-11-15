# InboxAI - Autonomous Development Mission

## MISSION
Build and ship a Lindy AI-like email automation platform with AI-powered email triaging, response drafting, sender research, workflow automation, and credit-based billing system.

## PROJECT GOAL
Create a production-ready email automation SaaS platform that automatically triages emails (Urgent/FYI/Archive), drafts responses in the user's voice, researches senders, schedules follow-ups, and provides a no-code workflow builder with 100+ integrations.

## TECH STACK & TARGETS
- **Backend**: Python 3.10+, Flask 3.0+
- **Database**: Supabase (PostgreSQL)
- **AI/ML**: OpenAI GPT-4, LangChain for workflow orchestration
- **Frontend**: HTML5, TailwindCSS, Alpine.js
- **Icons**: Google Material Icons (no emojis)
- **Email**: Gmail API, IMAP/SMTP support
- **Queue**: Celery + Redis for background tasks
- **Deployment**: Render.com
- **Testing**: pytest, pytest-cov
- **CI/CD**: GitHub Actions

## REPO/ENV
- **Repo**: /Users/murali/1backup/agentsdr/AgentSDR_3
- **Package Manager**: pip (requirements.txt)
- **OS**: macOS (Darwin 24.6.0)
- **Python**: 3.14
- **Virtual Env**: ./venv

## OPERATING RULES
1. **No confirmations required** - Make sensible assumptions and proceed
2. **No emojis** - Use Google Material Icons only
3. **Version control** - Auto-increment version (1.0, 1.1, 1.2...) on each git push
4. **Footer** - Include version, date, and repo name in fine print
5. **Testing** - Provide local port URL after each task completion
6. **Incremental delivery** - Work in verifiable increments with tests
7. **Production-grade** - Security, error handling, logging, monitoring
8. **Documentation** - Clear README, setup scripts, deployment guides

## DELIVERABLES CHECKLIST
- [ ] Working code with meaningful commits
- [ ] Setup scripts: `make dev`, `make build`, `make test`
- [ ] Comprehensive test suite (>80% coverage)
- [ ] .env.example with all required variables
- [ ] README.md with quickstart, deployment, FAQ
- [ ] Error handling with user-friendly messages
- [ ] Lint/format config: `make lint`, `make format`
- [ ] CHANGELOG.md tracking all features
- [ ] Version footer on all pages
- [ ] Material Icons implementation
- [ ] Local testing URLs provided

## QUALITY BARS
- Zero lint errors
- No failing tests
- No unhandled exceptions
- No secrets in code
- Input validation on all endpoints
- Rate limiting on API routes
- Documentation matches actual implementation
- 100% environment variable coverage

## BLOCKED HANDLING
- Use mocks for missing API keys
- Isolate external dependencies behind interfaces
- Choose stable alternatives if dependencies fail
- Document all assumptions and workarounds

## FINAL HANDOFF
- Complete repo tree
- Exact run/deploy commands
- Local and production URLs
- Admin test credentials
- Operations notes (backups, logs, rotation)
- Performance metrics and monitoring setup

---
**Version**: 1.0
**Last Updated**: 2025-11-16
**Repository**: chatgptnotes/AgentSDR_3
