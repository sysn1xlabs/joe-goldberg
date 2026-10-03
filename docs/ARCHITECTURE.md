# Architecture

`cli.py` handles the menu, arguments and explicit output requests. `core.py` owns normalization, planning, report data, conservative associations and serializers. `sources.py` owns fixed-host read-only API access and collection orchestration. No generic fetch or executable plugin mechanism exists.

Data flow: inputs → local normalization → query plan → optional public API collection → candidate associations → console → optional export.

Each report has schema_version, purpose, UTC created_at, inputs, derived hypotheses, unexecuted queries, unverified candidates, observed findings, source statuses and correlations. Missing public fields remain absent. Reports never flatten several accounts into a confirmed person.

To add an adapter: define an explicitly selected public endpoint; document fields and permission requirements; keep identifiers URL-encoded; cap response size/time and pagination; block redirects; distinguish not-found from authorization/network/rate-limit failures; preserve source provenance; use field allowlists; add fixture and failure tests. Expand the host allowlist only after reviewing the endpoint. Prefer documented APIs over generic HTML fetching.

PublicClient caches within one client instance only. Normal CLI runs make one request per selected adapter, so this release makes little use of caching. Neither cache nor raw API bodies are persisted. Exports do not encrypt or redact user-supplied inputs. An operator-supplied purpose is an accountability prompt, not technical proof of authorization.
