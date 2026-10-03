# Feature coverage and ethical scope

The supplied brief is a roadmap. This checklist deliberately separates delivered functionality from future integrations.

| Brief category | Status in this release |
|---|---|
| Name search | Offline quoted/site-restricted search queries; no automated people matching |
| Username search | GitHub/GitLab APIs plus 30-platform manual query registry |
| Email | Syntax/domain normalization, public search links, local-part hypothesis; no ownership claim |
| Phone | International-format normalization and public search links; no carrier, person, country or current-location claims |
| Profile URL | HTTPS validation, host/path extraction, GitHub/GitLab profile dispatch; no generic webpage fetch |
| Combined identifiers | Single report containing all supplied inputs; no automatic enrichment of derived hypotheses |
| Public display name, bio, website, creation date | Collected only when the two supported APIs expose them |
| Repository count | GitHub public count; no repository-content crawl |
| Aliases | Supplied username only; no alias discovery engine |
| Profile images | Not downloaded or analyzed |
| Birthdays, age, education, occupation | Not automatically extracted |
| Contact details and location | Not harvested from API responses |
| Posts/comments/replies/reviews/playlists/likes/followers | Manual source discovery only; no activity or social-network collection |
| Interests | No inference engine |
| Google/Bing/DuckDuckGo | Google and DuckDuckGo query links; no scraping or licensed search API integration |
| Gravatar | Deferred; email-hash lookup not included |
| HIBP | Deferred; requires a separate licensed/authorized integration; no breach dumps |
| Correlation | Exact username/shared website signals, unverified associations, no identity conclusions |
| Explicit cross-links/name/bio similarity | Deferred, not silently approximated |
| Evidence | Source URL, API endpoint, method, timestamp, selected fields, response hash |
| CLI/menu | Implemented, Ctrl+C/EOF handling |
| Dependency manager | Standard-library-only doctor; no dependency installation needed |
| Exports | TXT, MD, JSON, HTML, CSV findings, JSON account graph |
| Concurrency/cache/rate limiting | Two workers maximum, per-client memory cache and one-second spacing; stop on rate limit, no automatic retry |
| Case/workspace persistence | Explicit report exports only; no case database or importer |
| Plugin architecture | Python adapter boundary; no dynamic third-party plugin loading |
| API key management | Not needed for included unauthenticated requests; no secrets collected |
| Source health dashboard | Per-run source statuses only; no separate monitoring service |
| Tests/docs/package | Included; live networking and target OS validation remain open |

## Excluded by design

Private-account access, password recovery enumeration, CAPTCHA bypass, stealth scraping, proxy rotation to evade blocks, leaked credentials, home-address aggregation, real-time physical tracking, face recognition, sensitive-trait inference and automated relationship surveillance.

## Responsible extensions

Prioritize opt-in search-provider APIs, analyst-entered evidence with provenance, explicit cross-link review, report redaction, case retention controls and platform-specific public APIs. Evaluate access terms before adding an adapter. Never treat a generic HTTP 200 response as account existence. Do not silently enable new sources or transmit additional identifiers. Avoid building broad profiles of private individuals without consent or appropriate authority.
