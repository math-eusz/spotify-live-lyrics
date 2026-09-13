"""Publish reviewed historical releases. Default mode only validates snapshots.

Run in a full repository checkout. --publish uses the repository-scoped GH_TOKEN
provided by GitHub Actions. No tokens are saved or printed.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import urllib.error
import urllib.parse
import urllib.request

ROOT = Path(__file__).resolve().parents[1]


def prepare(root=ROOT):
    manifest = json.loads((root / 'releases/manifest.json').read_text())
    prepared, tags = [], set()
    assert sum(bool(r['latest']) for r in manifest) == 1, 'Exactly one latest release required'
    for item in manifest:
        tag, commit = item['tag'], item['commit']
        if not re.fullmatch(r'v\d+\.\d+\.\d+', tag) or tag in tags:
            raise ValueError('Invalid or duplicate version')
        if not re.fullmatch(r'[0-9a-f]{40}', commit):
            raise ValueError('Release must point to an exact commit')
        tags.add(tag)
        note = root / item['notes']
        if not note.resolve().is_relative_to(root.resolve()):
            raise ValueError('Notes outside repository')
        body = note.read_text(encoding='utf-8')
        assets = {}
        for path in item['assets']:
            if '/' in path or path.startswith('.'):
                raise ValueError('Assets must be top-level source files')
            content = subprocess.check_output(['git', 'show', f'{commit}:{path}'], cwd=root)
            if path.endswith('.py'):
                compile(content, path, 'exec')
            assets[path] = content
        assets['SHA256SUMS.txt'] = ''.join(
            f'{hashlib.sha256(content).hexdigest()}  {name}\n'
            for name, content in assets.items()).encode()
        prepared.append((item, body, assets))
    return prepared


class GitHub:
    def __init__(self, token, repository):
        if not re.fullmatch(r'[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+', repository):
            raise ValueError('Invalid repository')
        self.token = token
        self.base = 'https://api.github.com/repos/' + repository

    def call(self, path, method='GET', data=None, binary=False, missing=False):
        url = path if path.startswith('https://') else self.base + path
        if urllib.parse.urlparse(url).hostname not in ('api.github.com', 'uploads.github.com'):
            raise ValueError('Unexpected API host')
        headers = {'Authorization': 'Bearer ' + self.token,
                   'Accept': 'application/vnd.github+json',
                   'X-GitHub-Api-Version': '2022-11-28',
                   'Content-Type': 'application/octet-stream' if binary else 'application/json'}
        encoded = data if binary else json.dumps(data).encode() if data is not None else None
        request = urllib.request.Request(url, data=encoded, headers=headers, method=method)
        try:
            with urllib.request.urlopen(request, timeout=60) as response:
                raw = response.read()
                return json.loads(raw) if raw else None
        except urllib.error.HTTPError as error:
            if missing and error.code == 404:
                return None
            raise RuntimeError(f'GitHub API {method} failed with HTTP {error.code}') from None


def publish(api, prepared):
    # Check every existing tag before publishing anything. Never move old tags.
    for item, _, _ in prepared:
        ref = api.call('/git/ref/tags/' + item['tag'], missing=True)
        if ref:
            obj = ref['object']
            if obj['type'] == 'tag':
                obj = api.call('/git/tags/' + obj['sha'])['object']
            if obj['type'] != 'commit' or obj['sha'] != item['commit']:
                raise ValueError('Existing tag points to another snapshot: ' + item['tag'])
    for item, body, assets in prepared:
        tag = item['tag']
        release = api.call('/releases/tags/' + tag, missing=True)
        if release and not release['draft']:
            print(tag + ': already published; leaving it unchanged', flush=True)
            continue
        if not release:
            release = api.call('/releases', 'POST', {
                'tag_name': tag, 'target_commitish': item['commit'],
                'name': item['title'], 'body': body, 'draft': True,
                'prerelease': False, 'make_latest': 'false'})
        existing = {asset['name']: asset for asset in api.call(f"/releases/{release['id']}/assets")}
        for name, content in assets.items():
            if name in existing:
                # Only drafts can reach here. Replace partially uploaded draft assets.
                api.call(f"/releases/assets/{existing[name]['id']}", 'DELETE')
            upload = release['upload_url'].split('{', 1)[0] + '?name=' + urllib.parse.quote(name)
            api.call(upload, 'POST', content, binary=True)
        api.call(f"/releases/{release['id']}", 'PATCH', {
            'name': item['title'], 'body': body, 'draft': False,
            'prerelease': False, 'make_latest': 'true' if item['latest'] else 'false'})
        print(tag + ': published with ' + str(len(assets)) + ' assets', flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--publish', action='store_true')
    args = parser.parse_args()
    prepared = prepare()
    print(f'Validated {len(prepared)} complete historical snapshots.', flush=True)
    if args.publish:
        token = os.environ.get('GH_TOKEN')
        if not token:
            raise RuntimeError('GH_TOKEN is required for publication')
        publish(GitHub(token, os.environ.get('GH_REPO', 'math-eusz/spotify-live-lyrics')), prepared)


if __name__ == '__main__':
    main()
