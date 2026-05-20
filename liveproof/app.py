from flask import Flask, render_template, request, jsonify, session
import smtplib, ssl, random, re, os, base64, io, math
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from models import init_db, save_verified_user
from PIL import Image
import numpy as np
import cv2
from mediapipe.python.solutions import face_mesh

app = Flask(__name__)
app.secret_key = "liveproof-secret-key-change-me"

SMTP_SERVER   = "smtp.gmail.com"
SMTP_PORT     = 465
SENDER_EMAIL  = os.environ.get("SENDER_EMAIL", "your_email@gmail.com")
SENDER_PASS   = os.environ.get("SENDER_PASS",  "your_app_password")

init_db()

def send_otp_email(to_email: str, otp: str, name: str) -> None:
    msg = MIMEMultipart("alternative")
    msg["Subject"] = "Your LiveProof OTP Code"
    msg["From"]    = f"LiveProof Authority <{SENDER_EMAIL}>"
    msg["To"]      = to_email
    html = f"<p>Hello {name}, your OTP is <b>{otp}</b>. It expires in 5 minutes.</p>"
    msg.attach(MIMEText(html, "html"))
    ctx = ssl.create_default_context()
    with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT, context=ctx) as server:
        server.login(SENDER_EMAIL, SENDER_PASS)
        server.sendmail(SENDER_EMAIL, to_email, msg.as_string())

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/send-otp", methods=["POST"])
def send_otp():
    data = request.get_json(force=True)
    name, aadhaar, email = data.get("name","").strip(), data.get("aadhaar","").strip(), data.get("email","").strip()
    if not re.fullmatch(r"\d{12}", aadhaar):
        return jsonify(success=False, message="Aadhaar must be 12 digits"), 400
    otp = f"{random.randint(0, 999999):06d}"
    session.update({"otp":otp,"otp_email":email,"otp_name":name,"otp_aadhaar":aadhaar,
                    "otp_expiry":(datetime.utcnow()+timedelta(minutes=5)).isoformat()})
    send_otp_email(email, otp, name)
    return jsonify(success=True, message=f"OTP sent to {email}")

@app.route("/verify-otp", methods=["POST"])
def verify_otp():
    data = request.get_json(force=True)
    if datetime.utcnow() > datetime.fromisoformat(session.get("otp_expiry")):
        return jsonify(success=False, message="OTP expired"), 400
    if data.get("otp") != session.get("otp"):
        return jsonify(success=False, message="Incorrect OTP"), 400
    session["verified_user"] = {"name":session["otp_name"],"aadhaar":session["otp_aadhaar"],"email":session["otp_email"]}
    return jsonify(success=True, message="OTP verified", redirect="/verify")

@app.route("/verify")
def verify_page():
    return render_template("verify.html")

@app.route("/liveness-check", methods=["POST"])
def liveness_check():
    data = request.get_json(force=True)
    frame_b64 = data.get("frame")
    img = Image.open(io.BytesIO(base64.b64decode(frame_b64.split(",")[1])))
    frame = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)

    with face_mesh.FaceMesh(static_image_mode=False,max_num_faces=1,refine_landmarks=True,
                            min_detection_confidence=0.5,min_tracking_confidence=0.5) as fm:
        results = fm.process(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        if not results.multi_face_landmarks:
            return jsonify(success=False, message="No face detected")

        landmarks = results.multi_face_landmarks[0].landmark

        def dist(i,j): return math.dist([landmarks[i].x,landmarks[i].y],[landmarks[j].x,landmarks[j].y])
        left_eye,right_eye=[33,160,158,133,153,144],[362,385,387,263,373,380]
        ear_left=(dist(left_eye[1],left_eye[5])+dist(left_eye[2],left_eye[4]))/(2.0*dist(left_eye[0],left_eye[3]))
        ear_right=(dist(right_eye[1],right_eye[5])+dist(right_eye[2],right_eye[4]))/(2.0*dist(right_eye[0],right_eye[3]))
        ear=(ear_left+ear_right)/2.0

        # Head turn check (nose x position)
        nose_x = landmarks[1].x
        if ear < 0.20:
            return jsonify(success=True, message="Blink detected → Live user")
        elif nose_x < 0.45 or nose_x > 0.55:
            return jsonify(success=True, message="Head turn detected → Live user")
        else:
            return jsonify(success=False, message="No blink/head movement → Possible spoof")

@app.route("/liveness-success", methods=["POST"])
def liveness_success():
    user = session.get("verified_user")
    if not user: return jsonify(success=False, message="No verified user"), 400
    save_verified_user(user["name"], user["aadhaar"], user["email"])
    session.clear()
    return jsonify(success=True, message="Liveness verified and user saved")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8084, debug=True)
