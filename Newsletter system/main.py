from flask import Flask, request, render_template, redirect, url_for
import MySQLdb
import random
import smtplib
from email.mime.text import MIMEText
import schedule
import time
from threading import Thread
import requests



app = Flask(__name__)




db = MySQLdb.connect(
    host="localhost",
    user="root",
    passwd="markus",
    db="newsLetterDatabase"
)


def send_welcome_email(email):
    subject = "Thank You for Signing Up!"
    message = f"""
    Thank you for signing up for our newsletter! We're excited to have you with us.
    
    If you wish to unsubscribe, click the link below:
    http://epost.it4.iktim.no/unsubscribe?email={email}
    """

    msg = MIMEText(message)
    msg["Subject"] = subject
    msg["From"] = "gamblinbourghirs@gmail.com"
    msg["To"] = email

    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login("gamblinbourghirs@gmail.com", "xnrf lhwp nlee wjta")
            server.sendmail("gamblinbourghirs@gmail.com", email, msg.as_string())
            print(f"Welcome email sent to {email}")
    except Exception as e:
        print(f"Failed to send welcome email to {email}: {str(e)}")




@app.route('/')
def index():
    return render_template('index.html')


import requests

@app.route('/subscribe', methods=['POST'])
def subscribe():
    email = request.form.get('email')
    captcha_response = request.form.get('g-recaptcha-response')

    
    secret_key = "6Ley3H8qAAAAAMOQtIgxe-AJKkGO_1ZepRKW7fZS"
    verify_url = "https://www.google.com/recaptcha/api/siteverify"
    data = {'secret': secret_key, 'response': captcha_response}
    response = requests.post(verify_url, data=data)
    result = response.json()

    if not result.get('success'):
        return """
        <html>
        <body>
            <h1>CAPTCHA Failed</h1>
            <p>Please complete the CAPTCHA and try again.</p>
        </body>
        </html>
        """

    cursor = db.cursor()
    query = "INSERT INTO subscribers (email) VALUES (%s)"
    try:
        cursor.execute(query, (email,))
        db.commit()
        return """
        <html>
        <body>
            <h1>Thank you for subscribing!</h1>
        </body>
        </html>
        """
    except Exception as e:
        db.rollback()
        return f"An error occurred: {str(e)}", 500
    finally:
        cursor.close()



@app.route('/unsubscribe', methods=['GET'])
def unsubscribe():
    email = request.args.get('email')
    cursor = db.cursor()
    query = "DELETE FROM subscribers WHERE email = %s"
    try:
        cursor.execute(query, (email,))
        db.commit()
        return f"""
        <html>
        <body>
            <h1>You've been unsubscribed</h1>
            <p>We're sorry to see you go. If this was a mistake, feel free to sign up again!</p>
            <a href="http://epost.it4.iktim.no">Go here to resubscribe!</a>
        </body>
        </html>
        """
    except Exception as e:
        db.rollback()
        return f"An error occurred: {str(e)}", 500
    finally:
        cursor.close()


def generate_coupon():
    norwegian_words = ['BURGER', 'BIFF', 'SALAT', 'TOMAT', 'OST']
    word = random.choice(norwegian_words)
    numbers = random.randint(10, 99)
    return f"{word}{numbers}"


def send_coupon(email):
    coupon = generate_coupon()
    subject = "Your Exclusive Coupon"
    message = f"""
    Here is your exclusive coupon: {coupon}
    
    If you wish to unsubscribe from our newsletter, click the link below:
    http://epost.it4.iktim.no/unsubscribe?email={email}
    """

    msg = MIMEText(message)
    msg["Subject"] = subject
    msg["From"] = "gamblinbourghirs@gmail.com"
    msg["To"] = email

    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login("gamblinbourghirs@gmail.com", "xnrf lhwp nlee wjta")
            server.sendmail("gamblinbourghirs@gmail.com", email, msg.as_string())
            print(f"Coupon email sent to {email}")
    except Exception as e:
        print(f"Failed to send coupon email to {email}: {str(e)}")



def weekly_coupon_task():
    cursor = db.cursor()
    cursor.execute("SELECT email FROM subscribers")
    subscribers = cursor.fetchall()
    cursor.close()

    for (email,) in subscribers:
        send_coupon(email)

schedule.every().friday.at("09:24").do(weekly_coupon_task)


def run_scheduler():
    while True:
        schedule.run_pending()
        time.sleep(60)


if __name__ == "__main__":
    Thread(target=run_scheduler).start()
    app.run(port=3000, host="0.0.0.0")
