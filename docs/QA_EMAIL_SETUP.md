# QA Email Reports Setup Guide

Your QA agent can now send beautiful HTML email reports with detailed coverage metrics!

## 📧 What You Get

- **Professional HTML emails** with color-coded scores
- **Complete metrics table** showing coverage, tests, gaps
- **Attached JSON report** for detailed analysis
- **Mobile-friendly** design
- **Automatic scheduling** via GitHub Actions

## 🚀 Quick Start (3 Steps)

### Step 1: Get Gmail App Password

1. Go to [Google Account Security](https://myaccount.google.com/security)
2. Enable **2-Step Verification** (required)
3. Go to [App Passwords](https://myaccount.google.com/apppasswords)
4. Generate password for "Mail"
5. Copy the 16-character password (save it!)

### Step 2: Add GitHub Secrets

1. Go to your repository on GitHub
2. **Settings** → **Secrets and variables** → **Actions**
3. Click **New repository secret**
4. Add these secrets:

| Secret Name | Value | Example |
|-------------|-------|---------|
| `EMAIL_USERNAME` | Your Gmail address | `yourname@gmail.com` |
| `EMAIL_PASSWORD` | Gmail App Password from Step 1 | `abcd efgh ijkl mnop` |
| `QA_EMAIL_RECIPIENT` | Where to send reports | `yourname@gmail.com` |

### Step 3: Update GitHub Actions Workflow

The workflow is already configured! It will automatically send emails when:
- You push to `main` or `develop` branches
- Someone creates a pull request

---

## 📝 Usage

### Command Line (Local Testing)

```bash
# Set environment variables
export EMAIL_USERNAME="your@gmail.com"
export EMAIL_PASSWORD="your-app-password"

# Run QA and send email
python backend/services/qa_service.py --email recipient@example.com

# Combine with JSON export
python backend/services/qa_service.py --json --email recipient@example.com
```

### In Python Code

```python
from backend.services.qa_service import QAService

# Create service
qa = QAService()

# Generate report
report = qa.run_qa_report()

# Send email
success = qa.send_email_report(
    report=report,
    to_email="your@email.com",
    subject_prefix="🧪 Daily QA Report"
)

if success:
    print("✅ Email sent!")
else:
    print("❌ Email failed")
```

### In GitHub Actions (Automatic)

Already configured in `.github/workflows/tests.yml`!

When enabled, you'll receive emails automatically when:
- Tests run on push to main/develop
- Pull requests are created
- QA quality score changes

---

## ⚙️ Configuration

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `EMAIL_USERNAME` | ✅ Yes | - | SMTP username (Gmail address) |
| `EMAIL_PASSWORD` | ✅ Yes | - | SMTP password (App Password) |
| `QA_EMAIL_RECIPIENT` | For CI | - | Email address to receive reports |
| `SMTP_SERVER` | No | `smtp.gmail.com` | SMTP server address |
| `SMTP_PORT` | No | `587` | SMTP server port |
| `EMAIL_FROM` | No | Same as username | Sender email address |

### Using Other Email Providers

#### SendGrid
```bash
export SMTP_SERVER="smtp.sendgrid.net"
export SMTP_PORT="587"
export EMAIL_USERNAME="apikey"
export EMAIL_PASSWORD="your-sendgrid-api-key"
```

#### Office 365
```bash
export SMTP_SERVER="smtp.office365.com"
export SMTP_PORT="587"
export EMAIL_USERNAME="your@company.com"
export EMAIL_PASSWORD="your-password"
```

#### AWS SES
```bash
export SMTP_SERVER="email-smtp.us-east-1.amazonaws.com"
export SMTP_PORT="587"
export EMAIL_USERNAME="your-smtp-username"
export EMAIL_PASSWORD="your-smtp-password"
```

---

## 📊 Email Content

Your emails will include:

### Header
- **Quality Score** (0-100) with color coding
- **Status Badge** (Excellent/Good/Fair/Needs Improvement)
- **Timestamp**

### Metrics Table
- **Code Coverage** percentage
- **Lines Covered** (covered/total)
- **Tests Passing** (passed/total)
- **Tests Failing** count
- **Tests Skipped** count
- **Missing Test Files** count

### Coverage Gaps
- **Critical** issues (🔴)
- **High** priority (🟠)
- **Medium** priority (🟡)
- **Low** priority (🟢)
- **Total gaps**

### Details
- **Top 10 missing test files**
- **Top 10 coverage gaps** with file names and reasons

### Attachment
- **JSON report** with complete data for further analysis

---

## 🎨 Email Preview

```
┌─────────────────────────────────────┐
│   🧪 QA Analysis Report             │
│                                     │
│         65/100                      │
│         [Good]                      │
│                                     │
│   Generated: Nov 10, 2025 3:45 PM  │
├─────────────────────────────────────┤
│   📊 Quality Metrics                │
│                                     │
│   📈 Code Coverage      65.0%       │
│   📏 Lines Covered      1,501/2,316 │
│   ✅ Tests Passing      350/350     │
│   ❌ Tests Failing      0           │
│   ⏭️ Tests Skipped      0           │
│   📝 Missing Test Files 3           │
├─────────────────────────────────────┤
│   ⚠️ Coverage Gaps                  │
│                                     │
│   🔴 Critical           0           │
│   🟠 High               5           │
│   🟡 Medium             10          │
│   🟢 Low                3           │
│   Total Gaps            18          │
├─────────────────────────────────────┤
│   📝 Files Missing Tests            │
│   • qa_service.py                   │
│   • analytics_service.py            │
│   • security_service.py             │
├─────────────────────────────────────┤
│   📋 Sample Coverage Gaps           │
│   🟠 get_recommendations            │
│      in recommendation_service.py   │
│      Function not covered by tests  │
│                                     │
│   🟡 calculate_score                │
│      in scoring_service.py          │
│      Function not covered by tests  │
└─────────────────────────────────────┘

Attachment: qa_report_20251110_154500.json
```

---

## 🔧 Troubleshooting

### "SMTP Authentication failed"
- ✅ Check you're using **App Password**, not your regular Gmail password
- ✅ Ensure 2-Step Verification is enabled in Google Account
- ✅ Verify `EMAIL_USERNAME` and `EMAIL_PASSWORD` secrets are set correctly

### "Connection refused" or "Timeout"
- ✅ Check firewall/network allows outbound connections on port 587
- ✅ Try port 465 with SSL: `export SMTP_PORT=465`
- ✅ Verify SMTP server address is correct

### "Sender address rejected"
- ✅ Make sure `EMAIL_FROM` matches your Gmail address
- ✅ Some providers require verified sender addresses

### Email not received
- ✅ Check spam/junk folder
- ✅ Wait a few minutes (email can be delayed)
- ✅ Verify recipient email address is correct
- ✅ Check GitHub Actions logs for errors

---

## 🔒 Security Best Practices

1. **Never commit credentials** to git
   - Use environment variables
   - Use GitHub Secrets for CI/CD
   - Add `.env` to `.gitignore`

2. **Use App Passwords** for Gmail
   - Never use your main Google password
   - App Passwords can be revoked individually

3. **Limit Secret Access**
   - Only add secrets to repositories that need them
   - Regularly rotate passwords
   - Remove unused secrets

4. **Monitor Usage**
   - Check GitHub Actions logs regularly
   - Review email sending logs
   - Set up alerts for failed authentications

---

## 📅 Scheduling Options

### Daily Reports
Add a scheduled workflow:

```yaml
# .github/workflows/daily-qa.yml
name: Daily QA Report

on:
  schedule:
    - cron: '0 9 * * 1-5'  # 9 AM weekdays

jobs:
  qa-report:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.9'
      - name: Run QA and Send Email
        env:
          EMAIL_USERNAME: ${{ secrets.EMAIL_USERNAME }}
          EMAIL_PASSWORD: ${{ secrets.EMAIL_PASSWORD }}
        run: |
          pip install -r requirements.txt
          python backend/services/qa_service.py --email ${{ secrets.QA_EMAIL_RECIPIENT }}
```

### Weekly Summary
Change cron to: `'0 9 * * 1'` (9 AM every Monday)

### On Deployment
Add to your deployment workflow:

```yaml
- name: Send QA Report
  if: success()
  env:
    EMAIL_USERNAME: ${{ secrets.EMAIL_USERNAME }}
    EMAIL_PASSWORD: ${{ secrets.EMAIL_PASSWORD }}
  run: |
    python backend/services/qa_service.py --json --email ${{ secrets.QA_EMAIL_RECIPIENT }}
```

---

## 💡 Tips & Tricks

### Multiple Recipients
Send to multiple people:

```python
recipients = ["dev1@company.com", "dev2@company.com", "qa@company.com"]
for email in recipients:
    qa.send_email_report(report, email)
```

### Custom Subject Line
```python
qa.send_email_report(
    report,
    "team@company.com",
    subject_prefix="🎯 Sprint QA Report"
)
```

### Conditional Sending
Only send if quality score is low:

```python
report = qa.run_qa_report()
if report['quality_score'] < 70:
    qa.send_email_report(report, "alerts@company.com")
```

### Integration with Slack
Use email-to-Slack feature:
1. Get your Slack email address (Workspace → Add apps → Email)
2. Forward QA reports to that address
3. Reports appear in designated channel

---

## 📞 Support

- **Documentation**: See this file
- **Issues**: [GitHub Issues](https://github.com/your-repo/issues)
- **Email**: Check GitHub Actions logs for detailed error messages

---

## ✨ What's Next

Potential enhancements:
- [ ] PDF report generation
- [ ] Charts and graphs
- [ ] Trend analysis over time
- [ ] Slack/Discord direct integration
- [ ] Teams/Webex support
- [ ] Custom email templates
- [ ] Report archiving
- [ ] Automatic PR comments with QA results

---

**Last Updated**: November 2025
**Version**: 1.0.0
