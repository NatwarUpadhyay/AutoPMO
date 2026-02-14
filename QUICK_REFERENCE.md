# AutoPMO Quick Reference Card

## 🎯 One-Page Overview

### What is AutoPMO?
AI-powered Project Management Office for cloud migrations
- 5 AI agents working together
- 4 ML models making predictions
- Enterprise security built-in
- Reduces planning from 6 weeks → 6 hours

### Tech Stack
```
Platform:    OpenShift 4.14+
AI/ML:       OpenShift AI + LangChain
LLM:         Mistral 7B
Language:    Python 3.11+
Frontend:    React + TypeScript
Database:    PostgreSQL + Redis
Security:    Keycloak + Vault + SELinux
```

### Quick Commands

```bash
# Installation
git clone https://github.com/YOUR_USERNAME/autopmo.git
cd autopmo
make install

# Local Demo
./skills.sh demo
# → Dashboard: http://localhost:3000
# → Login: demo-pm / AutoPMO2024!

# Development
make dev              # Setup dev environment
make test             # Run tests
make lint             # Check code
make format           # Format code

# Deployment
./skills.sh cluster   # Deploy to OpenShift
./skills.sh reset     # Clean up

# Documentation
make docs             # Build docs
make docs-serve       # Serve docs locally
```

### File Structure
```
autopmo/
├── agents/           # AI agents (Python)
├── models/           # ML models
├── api/              # FastAPI backend
├── dashboard/        # React frontend
├── openshift/        # K8s manifests
├── security/         # Policies & configs
├── docs/             # Documentation
└── skills.sh         # One-command deployment
```

### LinkedIn Post
**File:** `docs/LINKEDIN_POST.md`
**Best Time:** Tuesday/Thursday, 9-10 AM
**Hook:** "Cloud migrations fail 70% of the time..."
**Hashtags:** #AI #OpenShift #CloudMigration #DevOps

### Key Features
✅ 5 specialized AI agents (Orchestrator, Planning, Risk, Infrastructure, Communications)
✅ 4 ML models (Risk Predictor, Velocity Forecaster, Sentiment Analyzer, Dependency Mapper)
✅ PM framework (WBS, RACI, Risk Register, EVM)
✅ Enterprise security (SSO, SELinux, Network Policies)
✅ One-command deployment
✅ Open source (Apache 2.0)

### Red Hat Certifications Used
1. ✅ AI/ML on OpenShift AI → ML model deployment
2. ✅ OpenShift Developer II → Cloud-native apps
3. ✅ Identity Management → SSO & RBAC
4. ✅ Security → SELinux & hardening

### API Endpoints
```
POST   /api/v1/projects           # Create project
GET    /api/v1/projects/{id}      # Get project
POST   /api/v1/agents/execute     # Execute agent
GET    /api/v1/models/predict     # ML prediction
POST   /api/v1/auth/login         # Login
```

### Example Usage
```python
from agents import create_orchestrator, PlanningAgent

# Create agents
planning = PlanningAgent()
orchestrator = create_orchestrator(planning_agent=planning)

# Process request
result = await orchestrator.process_request(
    "Create migration plan for e-commerce app"
)

print(result['response'])
```

### Performance Targets
- API Response: < 200ms (p95)
- Agent Decision: < 5s (p95)
- ML Inference: < 100ms (p95)
- Concurrent Users: 100+

### Security Features
- OAuth2/OIDC authentication (Keycloak)
- Role-based access control (5 roles)
- Secrets management (Vault)
- Network policies (deny-all default)
- SELinux container isolation
- mTLS service mesh (Istio)
- Full audit trail

### Deployment Options
1. **Local Demo** (Docker Compose)
   - Quick start in 5 minutes
   - No cluster required
   - Great for development

2. **OpenShift Cluster** (Production)
   - Full feature set
   - HA and scaling
   - Enterprise security

3. **CRC** (CodeReady Containers)
   - Local OpenShift
   - Test full stack
   - Limited resources

### Support
- 📚 Docs: `/docs` directory
- 🐛 Issues: GitHub Issues
- 💬 Discussions: GitHub Discussions
- 📧 Email: your.email@example.com

### Contributing
1. Fork repository
2. Create feature branch
3. Write tests
4. Submit PR
5. See CONTRIBUTING.md

### License
Apache License 2.0 - See LICENSE file

### Quick Troubleshooting

**Problem:** Agents not responding
**Fix:** Check LLM service: `curl http://localhost:8000/v1/models`

**Problem:** Database connection failed
**Fix:** Check PostgreSQL: `docker ps | grep postgres`

**Problem:** Skills.sh fails
**Fix:** Check prerequisites: `make help`

**Problem:** Tests failing
**Fix:** Install deps: `make install`

### Next Steps
1. ✅ Push to GitHub
2. ✅ Post on LinkedIn
3. ✅ Add demo video
4. ✅ Write Medium article
5. ✅ Engage with community

---

**Remember:**
- 🎯 Focus on business value (6 weeks → 6 hours)
- 🤖 Emphasize agentic AI (not just chatbots)
- 🔐 Highlight enterprise security
- 📊 Show PM + AI combination
- 🌟 Make it personal (your learning journey)

**You've got this!** 🚀
