#!/usr/bin/env python3
"""
Download Windows Enterprise N ESD and convert to WIM
NOTE: Creates WIM file, NOT bootable ISO - you need Windows boot files for that
"""

import sys
import os
import subprocess
import tempfile
import platform
from pathlib import Path
import xml.etree.ElementTree as ET

import requests
from tqdm import tqdm


def check_tools():
    """Check for required conversion tools"""
    system = platform.system()

    # Check for CAB extraction tool
    has_cabextract = subprocess.run(['which', 'cabextract'], capture_output=True).returncode == 0
    has_tar = subprocess.run(['which', 'tar'], capture_output=True).returncode == 0

    if not has_cabextract and not has_tar:
        print("❌ Missing CAB extraction tool!")
        if system == "Darwin":  # macOS
            print("Install: brew install cabextract")
        else:  # Linux
            print("Install: sudo apt install cabextract")
        sys.exit(1)

    # Check for ESD conversion tool
    has_wimlib = subprocess.run(['which', 'wimlib-imagex'], capture_output=True).returncode == 0

    if not has_wimlib:
        print("❌ Missing ESD conversion tool (wimlib-imagex)!")
        if system == "Darwin":  # macOS
            print("Install: brew install wimlib")
        else:  # Linux
            print("Install: sudo apt install wimtools")
        sys.exit(1)

    print("✓ All required tools found")
    return True


def download_file(url, filename, desc="Downloading"):
    """Download file with progress bar"""
    response = requests.get(url, stream=True)
    total_size = int(response.headers.get('content-length', 0))

    with open(filename, 'wb') as f:
        with tqdm(total=total_size, unit='B', unit_scale=True, desc=desc) as pbar:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    pbar.update(len(chunk))


def extract_xml_from_cab(cab_path):
    """Extract products.xml from Microsoft CAB file"""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Try cabextract first (Linux/macOS with cabextract installed)
        try:
            subprocess.run(['cabextract', '-q', '-d', tmpdir, cab_path],
                         check=True, capture_output=True)
            xml_path = os.path.join(tmpdir, 'products.xml')
            if os.path.exists(xml_path):
                with open(xml_path, 'r', encoding='utf-8') as f:
                    return f.read()
        except (subprocess.CalledProcessError, FileNotFoundError):
            pass

        # Try tar (macOS)
        try:
            subprocess.run(['tar', 'xf', cab_path, 'products.xml'],
                         cwd=tmpdir, capture_output=True, check=True)
            xml_path = os.path.join(tmpdir, 'products.xml')
            if os.path.exists(xml_path):
                with open(xml_path, 'r', encoding='utf-8') as f:
                    return f.read()
        except (subprocess.CalledProcessError, FileNotFoundError):
            pass

        # Try 7z if available
        try:
            subprocess.run(['7z', 'e', '-y', f'-o{tmpdir}', cab_path, 'products.xml'],
                         capture_output=True, check=True)
            xml_path = os.path.join(tmpdir, 'products.xml')
            if os.path.exists(xml_path):
                with open(xml_path, 'r', encoding='utf-8') as f:
                    return f.read()
        except (subprocess.CalledProcessError, FileNotFoundError):
            pass

        # Last resort: look for XML in raw CAB data
        with open(cab_path, 'rb') as f:
            cab_data = f.read()
            xml_start = cab_data.find(b'<?xml')
            if xml_start != -1:
                xml_end = cab_data.find(b'</Products>', xml_start)
                if xml_end != -1:
                    xml_end += len(b'</Products>')
                    return cab_data[xml_start:xml_end].decode('utf-8')

    raise ValueError("Could not extract products.xml - install cabextract: brew install cabextract (macOS) or apt install cabextract (Ubuntu)")


def main():
    # Check tools first
    check_tools()

    print("\nFetching Microsoft catalog...")

    # Download CAB
    cab_url = "https://go.microsoft.com/fwlink/?LinkId=2156292"
    with tempfile.NamedTemporaryFile(suffix='.cab', delete=False) as tmp:
        download_file(cab_url, tmp.name, "Catalog")
        cab_path = tmp.name

    # Extract and parse XML
    try:
        xml_content = extract_xml_from_cab(cab_path)
        root = ET.fromstring(xml_content)
    finally:
        os.unlink(cab_path)

    print("Finding Enterprise N edition...")

    # Find Enterprise N
    found = None
    for file_elem in root.findall(".//File"):
        lang = file_elem.find("LanguageCode")
        edition = file_elem.find("Edition")
        arch = file_elem.find("Architecture")

        if (lang is not None and lang.text == "en-us" and
            edition is not None and edition.text == "EnterpriseN" and
            arch is not None and arch.text == "x64"):

            found = {
                'url': file_elem.find("FilePath").text,
                'size': int(file_elem.find("Size").text) / (1024**3)
            }
            break

    if not found:
        print("Enterprise N not found in catalog")
        sys.exit(1)

    print(f"Found Enterprise N ({found['size']:.1f} GB)")

    # Check if already downloaded
    if os.path.exists('win.esd'):
        print("✓ win.esd already exists, skipping download")
    else:
        print("Downloading ESD...")
        download_file(found['url'], 'win.esd', "Enterprise N ESD")
        print("✓ Downloaded: win.esd")

    # Convert ESD to WIM
    print("\nConverting ESD to WIM...")

    # Export all images to WIM
    print("Exporting images...")
    result = subprocess.run(['wimlib-imagex', 'export', 'win.esd', 'all', 'win.wim'],
                          capture_output=True, text=True)

    if result.returncode == 0:
        print("✓ Created win.wim")
        print("\n⚠️  NOTE: This is NOT a bootable ISO!")
        print("To make it bootable you need Windows boot files.")
        print("See README.md for options.")
    else:
        print(f"Error converting ESD: {result.stderr}")


if __name__ == '__main__':
    main()