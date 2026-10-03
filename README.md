# Joe Goldberg OSINT

**Public-source research with evidence provenance. Built by sysn1xlabs.**

A dependency-free Python CLI for self-audits, consent-based research and authorized investigations. Offline first, explicit live requests, explicit exports. A username match never establishes a person's identity.

## Quick start

Requires Python 3.10 or newer. Extract the ZIP, open a terminal in `joe-goldberg`, then:

```bash
python3 joe_goldberg.py
```

Windows:

```powershell
py joe_goldberg.py
```

No pip install is required. Optional installation in a virtual environment gives a `joe-goldberg` command:

```bash
python3 -m venv .venv
# Linux/macOS: source .venv/bin/activate
# Windows PowerShell: .venv\Scripts\Activate.ps1
python -m pip install .
joe-goldberg --help
```

## Examples

```bash
# Offline: prepares links; sends nothing to external services
python3 -m joe_goldberg search --username example --purpose "My own account audit"

# Public API requests: explicitly sends the username to GitHub and GitLab
python3 -m joe_goldberg search --username example --purpose "My own account audit" --live

# Multiple inputs; international phone format is required
python3 -m joe_goldberg search --name "Example Person" --email me@example.com --phone +919876543210 --purpose "Consented public footprint review"

# Supported profile URL dispatch (single-segment GitHub/GitLab profiles)
python3 -m joe_goldberg search --url https://github.com/octocat --purpose "Public API demonstration" --live --sources GitHub

# Export request is explicit; existing files are never overwritten
python3 -m joe_goldberg search --username example --purpose "My own account audit" --format html --output audit.html
python3 -m joe_goldberg search --username example --purpose "My own account audit" --format json --full
python3 -m joe_goldberg sources
python3 -m joe_goldberg doctor
```

## What is included

- Interactive 0–9 menu and scriptable CLI.
- Name, username, email, international phone and HTTPS profile URL inputs, alone or combined.
- Normalization and validation, IDNA email domains, explicit derived hypotheses.
- Search query generation across 30 platforms plus general web, with Google and DuckDuckGo links.
- Twenty candidate profile URL templates, explicitly marked unverified.
- Two read-only public API adapters: GitHub and GitLab exact username lookups.
- Bounded concurrent collection, timeouts, response-size cap, in-memory cache per client, request spacing, no redirects, explicit failure states.
- Minimal public profile fields, API URL, observation time, response hash and collection method.
- Pairwise candidate association based on username/shared self-reported website; no identity merge or probabilistic score.
- TXT, Markdown, JSON, standalone HTML, findings CSV and JSON account-association graph exports.
- UTF-8 file handling, HTML escaping, terminal control-character filtering, CSV formula-prefix protection and no-overwrite exports.
- No runtime dependencies, credentials, automatic package installs, telemetry, persistent cache or automatic report files.
- Tests, architecture notes, feature coverage checklist and extension guidance.

## Important distinctions

A generated link is not a found account. A public API account is not a verified identity. A same-name match is not proof. An HTTP error is not evidence that an account is absent. Query links are not executed automatically. CSV exports observed findings only, so offline CSV exports contain only the header. Graph output is structured JSON, not a rendered visualization.

Opening a generated search link sends its query to the search provider. `--live` sends the username to the selected platforms. Public fields may be stale or inaccurate. Exports are ordinary unencrypted local files: review before sharing and delete when no longer needed. Response hashes identify retrieved bytes; without retaining those bytes they are not independent proof of the response contents.

## Scope and validation

See [docs/SCOPE.md](docs/SCOPE.md) for all requested categories and their implemented, manual, deferred or excluded status. This is a working initial release, not a claim to collect everything on the internet.

```bash
python3 -m unittest discover -s tests -v
```

15 tests passed on Python 3.12 in the build environment. Live GitHub smoke testing returned a network error in that environment; successful real-network operation remains unverified. Kali Linux, Windows and macOS are intended targets, not separately tested platforms.

API documentation consulted on 2026-10-03:
- https://docs.github.com/en/rest/users/users
- https://docs.gitlab.com/api/users/

MIT licensed. Maintainer identity: **sysn1xlabs**.
