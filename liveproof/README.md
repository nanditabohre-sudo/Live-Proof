# LiveProof Authority — Minor Project

Aadhaar-style credential authentication gateway with **Email OTP** verification.

## Files (only 3!)
- `app.py` — Flask backend (sends OTP via Python's built-in `smtplib`)
- `templates/index.html` — frontend UI
- `README.md` — this file

## Setup

1. Install Flask:
   ```
   pip install flask
   ```

2. Configure your Gmail in `app.py` (or use environment variables):
   - Generate an **App Password**: https://myaccount.google.com/apppasswords
   - Replace `SENDER_EMAIL` and `SENDER_PASS` in `app.py`.

3. Run:
   ```
   python app.py
   ```

4. Open: http://localhost:8084

## Flow
1. Enter Name + 12-digit Aadhaar + Email → click **Send OTP**
2. Check your email for the 6-digit OTP
3. Enter OTP → click **Verify OTP**

## Notes
- OTP is valid for 5 minutes.
- Uses only built-in Python email APIs (`smtplib`, `email`) — no third-party email service.
- Aadhaar is validated as 12 digits but not actually verified with UIDAI (this is a demo/minor project).
