# Gamblin Bourghirs Newsletter System

A perfectly working newsletter subscription system created for a mock website called Gamblin Bourghirs with a burger theme

## Features

- **User Subscription**: Visitors can sign up for the newsletter with their email, protected by reCAPTCHA validation.
- **Welcome Email**: A beautifully formatted HTML welcome email is automatically sent after a successful subscription.
- **Automatic Emails**:
	- **Coupons**: Regularly scheduled coupon emails are sent to all subscribers.
	- **We Miss You**: Subscribers who haven't interacted within a given timeframe receive a “We Miss You” email, encouraging them to return.
- **Admin Dashboard**:
	 - Secure login for admins.
	 - View the subscriber list.
	 - Send custom emails to selected subscribers.
	 - Manually trigger sending coupons and "We Miss You" emails.
- **Unsubscribe Functionality**: Users can easily unsubscribe at any time, ensuring compliance and good user experience.
## Requirements
- **Python 3.7+**
- **MySQL Database**
- **Gmail Account (or another SMTP-compatible email provider)**
- **[python-dotenv](https://pypi.org/project/python-dotenv/)**
- **[schedule](https://pypi.org/project/schedule/)**
- **[requests](https://pypi.org/project/requests/)**
- **[MySQLdb](https://pypi.org/project/mysqlclient/) (mysqlclient)**

## Installation

1. **Clone the repository**:
	```git clone https://github.com/yourusername/gamblin-bourghirs-newsletter.git cd gamblin-bourghirs-newsletter```
2. **Install dependencies**:
	```pip install -r requirements.txt```
3. **Environment Variables**: Create a .env file in the project root:
```arduino
FLASK_SECRET_KEY=your_secret_key
EMAIL_ADDRESS=your_email@gmail.com 
EMAIL_PASSWORD=your_app_password 
RECAPTCHA_SECRET_KEY=your_recaptcha_secret_key
``` 
4. **Database Setup**:
- Ensure MySQL is running and create the ```newsLetterDatabase``` database:
	```sql 
	CREATE DATABASE newsLetterDatabase;	
	USE newsLetterDatabase;
	```
## Admin Credentials

- Default credentials are defined in the code:
    - Username: `markus`
    - Password: `secret`

Change these for security in production.

## Running the Application
```bash
python main.py
```

- Access the site at: http://localhost:3000
- The admin panel is accessible at http://localhost:3000/admin


## Email and Scheduling

- The system uses `smtplib` to send emails via your provided Gmail account.
- Coupon and "We Miss You" emails are scheduled using `schedule` and run in a background thread.
- Adjust the scheduling times in the code to meet your needs.

## Customization

- Update HTML templates in `templates/` directory for branding and styling changes.
- Adjust the logic in `main.py` for different intervals, email formats, or additional features.

## Troubleshooting

- **.env Not Loading**: Ensure you run `pip install python-dotenv` and call `load_dotenv()` before accessing environment variables.
- **SMTP Errors**: Check your Gmail account security settings. Consider using an App Password with 2FA enabled.
- **Database Errors**: Verify your MySQL credentials and database schema.

## License

This project is licensed under the MIT License. See the LICENSE file for details.
