---
id: settings-authentication
topic: Authentication Settings
category: settings
tags: [authentication, api, credentials, login, aws]
requires: [settings-overview]
related_to: [settings-environment-variables, settings-schema]
official_docs: https://code.claude.com/en/settings#available-settings
---

# Authentication Settings

Configure authentication methods and credential helpers.

## apiKeyHelper

Custom script to generate auth values. Executed via `/bin/sh`.

```json
{
  "apiKeyHelper": "/bin/generate_temp_api_key.sh"
}
```

The script output is sent as:
- `X-Api-Key` header
- `Authorization: Bearer` header

**Refresh interval:** Set via `CLAUDE_CODE_API_KEY_HELPER_TTL_MS` environment variable.

## forceLoginMethod

Restrict login to a specific account type.

```json
{
  "forceLoginMethod": "claudeai"
}
```

| Value | Effect |
|-------|--------|
| `claudeai` | Restrict to Claude.ai accounts |
| `console` | Restrict to Console accounts (API billing) |

## forceLoginOrgUUID

Auto-select organization during login, bypassing selection step.

```json
{
  "forceLoginMethod": "console",
  "forceLoginOrgUUID": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
}
```

**Requirement:** `forceLoginMethod` must also be set.

## AWS Credential Helpers

### awsAuthRefresh

Script to modify `.aws` directory for credential refresh.

```json
{
  "awsAuthRefresh": "aws sso login --profile myprofile"
}
```

### awsCredentialExport

Script that outputs JSON with AWS credentials.

```json
{
  "awsCredentialExport": "/bin/generate_aws_grant.sh"
}
```

The script must output valid JSON with AWS credential fields.

## OpenTelemetry Headers

### otelHeadersHelper

Script to generate dynamic OpenTelemetry headers at startup and periodically.

```json
{
  "otelHeadersHelper": "/bin/generate_otel_headers.sh"
}
```

**Refresh interval:** Controlled by `CLAUDE_CODE_OTEL_HEADERS_HELPER_DEBOUNCE_MS` (default: 29 minutes).

## Key Points

- `apiKeyHelper` generates credentials dynamically
- Use `forceLoginMethod` for organizational login restrictions
- AWS helpers support SSO and custom credential workflows
- All helper scripts execute via shell
