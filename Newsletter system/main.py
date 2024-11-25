from flask import Flask, request, render_template, redirect, url_for, session
import MySQLdb
import random
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import schedule
import time
from threading import Thread
import requests
import re
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv



app = Flask(__name__)

load_dotenv(".env")

print("FLASK_SECRET_KEY:", os.getenv('FLASK_SECRET_KEY'))
print("EMAIL_ADDRESS:", os.getenv('EMAIL_USER'))

app.secret_key = os.getenv('FLASK_SECRET_KEY')

db = MySQLdb.connect(
    host=os.getenv('DB_HOST'),
    user=os.getenv('DB_USER'),
    passwd=os.getenv('DB_PASS'),
    db=os.getenv('DB_NAME')
)

EMAIL_ADDRESS = os.getenv('EMAIL_USER')
EMAIL_PASSWORD = os.getenv('EMAIL_PASS')

RECAPTCHA_SECRET_KEY = os.getenv('RECAPTCHA_SECRET')

def is_valid_email(email):
    email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(email_regex, email) is not None


def send_email_template(email, subject, body_html):
    msg = MIMEMultipart()
    msg['From'] = EMAIL_ADDRESS
    msg['To'] = email[0]
    msg['Subject'] = subject
    msg.attach(MIMEText(body_html, 'html'))

    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            server.sendmail(EMAIL_ADDRESS, email, msg.as_string())
            print(f"Email sent to {email}")
    except Exception as e:
        print(f"Error sending email to {email}: {e}")
        return False
    return True


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/subscribe', methods=['POST'])
def subscribe():
    email = request.form.get('email')
    captcha_response = request.form.get('g-recaptcha-response')

    if not is_valid_email(email):
        return render_template('invalid_email.html', email=email)

    verify_url = "https://www.google.com/recaptcha/api/siteverify"
    data = {'secret': RECAPTCHA_SECRET_KEY, 'response': captcha_response}
    response = requests.post(verify_url, data=data)
    result = response.json()

    if not result.get('success'):
        return render_template('captcha_failed.html')

    cursor = db.cursor()
    cursor.execute("SELECT * FROM subscribers WHERE email = %s", (email,))
    if cursor.fetchone():
        cursor.close()
        return render_template('already_subscribed.html')

    cursor.execute("INSERT INTO subscribers (email, last_interaction_date) VALUES (%s, %s)", (email, datetime.now()))
    db.commit()
    cursor.close()

    send_welcome_email(email)

    return render_template('success.html')


def send_welcome_email(email):
    subject = "Welcome to Gamblin Bourghirs!"
    body_html = """
    <html>
    <body style="font-family: Arial, sans-serif; background-color: #f4f4f9; padding: 20px; margin: 0;">
        <div style="max-width: 600px; margin: auto; background-color: #ffffff; padding: 30px; border-radius: 8px; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);">
            <div style="text-align: center; margin-bottom: 20px;">
                <img src="Gamblin_Bourghirs_Transparent.png" alt="Gamblin Bourghirs Logo" style="max-width: 100px;">
            </div>
            <h1 style="text-align: center; color: #BF5B04; margin-bottom: 10px;">Welcome to the Family!</h1>
            <p style="color: #333333; font-size: 16px; line-height: 1.6; text-align: center;">
                Hello, and welcome to the Gamblin Bourghirs community! We're thrilled to have you on board.
            </p>
            <div style="background-color: #FFEDD5; padding: 15px; margin: 20px 0; border-radius: 5px; text-align: center;">
                <p style="color: #BF5B04; font-size: 18px; font-weight: bold; margin: 0;">🎉 Exclusive deals, exciting news, and delicious updates await you!</p>
            </div>
            <p style="color: #555555; font-size: 14px; line-height: 1.6; text-align: center;">
                Stay tuned for our latest updates, mouthwatering recipes, and amazing discounts sent straight to your inbox. 
                Check out our website for more exciting content.
            </p>
            <div style="text-align: center; margin: 20px 0;">
                <a href="http://epost.it4.iktim.no" style="background-color: #BF5B04; color: #ffffff; padding: 10px 20px; text-decoration: none; font-size: 16px; border-radius: 5px;">Visit Our Website</a>
            </div>
            <hr style="border: none; border-top: 1px solid #ddd; margin: 20px 0;">
            <p style="color: #777777; font-size: 12px; text-align: center; margin: 0;">
                You received this email because you subscribed to Gamblin Bourghirs. If you didn't subscribe, you can <a href="http://epost.it4.iktim.no/unsubscribe?email={email}" style="color: #BF5B04;">unsubscribe here</a>.
            </p>
        </div>
    </body>
    </html>
    """
    return send_email_template(email, subject, body_html)


