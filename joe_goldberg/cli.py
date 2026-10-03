import argparse
import json
import sys
from .core import SITES, plan, render, export, clean
from .sources import collect

PURPOSE = 'Use only for self-audits, consent-based research or authorized investigations.'

def show(report):
    print('\nJOE GOLDBERG | PUBLIC-SOURCE RESEARCH\n' + PURPOSE)
    print('Inputs: ' + clean(json.dumps(report['inputs'], ensure_ascii=False)))
    print(f"\n{len(report['queries'])} search queries prepared (not executed).")
    for q in report['queries']:
        if q['source'] == 'General web':
            print(clean(q['url']))
    print(f"\n{len(report['candidates'])} unverified profile links (existence not checked):")
    for c in report['candidates']:
        print(clean(f"  {c['source']}: {c['url']}"))
    print('\nObserved public accounts:')
    for f in report['findings']:
        print(clean(f"  {f['source']} | {f['source_url']} | identity UNVERIFIED"))
        print(clean(json.dumps(f['data'], ensure_ascii=False)))
    for status in report['source_status']:
        print(clean(json.dumps(status)))
    print('\n' + report['notice'])

def menu():
    while True:
        print('\nJOE GOLDBERG — sysn1xlabs\n' + PURPOSE)
        print('1 Name\n2 Username\n3 Email\n4 Phone\n5 Profile URL\n6 Multiple identifiers\n7 Sources\n8 Help\n9 Dependency check\n0 Exit')
        choice = input('Choice: ').strip()
        if choice == '0':
            return 0
        if choice == '7':
            for source in SITES:
                print(source + (' — public API + manual links' if source in ('GitHub','GitLab') else ' — manual search only'))
            continue
        if choice == '8':
            print('Offline by default. Live mode sends the supplied username to GitHub/GitLab.\nNo identity confirmation, private accounts, account recovery, tracking, biometric matching or breach dumps.\nNothing is saved unless you choose an export. See README.md and docs/SCOPE.md.')
            continue
        if choice == '9':
            print('Python ' + sys.version.split()[0] + '; standard library only. No packages to install or update.')
            continue
        kinds = {'1':['name'],'2':['username'],'3':['email'],'4':['phone'],'5':['url'],'6':['name','username','email','phone','url']}.get(choice)
        if not kinds:
            print('Choose 0–9.')
            continue
        try:
            inputs = {k: input(k + ' (blank to skip): ').strip() for k in kinds}
            purpose = input('Authorized research purpose: ').strip()
            report = plan(inputs, purpose)
            if input('Fetch public GitHub/GitLab account data? This transmits the username. [y/N] ').lower() == 'y':
                collect(report)
            show(report)
            if input('Export this report? [y/N] ').lower() == 'y':
                fmt = input('Format [json/txt/md/html/csv/graph]: ').strip()
                path = input('New output file path: ').strip()
                print('Saved. SHA-256: ' + export(report, path, fmt))
        except (ValueError, OSError) as exc:
            print('Error: ' + clean(exc))

def main(argv=None):
    parser = argparse.ArgumentParser(description='Joe Goldberg — ethical public-source research toolkit')
    sub = parser.add_subparsers(dest='command')
    search = sub.add_parser('search', help='Prepare queries; optionally check public APIs')
    for k in ('name','username','email','phone','url'):
        search.add_argument('--'+k)
    search.add_argument('--purpose', required=True)
    search.add_argument('--live', action='store_true', help='Explicitly authorize sending username to selected public APIs')
    search.add_argument('--sources', nargs='+', choices=['GitHub','GitLab'], default=['GitHub','GitLab'])
    search.add_argument('--format', choices=['json','txt','md','html','csv','graph'], default='json')
    search.add_argument('--output', help='Explicit export request; existing files are never overwritten')
    search.add_argument('--full', action='store_true', help='Print the complete report to stdout')
    sub.add_parser('sources')
    sub.add_parser('doctor')
    sub.add_parser('menu')
    args = parser.parse_args(argv)
    try:
        if args.command in (None, 'menu'):
            return menu()
        if args.command == 'doctor':
            print('Python '+sys.version.split()[0]+'; no external runtime dependencies; no network test performed.')
            return 0
        if args.command == 'sources':
            for s in SITES:
                print(s + (' | public API + manual discovery' if s in ('GitHub','GitLab') else ' | manual discovery'))
            return 0
        report = plan({k:getattr(args,k) for k in ('name','username','email','phone','url')}, args.purpose)
        if args.live:
            collect(report, args.sources)
        if args.full:
            print(render(report,args.format), end='')
        else:
            show(report)
        if args.output:
            digest = export(report,args.output,args.format)
            print('Saved '+args.output+' | SHA-256 '+digest, file=sys.stderr)
        return 0
    except (ValueError, OSError) as exc:
        print('Error: '+clean(exc), file=sys.stderr)
        return 2
    except (KeyboardInterrupt, EOFError):
        print('\nStopped. No automatic report was saved.', file=sys.stderr)
        return 130
