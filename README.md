# Mini-Competition System

A comprehensive competitive programming contest platform built with Flask (Python) backend, SvelteKit (TypeScript) frontend, and PostgreSQL database. Features ICPC-style contest management, real-time leaderboards, automated judging, and team-based competitions. 

Mini-Judge is needed to judge submissions: https://github.com/LeGusto/Mini-Judge

## 🏗️ Architecture Overview

### System Components

- **Backend**: Flask REST API with PostgreSQL database
- **Frontend**: SvelteKit SPA with modern UI components
- **Judge Service**: External judging system for code evaluation
- **Database**: PostgreSQL with optimized schemas for contest data
- **Authentication**: JWT-based user authentication with role management

### Directory Structure

```
Mini-Competition/
├── backend/                    # Flask API server
│   ├── routes/                # API endpoints (auth, contest, submission, general)
│   ├── services/              # Business logic layer
│   ├── models/                # Data models
│   ├── utils/                 # Database setup and utilities
│   ├── docker/                # Backend containerization
│   └── config.py             # Configuration management
├── frontend/                  # SvelteKit web application
│   ├── src/
│   │   ├── routes/           # Page components and routing
│   │   ├── lib/              # Shared utilities and services
│   │   └── components/       # Reusable UI components
│   └── docker/               # Frontend containerization
├── docker-compose.yaml       # Multi-service orchestration
└── Mini-Judge/              # External judging service
```

## ✨ Key Features

### 🎯 Contest Management
- **Create Contests**: Admin users can create contests with custom problem sets, start/end times, and descriptions
- **Flexible Registration**: Users can register as individuals or create/join teams for contests
- **Real-time Status**: Live contest timer showing remaining time with automatic status updates
- **Timezone Support**: Automatic timezone conversion for international participants

### 🏆 ICPC-Style Leaderboards
- **Problem-by-Problem Visualization**: Color-coded grid showing attempt counts and solve status
- **Accurate Scoring**: 100 points per solved problem with 20-minute penalty for failed attempts
- **Ranking Logic**: Sorted by problems solved → total penalty → solve time
- **Team & Individual Support**: Separate leaderboards for individual and team participants
- **Real-time Updates**: Auto-refreshing leaderboards with live contest data

### 🔐 Authentication & Authorization
- **JWT Authentication**: Secure token-based authentication with configurable expiration
- **Role-based Access**: User and admin roles with appropriate permissions
- **Session Management**: Automatic token refresh and validation
- **Timezone Tracking**: User-specific timezone preferences for accurate time display

### 💻 Code Submission & Judging
- **Multi-language Support**: Support for C++, Python, and other programming languages
- **Real-time Judging**: Integration with external judge service for code evaluation
- **Submission History**: Complete submission tracking with status updates
- **Detailed Feedback**: Execution time, memory usage, and judge response data

### 👥 Team Management
- **Contest-Specific Teams**: Teams are created per contest, not globally
- **Flexible Team Creation**: Users can create new teams or join existing ones during registration
- **Team Registration**: Streamlined registration process with team validation
- **Team Leaderboards**: Separate ranking system for team-based competitions

### 📊 Analytics & Monitoring
- **Contest Statistics**: Real-time participant counts and submission metrics
- **Performance Monitoring**: Execution time and memory usage tracking
- **Submission Analytics**: Detailed submission patterns and success rates
- **Health Checks**: System health monitoring with Docker health checks

## 🚀 Quick Start

### Prerequisites
- Docker and Docker Compose
- Node.js 18+ (for frontend development)
- Python 3.8+ (for backend development)

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd Mini-Competition
   ```

2. **Create Docker network**
   ```bash
   docker network create mini-competition-network
   ```

3. **Start the services**
   ```bash
   docker-compose up -d
   ```

4. **Set up the database**
   ```bash
   # Connect to PostgreSQL container
   docker exec -it mini-competition-postgres-1 psql -U postgres -d mini_competition_db

   # Run the database setup script
   \i /app/backend/utils/db_setup.sql
   ```

5. **Access the application**
   - Frontend: http://localhost:5173
   - Backend API: http://localhost:5000
   - Database: localhost:5432

### Development Setup

#### Backend Development
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python main.py
```

