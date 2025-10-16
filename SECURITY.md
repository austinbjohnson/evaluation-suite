# Security Policy

## Reporting a Vulnerability

If you discover a security vulnerability in this project, please report it responsibly.

**Please email:** security@[yourdomain].com or create a private security advisory on GitHub

**Please include:**
- Description of the vulnerability
- Steps to reproduce the issue
- Potential impact assessment
- Suggested fix (if you have one)

**Response timeline:**
- We will acknowledge receipt within 48 hours
- We will provide an initial assessment within 7 days
- We will work with you to understand and resolve the issue

## Scope

### In Scope
The following are considered in scope for security reports:

- **API Key Exposure:** Hardcoded or accidentally committed API keys
- **Injection Vulnerabilities:** Code injection, command injection, or prompt injection in eval specs
- **Unauthorized Access:** Bypass of authentication or authorization controls
- **Data Leakage:** Exposure of sensitive data in logs, errors, or outputs
- **Denial of Service:** Resource exhaustion or infinite loops via malicious inputs
- **Dependency Vulnerabilities:** Known CVEs in project dependencies

### Out of Scope
The following are NOT considered security vulnerabilities:

- Issues in third-party LLM providers (OpenAI, Anthropic, etc.)
- Theoretical attacks without proof of concept
- Social engineering attacks
- Physical security issues
- Issues requiring physical access to systems
- Rate limiting bypasses (unless causing actual harm)

## Security Best Practices

### For Contributors

1. **Never commit secrets:**
   - Use `.env` files for all API keys and credentials
   - Add all sensitive files to `.gitignore`
   - Use environment variables via `os.getenv()`
   - Review diffs carefully before committing

2. **Validate inputs:**
   - Sanitize file paths to prevent directory traversal
   - Validate model names against known providers
   - Check YAML specs for malicious content
   - Limit file sizes for fixtures

3. **Handle errors safely:**
   - Don't expose internal paths in error messages
   - Don't leak partial API keys
   - Log security-relevant events
   - Use generic error messages for users

4. **Keep dependencies updated:**
   - Run `pip-audit` regularly: `pip-audit --requirement requirements.txt`
   - Update vulnerable packages promptly
   - Review dependency changes in PRs

### For Users

1. **Protect your credentials:**
   - Never share your `.env` file
   - Rotate API keys if exposed
   - Use separate keys for testing vs production
   - Enable billing alerts on provider accounts

2. **Review eval results:**
   - Don't share results containing sensitive data
   - Check that fixtures don't include real PII
   - Be cautious when uploading to public dashboards

3. **Run in isolated environments:**
   - Use virtual environments (`venv/`)
   - Don't run evals with elevated privileges
   - Review eval code before executing

## Vulnerability Disclosure Timeline

We follow responsible disclosure practices:

1. **Day 0:** Vulnerability reported
2. **Day 2:** Acknowledgment sent to reporter
3. **Day 7:** Initial assessment and timeline provided
4. **Day 30:** Fix developed and tested (target)
5. **Day 45:** Fix released and public disclosure (after users have time to update)

If the vulnerability is critical and actively exploited, we will expedite the timeline.

## Security Updates

Security updates are released as:
- **Patch versions** for security fixes (e.g., 1.0.1)
- **Minor versions** for non-breaking security improvements (e.g., 1.1.0)

Subscribe to repository notifications to stay informed about security releases.

## Attribution

We believe in giving credit where it's due. Security researchers who responsibly disclose vulnerabilities will be acknowledged in:
- The security advisory
- The CHANGELOG
- This SECURITY.md file (with permission)

Thank you for helping keep this project secure! 🔒

