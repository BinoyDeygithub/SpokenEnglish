import os
from flask import Flask, render_template, request, jsonify
import razorpay
import smtplib
from email.mime.text import MIMEText
from dotenv import load_dotenv # Import load_dotenv for local development

# Load environment variables from .env file for local development
# In production (e.g., Render), these variables will be provided by the platform directly.
load_dotenv()

app = Flask(__name__)
# It's crucial to set FLASK_SECRET_KEY for session security.
# Get it from environment variables. Generate a strong random one for production.
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "a_super_secret_fallback_key_DO_NOT_USE_IN_PROD")

# Correctly load environment variables for Razorpay and SMTP
RAZORPAY_KEY_ID = os.environ.get("RAZORPAY_KEY_ID")
RAZORPAY_KEY_SECRET = os.environ.get("RAZORPAY_KEY_SECRET")

SMTP_EMAIL = os.environ.get("SMTP_EMAIL")
# For Gmail, use an App Password for SMTP_PASSWORD, not your main account password, for security.
SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD")
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587

# Initialize Razorpay client. Check if keys are available.
if RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET:
    client = razorpay.Client(auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET))
else:
    print("WARNING: Razorpay API keys are not set. Payment functionality may not work.")
    client = None # Set client to None if keys are missing

@app.route('/')
def index1():
    # Pass the RAZORPAY_KEY_ID to the index1.html template for any embedded payment forms (if any)
    return render_template('index1.html', key_id=RAZORPAY_KEY_ID)

@app.route('/payment')
def payment():
    # Pass the RAZORPAY_KEY_ID to the payment.html template
    return render_template('payment.html', key_id=RAZORPAY_KEY_ID)

@app.route('/verify', methods=['POST'])
def verify():
    data = request.get_json()
    payment_id = data.get('razorpay_payment_id')
    email = data.get('email', '')

    print(f"Received verification request for payment_id: {payment_id}, email: {email}")

    if not client:
        print("ERROR: Razorpay client not initialized. API keys missing.")
        return jsonify({'status': 'failed', 'message': 'Razorpay client not initialized. API keys missing.'})

    try:
        payment = client.payment.fetch(payment_id)
        print(f"Razorpay payment fetch response: {payment}") # Log the full payment object for debugging

        if payment['status'] == 'captured':
            print(f"Payment {payment_id} successfully CAPTURED.")
            # Record the email of the paid user
            with open("paid_emails.txt", "a") as f:
                f.write(email + "\n")
            send_success_email(email)
            return jsonify({'status': 'success'})
        else:
            print(f"Payment {payment_id} status is NOT captured. Current status: {payment['status']}")
            return jsonify({'status': 'failed', 'message': f"Payment not captured. Current status: {payment['status']}"})
    except Exception as e:
        print(f"Payment verification failed with exception: {e}")
        return jsonify({'status': 'failed', 'message': str(e)})

@app.route('/dashboard')
def dashboard():
    # This route will render the dashboard for successful payments
    return render_template('dashboard.html')

def send_success_email(to_email):
    subject = "✅ EnglishPr0 Course Access - Payment Successful"
    body = '''
Dear Student,

✅ Your payment was successful!

Here are your course access links:
📘 PDF Books: https://drive.google.com/drive/folders/1HNWohGqjIiy_TVEk_y710OrbDb0g-ae3
🎥 Video Lessons: https://drive.google.com/drive/folders/1EBzBgWNDUwv-gPvHZFO9pMP0Cs-e6hYU
📚 IELTS Pack: https://drive.google.com/drive/folders/1iqee_2QBbODOu8xis9BqPTOT0FHogzCi

Thanks for joining EnglishPr0!
'''
    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = SMTP_EMAIL
    msg['To'] = to_email

    if not SMTP_EMAIL or not SMTP_PASSWORD:
        print("WARNING: SMTP credentials not set. Email cannot be sent.")
        return

    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls() # Enable TLS encryption
            server.login(SMTP_EMAIL, SMTP_PASSWORD) # Log in to SMTP server
            server.sendmail(SMTP_EMAIL, to_email, msg.as_string()) # Send the email
            print(f"Email sent to {to_email}")
    except Exception as e:
        print(f"Failed to send email: {e}")

if __name__ == '__main__':
    # Set debug to False in a production environment for security and performance
    app.run(debug=True)
