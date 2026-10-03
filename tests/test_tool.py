import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from urllib.error import HTTPError, URLError
from joe_goldberg.core import plan, normalize, correlate, render, export, clean
from joe_goldberg.sources import lookup, collect, PublicClient, NoRedirect
from joe_goldberg.cli import main

class Fake:
    def __init__(self, payload): self.payload = payload
    def get(self, url): return self.payload, 'abc123'

class ToolkitTests(unittest.TestCase):
    def test_normalization(self):
        self.assertEqual(normalize('phone','+91 (98765) 43210'), '+919876543210')
        self.assertEqual(normalize('email','Me@EXAMPLE.COM'), 'Me@example.com')
        self.assertEqual(normalize('username','@demo'), 'demo')
    def test_invalid_inputs(self):
        for kind, value in [('phone','9876543210'),('username','../secret'),('email','bad'),('url','http://example.com'),('url','https://u:p@example.com'),('name','a\x1bb')]:
            with self.subTest(kind=kind):
                with self.assertRaises(ValueError): normalize(kind,value)
    def test_offline_never_fetches(self):
        with patch('urllib.request.OpenerDirector.open', side_effect=AssertionError('network')):
            r = plan({'username':'demo','email':'a@example.com'}, 'self audit')
        self.assertEqual(r['findings'], [])
        self.assertTrue(all(c['status']=='unverified_link' for c in r['candidates']))
        self.assertEqual(len(r['queries']),62)
    def test_github_allowlist(self):
        f,s = lookup('GitHub','demo',Fake({'login':'demo','name':'Demo','email':'secret@example.com','location':'hidden','private_repos':99}))
        self.assertEqual(s['status'],'ok')
        self.assertNotIn('email',f['data'])
        self.assertNotIn('location',f['data'])
        self.assertEqual(f['identity_confidence'],'unverified')
    def test_gitlab_exact_match(self):
        f,s = lookup('GitLab','demo',Fake([{'username':'another'}]))
        self.assertIsNone(f)
        self.assertEqual(s['status'],'not_found')
    def test_bad_schema(self):
        f,s = lookup('GitHub','demo',Fake([]))
        self.assertEqual(s['status'],'unavailable')
    def test_rate_limit(self):
        with patch.object(PublicClient,'get',side_effect=HTTPError('https://api.github.com',429,'limit',{},None)):
            f,s = lookup('GitHub','demo')
        self.assertEqual(s['status'],'rate_limited')
        self.assertIsNone(f)
    def test_network_failure(self):
        with patch.object(PublicClient,'get',side_effect=URLError('offline')):
            self.assertEqual(lookup('GitHub','demo')[1]['status'],'unavailable')
    def test_redirects_and_hosts(self):
        self.assertIsNone(NoRedirect().redirect_request(None,None,None,None,None,None))
        with self.assertRaises(ValueError): PublicClient().get('https://127.0.0.1/admin')
    def test_no_automatic_identity_merge(self):
        r=plan({'username':'demo'},'self audit')
        r['findings']=[lookup('GitHub','demo',Fake({'login':'demo'}))[0],lookup('GitLab','demo',Fake([{'username':'demo'}]))[0]]
        correlate(r)
        self.assertIn('manual review',r['correlations'][0]['conclusion'])
    def test_export_no_overwrite_unicode(self):
        r=plan({'name':'മലയാളം'},'self audit')
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'case.json'
            self.assertEqual(len(export(r,p,'json')),64)
            self.assertEqual(json.loads(p.read_text(encoding='utf-8'))['inputs']['name'],'മലയാളം')
            with self.assertRaises(FileExistsError): export(r,p,'json')
    def test_html_escape(self):
        r=plan({'name':'<script>alert(1)</script>'},'self audit')
        self.assertNotIn('<script>',render(r,'html'))
    def test_formats(self):
        r=plan({'username':'demo'},'self audit')
        for fmt in ('json','txt','md','html','csv','graph'):
            self.assertTrue(render(r,fmt))
    def test_url_dispatch(self):
        r=plan({'url':'https://github.com/demo'},'self audit')
        with patch('joe_goldberg.sources.lookup',return_value=(None,{'status':'not_found'})) as mock:
            collect(r)
        mock.assert_called_once_with('GitHub','demo')
    def test_terminal_clean(self):
        self.assertEqual(clean('hi\x1b\u202e'),'hi')

if __name__ == '__main__': unittest.main()
