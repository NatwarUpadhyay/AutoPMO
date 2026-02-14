# Contributing Guide
## How to Contribute to AutoPMO

---

## Welcome! 🎉

Thank you for considering contributing to AutoPMO! This guide will help you get started.

---

## Code of Conduct

Please be respectful, inclusive, and professional. We don't tolerate harassment or discrimination of any kind.

---

## Ways to Contribute

1. **Report Bugs**: Found a bug? Open an issue
2. **Suggest Features**: Have ideas? We'd love to hear them
3. **Fix Issues**: Check our [good first issue](https://github.com/NatwarUpadhyay/AutoPMO/labels/good%20first%20issue) label
4. **Improve Documentation**: Typos, clarifications, examples
5. **Write Tests**: Increase code coverage
6. **Review PRs**: Help review community contributions

---

## Getting Started

### 1. Fork and Clone

```bash
# Fork the repo on GitHub, then:
git clone https://github.com/YOUR_USERNAME/AutoPMO.git
cd AutoPMO
```

### 2. Set Up Development Environment

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Install pre-commit hooks
pre-commit install
```

### 3. Create a Branch

```bash
git checkout -b feature/your-feature-name
# or
git checkout -b fix/issue-number-description
```

---

## Development Workflow

### 1. Make Changes

```bash
# Edit files
vim src/agents/orchestrator.py

# Run tests locally
pytest tests/

# Run linter
flake8 src/
black src/
mypy src/
```

### 2. Commit Changes

```bash
# Stage changes
git add .

# Commit with conventional commit message
git commit -m "feat: add risk prediction caching"
```

**Commit Message Format**:
```
<type>: <description>

[optional body]

[optional footer]
```

**Types**:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting)
- `refactor`: Code refactoring
- `test`: Adding tests
- `chore`: Maintenance tasks

### 3. Push and Create PR

```bash
# Push to your fork
git push origin feature/your-feature-name

# Open PR on GitHub
# Fill out the PR template with:
# - Description of changes
# - Related issue number
# - Testing performed
# - Screenshots (if UI changes)
```

---

## Code Standards

### Python Code Style

- Follow PEP 8
- Use type hints
- Max line length: 100 characters
- Use docstrings (Google style)

**Example**:
```python
from typing import List, Optional

class ProjectService:
    """Service for managing projects.
    
    Attributes:
        db: Database connection instance
        cache: Redis cache instance
    """
    
    def __init__(self, db: Database, cache: RedisCache):
        self.db = db
        self.cache = cache
    
    async def create_project(
        self,
        name: str,
        budget: float,
        owner_id: str
    ) -> Project:
        """Create a new project.
        
        Args:
            name: Project name
            budget: Project budget in USD
            owner_id: User ID of project owner
            
        Returns:
            Created project instance
            
        Raises:
            ValidationError: If inputs are invalid
            DatabaseError: If database operation fails
        """
        # Validate inputs
        if budget <= 0:
            raise ValidationError("Budget must be positive")
        
        # Create project
        project = await self.db.projects.create({
            "name": name,
            "budget": budget,
            "owner_id": owner_id
        })
        
        # Cache project
        await self.cache.set(f"project:{project.id}", project)
        
        return project
```

### Testing

- Write unit tests for all new code
- Aim for >80% code coverage
- Use pytest fixtures
- Mock external dependencies

**Example**:
```python
import pytest
from unittest.mock import AsyncMock, Mock

@pytest.fixture
def mock_database():
    db = AsyncMock()
    db.projects.create.return_value = {
        "id": "proj_123",
        "name": "Test Project"
    }
    return db

@pytest.mark.asyncio
async def test_create_project(mock_database):
    service = ProjectService(db=mock_database, cache=Mock())
    
    project = await service.create_project(
        name="Test Project",
        budget=100000,
        owner_id="user_456"
    )
    
    assert project["name"] == "Test Project"
    mock_database.projects.create.assert_called_once()
```

---

## Documentation

### Docstrings

Use Google-style docstrings for all public functions, classes, and modules.

### README Updates

If adding a new feature, update the main README.md with:
- Feature description
- Usage example
- Configuration options

### API Documentation

Update API docs in `docs/api-reference.md` if changing endpoints.

---

## Pull Request Checklist

Before submitting your PR, ensure:

- [ ] Code follows project style guidelines
- [ ] All tests pass (`pytest tests/`)
- [ ] Linting passes (`flake8`, `black`, `mypy`)
- [ ] New code has tests
- [ ] Documentation is updated
- [ ] Commit messages follow conventional commits
- [ ] PR description is clear and complete
- [ ] Screenshots attached (if UI changes)

---

## Review Process

1. **Automated Checks**: CI/CD runs tests and linters
2. **Code Review**: Maintainer reviews code quality
3. **Testing**: Reviewer tests changes locally
4. **Approval**: Once approved, maintainer merges
5. **Deployment**: Changes deployed in next release

**Review Timeline**: We aim to review PRs within 48 hours.

---

## Issue Guidelines

### Reporting Bugs

Use the bug report template and include:
- Clear description of the issue
- Steps to reproduce
- Expected vs actual behavior
- Environment details (OS, Python version, etc.)
- Error logs/screenshots

### Requesting Features

Use the feature request template and include:
- Problem you're trying to solve
- Proposed solution
- Alternative solutions considered
- Willingness to contribute

---

## Community

- **Discussions**: https://github.com/NatwarUpadhyay/AutoPMO/discussions
- **Slack**: Coming soon
- **Twitter**: @AutoPMO

---

## License

By contributing, you agree that your contributions will be licensed under the same license as the project (MIT License).

---

## Questions?

- Open a [Discussion](https://github.com/NatwarUpadhyay/AutoPMO/discussions)
- Email: contributors@autopmo.com

---

**Thank you for contributing to AutoPMO!** 🚀
