# Mini-Competition System

A competitive programming contest platform I built for running ICPC-style contests. Built with Flask backend, SvelteKit frontend, and PostgreSQL. Supports real-time leaderboards, team competitions, and automated judging.

Requires [Mini-Judge](https://github.com/LeGusto/Mini-Judge) for code evaluation.

## What It Does

**Contest Management**
- Create contests with custom problem sets and time windows
- Individual or team registration
- Live countdown timer with timezone support
- Admin controls for managing contests

**ICPC-Style Leaderboards**
- Color-coded problem grid showing solve status
- 100 points per problem, 20-minute penalties for wrong attempts
- Sorted by problems solved, then penalty time
- Real-time updates during contests

**Code Judging**
- C++ and Python support (extensible to other languages)
- Integrates with Mini-Judge service for secure code execution
- Submission history with execution time and memory stats
- Detailed verdict feedback

**Authentication**
- JWT-based auth with bcrypt password hashing
- Role-based permissions (users and admins)

## Architecture

```
Mini-Competition/
├── backend/          # Flask REST API
├── frontend/         # SvelteKit app
└── docker/           # Containerization
```

**Stack:**
- Backend: Flask, PostgreSQL, psycopg2, PyJWT, bcrypt
- Frontend: SvelteKit, TypeScript, Skeleton UI
- Deployment: Docker Compose
- Judge: External microservice (Node.js + Docker)

## Getting Started

**Prerequisites:** Docker, Docker Compose

```bash
# Clone and set up network
git clone <repo-url>
cd Mini-Competition
docker network create mini-competition-network

# Start services
docker-compose up -d

# Initialize database
docker exec -it mini-competition-postgres-1 psql -U postgres -d mini_competition_db
\i /app/backend/utils/db_setup.sql
```

Access at:
- Frontend: http://localhost:5173
- Backend: http://localhost:5000

## API Overview

**Auth**
- `POST /auth/register` - Create account
- `POST /auth/login` - Get JWT token
- `POST /auth/verify` - Verify token

**Contests**
- `GET /contests` - List all contests
- `POST /contest` - Create contest (admin only)
- `GET /contest/<id>` - Contest details
- `POST /contest/<id>/register` - Register for contest
- `GET /contest/<id>/leaderboard` - Get rankings

**Submissions**
- `POST /submit` - Submit code
- `GET /submissions` - Your submission history
- `GET /submission/<id>` - Submission details

## Database Schema

Main tables: `users`, `contests`, `submissions`, `contest_submissions`, `contest_participants`, `teams`

The schema supports:
- User authentication and roles
- Contest management with JSONB problem lists
- Submission tracking with judge results
- Team-based competitions
- ICPC scoring calculations

## Development

**Backend:**
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python main.py
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

## Security

- bcrypt password hashing
- JWT with expiration
- CORS configuration
- SQL injection prevention via parameterized queries
- Role-based route protection
- Docker container isolation for code execution

## Configuration

Set these in `docker-compose.yaml` or `.env`:

```
JWT_SECRET=your-secret-key
DB_HOST=postgres
DB_NAME=mini_competition_db
JUDGE_HOST=mini-judge
JUDGE_PORT=3000
```

## Known Issues

- JWT tokens need manual refresh (no auto-refresh yet)
- Leaderboard can be slow with 100+ participants
- No rate limiting on submission endpoint
- Timezone handling could be more robust

## Future Plans

- WebSocket support for real-time updates
- Redis caching for leaderboards
- Problem statement editor in admin panel
- Submission code syntax highlighting
- Export leaderboard as CSV

## License

MIT
