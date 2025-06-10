# Authentication Setup Guide

## Overview
This guide explains the authentication system added to the US Roads & Businesses Explorer application.

## Features Added

### 1. Login Page
- Clean, modern login interface with Material-UI components
- Multi-language support (English/Vietnamese)
- Form validation and error handling
- Password visibility toggle

### 2. Backend Authentication
- JWT-based authentication system
- Secure password hashing with bcrypt
- Protected API endpoints
- User session management

### 3. Database Schema
- Users table with authentication fields
- Support for user roles (admin/regular user)
- Audit fields (created_at, last_login)

### 4. Frontend Protection
- Protected routes requiring authentication
- Automatic redirect to login for unauthenticated users
- Persistent login state using localStorage
- Logout functionality in header

## Setup Instructions

### 1. Install Dependencies

Backend:
```bash
cd google_maps_crawler
pip install -r requirements.txt
```

Frontend:
```bash
cd google_maps_crawler/frontend
npm install
```

### 2. Initialize Database

Run the setup script:
```bash
./setup_auth.sh
```

Or manually:
```bash
# Start PostgreSQL
docker-compose up -d postgres

# Create users table
docker-compose exec -T postgres psql -U postgres -d roads_db < google_maps_crawler/app/database/schemas_users.sql
```

### 3. Default Users

Two default users are created:

**Admin User:**
- Username: `admin`
- Password: `admin123`
- Has superuser privileges

**Regular User:**
- Username: `user`
- Password: `user123`
- Standard user privileges

⚠️ **IMPORTANT**: Change these passwords immediately in production!

### 4. Start the Application

Backend:
```bash
cd google_maps_crawler
python -m app.main
```

Frontend:
```bash
cd google_maps_crawler/frontend
npm start
```

## API Endpoints

### Authentication Endpoints
- `POST /api/auth/login` - User login
- `GET /api/auth/me` - Get current user info
- `POST /api/auth/logout` - Logout user

### Protected Endpoints
All existing API endpoints now require authentication:
- `/stats`
- `/roads/*`
- `/crawl/*`
- `/api/businesses/*`
- `/api/crawl-sessions/*`

## Security Features

1. **Password Hashing**: Uses bcrypt for secure password storage
2. **JWT Tokens**: Stateless authentication with expiration
3. **CORS Protection**: Configured for localhost development
4. **Request Headers**: Automatic token injection for API calls

## Customization

### Change JWT Secret
Edit the `JWT_SECRET_KEY` in `google_maps_crawler/app/api/auth_api.py`:
```python
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-this-in-production")
```

### Token Expiration
Default: 24 hours. Change in `auth_api.py`:
```python
ACCESS_TOKEN_EXPIRE_MINUTES = 1440  # 24 hours
```

### Add New Users
Use bcrypt to hash passwords:
```python
import bcrypt
password_hash = bcrypt.hashpw("password".encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
```

Then insert into database:
```sql
INSERT INTO users (username, email, password_hash, full_name)
VALUES ('newuser', 'user@example.com', '<password_hash>', 'New User');
```

## Troubleshooting

### Cannot Login
1. Check database is running: `docker ps`
2. Verify users table exists: `docker-compose exec postgres psql -U postgres -d roads_db -c "\dt users"`
3. Check backend logs for errors

### Frontend Not Redirecting
1. Clear browser localStorage
2. Check console for errors
3. Verify backend is running on port 8000

### Token Expired
- Tokens expire after 24 hours
- User will be redirected to login
- Can adjust expiration time in backend

## Future Enhancements

1. **User Registration**: Add signup functionality
2. **Password Reset**: Email-based password recovery
3. **Role-Based Access**: Different permissions for admin/users
4. **Session Management**: Track active sessions
5. **OAuth Integration**: Google/GitHub login
6. **API Rate Limiting**: Per-user API quotas