@app.route('/admin', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username == os.getenv('ADMIN_USER') and password == os.getenv('ADMIN_PASS'):
            session['admin_logged_in'] = True
            return redirect('/admin/dashboard')
        return "Invalid Credentials", 401
    return render_template('admin_login.html')


@app.route('/admin/dashboard')
def admin_dashboard():
    if not session.get('admin_logged_in'):
        return redirect('/admin')
    cursor = db.cursor()
    cursor.execute("SELECT email FROM subscribers")
    email_list = cursor.fetchall()
    cursor.close()
    return render_template('admin_dashboard.html', email_list=email_list)


@app.route('/admin/send-email', methods=['POST'])
def admin_send_email():
    if not session.get('admin_logged_in'):
        return redirect('/admin')
    recipients = request.form.getlist('recipients')
    subject = request.form['subject']
    body = request.form['body']

    for email in recipients:
        send_email_template(email, subject, body)

    return "Emails sent successfully!"


@app.route('/unsubscribe', methods=['GET'])
def unsubscribe():
    email = request.args.get('email')
    cursor = db.cursor()
    try:
        cursor.execute("DELETE FROM subscribers WHERE email = %s", (email,))
        db.commit()
        return render_template('unsubscribe.html', email=email)
    except Exception as e:
        db.rollback()
        return f"An error occurred: {e}", 500
    finally:
        cursor.close()


def send_we_miss_you_emails():
    cursor = db.cursor()
    cursor.execute("SELECT email FROM subscribers WHERE last_active < NOW() - INTERVAL 14 DAY")
    users = cursor.fetchall()

    subject = "We Miss You at Gamblin Bourghirs!"
    for user in users:
        email = user[0] 
        body_html = f"""
    <html>
    <body style="font-family: Arial, sans-serif; background-color: #f4f4f9; padding: 20px;">
        <div style="max-width: 600px; margin: auto; background-color: #ffffff; padding: 30px; border-radius: 8px; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);">
            <h2 style="text-align: center; color: #082040;">We Miss You! 🎉 Spin the Wheel at Gamblin Bourghirs!</h2>
            <p style="color: #555555; font-size: 16px;">It’s been a while since we’ve seen you at Gamblin Bourghirs, and we’re starting to feel the void! 🥺</p>
            <p style="color: #555555; font-size: 16px;">We miss your energy, your appetite, and the excitement you bring. That’s why we’re inviting you to come back and enjoy some delicious fun with us. And guess what?</p>
            
            <h3 style="text-align: center; color: #07F2F2;">The Wheel of Fortune is back! 🎡✨</h3>
            <p style="color: #555555; font-size: 16px; text-align: center;">
                Spin the wheel for a chance to win amazing prizes like:
            </p>
            <ul style="color: #555555; font-size: 16px; list-style: none; padding-left: 0; text-align: center;">
                <li style="color: #D9B036;">🍔 <strong>Free Burgers</strong></li>
                <li style="color: #D9B036;">🎟️ <strong>Exclusive Discounts</strong></li>
                <li style="color: #D9B036;">🍹 <strong>Complimentary Drinks</strong></li>
            </ul>
            
            <p style="color: #555555; font-size: 16px;">Don’t let your luck pass you by! Drop by Gamblin Bourghirs this week and let the wheel decide your treat.</p>
            <p style="color: #555555; font-size: 16px;">We can’t wait to see your smiling face again! 😊</p>

            <div style="text-align: center; margin-top: 20px;">
                <a href="http://epost.it4.iktim.no" style="background-color: #BF5B04; color: #ffffff; padding: 10px 20px; text-decoration: none; border-radius: 5px;">Come Back & Spin the Wheel!</a>
            </div>
            
            <p style="color: #777777; font-size: 14px; text-align: center; margin-top: 30px;">Your friends at Gamblin Bourghirs 🍔🕺🎰</p>

            <p style="color: #777777; font-size: 14px; text-align: center;">P.S. Come hungry—and ready to win big! 🍀</p>
            
            <hr style="margin: 30px 0; border: 1px solid #8C2804;">
            
            <p style="color: #777777; font-size: 14px; text-align: center;">If you wish to unsubscribe from our newsletter, click the link below:</p>
            <p style="text-align: center;">
                <a href="http://epost.it4.iktim.no/unsubscribe?email={email}" style="color: #8C2804; text-decoration: none;">Unsubscribe</a>
            </p>
            <p style="color: #777777; font-size: 14px; text-align: center;">Gamblin Bourghirs &copy; 2024 | All Rights Reserved</p>
        </div>
    </body>
    </html>
    """
        send_email_template(email, subject, body_html)

    cursor.close()



def generate_coupon():
    norwegian_words = ["BURGER", "TOMATO", "KETCHUP", "SALAD", "FRIES", "BUNS", "BEEF", "ICECREAM", ""]
    word = random.choice(norwegian_words)
    numbers = ''.join(random.choices("0123456789", k=2))
    return f"{word}{numbers}"


def send_coupon_emails():
    cursor = db.cursor()
    cursor.execute("SELECT email FROM subscribers")
    users = cursor.fetchall()

    coupon = generate_coupon()
    subject = "Your Exclusive Coupon!"
    for user in users:
        email = user[0]
        body_html = f"""
        <html>
        <body style="font-family: Arial, sans-serif; background-color: #f4f4f9; padding: 20px;">
            <div style="max-width: 600px; margin: auto; background-color: #ffffff; padding: 30px; border-radius: 8px; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);">
                <h2 style="text-align: center; color: #082040;">Your Exclusive Coupon is Here!</h2>
                <p style="color: #555555; font-size: 16px;">Hi there,</p>
                <p style="color: #555555; font-size: 16px;">Thank you for being part of the Gamblin Bourghirs community! To show our appreciation, here’s an exclusive coupon just for you:</p>
                
                <div style="text-align: center; margin-top: 20px; padding: 15px; background-color: #07F2F2; color: #082040; font-size: 24px; font-weight: bold; border-radius: 5px;">
                    {coupon}
                </div>
                
                <p style="color: #555555; font-size: 16px; margin-top: 20px;">Don’t miss out on this special offer! Head over to our website to redeem your coupon now.</p>
                
                <div style="text-align: center; margin-top: 30px;">
                    <a href="http://epost.it4.iktim.no" style="background-color: #BF5B04; color: #ffffff; padding: 10px 20px; text-decoration: none; border-radius: 5px;">Visit Our Website</a>
                </div>
                
                <p style="color: #777777; font-size: 14px; text-align: center; margin-top: 30px;">If you wish to unsubscribe from our newsletter, click the link below:</p>
                <div style="text-align: center;">
                    <a href="http://epost.it4.iktim.no/unsubscribe?email={email}" style="color: #8C2804; font-size: 14px;">Unsubscribe</a>
                </div>
                
                <p style="color: #777777; font-size: 14px; text-align: center; margin-top: 30px;">Gamblin Bourghirs &copy; 2024 | All Rights Reserved</p>
            </div>
        </body>
        </html>
        """
        send_email_template(email, subject, body_html)

    cursor.close()



@app.route('/admin/send-coupon-emails', methods=['POST'])
def admin_send_coupon_emails():
    if not session.get('admin_logged_in'):
        return redirect('/admin')
    
    cursor = db.cursor()
    cursor.execute("SELECT email FROM subscribers")
    subscribers = cursor.fetchall()
    cursor.close()

    for email in subscribers:
        coupon = generate_coupon()
        subject = "Here's a Special Coupon for You!"
        body_html = f"""
    <html>
    <body style="font-family: Arial, sans-serif; background-color: #f4f4f9; padding: 20px;">
        <div style="max-width: 600px; margin: auto; background-color: #ffffff; padding: 30px; border-radius: 8px; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);">
            <h2 style="text-align: center; color: #082040;">Your Exclusive Coupon is Here!</h2>
            <p style="color: #555555; font-size: 16px;">Hi there,</p>
            <p style="color: #555555; font-size: 16px;">Thank you for being part of the Gamblin Bourghirs community! To show our appreciation, here’s an exclusive coupon just for you:</p>
            
            <div style="text-align: center; margin-top: 20px; padding: 15px; background-color: #07F2F2; color: #082040; font-size: 24px; font-weight: bold; border-radius: 5px;">
                {coupon}
            </div>
            
            <p style="color: #555555; font-size: 16px; margin-top: 20px;">Don’t miss out on this special offer! Head over to our website to redeem your coupon now.</p>
            
            <div style="text-align: center; margin-top: 30px;">
                <a href="http://epost.it4.iktim.no" style="background-color: #BF5B04; color: #ffffff; padding: 10px 20px; text-decoration: none; border-radius: 5px;">Visit Our Website</a>
            </div>
            
            <p style="color: #777777; font-size: 14px; text-align: center; margin-top: 30px;">If you wish to unsubscribe from our newsletter, click the link below:</p>
            <div style="text-align: center;">
                <a href="http://epost.it4.iktim.no/unsubscribe?email={email}" style="color: #8C2804; font-size: 14px;">Unsubscribe</a>
            </div>
            
            <p style="color: #777777; font-size: 14px; text-align: center; margin-top: 30px;">Gamblin Bourghirs &copy; 2024 | All Rights Reserved</p>
        </div>
    </body>
    </html>
    """
        send_email_template(email, subject, body_html)
    
    return f"Coupon emails sent successfully! code: {coupon}" , 200


@app.route('/admin/send-we-miss-you-emails', methods=['POST'])
def admin_send_we_miss_you_emails():
    if not session.get('admin_logged_in'):
        return redirect('/admin')
    
    cursor = db.cursor()
    cursor.execute("SELECT email FROM subscribers WHERE last_interaction_date IS NOT NULL AND DATEDIFF(NOW(), last_interaction_date) > 14")
    inactive_subscribers = cursor.fetchall()
    cursor.close()

    for email in inactive_subscribers:
        subject = "We Miss You!"
        body_html = f"""
    <html>
    <body style="font-family: Arial, sans-serif; background-color: #f4f4f9; padding: 20px;">
        <div style="max-width: 600px; margin: auto; background-color: #ffffff; padding: 30px; border-radius: 8px; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);">
            <h2 style="text-align: center; color: #082040;">We Miss You! 🎉 Spin the Wheel at Gamblin Bourghirs!</h2>
            <p style="color: #555555; font-size: 16px;">It’s been a while since we’ve seen you at Gamblin Bourghirs, and we’re starting to feel the void! 🥺</p>
            <p style="color: #555555; font-size: 16px;">We miss your energy, your appetite, and the excitement you bring. That’s why we’re inviting you to come back and enjoy some delicious fun with us. And guess what?</p>
            
            <h3 style="text-align: center; color: #07F2F2;">The Wheel of Fortune is back! 🎡✨</h3>
            <p style="color: #555555; font-size: 16px; text-align: center;">
                Spin the wheel for a chance to win amazing prizes like:
            </p>
            <ul style="color: #555555; font-size: 16px; list-style: none; padding-left: 0; text-align: center;">
                <li style="color: #D9B036;">🍔 <strong>Free Burgers</strong></li>
                <li style="color: #D9B036;">🎟️ <strong>Exclusive Discounts</strong></li>
                <li style="color: #D9B036;">🍹 <strong>Complimentary Drinks</strong></li>
            </ul>
            
            <p style="color: #555555; font-size: 16px;">Don’t let your luck pass you by! Drop by Gamblin Bourghirs this week and let the wheel decide your treat.</p>
            <p style="color: #555555; font-size: 16px;">We can’t wait to see your smiling face again! 😊</p>

            <div style="text-align: center; margin-top: 20px;">
                <a href="http://epost.it4.iktim.no" style="background-color: #BF5B04; color: #ffffff; padding: 10px 20px; text-decoration: none; border-radius: 5px;">Come Back & Spin the Wheel!</a>
            </div>
            
            <p style="color: #777777; font-size: 14px; text-align: center; margin-top: 30px;">Your friends at Gamblin Bourghirs 🍔🕺🎰</p>

            <p style="color: #777777; font-size: 14px; text-align: center;">P.S. Come hungry—and ready to win big! 🍀</p>
            
            <hr style="margin: 30px 0; border: 1px solid #8C2804;">
            
            <p style="color: #777777; font-size: 14px; text-align: center;">If you wish to unsubscribe from our newsletter, click the link below:</p>
            <p style="text-align: center;">
                <a href="http://epost.it4.iktim.no/unsubscribe?email={email}" style="color: #8C2804; text-decoration: none;">Unsubscribe</a>
            </p>
            <p style="color: #777777; font-size: 14px; text-align: center;">Gamblin Bourghirs &copy; 2024 | All Rights Reserved</p>
        </div>
    </body>
    </html>
    """
        send_email_template(email, subject, body_html)
    
    return '"We Miss You" emails sent successfully!', 200

# Scheduler
schedule.every().day.at("09:20").do(send_coupon_emails)


def run_scheduler():
    while True:
        schedule.run_pending()
        time.sleep(60)


if __name__ == "__main__":
    Thread(target=run_scheduler).start()
    app.run(port=3000, host="0.0.0.0")
