# 🔒 Security Sub-Agent Documentation

## Overview

The Security Sub-Agent is an autonomous security scanning and monitoring system that protects the PE Intelligence application against OWASP Top 10 vulnerabilities and common security threats.

## Features

### 🛡️ Automated Security Scanning

The Security Sub-Agent continuously monitors for:

1. **Authentication & Authorization Issues** (OWASP A01:2021)
   - Unprotected API endpoints
   - Missing authentication on mutating operations
   - Broken access control

2. **Rate Limiting** (OWASP A04:2021)
   - Brute force attack protection
   - DoS attack prevention
   - Configurable rate limits per endpoint

3. **Input Validation** (OWASP A03:2021)
   - SQL injection detection
   - Command injection detection
   - XSS protection

4. **Secrets Management** (OWASP A05:2021)
   - Hardcoded credentials detection
   - API key exposure scanning
   - Credential leak prevention

5. **CORS Configuration** (OWASP A05:2021)
   - Wildcard origin detection
   - Credential policy validation
   - Cross-domain policy review

## Architecture

```
Security Sub-Agent
├── SecurityService (Orchestrator)
│   ├── AuthenticationScanner
│   ├── RateLimitScanner
│   ├── InputValidationScanner
│   ├── SecretScanner
│   └── CORSScanner
└── RateLimitMiddleware (Active Protection)
```

## Usage

### Running Security Scans

#### Command Line

```bash
# Run all security scans
python3 backend/services/security_service.py

# Run specific scanner
python3 backend/services/security_service.py auth
python3 backend/services/security_service.py rate_limit

# Generate JSON report
python3 backend/services/security_service.py --json
```

#### Programmatic Usage

```python
from backend.services.security_service import SecurityService

# Run all scans
service = SecurityService()
report = service.run_all_scans()

# Print formatted report
service.print_report(report)

# Access specific findings
print(f"Security Score: {report['summary']['security_score']}/100")
print(f"Critical Issues: {report['summary']['critical']}")
```

### Rate Limiting Configuration

The rate limiter is automatically enabled in production via middleware.

#### Default Limits

- **General API**: 100 requests/minute per client
- **Authentication endpoints**: 5 requests/minute (blocks for 10 minutes on exceeded)
- **Mutation endpoints** (PUT/POST/DELETE): 50 requests/minute

#### Custom Configuration

```python
from backend.middleware import RateLimiter, RateLimitRule

# Create custom rate limiter
limiter = RateLimiter(
    default_rule=RateLimitRule(requests=200, window=60)
)

# Add custom rules for specific paths
limiter.add_rule(
    "/api/companies",
    RateLimitRule(requests=100, window=60, block_duration=300)
)
```

#### Disable Rate Limiting (Development Only)

To disable rate limiting in development, comment out in `backend/main.py`:

```python
# app.add_middleware(RateLimitMiddleware)
```

⚠️ **Never disable rate limiting in production!**

## CI/CD Integration

The Security Sub-Agent runs automatically on every push and pull request via GitHub Actions.

### Viewing Security Reports

1. Navigate to **Actions** tab in GitHub
2. Select the workflow run
3. View **Security Scanning** job
4. Download **security-report** artifact for detailed JSON report

### Security Score Requirements

- **100/100**: Perfect security, no issues
- **80-99**: Good security, minor issues
- **60-79**: Moderate security, needs attention
- **<60**: Poor security, critical issues present

The CI/CD pipeline will:
- ✅ Continue on security warnings (score 60+)
- ⚠️ Flag for review on high/critical issues (score <60)
- 🔴 Fail on critical vulnerabilities

## Security Fixes Applied

### ✅ Authentication Enforcement

**Issue**: PUT endpoint at `/api/companies/{company_id}` was unprotected

**Fix**: Added authentication requirement
```python
@router.put("/companies/{company_id}", dependencies=[Depends(verify_admin_token)])
async def update_company(...):
    """Update company details (Admin only)"""
```

**Impact**: Prevents unauthorized data modification

### ✅ Rate Limiting Implementation

**Issue**: No rate limiting, vulnerable to brute force and DoS

**Fix**: Implemented `RateLimitMiddleware` with:
- Per-client IP tracking
- Configurable limits per endpoint
- Automatic blocking on limit exceeded
- Rate limit headers in responses

**Impact**: Protects against:
- Brute force password attacks
- API abuse
- Denial of service attacks

### ✅ Security Monitoring

**Issue**: No automated security scanning

