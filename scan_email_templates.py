"""
Follow tracking redirect URLs from J&T E-Invoice email to discover real download URLs.
Also examine VTP email attachments/links for comparison.
"""
import sys
import os
import requests
from urllib.parse import urlparse

project_root = r"d:\TOOL AI\TOOL_AUTO_DOWNLOAD_VAT\ext_auto_load_mail"
sys.path.insert(0, project_root)
os.chdir(project_root)

from src.gmail_client import GmailClient
from bs4 import BeautifulSoup


def follow_redirect(url, label=""):
    """Follow redirect chain, show each hop."""
    print(f"\n  [{label}] Following redirect chain:")
    print(f"    Start: {url[:100]}...")
    
    try:
        resp = requests.get(url, allow_redirects=False, timeout=10)
        hop = 1
        while resp.is_redirect or resp.status_code in (301, 302, 303, 307, 308):
            location = resp.headers.get("Location", "")
            print(f"    Hop {hop}: {resp.status_code} → {location[:120]}")
            resp = requests.get(location, allow_redirects=False, timeout=10)
            hop += 1
        
        print(f"    Final: {resp.status_code} | Content-Type: {resp.headers.get('Content-Type', '?')}")
        print(f"    Final URL: {resp.url[:120] if hasattr(resp, 'url') else 'N/A'}")
        print(f"    Content-Length: {resp.headers.get('Content-Length', len(resp.content))} bytes")
        
        # If it's HTML, show title
        ct = resp.headers.get("Content-Type", "")
        if "html" in ct:
            soup = BeautifulSoup(resp.text, "lxml")
            title = soup.title.string if soup.title else "(no title)"
            print(f"    HTML Title: {title}")
            # Show first 300 chars of text
            text = soup.get_text(strip=True)[:300]
            print(f"    Preview: {text[:200]}")
        
        return resp
        
    except Exception as e:
        print(f"    Error: {e}")
        # Try with full redirect following
        try:
            resp = requests.get(url, allow_redirects=True, timeout=15)
            print(f"    (Full redirect) Final status: {resp.status_code}")
            print(f"    Final URL: {resp.url[:120]}")
            print(f"    Content-Type: {resp.headers.get('Content-Type', '?')}")
            print(f"    Content-Length: {resp.headers.get('Content-Length', len(resp.content))} bytes")
            ct = resp.headers.get("Content-Type", "")
            if "html" in ct:
                soup = BeautifulSoup(resp.text, "lxml")
                title = soup.title.string if soup.title else "(no title)"
                print(f"    HTML Title: {title}")
            return resp
        except Exception as e2:
            print(f"    Full redirect also failed: {e2}")
            return None


def main():
    client = GmailClient()
    client.authenticate()
    print(f"Authenticated: {client.user_email}\n")
    
    # ── Part 1: J&T E-Invoice links ──
    print("=" * 80)
    print("PART 1: J&T E-Invoice — Following tracking redirects")
    print("=" * 80)
    
    email_id = "19d116948dea2885"  # J&T invoice #31784
    body = client.get_email_body(email_id)
    
    # Parse HTML to get all links with context
    soup = BeautifulSoup(body, "lxml")
    links = soup.find_all("a", href=True)
    
    for i, link in enumerate(links):
        href = link.get("href", "")
        text = link.get_text(strip=True)
        
        # Skip mailto and empty
        if not href or href.startswith("mailto:"):
            continue
        
        # Get context (text before this link)
        prev = link.previous_sibling
        context = ""
        if prev:
            context = str(prev).strip()[-80:] if prev else ""
        
        print(f"\n  Link #{i+1}: text='{text[:40]}' | context='{context[:60]}'")
        
        # Only follow tracking URLs
        if "url3815.hq.jtexpress.vn" in href:
            follow_redirect(href, f"Link #{i+1}")
    
    # ── Part 2: VTP email for comparison ──
    print("\n\n" + "=" * 80)
    print("PART 2: VTP Invoice — Existing attachments & links")  
    print("=" * 80)
    
    # Search for VTP email
    vtp_emails = client.search_emails("Tổng công ty Cổ phần Bưu Chính Viettel", max_results=2)
    
    if vtp_emails:
        vtp = vtp_emails[0]
        print(f"  Subject: {vtp.subject}")
        print(f"  Date: {vtp.date}")
        
        # Attachments
        atts = client.get_attachments(vtp.id)
        print(f"  Attachments: {len(atts)}")
        for att in atts:
            print(f"    📎 {att.filename} ({att.mime_type}, {att.size} bytes)")
        
        # Body links
        vtp_body = client.get_email_body(vtp.id)
        vtp_soup = BeautifulSoup(vtp_body, "lxml")
        vtp_links = vtp_soup.find_all("a", href=True)
        for link in vtp_links:
            href = link.get("href", "")
            text = link.get_text(strip=True)
            if href and not href.startswith("mailto:"):
                print(f"    🔗 [{text[:40]}] → {href[:100]}")
                
                # Follow VTP links too
                if "viettelpost.vn" in href:
                    follow_redirect(href, "VTP link")
    else:
        print("  No VTP emails found.")
    
    # ── Part 3: J&T COD attachment ──
    print("\n\n" + "=" * 80)
    print("PART 3: J&T COD — Attachment details")
    print("=" * 80)
    
    cod_id = "19d1168526637969"  # J&T COD 20/03
    cod_atts = client.get_attachments(cod_id)
    print(f"  Attachments: {len(cod_atts)}")
    for att in cod_atts:
        print(f"    📎 {att.filename}")
        print(f"       Type: {att.mime_type}")
        print(f"       Size: {att.size} bytes")


if __name__ == "__main__":
    main()
