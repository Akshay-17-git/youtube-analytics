# 📊 YouTube Analytics Dashboard

**Built by: Akshay Kasimahanthi**

An AI-powered YouTube growth analytics tool that helps creators optimize their content strategy, predict performance, and make data-driven decisions.

![Dashboard Preview](https://img.shields.io/badge/Streamlit-Live%20App-red?logo=streamlit)
![Python](https://img.shields.io/badge/Python-3.9+-blue?logo=python)
![License](https://img.shields.io/badge/License-MIT-green)

## 🚀 Live Demo

**[Click here to view the live dashboard](https://yourusername-youtube-analytics.streamlit.app)**

## ✨ Features

### 📈 Dashboard
- **Channel Overview**: Total views, likes, engagement rate, and performance metrics
- **Trend Analysis**: Views and engagement trends over time
- **Performance by Day/Hour**: Identify optimal posting times
- **Top Videos**: Discover your best-performing content

### 🔮 Forecasting
- **30-Day Predictions**: AI-powered forecasts for views and subscribers
- **Growth Trajectory**: Track if your channel is growing, stable, or declining
- **Confidence Scores**: Know how reliable the predictions are

### 📅 Calendar Optimizer
- **Best Days to Post**: Data-driven recommendations for optimal posting days
- **Best Hours**: Find when your audience is most active
- **Content Calendar**: Auto-generated posting schedule with content type suggestions

### 🔍 Pattern Detection
- **Content Themes**: Discover which topics perform best
- **Title Analysis**: Optimal title length and patterns
- **Duration Patterns**: Find the best video length for your audience
- **Upload Consistency**: Track and improve your posting schedule

### 🧪 A/B Testing
- **Title A/B Test**: Compare two titles and predict which will perform better
- **Thumbnail A/B Test**: Upload two thumbnails and get AI-powered visual analysis
- **Improvement Tips**: Get actionable suggestions for better titles and thumbnails

### 🤖 AI Chatbot
- **Natural Language Queries**: Ask questions about your channel in plain English
- **Instant Insights**: Get answers about views, performance, growth, and recommendations
- **PDF Reports**: Generate comprehensive analytics reports
- **Quick Actions**: One-click access to common analytics questions

## 🛠️ Tech Stack

- **Frontend**: Streamlit
- **Data Processing**: Pandas, NumPy
- **Visualization**: Plotly
- **Machine Learning**: Scikit-learn (Linear Regression for forecasting)
- **AI/LLM**: OpenAI GPT-3.5
- **APIs**: YouTube Data API v3
- **Image Processing**: Pillow (for thumbnail analysis)
- **PDF Generation**: FPDF, ReportLab

## 📋 Prerequisites

- Python 3.9+
- YouTube Data API v3 key
- OpenAI API key (optional, for chatbot features)

## 🚀 Deployment to Streamlit Cloud

### Step 1: Push to GitHub
```bash
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/youtube-analytics.git
git push -u origin main
```

### Step 2: Deploy
1. Go to [share.streamlit.io](https://share.streamlit.io)
2. Sign in with GitHub
3. Click "New app"
4. Select your repository and branch
5. Main file path: `app.py`
6. Click "Deploy"

### Step 3: Add Secrets
In Streamlit Cloud dashboard:
1. Click your app → Settings (gear icon)
2. Go to "Secrets" tab
3. Add your API keys:
```toml
YOUTUBE_API_KEY = "your_youtube_api_key_here"
OPENAI_API_KEY = "your_openai_api_key_here"
```

## 💻 Local Development

### Installation
```bash
# Clone the repository
git clone https://github.com/yourusername/youtube-analytics.git
cd youtube-analytics

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your API keys
```

### Running Locally
```bash
streamlit run app.py
```

The app will open at `http://localhost:8501`

## 🔑 API Keys Setup

### YouTube Data API
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project
3. Enable YouTube Data API v3
4. Create credentials → API Key
5. Copy the key to your `.env` file or Streamlit secrets

### OpenAI API (Optional)
1. Go to [OpenAI Platform](https://platform.openai.com/)
2. Create an account
3. Generate an API key
4. Copy the key to your `.env` file or Streamlit secrets

## 📊 How to Use

1. **Enter a YouTube channel** in the sidebar (name, URL, or channel ID)
2. **Fetch data** - the app will analyze up to 150 recent videos
3. **Explore different pages**:
   - Dashboard: Overview and trends
   - Forecasting: Future predictions
   - Calendar Optimizer: Best posting times
   - Pattern Detection: Content insights
   - A/B Testing: Test titles and thumbnails
   - AI Chatbot: Ask questions about your data

## 🎯 Key Insights Provided

- **Engagement Rate**: (Likes + Comments) / Views × 100
- **Proxy CTR**: Views per Impression (click-through rate indicator)
- **Video Velocity**: Views per day since published
- **Subscriber Conversion**: Subscribers gained per view
- **Performance Tiers**: Viral, Good, Average, Low categorization

## 📝 Project Structure

```
youtube_project/
├── app.py                 # Main Streamlit application
├── config/
│   └── settings.py        # Configuration and API keys
├── src/
│   ├── ab_testing.py      # A/B testing simulator
│   ├── analytics_explanations.py  # Metric explanations
│   ├── calendar_optimizer.py      # Posting time optimizer
│   ├── chatbot.py         # AI chatbot
│   ├── database.py        # Database operations
│   ├── etl.py            # Data processing pipeline
│   ├── forecasting.py     # ML forecasting models
│   ├── metrics.py         # Analytics calculations
│   ├── pattern_detection.py       # Content pattern analysis
│   ├── sample_data.py     # Demo data generator
│   └── youtube_api.py     # YouTube API wrapper
├── docs/
│   └── ANALYTICS_EXPLANATION.md   # Technical documentation
├── requirements.txt       # Python dependencies
└── README.md             # This file
```

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License

This project is licensed under the MIT License.

## 🙏 Acknowledgments

- YouTube Data API for providing video metrics
- Streamlit for the amazing web app framework
- OpenAI for powering the chatbot features

---

**Built with ❤️ by Akshay Kasimahanthi for YouTube creators who want to grow with data**