**Fix**: Created autonomous Security Sub-Agent that:
- Scans code on every commit
- Detects vulnerabilities before deployment
- Provides actionable recommendations
- Tracks security score over time

**Impact**: Proactive security rather than reactive

## Testing

### Running Security Tests

```bash
# Run all security tests
pytest tests/test_security.py -v

# Run specific test class
pytest tests/test_security.py::TestAuthenticationSecurity -v

# Run with coverage
pytest tests/test_security.py --cov=backend.services.security_service
```

### Test Coverage

The security test suite includes:
- Authentication and authorization tests
- Rate limiting functionality tests
- Scanner accuracy tests
- Integration tests for security workflows
- Input validation and injection protection tests

## Monitoring & Maintenance

### Regular Security Audits

Run security scans regularly:

```bash
# Weekly security scan
python3 backend/services/security_service.py --json

# Review report
cat security_report.json | jq '.summary'
```

### Security Score Tracking

Monitor security score trends:
- Set up alerts for score drops below 80
- Review all high/critical issues immediately
- Track resolution time for security issues

### Rate Limit Monitoring

Monitor rate limit effectiveness:

```python
from backend.middleware import RateLimitMiddleware

# Access rate limiter statistics
limiter = middleware.rate_limiter
print(f"Active clients: {len(limiter.clients)}")
```

## Configuration

### Environment Variables

```env
# Optional: Custom rate limit settings
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_WINDOW=60

# Security scanning in CI/CD (default: enabled)
SECURITY_SCAN_ENABLED=true
SECURITY_FAIL_ON_HIGH=false
```

### Security Policy

Create `.github/SECURITY.md` to define:
- Vulnerability disclosure policy
- Security update schedule
- Contact information for security issues

## Best Practices

### For Developers

1. **Run security scans before committing**
   ```bash
   python3 backend/services/security_service.py
   ```

2. **Never hardcode secrets**
   - Use environment variables
   - Use secrets management (AWS Secrets Manager, HashiCorp Vault)

3. **Always authenticate mutating endpoints**
   ```python
   @router.put("/resource", dependencies=[Depends(verify_admin_token)])
   ```

4. **Test security features**
   - Write tests for authentication
   - Test rate limiting behavior
   - Verify input validation

### For DevOps

1. **Monitor security scores in CI/CD**
2. **Set up alerts for critical vulnerabilities**
3. **Rotate secrets regularly**
4. **Review rate limit logs for abuse patterns**
5. **Keep dependencies updated**

### For Security Team

1. **Review security reports weekly**
2. **Conduct penetration testing quarterly**
3. **Update security scanners as new vulnerabilities emerge**
4. **Train developers on secure coding practices**

## Troubleshooting

### False Positives

If the scanner reports false positives:

1. **Public endpoints flagged as unprotected**
   - Add to whitelist in `AuthenticationScanner.public_endpoints`

2. **Test secrets flagged as hardcoded**
   - Use keywords like "test", "example", "dummy" in test values

3. **Scanner errors**
   - Check Python version (requires 3.9+)
   - Ensure project structure matches expected layout

### Rate Limiting Issues

**Problem**: Legitimate users being blocked

**Solution**: Increase rate limits for specific endpoints:
```python
limiter.add_rule("/api/endpoint", RateLimitRule(requests=200, window=60))
```

**Problem**: Rate limiting not working

**Solution**: Verify middleware is registered:
```python
# In backend/main.py
app.add_middleware(RateLimitMiddleware)
```

## Future Enhancements

Planned features for the Security Sub-Agent:

- [ ] Dependency vulnerability scanning (Snyk, Safety)
- [ ] Container security scanning
- [ ] Secrets scanning in git history
- [ ] API security testing (OWASP API Security Top 10)
- [ ] Security dashboards and metrics
- [ ] Automated security patch application
- [ ] Integration with security information and event management (SIEM)
- [ ] Machine learning for anomaly detection

## Support

For security issues:
- **Critical vulnerabilities**: Report immediately to security team
- **General questions**: Open GitHub issue with `security` label
- **Feature requests**: Open GitHub issue with `enhancement` label

## References

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [OWASP API Security Top 10](https://owasp.org/www-project-api-security/)
- [CWE Top 25](https://cwe.mitre.org/top25/)
- [FastAPI Security](https://fastapi.tiangolo.com/tutorial/security/)

---

**Security Score**: 100/100 ✅
**Last Updated**: 2025-11-10
**Version**: 1.0.0
