import os
from flask import Flask, render_template, request, jsonify
import razorpay
import smtplib
from email.mime.text import MIMEText

app = Flask(__name__)
# It's highly recommended to set your secret_key via an environment variable in production
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "your_default_secret_key_if_not_set_in_env")

# Correctly load environment variables for Razorpay and SMTP.
# These MUST be set in your deployment environment (e.g., Render, Heroku, or locally).
RAZORPAY_KEY_ID = os.environ.get("RAZORPAY_KEY_ID")
RAZORPAY_KEY_SECRET = os.environ.get("RAZORPAY_KEY_SECRET")

SMTP_EMAIL = os.environ.get("SMTP_EMAIL")
# For Gmail, use an App Password for SMTP_PASSWORD, not your main account password.
SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD")
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587

# Initialize Razorpay client with keys from environment variables
if RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET:
    client = razorpay.Client(auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET))
else:
    print("Warning: Razorpay API keys are not set. Payment functionality may not work.")
    client = None # Or raise an error, depending on desired behavior

@app.route('/')
def index1():
    # Pass the RAZORPAY_KEY_ID to the index1.html template
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

    if not client:
        return jsonify({'status': 'failed', 'message': 'Razorpay client not initialized. API keys missing.'})

    try:
        # Fetch payment details from Razorpay to verify status
        payment = client.payment.fetch(payment_id)
        if payment['status'] == 'captured':
            # Record the email of the paid user
            with open("paid_emails.txt", "a") as f:
                f.write(email + "\n")
            # Send success email to the user
            send_success_email(email)
            return jsonify({'status': 'success'})
        else:
            return jsonify({'status': 'failed', 'message': 'Payment not captured'})
    except Exception as e:
        print(f"Payment verification failed: {e}")
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
        print("Warning: SMTP credentials not set. Email cannot be sent.")
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
    # Set debug to False in a production environment for security
    app.run(debug=True)