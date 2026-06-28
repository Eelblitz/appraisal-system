# Security Policy

## Supported Versions

|Version|Supported       |
|-------|----------------|
|1.0.x  |✅ Active support|

-----

## Reporting a Vulnerability

If you discover a security vulnerability in this system, please report it
responsibly. **Do not create a public GitHub issue for security vulnerabilities.**

### How to Report

Contact Code With Iman directly:

- **GitHub:** [@Eelblitz](https://github.com/Eelblitz)
- **Subject Line:** `[SECURITY] Brief description of issue`

### What to Include

1. Description of the vulnerability
1. Steps to reproduce it
1. Potential impact
1. Suggested fix (if you have one)

### Response Timeline

- **Acknowledgement:** Within 48 hours
- **Assessment:** Within 7 days
- **Fix:** Within 30 days depending on severity

-----

## Security Architecture

### Data Isolation

Every database query is scoped to the user’s organisation. Cross-organisation
data access is prevented at the application layer.

### Authentication

- Django’s built-in authentication with PBKDF2 password hashing
- Session-based authentication
- CSRF protection on all forms

### Payment Security

- Card details are never processed or stored by this application
- All payments go through Paystack’s PCI-compliant infrastructure
- Every payment is verified via Paystack’s server-side API before access is granted

### Environment Variables

All secrets (SECRET_KEY, database credentials, Paystack keys) are stored in
environment variables and never committed to version control.