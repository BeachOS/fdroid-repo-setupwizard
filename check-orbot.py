#!/usr/bin/env python3
#
# download the most recent Orbot release, preferring the
# arm64-v8a-only version, if available.  This relies on Orbot using
# ABI splits, where the single-ABI APKs have igher Version Codes than
# the APK with all the ABIs (aka "universal").
#
# Relies on this being present and working:
# https://gitlab.com/guardianproject/fdroid-metadata/-/merge_requests/4

import hashlib
import json
import os
import requests


# use generic User Agent to avoid being targetted
HEADERS = {'User-Agent': 'Wget/1.21.1'}


def download_file(url):
    # the stream=True parameter keeps memory usage low
    r = requests.get(url, stream=True, allow_redirects=True, headers=HEADERS)
    r.raise_for_status()
    os.makedirs('tmp', exist_ok=True)
    h = hashlib.sha256()
    f = os.path.join('tmp', os.path.basename(url))
    with open(f, 'wb') as fp:
        for chunk in r.iter_content(chunk_size=8192):
            if chunk:  # filter out keep-alive new chunks
                fp.write(chunk)
                h.update(chunk)
    return f, h.hexdigest()


def main():
    baseurl = 'https://guardianproject.info/releases'
    indexurl = os.path.join(baseurl, 'index-v1.json')
    r = requests.get(indexurl, allow_redirects=True, headers=HEADERS)
    r.raise_for_status()
    for package in r.json()['packages']['org.torproject.android']:
        s = package['signer']
        if s != 'a454b87a1847a89ed7f5e70fba6bba96f3ef29c26e0981204fe347bf231dfd5b':
            print('ERROR: Orbot entry with bad signing key!')
            print(json.dumps(package, indent=2, sort_keys=True))
            exit(1)
        nativecode = package.get('nativecode')
        if nativecode and len(nativecode) == 1 and nativecode[0] == 'arm64-v8a':
            break
        elif len(nativecode) > 1:
            print('WARNING: no single ABI found for this release, using the full APK')
            break
    apkfile = os.path.join(
        'repo', '%s_%s.apk' % (package['packageName'], package['versionCode'])
    )
    if not os.path.exists(apkfile):
        print(apkfile, 'does not exist, downloading')
        f, sha256 = download_file(os.path.join(baseurl, package['apkName']))
        if package['hash'] != sha256:
            print('ERROR', f, 'SHA-256', sha256, 'does not match:')
            print(json.dumps(package, indent=2, sort_keys=True))
            exit(1)
        os.link(f, apkfile)


if __name__ == "__main__":
    os.chdir(os.path.dirname(__file__))
    main()
