"""Read-only, unauthenticated public API adapters. No arbitrary URL fetching."""
import hashlib
import json
import time
from concurrent.futures import ThreadPoolExecutor
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode, urlsplit
from urllib.request import Request, build_opener, HTTPRedirectHandler
from .core import now, correlate

class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None

class PublicClient:
    def __init__(self):
        self.cache = {}
        self.last_request = 0.0
        self.opener = build_opener(NoRedirect())

    def get(self, url):
        parts = urlsplit(url)
        if parts.scheme != 'https' or parts.hostname not in ('api.github.com', 'gitlab.com') or parts.username or parts.port not in (None, 443):
            raise ValueError('Only supported public API hosts are permitted')
        if url in self.cache:
            return self.cache[url]
        time.sleep(max(0, 1 - (time.monotonic() - self.last_request)))
        self.last_request = time.monotonic()
        req = Request(url, headers={'User-Agent': 'JoeGoldbergOSINT/1.0 (public research)', 'Accept': 'application/json'})
        with self.opener.open(req, timeout=12) as response:
            raw = response.read(1_000_001)
            if len(raw) > 1_000_000:
                raise ValueError('Response exceeded 1 MB limit')
            result = (json.loads(raw), hashlib.sha256(raw).hexdigest())
            self.cache[url] = result
            return result

def lookup(source, username, client=None):
    client = client or PublicClient()
    url = ('https://api.github.com/users/' + quote(username, safe='') if source == 'GitHub'
           else 'https://gitlab.com/api/v4/users?' + urlencode({'username': username}))
    observed = now()
    try:
        payload, digest = client.get(url)
        if source == 'GitLab':
            if not isinstance(payload, list):
                raise ValueError('Unexpected GitLab response')
            matches = [r for r in payload if isinstance(r, dict) and str(r.get('username','')).casefold() == username.casefold()]
            if not matches:
                return None, {'source': source, 'status': 'not_found', 'checked_at': observed}
            row = matches[0]
            mapping = {'username': 'username', 'name': 'name', 'bio': 'bio', 'website': 'website_url', 'created_at': 'created_at'}
            profile = 'https://gitlab.com/' + quote(username, safe='')
        else:
            row = payload
            if not isinstance(row, dict) or str(row.get('login','')).casefold() != username.casefold():
                raise ValueError('Unexpected GitHub response or renamed account')
            mapping = {'username':'login', 'name':'name', 'bio':'bio', 'website':'blog', 'created_at':'created_at', 'public_repositories':'public_repos'}
            profile = 'https://github.com/' + quote(username, safe='')
        data = {k: row[v] for k,v in mapping.items() if row.get(v) is not None}
        finding = {'source':source, 'source_url':profile, 'api_url':url, 'observed_at':observed,
                   'status':'public_account_observed', 'identity_confidence':'unverified',
                   'method':'exact username via public API', 'response_sha256':digest,
                   'data':data, 'limitations':'Self-reported fields; no identity or ownership verification'}
        return finding, {'source':source, 'status':'ok', 'checked_at':observed}
    except HTTPError as exc:
        status = {404:'not_found', 429:'rate_limited', 403:'forbidden_or_rate_limited', 401:'authentication_required'}.get(exc.code, 'http_error')
        return None, {'source':source, 'status':status, 'http_status':exc.code, 'checked_at':observed}
    except (URLError, TimeoutError, OSError, ValueError, TypeError) as exc:
        return None, {'source':source, 'status':'unavailable', 'error_type':type(exc).__name__, 'checked_at':observed}

def collect(report, selected=('GitHub','GitLab')):
    username = report['inputs'].get('username')
    targets = [(source, username) for source in selected] if username else []
    if not username and report['inputs'].get('url'):
        u = urlsplit(report['inputs']['url'])
        parts = u.path.strip('/').split('/')
        source = {'github.com':'GitHub','gitlab.com':'GitLab'}.get(u.hostname)
        if source in selected and len(parts) == 1 and parts[0]:
            from .core import normalize
            targets = [(source, normalize('username', parts[0]))]
    if not targets:
        report['source_status'].append({'status':'skipped', 'reason':'Live APIs require username or supported profile URL'})
        return report
    with ThreadPoolExecutor(max_workers=2) as pool:
        for finding, status in pool.map(lambda task: lookup(*task), targets):
            report['source_status'].append(status)
            if finding:
                report['findings'].append(finding)
    return correlate(report)
