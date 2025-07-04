# 🚀 Ajirawise - Smart Job Alert Bot for Kenya 🇰🇪

An intelligent dual-platform bot (WhatsApp & Telegram) that helps Kenyan job seekers find employment opportunities with AI-powered career assistance.

## ✨ Features

- 🤖 **AI-Powered Career Assistant** - Get personalized career advice using DeepSeek AI
- 🎯 **Smart Job Matching** - Find jobs across multiple categories
- 📱 **WhatsApp Integration** - Easy access via WhatsApp (no app download needed)
- 🌍 **Kenya-Focused** - Tailored for the Kenyan job market
- 🔄 **Real-time Updates** - Fresh job listings from top Kenyan job sites
- 💬 **Natural Language** - Chat naturally with AI about your career goals

## 🚀 Quick Start

### For Users

1. **Join WhatsApp Sandbox**: Send a WhatsApp message to **+1 415 523 8886**
2. **Send Join Code**: Type `join seat-dear` to activate the bot
3. **Start Chatting**: Send `hi` to begin your job search journey!

### Sample Conversations

```
You: hi
Bot: 🔍 Welcome to Ajirawise - Your Smart Job Assistant! Choose your job interest...

You: software engineering
Bot: 🎯 Great choice! Here are the latest software engineering jobs...

You: What skills do I need for data science?
Bot: 🤖 For data science in Kenya, you'll need skills like Python, SQL, statistics...
```

## 🛠️ Technical Setup (For Developers)

### Prerequisites

- Python 3.8+
- Twilio Account (WhatsApp Sandbox)
- Supabase Account (Database)
- OpenRouter Account (AI Integration)
- ngrok (for webhook tunneling)

### Installation

1. **Clone Repository**

```bash
git clone <repository-url>
cd vibeCoding
```

2. **Install Dependencies**

```bash
pip install -r requirements.txt
```

3. **Environment Setup**
   Create `.env` file with:

```env
# Twilio WhatsApp Configuration
TWILIO_SID=your_twilio_account_sid
TWILIO_TOKEN=your_twilio_auth_token
TWILIO_WHATSAPP_NUMBER=whatsapp:+14155238886

# AI Configuration
OPENROUTER_API_KEY=your_openrouter_key

# Database Configuration
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key
```

4. **Database Setup**
   Run the SQL schema in Supabase:

```sql
-- See schema.sql for complete database setup
```

5. **Start the Bot**

```bash
# Start Flask app
python run.py

# In another terminal, start ngrok
python get_url.py
```

6. **Configure Webhook**

- Copy webhook URL from ngrok output
- Go to [Twilio Console](https://console.twilio.com)
- Navigate to WhatsApp → Sandbox Settings
- Set webhook URL to: `https://your-ngrok-url.ngrok-free.app/whatsapp`

## 🎯 Job Categories

- 💼 Data Entry
- 📈 Sales & Marketing
- 🚚 Delivery & Logistics
- 📞 Customer Service
- 💰 Finance & Accounting
- 🏢 Admin & Office Work
- 🎓 Teaching / Training
- 🎯 Internships / Attachments
- 💻 Software Engineering

## 🤖 AI Features

### Career Guidance

- Job role explanations
- Skill requirements
- Career path recommendations
- Interview preparation tips

### Smart Responses

- Natural language understanding
- Context-aware conversations
- Personalized job matching
- Kenya-specific career advice

## 📱 WhatsApp Setup

### For Testing

1. **WhatsApp Sandbox**: +1 415 523 8886
2. **Join Code**: `join seat-dear`
3. **Test Message**: Send `hi` to start

### For Production

- Upgrade to Twilio WhatsApp Business API
- Get approved WhatsApp Business number
- Update webhook configuration

## 🔧 API Integrations

### Job Sources

- BrighterMonday Kenya
- MyJobMag Kenya
- Fuzu Kenya
- (Expandable to more sources)

### AI Provider

- **OpenRouter** with DeepSeek R1 model
- Free tier: 50 requests/day
- Fallback responses when rate limited

### Database

- **Supabase** PostgreSQL
- User management
- Job tracking
- AI interaction logs

## 📊 Architecture

```
User (WhatsApp) → Twilio → ngrok → Flask App → AI/Database
                                      ↓
                              Job Scrapers → External APIs
```

## 🚀 Deployment

### Local Development

```bash
python run.py  # Start Flask app
python get_url.py  # Start ngrok tunnel
```

### Production (Heroku)

```bash
# See DEPLOYMENT.md for complete instructions
git push heroku main
```

## 🔒 Security

- Environment variables for sensitive data
- Webhook validation
- Rate limiting on AI requests
- Secure database connections

## 📈 Monitoring

- Real-time logs via Flask
- AI usage tracking
- User interaction analytics
- Job matching success rates

## 🤝 Contributing

1. Fork the repository
2. Create feature branch
3. Add tests for new features
4. Submit pull request

## 📄 License

MIT License - See LICENSE file for details

## 🆘 Support

- **Issues**: Create GitHub issue
- **WhatsApp**: Test the bot directly
- **Email**: [Your contact email]

## 🔮 Roadmap

- [ ] Multi-language support (Swahili)
- [ ] Voice message responses
- [ ] PDF resume generation
- [ ] Interview scheduling
- [ ] Salary insights
- [ ] Company reviews integration

---

**Made with ❤️ for Kenyan Job Seekers**

_Empowering careers through AI and automation_
