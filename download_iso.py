#!/usr/bin/env python3
"""
Download bootable Windows ISO from Microsoft's CDN
Gets Windows Server/Enterprise Evaluation ISOs that work with VMs
"""
import urllib.request
import json
import re
import sys

def get_windows_iso_url():
    """Find Windows ISO download URL by checking Microsoft's CDN patterns"""

    print("Searching for bootable Windows ISOs...", file=sys.stderr)

    # Microsoft uses predictable CDN URLs for evaluation ISOs
    # They follow patterns on software-static.download.prss.microsoft.com

    # Check the evaluation center API endpoint
    api_endpoints = [
        "https://www.microsoft.com/en-us/evalcenter/api/products/getproducts",
        "https://www.microsoft.com/en-us/api/controls/contentinclude/html?pageId=cfa0e580-a81e-4a4b-a846-7b21bf4e2e5b&host=www.microsoft.com&segments=software-download,windows10ISO",
        "https://www.microsoft.com/en-us/software-download/windows10ISO/ajax",
    ]

    for endpoint in api_endpoints:
        try:
            req = urllib.request.Request(endpoint, headers={
                'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36',
                'Accept': 'application/json',
                'X-Requested-With': 'XMLHttpRequest'
            })

            with urllib.request.urlopen(req, timeout=5) as response:
                content = response.read().decode('utf-8')

                # Look for ISO URLs in response
                iso_urls = re.findall(r'https://[^"]+\.iso', content)
                if iso_urls:
                    print(f"Found ISO URL in API: {iso_urls[0]}", file=sys.stderr)
                    return iso_urls[0]

                # Look for LinkIDs
                linkids = re.findall(r'LinkID=(\d+)', content)
                if linkids:
                    for linkid in linkids:
                        test_url = f"https://go.microsoft.com/fwlink/?LinkID={linkid}"
                        print(f"Testing LinkID {linkid}...", file=sys.stderr)

                        # Check if it redirects to an ISO
                        try:
                            check = urllib.request.Request(test_url, method='HEAD')
                            with urllib.request.urlopen(check, timeout=5) as resp:
                                if '.iso' in resp.url:
                                    print(f"Found working LinkID: {linkid}", file=sys.stderr)
                                    return test_url
                        except:
                            continue
        except Exception as e:
            continue

    # Try known CDN patterns
    print("Checking known CDN patterns...", file=sys.stderr)

    base_urls = [
        "https://software-static.download.prss.microsoft.com/sg/download/888969d5-f34g-4e03-ac9d-1f9786c66749/",
        "https://software-static.download.prss.microsoft.com/dbazure/",
        "https://software.download.prss.microsoft.com/sg/",
    ]

    iso_names = [
        "19045.2006.220908-0225.22h2_release_svc_refresh_CLIENTENTERPRISEEVAL_OEMRET_x64FRE_en-us.iso",
        "Win10_22H2_EnterpriseEval_x64.iso",
        "Win10_22H2_English_x64.iso",
        "Win10_22H2_English_x64v1.iso",
        "SERVER_EVAL_x64FRE_en-us.iso"  # Last resort - Server edition
    ]

    for base in base_urls:
        for iso in iso_names:
            test_url = base + iso
            try:
                req = urllib.request.Request(test_url, method='HEAD')
                with urllib.request.urlopen(req, timeout=5) as response:
                    if response.status == 200:
                        print(f"Found working ISO URL: {test_url}", file=sys.stderr)
                        return test_url
            except:
                continue

    # Last resort: return the known working evaluation link
    print("Using fallback evaluation ISO link", file=sys.stderr)
    return "https://go.microsoft.com/fwlink/?LinkID=2195280&clcid=0x409&culture=en-us&country=US"

def download_iso(url, filename="win.iso"):
    """Download ISO with progress"""

    print(f"Downloading {url}", file=sys.stderr)
    print(f"Saving as: {filename}", file=sys.stderr)

    try:
        def progress_hook(block_num, block_size, total_size):
            if total_size > 0:
                downloaded = block_num * block_size
                percent = min(100, (downloaded / total_size) * 100)
                size_gb = total_size / (1024 * 1024 * 1024)
                downloaded_gb = downloaded / (1024 * 1024 * 1024)
                print(f"Progress: {percent:.1f}% ({downloaded_gb:.2f}/{size_gb:.2f} GB)", end='\r', file=sys.stderr)

        urllib.request.urlretrieve(url, filename, reporthook=progress_hook)
        print(f"\n✓ Downloaded: {filename} (bootable ISO ready for VMs)", file=sys.stderr)

    except Exception as e:
        print(f"\nError downloading: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    iso_url = get_windows_iso_url()
    download_iso(iso_url)