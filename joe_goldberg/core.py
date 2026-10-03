"""Offline planning, bounded public API collection and evidence reports."""
import csv
import hashlib
import html
import io
import json
import re
import unicodedata
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit, quote, urlencode

SITES = {
 'GitHub': ('github.com', 'https://github.com/{u}'),
 'GitLab': ('gitlab.com', 'https://gitlab.com/{u}'),
 'Reddit': ('reddit.com', 'https://www.reddit.com/user/{u}/'),
 'Instagram': ('instagram.com', 'https://www.instagram.com/{u}/'),
 'X': ('x.com', 'https://x.com/{u}'),
 'LinkedIn': ('linkedin.com', None),
 'Facebook': ('facebook.com', None),
 'TikTok': ('tiktok.com', 'https://www.tiktok.com/@{u}'),
 'YouTube': ('youtube.com', 'https://www.youtube.com/@{u}'),
 'Twitch': ('twitch.tv', 'https://www.twitch.tv/{u}'),
 'Pinterest': ('pinterest.com', 'https://www.pinterest.com/{u}/'),
 'Tumblr': ('tumblr.com', None),
 'Quora': ('quora.com', None),
 'Stack Overflow': ('stackoverflow.com', None),
 'XDA': ('xdaforums.com', None),
 'Spiceworks': ('community.spiceworks.com', None),
 'Vimeo': ('vimeo.com', None),
 'SoundCloud': ('soundcloud.com', 'https://soundcloud.com/{u}'),
 'Goodreads': ('goodreads.com', None),
 'Medium': ('medium.com', 'https://medium.com/@{u}'),
 'Dev.to': ('dev.to', 'https://dev.to/{u}'),
 'Hacker News': ('news.ycombinator.com', 'https://news.ycombinator.com/user?id={u}'),
 'CodePen': ('codepen.io', 'https://codepen.io/{u}'),
 'Behance': ('behance.net', 'https://www.behance.net/{u}'),
 'Dribbble': ('dribbble.com', 'https://dribbble.com/{u}'),
 'Keybase': ('keybase.io', 'https://keybase.io/{u}'),
 'ORCID': ('orcid.org', None),
 'npm': ('npmjs.com', 'https://www.npmjs.com/~{u}'),
 'PyPI': ('pypi.org', 'https://pypi.org/user/{u}/'),
 'Hugging Face': ('huggingface.co', 'https://huggingface.co/{u}'),
}

def now():
    return datetime.now(timezone.utc).isoformat()

def clean(value):
    return ''.join(c for c in str(value) if unicodedata.category(c) not in ('Cc', 'Cf'))

def normalize(kind, value):
    value = value.strip()
    if not value or len(value) > 300 or clean(value) != value:
        raise ValueError('Input must be 1–300 characters without control characters')
    if kind == 'username':
        value = value.removeprefix('@')
        if not re.fullmatch(r'[A-Za-z0-9_][A-Za-z0-9_.-]{0,79}', value):
            raise ValueError('Username must contain letters, numbers, underscore, dot or hyphen')
    elif kind == 'email':
        if not re.fullmatch(r'[^\s@]+@[^\s@]+\.[^\s@]+', value):
            raise ValueError('Enter a complete email address')
        local, domain = value.rsplit('@', 1)
        value = local + '@' + domain.encode('idna').decode().lower()
    elif kind == 'phone':
        value = re.sub(r'[\s().-]', '', value)
        if not re.fullmatch(r'\+[1-9][0-9]{6,14}', value):
            raise ValueError('Use international format, for example +919876543210; no country guessing')
    elif kind == 'url':
        u = urlsplit(value)
        if u.scheme != 'https' or not u.hostname or u.username or u.password or u.port not in (None, 443):
            raise ValueError('Use an HTTPS URL without credentials or a custom port')
        value = value.split('#')[0]
    elif kind != 'name':
        raise ValueError('Unknown identifier type')
    return value

