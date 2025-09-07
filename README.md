# Smart Lead Scoring CRM

A comprehensive ML-powered CRM tool that scores leads by conversion likelihood and revenue potential, served via FastAPI API and visualized in a React dashboard. Deployed on GCP with Docker + CI/CD pipeline, enabling real-time lead recommendations and chatbot query support.

## Features

### Data Pipeline
- **Lead Data Simulation**: Generate realistic customer/lead data with demographics, interaction history, email engagement, and site visits
- **ETL Pipeline**: Built with Prefect for automated daily lead processing and data transformation
- **Data Quality**: Automated data validation and quality scoring

### ML Model (Core)
- **Multi-Model Training**: XGBoost, LightGBM, Gradient Boosting, Random Forest, and Logistic Regression
- **Revenue Impact Scoring**: Conversion probability × estimated deal size
- **Experiment Tracking**: MLflow integration for model versioning and performance monitoring
- **Real-time Predictions**: FastAPI inference API with sub-100ms response times

### Dashboard & Integration
- **React Frontend**: Modern CRM-like interface with lead management
- **Lead Analytics**: Conversion trends, industry breakdowns, and performance metrics
- **AI Assistant**: RAG-lite chatbot for lead queries ("Who are my top 10 leads this week?")
- **Next Best Actions**: Automated recommendations (Call, Email, Nurture)

### Deployment & MLOps
- **Containerized**: Docker + Docker Compose for local development
- **Cloud Deployment**: GCP Cloud Run + App Engine configuration
- **Experiment Tracking**: MLflow + Weights & Biases integration
- **CI/CD Pipeline**: GitHub Actions for automated testing and deployment
- **Monitoring**: Health checks, performance metrics, and error tracking

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   React App     │    │   FastAPI API   │    │   ML Pipeline   │
│   (Frontend)    │◄──►│   (Backend)     │◄──►│   (Prefect)     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   AI Chatbot    │    │   MLflow        │    │   PostgreSQL    │
│   (RAG-lite)    │    │   (Tracking)    │    │   (Database)    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 🚀 Quick Start

### Prerequisites
- Python 3.9+
- Node.js 18+
- Docker & Docker Compose
- PostgreSQL (for production)

### Local Development

1. **Clone and setup**:
```bash
git clone <repository-url>
cd Smart_Lead_Scoring
```

2. **Backend setup**:
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Generate sample data
python data_pipeline/lead_data_simulator.py

# Train initial model
python ml_model/train_model.py

# Start API server
uvicorn api.enhanced_main:app --reload --host 0.0.0.0 --port 8000
```

3. **Frontend setup**:
```bash
cd frontend
npm install
npm start
```

4. **Access the application**:
- Frontend: http://localhost:3000
- API: http://localhost:8000
- API Docs: http://localhost:8000/docs

### Docker Deployment

1. **Start all services**:
```bash
docker-compose up -d
```

2. **Access services**:
- Frontend: http://localhost:3000
- API: http://localhost:8000
- MLflow: http://localhost:5000
- Prefect: http://localhost:4200

### GCP Deployment

1. **Setup GCP project**:
```bash
# Set project ID
export PROJECT_ID=your-project-id

# Enable APIs
gcloud services enable run.googleapis.com
gcloud services enable cloudbuild.googleapis.com
gcloud services enable sqladmin.googleapis.com
```

2. **Deploy with Cloud Build**:
```bash
gcloud builds submit --config gcp/cloudbuild.yaml
```

## 📊 Usage

### API Endpoints

#### Health Check
```bash
curl http://localhost:8000/health
```

#### Single Lead Prediction
```bash
curl -X POST "http://localhost:8000/predict/single" \
  -H "Content-Type: application/json" \
  -d '{
    "company_name": "TechCorp Inc.",
    "email": "contact@techcorp.com",
    "industry": "Technology",
    "company_size": "51-200",
    "region": "NA",
    "deal_size_estimate": 50000,
    "page_views_7d": 15,
    "emails_opened_30d": 8,
    "calls_last_30d": 2
  }'
```

#### Batch Prediction
```bash
curl -X POST "http://localhost:8000/predict/batch" \
  -H "Content-Type: application/json" \
  -d '{
    "leads": [
      {
        "company_name": "Company A",
        "email": "contact@companya.com",
        "industry": "Finance",
        "company_size": "201-1000",
        "region": "EU",
        "deal_size_estimate": 25000,
        "page_views_7d": 10,
        "emails_opened_30d": 5,
        "calls_last_30d": 1
      }
    ]
  }'
```

### AI Assistant Queries

Try these queries in the chatbot:
- "Who are my top 10 leads this week?"
- "What's our conversion rate by industry?"
- "Show me leads that need immediate attention"
- "What's our revenue forecast?"

## 🔧 Configuration

### Environment Variables

```bash
# API Configuration
API_HOST=0.0.0.0
API_PORT=8000

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/leadscoring

# MLflow
MLFLOW_TRACKING_URI=http://localhost:5000

# GCP (for production)
GCP_PROJECT_ID=your-project-id
GCP_REGION=us-central1
```

### Model Configuration

The system supports multiple ML models:
- **XGBoost**: Best for tabular data with high performance
- **LightGBM**: Fast training and good accuracy
- **Gradient Boosting**: Robust baseline model
- **Random Forest**: Good for feature importance
- **Logistic Regression**: Interpretable and fast

## 📈 Monitoring

### MLflow Tracking
- Access: http://localhost:5000
- Track experiments, models, and performance metrics
- Model registry for versioning and deployment

### Health Monitoring
- API health: `/health` endpoint
- Model status and performance metrics
- Database connection monitoring

### Logging
- Structured logging with different levels
- Request/response logging
- Error tracking and alerting

## 🧪 Testing

### Run Tests
```bash
# Backend tests
pytest tests/ --cov=. --cov-report=html

# Frontend tests
cd frontend
npm test

# Integration tests
pytest tests/integration/
```

### Load Testing
```bash
# Install locust
pip install locust

# Run load tests
locust -f tests/load_test.py --host=http://localhost:8000
```

## 🚀 CI/CD Pipeline

The project includes a comprehensive CI/CD pipeline:

1. **Code Quality**: Linting, formatting, type checking
2. **Testing**: Unit tests, integration tests, coverage reports
3. **Security**: Vulnerability scanning with Trivy
4. **Build**: Docker image building and pushing
5. **Deploy**: Automated deployment to staging/production
6. **Monitoring**: Health checks and notifications

## 📚 API Documentation

### Interactive Docs
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### Key Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/predict/single` | POST | Single lead prediction |
| `/predict/batch` | POST | Batch lead prediction |
| `/predict/top-leads` | GET | Get top performing leads |
| `/model/info` | GET | Model information |

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For support and questions:
- Create an issue in the repository
- Check the documentation
- Review the API docs at `/docs`

## 🔮 Roadmap

- [ ] Advanced analytics dashboard
- [ ] Email campaign integration
- [ ] CRM system integration (Salesforce, HubSpot)
- [ ] Advanced ML features (deep learning, ensemble methods)
- [ ] Real-time data streaming
- [ ] Mobile app
- [ ] Advanced chatbot with GPT integration