#### Frontend Development
```bash
cd frontend
npm install
npm run dev
```

## 📋 API Reference

### Authentication Endpoints

#### POST `/auth/register`
Register a new user account.
```json
{
  "username": "string",
  "password": "string",
  "timezone": "string"
}
```

#### POST `/auth/login`
Authenticate user and receive JWT token.
```json
{
  "username": "string",
  "password": "string",
  "timezone": "string"
}
```

#### POST `/auth/verify`
Verify JWT token validity.
```json
{
  "token": "string"
}
```

### Contest Endpoints

#### GET `/contests`
Get all contests with user registration status.
- **Auth**: Required
- **Query**: `?timezone=UTC`

#### POST `/contest`
Create a new contest (Admin only).
```json
{
  "name": "Contest Name",
  "description": "Contest description",
  "start_time": "2024-01-01T10:00:00Z",
  "end_time": "2024-01-01T14:00:00Z",
  "problems": ["problem1", "problem2"]
}
```

#### GET `/contest/<contest_id>`
Get contest details and problems.
- **Auth**: Required (must be registered)

#### POST `/contest/<contest_id>/register`
Register for a contest as individual or team member.
- **Auth**: Required

#### GET `/contest/<contest_id>/leaderboard`
Get ICPC-style leaderboard for contest.
- **Auth**: Required

#### GET `/contest/<contest_id>/submissions`
Get user's submissions for contest.
- **Auth**: Required

### Submission Endpoints

#### POST `/submit`
Submit code for evaluation.
```json
{
  "problem_id": "string",
  "language": "cpp|python",
  "code": "string",
  "contest_id": "integer"
}
```

#### GET `/submissions`
Get user's submission history.

#### GET `/submission/<submission_id>`
Get detailed submission information.

## 🗄️ Database Schema

### Core Tables

#### users
```sql
- id: SERIAL PRIMARY KEY
- username: VARCHAR(255) UNIQUE NOT NULL
- password: VARCHAR(255) NOT NULL
- created_at: TIMESTAMP DEFAULT CURRENT_TIMESTAMP
- role: VARCHAR(50) DEFAULT 'user'
```

#### contests
```sql
- id: SERIAL PRIMARY KEY
- name: VARCHAR(255) NOT NULL
- description: TEXT
- start_time: TIMESTAMP NOT NULL
- end_time: TIMESTAMP NOT NULL
- created_at: TIMESTAMP DEFAULT CURRENT_TIMESTAMP
- updated_at: TIMESTAMP DEFAULT CURRENT_TIMESTAMP
- problems: JSONB
```

#### submissions
```sql
- id: SERIAL PRIMARY KEY
- problem_id: VARCHAR(50) NOT NULL
- language: VARCHAR(50) NOT NULL
- submission_time: TIMESTAMP DEFAULT CURRENT_TIMESTAMP
- status: VARCHAR(50) DEFAULT 'pending'
- judge_response: JSONB
- execution_time: DECIMAL(10,3)
- memory_used: INTEGER
- user_id: INTEGER REFERENCES users(id)
```

#### contest_submissions
```sql
- id: SERIAL PRIMARY KEY
- contest_id: INTEGER REFERENCES contests(id)
- user_id: INTEGER REFERENCES users(id)
- problem_id: VARCHAR(50) NOT NULL
- submission_id: INTEGER REFERENCES submissions(id)
- submission_time: TIMESTAMP NOT NULL
- is_accepted: BOOLEAN DEFAULT FALSE
- score: INTEGER DEFAULT 0
- penalty_time: INTEGER DEFAULT 0
- contest_start_time: TIMESTAMP NOT NULL
- contest_end_time: TIMESTAMP NOT NULL
- created_at: TIMESTAMP DEFAULT CURRENT_TIMESTAMP
```