def plan(inputs, purpose):
    normalized = {k: normalize(k, v) for k, v in inputs.items() if v}
    if not normalized:
        raise ValueError('Supply at least one identifier')
    if len(purpose.strip()) < 5:
        raise ValueError('Describe the authorized research purpose (at least 5 characters)')
    queries, candidates = [], []
    for kind, value in normalized.items():
        literal = '"' + value.replace('"', ' ') + '"'
        for label, domain in [('General web', None)] + [(k, v[0]) for k, v in SITES.items()]:
            q = literal if not domain else f'site:{domain} {literal}'
            queries.append({'input_type': kind, 'source': label, 'query': q,
                            'url': 'https://www.google.com/search?' + urlencode({'q': q}),
                            'duckduckgo_url': 'https://duckduckgo.com/?' + urlencode({'q': q}),
                            'status': 'not_executed'})
    if 'username' in normalized:
        for label, (_, template) in SITES.items():
            if template:
                candidates.append({'source': label, 'url': template.format(u=quote(normalized['username'], safe='')),
                                   'status': 'unverified_link', 'identity_confidence': 'unknown'})
    derived = {}
    if 'email' in normalized:
        local, domain = normalized['email'].rsplit('@', 1)
        derived['email_domain'] = domain
        derived['possible_username'] = {'value': local, 'status': 'hypothesis_only'}
    if 'url' in normalized:
        u = urlsplit(normalized['url'])
        derived['url_host'] = u.hostname
        derived['url_path'] = u.path
    return {'schema_version': 1, 'created_at': now(), 'purpose': clean(purpose),
            'inputs': normalized, 'derived': derived, 'queries': queries,
            'candidates': candidates, 'findings': [], 'source_status': [], 'correlations': [],
            'notice': 'Public records may be wrong or stale. Matching identifiers do not establish identity.'}

def correlate(report):
    findings = report['findings']
    pairs = []
    for i, a in enumerate(findings):
        for b in findings[i+1:]:
            signals = []
            if a['data'].get('username', '').casefold() == b['data'].get('username', '').casefold():
                signals.append('same username: weak evidence')
            wa, wb = a['data'].get('website'), b['data'].get('website')
            if wa and wb and wa.rstrip('/') == wb.rstrip('/'):
                signals.append('same self-reported website: supporting evidence, not ownership proof')
            pairs.append({'sources': [a['source_url'], b['source_url']], 'signals': signals,
                          'conclusion': 'candidate association; manual review required'})
    report['correlations'] = pairs
    return report

def render(report, fmt):
    raw = json.dumps(report, ensure_ascii=False, indent=2)
    if fmt == 'json':
        return raw + '\n'
    if fmt == 'html':
        return ('<!doctype html><html lang="en"><meta charset="utf-8">'
                '<meta name="viewport" content="width=device-width,initial-scale=1">'
                '<meta http-equiv="Content-Security-Policy" content="default-src \'none\'; style-src \'unsafe-inline\'">'
                '<title>Joe Goldberg · Evidence report</title><style>body{background:#101722;color:#e5edf5;'
                'font:16px system-ui;max-width:1100px;margin:40px auto;padding:24px}pre{white-space:pre-wrap;'
                'overflow-wrap:anywhere;background:#1a2534;padding:24px;border-radius:12px}h1{color:#5de4b6}</style>'
                '<h1>Joe Goldberg · Evidence report</h1><p>Candidate matches require human verification.</p><pre>'
                + html.escape(raw) + '</pre></html>')
    if fmt in ('txt', 'md'):
        return '# Joe Goldberg — OSINT evidence report\n\n' + clean(raw) + '\n'
    if fmt == 'csv':
        stream = io.StringIO(newline='')
        writer = csv.writer(stream)
        writer.writerow(['source', 'url', 'status', 'evidence_json'])
        for row in report['findings']:
            vals = [row['source'], row['source_url'], row['status'], json.dumps(row['data'], ensure_ascii=False)]
            writer.writerow(["'"+v if v.lstrip().startswith(('=', '+', '-', '@')) else v for v in vals])
        return stream.getvalue()
    if fmt == 'graph':
        return json.dumps({'nodes': [{'id': str(i), 'url': f['source_url'], 'type': 'account_candidate'}
                                     for i, f in enumerate(report['findings'])],
                           'associations': report['correlations']}, indent=2) + '\n'
    raise ValueError('Unsupported format')

def export(report, path, fmt):
    content = render(report, fmt)
    # Exclusive creation prevents accidental replacement of evidence.
    with Path(path).open('x', encoding='utf-8', newline='') as handle:
        handle.write(content)
    return hashlib.sha256(content.encode('utf-8')).hexdigest()
