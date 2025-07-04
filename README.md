# 🚀 Ajirawise - Smart Job Alert Bot for Kenya 🇰🇪

An intelligent dual-platform bot (WhatsApp & Telegram) that helps Kenyan job seekers find employment opportunities with AI-powered career assistance.

## 🚨 Important Notice About AI Features

Our AI functionality has smart fallbacks but is **rate limited due to high traffic volumes**. When AI limits are reached, you'll still get our enhanced bot with full job search capabilities - just without AI-powered responses. Both platforms offer the same core functionality!

**💡 Pro Tip**: Our **Telegram bot is recommended** because unlike WhatsApp, it's **not limited by daily rates** and offers unlimited usage!

### 🏗️ Professional Infrastructure

We've invested in **professional cloud hosting on Render.com** to ensure:

- ⚡ **24/7 Uptime** - Your job search never stops
- 🚀 **Fast Response Times** - Instant job alerts and AI responses
- 🔒 **Enterprise Security** - Your data is protected with industry standards
- 📈 **Auto-scaling** - Handles high traffic without interruption
- 🌍 **Global CDN** - Fast access from anywhere in Kenya and beyond

### 🤖 Choose Your Platform:

- **📱 WhatsApp**: +1 415 523 8886 (join code: `join seat-dear`) - _Rate limited_
- **🚀 Telegram**: [t.me/Ajirawise_bot](https://t.me/Ajirawise_bot) - _Unlimited usage_ ⭐ **RECOMMENDED**

## 🎯 How to Use the Bot (For Job Seekers)

### 📱 Getting Started with WhatsApp

1. **Join WhatsApp Sandbox**: Send a WhatsApp message to **+1 415 523 8886**
2. **Send Join Code**: Type `join seat-dear` to activate the bot
3. **Start Your Journey**: Send `hi` to begin your job search!

### 💬 What You Can Do

- **🔍 Search Jobs**: Say "software engineering jobs" or "data entry jobs"
- **🤖 Get Career Advice**: Ask "What skills do I need for data science?"
- **📋 Browse Categories**: Choose from 9+ job categories
- **💡 Get Interview Tips**: Ask "How to prepare for interviews?"
- **📈 Career Guidance**: Get personalized advice for your career path
- **🎓 Educational Assistant**: Ask any question - from programming to business concepts
- **💰 Salary Insights**: Get current market rates for different roles
- **🏢 Company Information**: Learn about employers and industry trends
- **📝 Resume Tips**: Get advice on CV writing and optimization

### 🗣️ Sample Conversations

```
You: hi
Bot: 🔍 Welcome to Ajirawise - Your Smart Job Assistant!
     Choose your job interest or ask me anything about careers in Kenya!

You: software engineering jobs
Bot: 🎯 Here are the latest software engineering jobs in Kenya:
     [Lists current job openings with details]

You: What skills do I need for data science?
Bot: 🤖 For data science in Kenya, you'll need:
     • Python programming
     • SQL and database management
     • Statistics and mathematics
     • Machine learning basics
     [Detailed career advice continues...]

You: How much do software engineers earn in Kenya?
Bot: 💰 Software engineer salaries in Kenya typically range from:
     • Entry level: KES 50,000 - 100,000
     • Mid-level: KES 100,000 - 200,000
     • Senior level: KES 200,000+
     [More detailed insights...]

You: Explain what is machine learning?
Bot: 🎓 Machine learning is a subset of artificial intelligence (AI) that enables
     computers to learn and make decisions from data without being explicitly programmed.
     Think of it like teaching a computer to recognize patterns...
     [Detailed educational explanation continues...]

You: How do I start a tech startup in Kenya?
Bot: 🚀 Starting a tech startup in Kenya involves several key steps:
     • Market research and validation
     • Business registration with relevant authorities
     • Funding options (angel investors, VCs, grants)
     • Building your MVP (Minimum Viable Product)
     [Comprehensive business guidance continues...]
```

### 🎯 Available Job Categories

- 💻 **Software Engineering** - Development, programming, tech roles
- 📊 **Data Entry** - Data processing, administrative tasks
- 📈 **Sales & Marketing** - Business development, marketing roles
- 🚚 **Delivery & Logistics** - Transportation, supply chain
- 📞 **Customer Service** - Support, call center positions
- 💰 **Finance & Accounting** - Banking, accounting, finance roles
- 🏢 **Admin & Office Work** - Administrative, clerical positions
- 🎓 **Teaching / Training** - Education, training opportunities
- 🎯 **Internships / Attachments** - Entry-level, learning opportunities

## 🛠️ Running the Bot Locally (For Developers)

### 📋 Prerequisites

Before you start, make sure you have:

- Python 3.8 or higher
- A Twilio account (for WhatsApp integration)
- A Supabase account (for database)
- An OpenRouter account (for AI features)
- ngrok installed (for webhook tunneling)

### 🚀 Quick Setup

1. **Clone the Repository**

```bash
git clone <your-repository-url>
cd vibeCoding
```

2. **Install Dependencies**

```bash
pip install -r requirements.txt
```

3. **Set Up Environment Variables**
   Create a `.env` file in the root directory:

```env
# Twilio WhatsApp Configuration
TWILIO_SID=your_twilio_account_sid
TWILIO_TOKEN=your_twilio_auth_token
TWILIO_WHATSAPP_NUMBER=whatsapp:+14155238886

# AI Configuration (OpenRouter)
OPENROUTER_API_KEY=your_openrouter_api_key

# Database Configuration (Supabase)
SUPABASE_URL=your_supabase_project_url
SUPABASE_KEY=your_supabase_anon_key

# Optional: Flask Configuration
FLASK_DEBUG=true
PORT=5000
HOST=0.0.0.0
```

4. **Set Up the Database**

- Go to your Supabase project
- Run the SQL commands from `schema.sql` in the SQL editor
- This creates all necessary tables for users, jobs, and AI interactions

5. **Start the Application**

```bash
# Start the Flask application
python run.py
```

You should see output like:

```
🚀 Starting Ajirawise - Smart Job Alert Bot...
📍 Running on http://0.0.0.0:5000
🔧 Debug mode: True
💡 Send 'Hi' to your Ajirawise bot to get started!
🧠 Starting smart job scheduler...
⏰ Schedule: Every 2 minutes for first 5 jobs, then 2-4 hours
```

6. **Set Up Webhook (for WhatsApp)**
   In a new terminal window:

```bash
# Install ngrok if you haven't already
# Then start ngrok tunnel
ngrok http 5000
```

Copy the ngrok URL (e.g., `https://abc123.ngrok-free.app`) and:

- Go to [Twilio Console](https://console.twilio.com)
- Navigate to Messaging → Settings → WhatsApp Sandbox Settings
- Set webhook URL to: `https://your-ngrok-url.ngrok-free.app/whatsapp`

### 🔧 Alternative Running Methods

The bot includes multiple ways to start:

```bash
# Method 1: Using run.py (recommended)
python run.py

# Method 2: Using app.py directly
python app.py

# Method 3: Using the dual platform runner
python run_dual_platform.py
```

### 🧪 Testing the Bot

1. **WhatsApp Testing**:

   - Send a message to +1 415 523 8886
   - Type `join seat-dear`
   - Send `hi` to start

2. **Local Testing**:
   - The bot runs on `http://localhost:5000`
   - Check `/health` endpoint for status
   - View logs in the terminal

### 🔍 Troubleshooting

**Common Issues:**

1. **"Module not found" errors**:

   ```bash
   pip install -r requirements.txt
   ```

2. **Database connection issues**:

   - Check your Supabase URL and key
   - Ensure the database schema is set up correctly

3. **WhatsApp webhook not working**:

   - Verify ngrok is running
   - Check that the webhook URL is correctly set in Twilio
   - Ensure your Flask app is running

4. **AI responses not working**:
   - Verify your OpenRouter API key
   - Check if you have remaining credits/requests

## ✨ Cool Features

- 🤖 **AI-Powered Career Assistant** - Get personalized career advice using DeepSeek AI
- 🎓 **Educational AI Tutor** - Ask any question and get detailed explanations on programming, business, technology, and more
- 🎯 **Smart Job Matching** - Find jobs across multiple categories with intelligent filtering
- 📱 **Dual Platform Access** - WhatsApp & Telegram integration (no app download needed)
- 🌍 **Kenya-Focused** - Tailored specifically for the Kenyan job market and culture
- 🔄 **Real-time Updates** - Fresh job listings updated every 2-4 hours with smart scheduling
- 💬 **Natural Language** - Chat naturally with AI about careers, learning, and professional development
- 📊 **Smart Rate Limiting** - Intelligent fallbacks ensure you always get helpful responses
- 💰 **Market Insights** - Get current salary information and industry trends
- 🏢 **Company Intelligence** - Learn about employers, company culture, and hiring practices

## 🔧 API Integrations

### Job Sources

- BrighterMonday Kenya
- MyJobMag Kenya
- Fuzu Kenya
- (Expandable to more sources)

### AI Provider

- **OpenRouter** with DeepSeek R1 model
- Free tier: 50 requests/day
- Intelligent fallback responses when rate limited

### Database

- **Supabase** PostgreSQL
- User management and tracking
- Job caching and storage
- AI interaction logs

## 📊 Architecture & Infrastructure Design

### 🏗️ Thoughtful System Architecture

We've designed AjiraWise with **enterprise-grade architecture** for reliability and scalability:

```
User (WhatsApp/Telegram) → Twilio/Telegram API → Render.com → Flask App → AI/Database
                                                     ↓
                                            Job Scrapers → External APIs
```

### 🔧 Infrastructure Highlights

- **🌐 Production-Ready Hosting**: Deployed on Render.com with automatic scaling
- **🔄 Smart Job Scheduler**: Intelligent background tasks for job fetching
- **🛡️ Rate Limiting & Fallbacks**: Graceful handling of API limits
- **📊 Database Optimization**: Efficient Supabase PostgreSQL setup
- **🔒 Security First**: Environment variables, webhook validation, input sanitization
- **📈 Monitoring**: Real-time logs and performance tracking
- **⚡ CDN Integration**: Fast global content delivery

## 🚀 Deployment to Production

### 🏗️ Render.com (Our Choice - Recommended)

**Why we chose Render for AjiraWise:**

- ✅ **Zero-downtime deployments** - Updates without interrupting users
- ✅ **Automatic SSL certificates** - Secure connections by default
- ✅ **Built-in monitoring** - Real-time performance tracking
- ✅ **Easy scaling** - Handles traffic spikes automatically
- ✅ **GitHub integration** - Seamless CI/CD pipeline
- ✅ **Cost-effective** - Professional hosting without breaking the bank

The project includes a professionally configured `render.yaml` file:

1. Connect your GitHub repository to Render
2. The service will automatically deploy using our optimized render.yaml configuration
3. Set up environment variables in Render dashboard
4. Update Twilio webhook to point to your Render URL
5. **Bonus**: Automatic deployments on every push to main branch!

### Heroku

```bash
# Install Heroku CLI, then:
heroku create your-app-name
git push heroku main
```

### Manual Server

```bash
# Install dependencies
pip install -r requirements.txt

# Set production environment variables
export FLASK_ENV=production

# Run with gunicorn
gunicorn app:app --bind 0.0.0.0:$PORT
```

## 🔒 Security Features

- Environment variables for sensitive data
- Webhook validation for Twilio requests
- Rate limiting on AI requests
- Secure database connections
- Input validation and sanitization

## 📈 Monitoring & Analytics

- Real-time application logs
- AI usage tracking and rate limiting
- User interaction analytics
- Job matching success rates
- Smart scheduler performance metrics

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Make your changes and test thoroughly
4. Commit your changes: `git commit -m 'Add amazing feature'`
5. Push to the branch: `git push origin feature/amazing-feature`
6. Submit a pull request

## 📄 License

MIT License - See LICENSE file for details

## 🆘 Support & Help

- **Issues**: Create a GitHub issue for bugs or feature requests
- **WhatsApp**: Test the bot directly at +1 415 523 8886
- **Documentation**: Check SETUP_INSTRUCTIONS.md for detailed setup
- **Deployment**: See DEPLOYMENT_GUIDE.md for production deployment

## 🔮 Roadmap

- [ ] Multi-language support (Swahili)
- [ ] Voice message responses
- [ ] PDF resume generation
- [ ] Interview scheduling integration
- [ ] Salary insights and trends
- [ ] Company reviews integration
- [ ] Telegram bot enhancement
- [ ] Mobile app companion

---

**Made with ❤️ for Kenyan Job Seekers**

_Empowering careers through AI and automation_

**🌟 Star this repository if it helps you find your dream job!**

---

**AjiraWise cares for you** 💙
