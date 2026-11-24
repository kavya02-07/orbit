"""
Generates synthetic PDF documentation for Orbit evaluation suite using PyMuPDF.
Creates 3 documents:
1. Billing_and_Refund_Policy.pdf
2. Account_and_Security_Guide.pdf
3. Technical_Troubleshooting_Manual.pdf
"""
import os
from pathlib import Path
import fitz  # PyMuPDF

DOCS_DIR = Path("c:/orbit/backend/tests/sample_docs")
DOCS_DIR.mkdir(parents=True, exist_ok=True)


def create_billing_pdf():
    doc = fitz.open()
    
    # Page 1
    p1 = doc.new_page()
    text1 = """Orbit Knowledge Base - Billing and Refund Policy (Version 2.4)

1. Subscription Plans and Invoicing
Orbit offers Monthly ($29/month) and Annual ($290/year) subscription tiers. Subscriptions renew automatically on the billing date each month. Invoices are emailed within 24 hours of successful payment. Users can download tax receipts directly from the Account Settings page under Billing.

2. Refund Policy
We offer a full 14-day money-back guarantee for all new subscriptions. If you are unsatisfied with Orbit within the first 14 days of your initial purchase, contact support at billing@orbit.dev to request a full refund. Refunds typically take 3 to 5 business days to appear on your bank statement.

3. Prorated Upgrades and Downgrades
When upgrading your subscription plan mid-cycle, the remaining balance of your existing plan is credited towards the new plan immediately. When downgrading, the new rate takes effect at the beginning of the next billing cycle. No partial refunds are issued for mid-cycle downgrades.
"""
    p1.insert_text((50, 60), text1, fontsize=11)

    # Page 2
    p2 = doc.new_page()
    text2 = """Orbit Knowledge Base - Billing and Refund Policy (Page 2)

4. Payment Failures and Grace Period
If a subscription renewal charge fails due to an expired card or insufficient funds, our system automatically re-attempts payment after 3, 5, and 7 days. Your account enters a 7-day grace period during which services remain active. If payment is not resolved after 7 days, the account is temporarily suspended.

5. Cancellation and Account Closure
You may cancel your subscription at any time through the dashboard or by submitting a cancellation ticket. Cancellation stops upcoming automated renewals immediately. You will retain access until the end of the current paid billing period. No further charges will occur after cancellation.
"""
    p2.insert_text((50, 60), text2, fontsize=11)
    
    file_path = DOCS_DIR / "Billing_and_Refund_Policy.pdf"
    doc.save(str(file_path))
    doc.close()
    print(f"Created {file_path}")


def create_security_pdf():
    doc = fitz.open()
    
    # Page 1
    p1 = doc.new_page()
    text1 = """Orbit Knowledge Base - Account and Security Guide (Version 1.8)

1. Two-Factor Authentication (2FA)
Orbit enforces optional Two-Factor Authentication via TOTP apps including Google Authenticator, Authy, and 1Password. To enable 2FA, navigate to Settings > Security > Enable 2FA, scan the QR code with your authenticator application, and enter the 6-digit confirmation code. Always save your emergency backup codes in a secure location.

2. Password Requirements and Reset Process
Passwords must be at least 8 characters long and contain a combination of letters, numbers, and symbols. If you forget your password, click 'Forgot Password' on the sign-in screen. A secure single-use password reset link will be sent to your registered email address, valid for 30 minutes.

3. Account Lockout and Brute-force Prevention
To protect against brute-force attacks, user accounts are temporarily locked after 5 consecutive failed login attempts. The lockout duration is 15 minutes. Users can wait for the timer to expire or contact security@orbit.dev with identity verification to unlock immediately.
"""
    p1.insert_text((50, 60), text1, fontsize=11)

    # Page 2
    p2 = doc.new_page()
    text2 = """Orbit Knowledge Base - Account and Security Guide (Page 2)

4. Session Management and Token Expiration
Orbit uses JSON Web Tokens (JWT) for API authentication. Access tokens expire after 60 minutes of inactivity. Logging out from the dashboard invalidates the current session on that device. You can terminate all active sessions across all devices from Settings > Security > Revoke All Sessions.

5. Data Privacy and GDPR Compliance
Orbit complies with GDPR and CCPA privacy regulations. Your uploaded documentation is encrypted at rest using AES-256 and in transit via TLS 1.3. You may request an export of all your stored data or request complete account erasure by contacting privacy@orbit.dev.
"""
    p2.insert_text((50, 60), text2, fontsize=11)
    
    file_path = DOCS_DIR / "Account_and_Security_Guide.pdf"
    doc.save(str(file_path))
    doc.close()
    print(f"Created {file_path}")


def create_technical_pdf():
    doc = fitz.open()
    
    # Page 1
    p1 = doc.new_page()
    text1 = """Orbit Knowledge Base - Technical Troubleshooting Manual (Version 3.1)

1. System Requirements and Supported Formats
Orbit supports PDF files up to 50 MB in size. Documents must contain extractable text; scanned image-only PDFs without OCR are not supported. Supported browsers include Google Chrome 110+, Mozilla Firefox 115+, Microsoft Edge 110+, and Safari 16+.

2. PDF Upload Troubleshooting
If a document fails during upload:
a) Ensure the file has a .pdf extension and is smaller than 50 MB.
b) Verify the PDF is not password-protected or corrupted.
c) Check that the file contains actual text rather than scanned images.
d) Ensure your network connection remains uninterrupted during the upload process.

3. Vector Search and Indexing Details
Orbit indexes document chunks using the all-MiniLM-L6-v2 embedding model generating 384-dimensional dense vectors. Vectors are stored in a FAISS inner-product index with cosine similarity normalization. Chunks are generated using a 500-word window with a 50-word overlap to ensure semantic continuity across chunk boundaries.
"""
    p1.insert_text((50, 60), text1, fontsize=11)

    file_path = DOCS_DIR / "Technical_Troubleshooting_Manual.pdf"
    doc.save(str(file_path))
    doc.close()
    print(f"Created {file_path}")


if __name__ == "__main__":
    create_billing_pdf()
    create_security_pdf()
    create_technical_pdf()
    print("All evaluation documents generated successfully.")