#### contest_participants
```sql
- id: SERIAL PRIMARY KEY
- contest_id: INTEGER REFERENCES contests(id)
- user_id: INTEGER REFERENCES users(id)
- created_at: TIMESTAMP DEFAULT CURRENT_TIMESTAMP
- updated_at: TIMESTAMP DEFAULT CURRENT_TIMESTAMP
```

## 🎨 Frontend Components

### Core Pages
- **Login/Register**: User authentication with timezone selection
- **Contest List**: Browse available contests with registration status
- **Contest Detail**: View contest problems and submit solutions
- **Leaderboard**: ICPC-style ranking with problem-by-problem visualization
- **Submissions**: Personal submission history and status tracking

### Key Components
- **ContestTimer**: Real-time countdown with contest status
- **SubmissionForm**: Code editor with language selection
- **SubmissionPoller**: Real-time submission status updates
- **ProblemStatement**: Formatted problem display with samples

### UI Features
- **Responsive Design**: Mobile-first approach with tablet/desktop optimizations
- **Dark Theme**: Modern dark color scheme with accent highlights
- **Real-time Updates**: WebSocket-style polling for live data
- **Interactive Elements**: Hover effects, animations, and visual feedback

## 🔧 Configuration

### Environment Variables

#### Backend (.env)
```env
FLASK_ENV=development
JWT_SECRET=your-secret-key-change-this
JWT_EXPIRATION=3600
DB_HOST=postgres
DB_PORT=5432
DB_NAME=mini_competition_db
DB_USER=postgres
DB_PASSWORD=postgres
JUDGE_HOST=mini-judge
JUDGE_PORT=3000
```

#### Frontend (environment variables)
```env
VITE_API_BASE_URL=http://localhost:5000
```

## 🧪 Testing

### Backend Testing
```bash
cd backend
python -m pytest tests/
```

### Frontend Testing
```bash
cd frontend
npm run check
npm run build
```

### Integration Testing
```bash
docker-compose -f docker-compose.test.yml up --abort-on-container-exit
```

## 📈 Performance Optimization

### Database Indexes
- Composite indexes on frequently queried columns
- Time-based indexes for submission queries
- User-contest relationship optimizations

### Caching Strategy
- JWT token caching for authentication
- Contest data caching for leaderboard queries
- Static asset optimization with Vite

### Monitoring
- Health check endpoints for all services
- Database connection pooling
- Memory usage monitoring
- Request/response logging

## 🔒 Security Features

### Authentication Security
- Password hashing with bcrypt
- JWT token expiration and refresh
- CORS configuration for cross-origin requests
- Input validation and sanitization

### API Security
- Authentication middleware for protected routes
- Admin-only route protection
- Request rate limiting
- SQL injection prevention with parameterized queries

## 🚢 Deployment

### Production Setup
```bash
# Build production images
docker-compose -f docker-compose.prod.yml build

# Deploy with environment variables
docker-compose -f docker-compose.prod.yml up -d

# Set up reverse proxy (nginx)
# Configure SSL certificates
# Set up monitoring and logging
```

### Scaling Considerations
- Horizontal scaling with load balancer
- Database read replicas for leaderboard queries
- Redis caching for session management
- CDN for static assets

## 🤝 Contributing

### Development Workflow
1. Fork the repository
2. Create a feature branch
3. Make changes with proper testing
4. Submit a pull request with detailed description

### Code Standards
- Python: PEP 8 with type hints
- TypeScript: ESLint configuration
- Commit messages: Conventional commits format
- Documentation: Comprehensive docstrings and comments

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

### Common Issues
- **Database Connection**: Ensure PostgreSQL is running and accessible
- **CORS Errors**: Check frontend API base URL configuration
- **JWT Expiration**: Implement token refresh logic in frontend
- **Timezone Issues**: Verify pytz library installation

### Troubleshooting
- Check Docker container logs: `docker-compose logs`
- Verify network connectivity: `docker network inspect`
- Database issues: Check PostgreSQL logs and connection strings
- Frontend build issues: Clear node_modules and reinstall
