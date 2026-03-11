"""Debug script — run directly to trace the full download pipeline."""
import sys, os, json
from pathlib import Path

# Make sure imports resolve from project root
sys.path.insert(0, str(Path(__file__).parent))

print("=== DEBUG RUN START ===")

# 1) Delete processed_emails.json if it exists
pef = Path("config/processed_emails.json")
if pef.exists():
    pef.unlink()
    print(f"[OK] Deleted {pef}")
else:
    print("[OK] No processed_emails.json to delete")

# 2) Load settings & rules
from src.gmail_client import GmailClient
from src.rule_engine import RuleEngine
from src.link_extractor import LinkExtractor
from src.file_downloader import FileDownloader

settings_path = Path("config/settings.json")
with open(settings_path, "r", encoding="utf-8") as f:
    settings = json.load(f)

output_dir = Path(settings.get("output_dir", "downloads"))
print(f"[OK] output_dir = {output_dir}")

# 3) Authenticate Gmail
gmail = GmailClient()
try:
    email_addr = gmail.authenticate()
    print(f"[OK] Gmail authenticated: {email_addr}")
except Exception as e:
    print(f"[FAIL] Gmail auth error: {e}")
    sys.exit(1)

# 4) Load rules
rule_engine = RuleEngine(config_path=Path("config/rules.json"))
rule_engine.load_rules()
rules = rule_engine.get_enabled_rules()
print(f"[OK] Loaded {len(rules)} enabled rules")

for rule in rules:
    query = rule.to_gmail_query()
    print(f"\n--- Rule: {rule.name} ---")
    print(f"  Query: {query}")
    print(f"  Output folder: {rule.output_folder}")

    # Effective output dir
    rf = Path(rule.output_folder)
    effective_dir = rf if rf.is_absolute() else output_dir / rule.output_folder
    print(f"  Effective dir: {effective_dir}")

    # Search emails
    emails = gmail.search_emails(query, max_results=rule.max_emails)
    print(f"  Found {len(emails)} emails")

    downloader = FileDownloader(output_dir=effective_dir, skip_duplicates=True)
    link_extractor = LinkExtractor()

    for i, email in enumerate(emails[:3]):  # Process first 3
        print(f"\n  Email #{i+1}: {email.subject[:60]}")
        print(f"    ID: {email.id}")

        # Attachments
        try:
            attachments = gmail.get_attachments(email.id)
            print(f"    Attachments: {len(attachments)}")
            for att in attachments:
                ext = Path(att.filename).suffix.lower()
                in_filter = ext in rule.attachment_extensions
                print(f"      [{ext}] {att.filename}  → in_filter={in_filter}")
                if rule.download_attachments and in_filter:
                    data, _ = gmail.download_attachment(email.id, att.id)
                    res = downloader.save_attachment(data, att.filename)
                    print(f"      SAVE result: {res.status.value} | {res.filepath}")
        except Exception as e:
            print(f"    Attachment error: {e}")

        # Bảng kê
        if rule.download_bang_ke:
            try:
                body = gmail.get_email_body(email.id)
                print(f"    Body length: {len(body) if body else 0}")
                if body:
                    url = link_extractor.extract_bang_ke_link(body)
                    print(f"    Bảng kê URL: {url or 'NOT FOUND'}")
                    if url:
                        res = downloader.download_from_url(url, subfolder="bang_ke")
                        print(f"    BANGKE result: {res.status.value} | {res.error_message or res.filepath}")
            except Exception as e:
                print(f"    Bảng kê error: {e}")

print("\n=== DEBUG RUN END ===")
