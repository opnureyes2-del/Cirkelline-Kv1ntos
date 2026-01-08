# Crowdin Integration - Quick Start Guide

**For:** Cirkelline System
**Date:** 2025-12-09
**Setup Time:** 2-3 hours

---

## Prerequisites

- [ ] GitHub account with admin access to cirkelline-system repo
- [ ] Crowdin account (Team plan or higher recommended)
- [ ] Node.js 18+ installed (for validation script)

---

## Step 1: Crowdin Account Setup (30 min)

### 1.1 Create Crowdin Project

1. Go to [crowdin.com](https://crowdin.com) and sign up
2. Click "Create Project"
3. **Project Name:** `cirkelline-system`
4. **Source Language:** English
5. **Target Languages:** Select:
   - Danish (da)
   - Swedish (sv)
   - German (de)
   - Arabic (ar)

### 1.2 Get API Credentials

1. Go to Account Settings → API
2. Click "New Token"
3. **Name:** `GitHub Actions`
4. **Scopes:** Select all (or at minimum: `project`, `glossary`, `tm`)
5. Copy the token (save it securely - you'll need it in Step 3)
6. Note your Project ID (visible in project URL: `crowdin.com/project/YOUR_PROJECT_ID`)

---

## Step 2: Local Repository Setup (15 min)

### 2.1 Files Already Created

The following files have been created in your repository:

```
cirkelline-system/
├── crowdin.yml                                    # Crowdin config
├── .github/workflows/
│   ├── crowdin-sync.yml                          # Main sync workflow
│   └── crowdin-webhook.yml                       # Webhook handler
├── scripts/
│   └── validate-translations.js                  # Validation script
└── docs/
    ├── CROWDIN-INTEGRATION-BEST-PRACTICES.md    # Full guide
    └── CROWDIN-QUICKSTART.md                     # This file
```

### 2.2 Verify Files

```bash
cd /home/rasmus/Desktop/projects/cirkelline-system

# Check files exist
ls -la crowdin.yml
ls -la .github/workflows/crowdin-*.yml
ls -la scripts/validate-translations.js
```

---

## Step 3: GitHub Secrets Setup (10 min)

### 3.1 Add Repository Secrets

1. Go to GitHub repository: `github.com/your-username/cirkelline-system`
2. Navigate to: **Settings → Secrets and variables → Actions**
3. Click "New repository secret"

Add these two secrets:

**Secret 1:**
- **Name:** `CROWDIN_PROJECT_ID`
- **Value:** Your project ID from Step 1.2 (numeric, e.g., `123456`)

**Secret 2:**
- **Name:** `CROWDIN_PERSONAL_TOKEN`
- **Value:** Your personal access token from Step 1.2 (e.g., `abc123...`)

---

## Step 4: Initial Upload to Crowdin (15 min)

### 4.1 Install Crowdin CLI (Optional but Recommended)

```bash
# Install globally
npm install -g @crowdin/cli

# Verify installation
crowdin --version
```

### 4.2 Test Configuration

```bash
# Set environment variables (temporary)
export CROWDIN_PROJECT_ID="your-project-id"
export CROWDIN_PERSONAL_TOKEN="your-token"

# Test connection
crowdin list project

# Upload source files
crowdin upload sources

# Check Crowdin dashboard - files should appear
```

### 4.3 Alternative: Use GitHub Actions

If you prefer not to install CLI locally:

```bash
# Commit and push (this triggers upload)
git add crowdin.yml .github/workflows/
git commit -m "feat: add Crowdin integration"
git push origin main

# Go to GitHub → Actions tab
# Watch "Crowdin Sync" workflow run
```

---

## Step 5: Configure Crowdin Project (30 min)

### 5.1 Translation Memory (TM)

1. In Crowdin, go to **Resources → Translation Memories**
2. Click "Create TM"
3. **Name:** `cirkelline-shared-tm`
4. **Languages:** da, en, sv, de, ar
5. Click "Save"
6. Go back to your project → Settings → Translation Memories
7. Click "Assign" and select `cirkelline-shared-tm`
8. Set **Priority:** 5

### 5.2 Glossary

1. Go to **Resources → Glossaries**
2. Click "Create Glossary"
3. **Name:** `cirkelline-terminology`
4. Click "Import" and upload this CSV:

```csv
Term,Part of Speech,Definition,Danish,Swedish,German,Arabic
Agent,noun,AI specialist,Agent,Agent,Agent,وكيل
Session,noun,Chat conversation,Session,Session,Sitzung,جلسة
Document,noun,User uploaded file,Dokument,Dokument,Dokument,مستند
Knowledge Base,noun,Private storage,Videnbase,Kunskapsbas,Wissensbasis,قاعدة المعرفة
```

Or create terms manually:
- Click "Add Term"
- **Term:** Agent
- **Part of Speech:** noun
- **Definition:** AI specialist that performs specific tasks
- Add translations for each language

### 5.3 QA Checks

1. Go to **Settings → QA Checks**
2. Enable these checks:
   - ✅ Variables mismatch
   - ✅ Empty translation
   - ✅ Tags mismatch
   - ✅ Spaces mismatch
   - ✅ Punctuation mismatch
   - ✅ Numbers mismatch
   - ✅ Outdated translation
3. Click "Save"

### 5.4 Workflow Settings

1. Go to **Settings → Workflow**
2. **Translation approval:** Enable (recommended for production)
3. **Duplicate strings:** Show across files
4. Click "Save"

---

## Step 6: Test Workflow (30 min)

### 6.1 Make a Translation

1. In Crowdin Editor, select **Danish (da)**
2. Click on a string (e.g., `common.loading`)
3. Enter translation: "Indlæser..."
4. Click "Save"
5. Approve translation (click checkmark icon)

### 6.2 Test Automated Download

#### Option A: Manual Trigger

1. Go to GitHub → Actions
2. Select "Crowdin Sync" workflow
3. Click "Run workflow"
4. Select branch: `main`
5. Click "Run workflow"
6. Wait for completion (~1-2 min)
7. Check for new PR: `i18n: Update translations from Crowdin`

#### Option B: Wait for Scheduled Run

- Workflow runs daily at 03:00 UTC
- Check tomorrow morning for automatic PR

### 6.3 Review and Merge PR

1. Go to Pull Requests tab
2. Open the `i18n: Update translations` PR
3. Review changes:
   - Check `locales/da/messages.json` updated
   - Verify placeholder consistency
4. Run validation:

```bash
# Pull the branch locally
git fetch origin l10n_main
git checkout l10n_main

# Run validation
node scripts/validate-translations.js

# If validation passes:
# ✓ All translations valid!
```

5. Merge PR to main
6. Translations now live!

---

## Step 7: Setup Webhooks (Optional - 20 min)

For real-time updates when translators complete work:

### 7.1 Create GitHub Personal Access Token

1. GitHub → Settings → Developer settings → Personal access tokens
2. Click "Generate new token (classic)"
3. **Name:** `Crowdin Webhook`
4. **Scopes:** Select `repo`
5. Click "Generate token"
6. Copy token (save securely)

### 7.2 Configure Crowdin Webhook

1. Crowdin Project → Settings → Integrations → Webhooks
2. Click "Add Webhook"
3. **Name:** `GitHub Auto-PR`
4. **URL:** `https://api.github.com/repos/YOUR_USERNAME/cirkelline-system/dispatches`
5. **Method:** POST
6. **Events:** Select:
   - ✅ File is 100% translated
   - ✅ Translation updated
7. **Payload:**

```json
{
  "event_type": "crowdin_translation_updated",
  "client_payload": {
    "project": "cirkelline-system",
    "language": "%language%",
    "file": "%file_name%",
    "branch": "main"
  }
}
```

8. **Headers:**

```
Authorization: token YOUR_GITHUB_PAT
Accept: application/vnd.github.v3+json
Content-Type: application/json
```

9. Click "Test Request" to verify
10. Click "Save"

---

## Step 8: Validation & Testing (15 min)

### 8.1 Validate Existing Translations

```bash
# Run validation script
node scripts/validate-translations.js
```

**Expected output:**
```
Validating Translation Files
==================================================

Source language: English
Total source strings: 168

==================================================
Validating DA
==================================================
Total strings: 168/168
✓ All translations present
✓ All placeholders valid

DA Summary: 168 translations checked

... (similar for sv, de, ar)

==================================================
Validation Summary
==================================================
Errors:   0
Warnings: 0

✓ All translations valid!
Ready for deployment.
```

### 8.2 Test Arabic (RTL)

```bash
# Start dev server
cd cirkelline-ui
npm run dev

# Open in browser with Arabic
# http://localhost:3000?lang=ar
```

**Check:**
- [ ] Text displays right-to-left
- [ ] UI elements mirrored correctly
- [ ] Numbers display as Western numerals (123, not ١٢٣)
- [ ] No bold or italic formatting

---

## Daily Workflow

### For Developers

**When adding new strings:**

1. Update `locales/en/messages.json`
2. Commit and push to `main`
3. GitHub Action uploads to Crowdin automatically
4. Notify translators (or wait for them to see)

**When translations ready:**

1. Daily workflow downloads at 03:00 UTC
2. Review PR created automatically
3. Run validation: `node scripts/validate-translations.js`
4. Merge PR
5. Done!

### For Translators

1. Log into Crowdin
2. Select language (da, sv, de, or ar)
3. Translate strings
4. Use glossary terms (underlined)
5. Verify placeholders (e.g., `{field}`)
6. Approve when done
7. System auto-creates PR in GitHub

---

## Troubleshooting

### Issue: "Upload failed - 401 Unauthorized"

**Solution:**
- Check `CROWDIN_PROJECT_ID` is correct (numeric)
- Verify `CROWDIN_PERSONAL_TOKEN` is valid
- Ensure token has `project` scope

### Issue: "No files uploaded"

**Solution:**
- Check `crowdin.yml` source path: `/locales/en/**/*.json`
- Verify English files exist: `ls locales/en/messages.json`
- Run `crowdin upload sources --verbose` for details

### Issue: "Placeholders broken in translation"

**Solution:**
- Enable QA check: Variables mismatch
- Review strings with red highlights in Crowdin
- Fix placeholders to match source

### Issue: "Arabic displays left-to-right"

**Solution:**
- Check HTML has `dir="rtl"` for Arabic
- Verify CSS uses logical properties (`margin-inline-start`)
- Test with: `http://localhost:3000?lang=ar`

### Issue: "PR not created"

**Solution:**
- Check GitHub Actions logs for errors
- Verify workflow permissions: `contents: write`, `pull-requests: write`
- Ensure `GITHUB_TOKEN` has sufficient permissions

---

## Next Steps

1. **Review full documentation:**
   - Read `/docs/CROWDIN-INTEGRATION-BEST-PRACTICES.md` for detailed info

2. **Setup other repos:**
   - Apply same process to `lib-admin-main`
   - Apply same process to `Cosmic-Library-main`
   - Share TM across all three projects

3. **Optimize:**
   - Setup Machine Translation (DeepL Pro for da/sv/de)
   - Add screenshots for context
   - Create comprehensive style guide

4. **Scale:**
   - Invite translators
   - Setup approval workflow
   - Monitor translation progress

---

## Costs

**Crowdin:**
- Team plan: ~$50/month (~$600/year)
- Free plan available (limited features)

**Machine Translation (optional):**
- DeepL Pro: ~€30/year for your volume
- Google Translate: ~$10/year for Arabic

**Total estimated:** ~$650/year

---

## Resources

- **Full Documentation:** `/docs/CROWDIN-INTEGRATION-BEST-PRACTICES.md`
- **Crowdin Docs:** https://support.crowdin.com/
- **GitHub Action:** https://github.com/crowdin/github-action
- **Validation Script:** `/scripts/validate-translations.js`

---

## Support

**Issues with setup?**

1. Check GitHub Actions logs
2. Review Crowdin activity log
3. Run validation script for details
4. Check troubleshooting section above

**Need help?**

- Crowdin Support: support@crowdin.com
- GitHub Discussions: Open issue in repo

---

**Setup completed?**

- [ ] Crowdin project created
- [ ] API credentials added to GitHub secrets
- [ ] Initial upload successful
- [ ] TM and Glossary configured
- [ ] QA checks enabled
- [ ] Test translation and PR workflow successful
- [ ] Validation script runs without errors

**If all checked: You're ready to go!** 🎉

Start translating and let automation handle the rest.
