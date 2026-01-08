# Security Policy

## Supported Versions

The following versions of Cirkelline System are currently receiving security updates:

| Version | Supported          |
| ------- | ------------------ |
| 1.3.x   | :white_check_mark: |
| 1.2.x   | :white_check_mark: |
| < 1.2   | :x:                |

## Reporting a Vulnerability

We take the security of Cirkelline System seriously. If you believe you have found a security vulnerability, please report it to us as described below.

### How to Report

**Please do NOT report security vulnerabilities through public GitHub issues.**

Instead, please report them via email to: **security@cirkelline.com**

Include the following information in your report:
- Type of vulnerability (e.g., SQL injection, XSS, authentication bypass)
- Full paths of source file(s) related to the vulnerability
- Location of the affected source code (tag/branch/commit or direct URL)
- Step-by-step instructions to reproduce the issue
- Proof-of-concept or exploit code (if possible)
- Impact of the vulnerability

### Response Timeline

| Action | Timeline |
|--------|----------|
| Initial acknowledgment | Within 48 hours |
| Preliminary assessment | Within 7 days |
| Status update | Every 7 days until resolved |
| Fix deployment | Based on severity (see below) |

### Severity-Based Response

| Severity | Example | Fix Timeline |
|----------|---------|--------------|
| **Critical** | Remote code execution, auth bypass | 24-48 hours |
| **High** | Data exposure, privilege escalation | 7 days |
| **Medium** | Limited data exposure, DoS | 30 days |
| **Low** | Minor information disclosure | 90 days |

## Security Measures

### Authentication & Authorization
- JWT tokens with 30-minute expiration for access tokens
- Refresh tokens with 7-day expiration
- Role-based access control (RBAC)
- Session management with secure logout

### Data Protection
- All passwords hashed using bcrypt with appropriate work factor
- Sensitive data encrypted at rest (AES-256-GCM)
- TLS 1.3 for all data in transit
- Database credentials not stored in version control

### Input Validation
- All user inputs validated and sanitized
- SQL injection prevention via SQLAlchemy ORM
- XSS prevention through proper output encoding
- CSRF protection on state-changing operations

### Dependency Management
- Dependencies pinned to exact versions
- Regular security audits using `safety` and `bandit`
- Automated vulnerability scanning in CI/CD pipeline
- Dependabot enabled for security updates

### Infrastructure
- Secrets managed through environment variables
- Production credentials stored in AWS Secrets Manager
- Regular security audits and penetration testing
- Logging and monitoring for suspicious activities

## Security Best Practices for Contributors

1. **Never commit secrets** - Use environment variables
2. **Validate all inputs** - Trust nothing from users
3. **Use parameterized queries** - Prevent SQL injection
4. **Keep dependencies updated** - Check for vulnerabilities
5. **Follow least privilege** - Minimal permissions required
6. **Log security events** - But never log sensitive data

## Acknowledgments

We gratefully acknowledge security researchers who help keep Cirkelline System secure. With your permission, we will publicly acknowledge your contribution.

## Contact

For security-related inquiries that are not vulnerability reports, please contact:

- **Email:** security@cirkelline.com
- **PGP Key:** Available upon request

---

*This security policy is compliant with the OpenSSF Project Security Baseline.*
