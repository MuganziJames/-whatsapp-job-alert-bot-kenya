# 🤖 WhatsApp Job Alert Bot (Kenya MVP)

A comprehensive backend system that sends job alerts via WhatsApp using M-Pesa payments for credits. Built with Flask, Supabase, Twilio, and M-Pesa Daraja API.

## 🌟 Features

- **WhatsApp Integration**: Receive and send messages via Twilio WhatsApp API
- **Job Interest Selection**: Users select from 10 job categories (fundi, cleaner, tutor, etc.)
- **M-Pesa Payments**: Accept C2B payments via Paybill for job alert credits
- **Job Scraping**: Scrape latest jobs from Kenya job boards
- **Credit System**: 1 KES = 1 job alert credit
- **Duplicate Prevention**: Track sent jobs to avoid spam
- **Admin Broadcast**: Send jobs to all users with specific interests

## 📁 Project Structure

```
whatsapp-job-bot/
├── app.py              # Main Flask application
├── bot.py              # WhatsApp bot logic
├── db.py               # Supabase database functions
├── scraper.py          # Job scraping module
├── mpesa.py            # M-Pesa payment handling
├── register_url.py     # M-Pesa URL registration script
├── requirements.txt    # Python dependencies
├── .env                # Environment variables (create this)
└── README.md          # This file
```

## 🚀 Quick Start

### 1. Prerequisites

- Python 3.8+
- Supabase account
- Twilio account with WhatsApp API
- M-Pesa Daraja API credentials
- ngrok (for local testing)

### 2. Clone and Install

```bash
git clone <your-repo>
cd whatsapp-job-bot
pip install -r requirements.txt
```

### 3. Environment Setup

Create a `.env` file with your credentials:

```bash
# Supabase
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-supabase-anon-key

# Twilio
TWILIO_SID=AC...
TWILIO_TOKEN=your-twilio-token
TWILIO_WHATSAPP_NUMBER=whatsapp:+14155238886

# M-Pesa
MPESA_CONSUMER_KEY=your-consumer-key
MPESA_CONSUMER_SECRET=your-consumer-secret
MPESA_SHORTCODE=600000
MPESA_ENV=sandbox

# Flask
FLASK_ENV=development
FLASK_DEBUG=True
```

### 4. Database Setup

Create these tables in your Supabase database:

```sql
-- Users table
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    phone VARCHAR(20) UNIQUE NOT NULL,
    interest VARCHAR(50),
    balance INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Job alerts sent tracking
CREATE TABLE job_alerts_sent (
    id SERIAL PRIMARY KEY,
    phone VARCHAR(20) NOT NULL,
    job_id VARCHAR(100) NOT NULL,
    job_title TEXT,
    job_url TEXT,
    sent_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(phone, job_id)
);

-- Enable RLS (Row Level Security)
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE job_alerts_sent ENABLE ROW LEVEL SECURITY;

-- Create policies for authenticated access
CREATE POLICY "Allow all operations for authenticated users" ON users
FOR ALL USING (auth.role() = 'authenticated');

CREATE POLICY "Allow all operations for authenticated users" ON job_alerts_sent
FOR ALL USING (auth.role() = 'authenticated');
```

### 5. Register M-Pesa URLs

```bash
python register_url.py
```

Follow the prompts to register your webhook URLs with M-Pesa.

### 6. Start the Application

```bash
# For local development with ngrok
ngrok http 5000

# In another terminal
python app.py
```

### 7. Configure Twilio Webhook

Set your Twilio WhatsApp webhook URL to:

```
https://your-ngrok-url.ngrok.io/webhook
```

## 🔧 API Endpoints

### WhatsApp Webhook

- **POST** `/webhook` - Receive WhatsApp messages from Twilio

### M-Pesa Callbacks

- **POST** `/c2b/validate` - M-Pesa payment validation
- **POST** `/c2b/confirm` - M-Pesa payment confirmation

### Admin/Testing

- **GET** `/` - Health check
- **GET** `/test` - Test database connectivity
- **POST** `/admin/broadcast` - Broadcast jobs to users

## 📱 User Flow

1. **User sends "Hi" or "Help"** → Bot shows job category menu
2. **User selects category (1-10)** → Bot saves interest, shows payment info
3. **User pays via M-Pesa** → Credits added automatically
4. **User sends "JOBS"** → Bot sends latest job alerts
5. **User sends "BALANCE"** → Bot shows current credits

## 💳 M-Pesa Payment Flow

1. User sends money to Paybill: **600000**
2. Account number: **User's phone number**
3. M-Pesa sends validation request to `/c2b/validate`
4. M-Pesa sends confirmation to `/c2b/confirm`
5. Bot adds credits and sends confirmation message

## 🎯 Job Categories

1. Fundi (Technician/Handyman)
2. Cleaner/Housekeeping
3. Tutor/Teacher
4. Driver
5. Security Guard
6. Cook/Chef
7. Nanny/Childcare
8. Mechanic
9. Electrician
10. Nurse/Healthcare

## 🔍 Job Sources

- MyJobMag Kenya
- BrighterMonday Kenya
- KenyaMoja Jobs
- Mock data (for testing when scraping fails)

## 🛠️ Development

### Testing Locally

1. Use ngrok to expose your local server
2. Update Twilio webhook URL
3. Test with WhatsApp Sandbox
4. Use M-Pesa sandbox for payments

### Adding New Job Sources

1. Extend `scraper.py` with new scraping methods
2. Add keyword mapping for job categories
3. Test scraping logic

### Database Functions

```python
from db import db

# User management
user = db.get_user_by_phone("+254700000000")
db.add_or_update_user(phone, interest="fundi", balance=10)
db.add_balance(phone, 5)
db.deduct_credit(phone)

# Job tracking
db.log_job_sent(phone, job_id, title, url)
was_sent = db.was_job_sent(phone, job_id)
```

## 📊 Monitoring

Check application logs for:

- WhatsApp message processing
- M-Pesa payment confirmations
- Job scraping results
- Database operations

## 🚀 Deployment

### Railway/Render/Heroku

1. Connect your Git repository
2. Set environment variables
3. Deploy the application
4. Update webhook URLs to production domain

### Environment Variables for Production

```bash
MPESA_ENV=production  # Switch to live M-Pesa
FLASK_DEBUG=False
PORT=5000
```

## 🔒 Security

- Enable Supabase RLS policies
- Validate M-Pesa webhooks
- Sanitize user inputs
- Rate limit scraping requests
- Use HTTPS in production

## 📞 Support Commands

- `HELP` - Show main menu
- `JOBS` - Get job alerts
- `BALANCE` - Check credits
- `1-10` - Select job interest

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Test your changes
4. Submit a pull request

## 📄 License

MIT License - feel free to use and modify for your projects.

## 🐛 Troubleshooting

### Common Issues

1. **WhatsApp not responding**

   - Check Twilio webhook URL
   - Verify Twilio credentials
   - Check server logs

2. **M-Pesa payments not working**

   - Verify Daraja API credentials
   - Check C2B URL registration
   - Test in sandbox first

3. **Job scraping fails**

   - Check internet connectivity
   - Verify job board URLs
   - Falls back to mock data

4. **Database errors**
   - Verify Supabase credentials
   - Check table structure
   - Ensure RLS policies are correct

### Debug Mode

Set `FLASK_DEBUG=True` in `.env` for detailed error messages.

### Logs

Check application logs for detailed error information:

```bash
python app.py
```

## 📞 Contact

For support or questions, please create an issue in the repository.

---

**Built with ❤️ for the Kenyan job market** 🇰🇪
