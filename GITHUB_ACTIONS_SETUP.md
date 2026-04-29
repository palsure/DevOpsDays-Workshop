# GitHub Actions Setup Guide

This guide walks through every secret and repository variable required to run the CI/CD pipelines in this project end-to-end.  
All values live in **Settings → Secrets and variables → Actions** on your GitHub repository page.

---

## Quick-start checklist

```
Repository → Settings → Secrets and variables → Actions
├── Secrets tab  →  "New repository secret"   (16 secrets)
└── Variables tab →  "New repository variable" (13 variables)
```

---

## 1. Repository Secrets

Secrets are encrypted. GitHub never displays them after creation. Use the **Secrets** tab.

### Slack

| Secret | Description | How to obtain |
|---|---|---|
| `SLACK_BOT_TOKEN` | OAuth token for the Slack bot that posts threaded build notifications | Create a Slack app at [api.slack.com/apps](https://api.slack.com/apps), add scopes `chat:write`, `chat:write.public`, `reactions:write` → **Install to workspace** → copy *Bot User OAuth Token* (`xoxb-…`) |
| `SLACK_CHANNEL_ID` | ID of the channel that receives pipeline notifications | Open the channel in Slack → right-click the channel name → *Copy link* — the last segment (e.g. `C01AB2CD3EF`) is the ID |

### Firebase App Distribution

| Secret | Description | How to obtain |
|---|---|---|
| `FIREBASE_TOKEN` | CI service token for Firebase CLI commands | Run `firebase login:ci` locally; copy the printed token |
| `FIREBASE_APP_ID_ANDROID` | Numeric Firebase Android app ID | Firebase console → Project → Project settings → Your apps → Android app → *App ID* (e.g. `1:123456789:android:abc123`) |
| `FIREBASE_APP_ID_IOS` | Numeric Firebase iOS app ID | Same location, iOS app row |
| `FIREBASE_INTERNAL_TESTERS` | Comma-separated email list for internal (pre-release) builds | List the emails of your internal QA testers |
| `FIREBASE_PUBLIC_TESTERS` | Comma-separated email list for public release builds | List the emails of your external / beta testers |
| `FIREBASE_TESTERS` | Alias list used by the release workflow (may duplicate the above) | Same as `FIREBASE_INTERNAL_TESTERS` unless you have a unified list |
| `FIREBASE_PREVIEW_URL` | Base URL of the Firebase Hosting preview channel | Firebase console → Hosting → Preview channels → copy URL (used as secret when it contains auth info) |

### LambdaTest (cloud device lab)

| Secret | Description | How to obtain |
|---|---|---|
| `LT_ACCESS_KEY` | LambdaTest automation access key | [LambdaTest dashboard](https://app.lambdatest.com/settings/profile) → *Access Key* |

### New Relic (observability)

| Secret | Description | How to obtain |
|---|---|---|
| `NEW_RELIC_USER_API_KEY` | Personal or automation API key for NR API calls | New Relic UI → API keys → *Create a key* → type *User* |
| `NEW_RELIC_ACCOUNT_ID` | New Relic account number | New Relic UI → left sidebar footer, or *Account settings* |
| `NEW_RELIC_APM_GUID` | Entity GUID of the APM application | New Relic UI → APM → your app → *Metadata* → Entity GUID |
| `NEW_RELIC_REGION` | Data center region (`US` or `EU`) | Matches the base URL you use (`api.newrelic.com` = US, `api.eu.newrelic.com` = EU) |
| `NEW_RELIC_SLACK_DESTINATION_ID` | ID of the Slack notification destination configured in New Relic | New Relic UI → Alerts → Destinations → your Slack destination → copy ID from the URL |

### GitHub (automatic)

| Secret | Description |
|---|---|
| `GITHUB_TOKEN` | Automatically injected by GitHub Actions — **do not add manually**. Used for creating releases, deploying GitHub Pages, and reading PR metadata. |

---

## 2. Repository Variables

Variables are **not** encrypted and are visible in workflow logs. Use the **Variables** tab.

### API / deployment

| Variable | Example value | Description |
|---|---|---|
| `API_LIVE_URL` | `https://api.example.com` | Base URL of the production API, used by E2E and smoke tests that run against live infrastructure |

### Firebase Hosting

| Variable | Example value | Description |
|---|---|---|
| `FIREBASE_PROJECT_ID` | `my-project-12345` | Firebase project ID (the same one used in `.firebaserc`) |
| `FIREBASE_CHANNEL_ID` | `pr-preview` | Hosting channel name for PR preview deployments |
| `FIREBASE_PREVIEW_URL` | `https://my-project-12345.web.app` | Base URL of the hosting preview (non-sensitive version) |
| `FIREBASE_INTERNAL_GROUPS` | `qa-team` | Firebase App Distribution group name for internal testers |
| `FIREBASE_PUBLIC_GROUPS` | `beta-users` | Firebase App Distribution group name for public beta testers |
| `FIREBASE_INTERNAL_TESTERS` | `qa@example.com` | Tester emails for internal builds (non-sensitive duplicate) |
| `FIREBASE_PUBLIC_TESTERS` | `beta@example.com` | Tester emails for public builds (non-sensitive duplicate) |

### LambdaTest (cloud device lab)

| Variable | Example value | Description |
|---|---|---|
| `LT_USERNAME` | `john.doe` | LambdaTest username. **When this variable is set**, the Android workflow automatically routes BAT and Smoke tests to a real LambdaTest device instead of the local emulator. Leave empty to use the emulator. |
| `LT_DEVICE_ANDROID` | `Pixel 6 Pro-13` | Device + OS version string for LambdaTest (format: `<Model>-<API level>`). Falls back to `Pixel 6 Pro-13` when not set. |
| `LT_REGION` | `us` | LambdaTest data center region (`us`, `eu`, `apac`). Falls back to `us`. |

### Feature flags / circuit breakers

| Variable | Value | Effect |
|---|---|---|
| `NO_DEVICE_LAB` | `true` | Skips all device lab steps in every workflow. Set this when no lab is available (e.g. a budget cut or outage). |
| `SKIP_BAT` | `true` | Skips Build Acceptance Tests specifically. Unit-test gate still applies. Useful when the device lab is temporarily degraded. |

---

## 3. Where each value is consumed

```
Workflow                         Secrets / Variables used
-------------------------------- -------------------------------------------------------
stream-qoe-app-api.yml           SLACK_BOT_TOKEN, SLACK_CHANNEL_ID
stream-qoe-app-web.yml           SLACK_BOT_TOKEN, SLACK_CHANNEL_ID
                                 FIREBASE_TOKEN, FIREBASE_PROJECT_ID, FIREBASE_CHANNEL_ID,
                                 FIREBASE_PREVIEW_URL (var), API_LIVE_URL
stream-qoe-app-android.yml       SLACK_BOT_TOKEN, SLACK_CHANNEL_ID
                                 LT_ACCESS_KEY, LT_USERNAME (var), LT_DEVICE_ANDROID (var),
                                 LT_REGION (var), NO_DEVICE_LAB (var), SKIP_BAT (var)
stream-qoe-app-ios.yml           SLACK_BOT_TOKEN, SLACK_CHANNEL_ID
                                 FIREBASE_TOKEN, FIREBASE_APP_ID_IOS,
                                 FIREBASE_INTERNAL_TESTERS, FIREBASE_PUBLIC_TESTERS
stream-qoe-app-release.yml       SLACK_BOT_TOKEN, SLACK_CHANNEL_ID
                                 FIREBASE_TOKEN, FIREBASE_APP_ID_ANDROID, FIREBASE_APP_ID_IOS,
                                 FIREBASE_INTERNAL_TESTERS, FIREBASE_PUBLIC_TESTERS,
                                 FIREBASE_INTERNAL_GROUPS (var), FIREBASE_PUBLIC_GROUPS (var),
                                 LT_ACCESS_KEY, LT_USERNAME (var), LT_DEVICE_ANDROID (var),
                                 LT_REGION (var), SKIP_BAT (var)
stream-qoe-app-validation.yml    SLACK_BOT_TOKEN, SLACK_CHANNEL_ID, API_LIVE_URL (var)
stream-qoe-app-pr-e2e.yml        SLACK_BOT_TOKEN, SLACK_CHANNEL_ID
                                 FIREBASE_TOKEN, FIREBASE_PROJECT_ID, FIREBASE_CHANNEL_ID (var),
                                 FIREBASE_PREVIEW_URL (secret + var)
stream-qoe-app-newrelic.yml      NEW_RELIC_USER_API_KEY, NEW_RELIC_ACCOUNT_ID,
                                 NEW_RELIC_APM_GUID, NEW_RELIC_REGION,
                                 NEW_RELIC_SLACK_DESTINATION_ID
shared-notify-build-started.yml  SLACK_BOT_TOKEN, SLACK_CHANNEL_ID
```

---

## 4. Setting secrets and variables via GitHub CLI

If you prefer the CLI over the UI:

```bash
# Authenticate first
gh auth login

# Add a secret (value is read from stdin to avoid shell history)
gh secret set SLACK_BOT_TOKEN --body "xoxb-…"
gh secret set FIREBASE_TOKEN  --body "$(firebase login:ci --no-localhost)"

# Add a repository variable
gh variable set LT_USERNAME         --body "john.doe"
gh variable set LT_DEVICE_ANDROID   --body "Pixel 6 Pro-13"
gh variable set LT_REGION           --body "us"
gh variable set NO_DEVICE_LAB       --body "false"
gh variable set SKIP_BAT            --body "false"
gh variable set API_LIVE_URL        --body "https://api.example.com"
```

---

## 5. Minimum viable setup (local / open-source fork)

If you are running the project without a real device lab or Firebase account, these are the only values you **must** set to get every workflow to pass without errors:

| Item | Minimum value |
|---|---|
| `SLACK_BOT_TOKEN` | A valid bot token from a Slack workspace you control |
| `SLACK_CHANNEL_ID` | A channel the bot has been invited to |
| `FIREBASE_TOKEN` | Required only if you deploy to Firebase Hosting / App Distribution |
| `NO_DEVICE_LAB` | `true` (skips all device-lab steps so emulator path runs instead) |
| `SKIP_BAT` | `true` (if you have no emulator in CI either) |

All other secrets are only invoked by their respective workflow steps and are **gracefully skipped** when the corresponding feature flag variable is set.

---

## 6. Rotating credentials

| Credential | Recommended rotation |
|---|---|
| `SLACK_BOT_TOKEN` | When the Slack app is reinstalled or the token is revoked |
| `FIREBASE_TOKEN` | Annually, or immediately if compromised (`firebase logout --token <old>` first) |
| `LT_ACCESS_KEY` | When team membership changes; regenerate from the LambdaTest dashboard |
| `NEW_RELIC_USER_API_KEY` | Annually or on engineer offboarding |

To update a secret:  
**Settings → Secrets and variables → Actions → click the secret → Update**

Or via CLI:
```bash
gh secret set FIREBASE_TOKEN --body "<new-token>"
```
