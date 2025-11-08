# 🔐 Security Setup Guide

## Critical: Admin Password Configuration

⚠️ **IMPORTANT**: The authentication system now uses bcrypt password hashing. You **must** configure an admin password before deploying.

## Step 1: Generate Password Hash

Run this command to generate a secure password hash:

```bash
python -m backend.auth YourSecurePassword123
```

**Example output:**
```
Bcrypt password hash generated successfully!

ADMIN_PASSWORD_HASH=$2b$12$HvPJBGur1A6mxvI5QRIPHundESYLsWwpNqu0T4ltLrj7KmBXU5tFK

Set this in your environment variables (.env file or Railway/Vercel):
  1. Copy the hash above
  2. Add to .env: ADMIN_PASSWORD_HASH=<paste-hash-here>
  3. Also set ADMIN_EMAIL if different from default
```

## Step 2: Configure Environment Variables

### For Local Development

Create a `.env` file in the project root:

```env
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/pe_intelligence

# JWT Configuration
JWT_SECRET_KEY=your-secret-jwt-key-change-in-production-min-32-chars

# Admin Credentials
ADMIN_EMAIL=your-admin@example.com
ADMIN_PASSWORD_HASH=$2b$12$your-generated-hash-here
```

### For Production (Railway/Vercel)

Set these environment variables in your hosting platform:

1. **Railway**: Go to your project → Variables → Add these:
   - `DATABASE_URL` (automatically provided by Railway if using Railway PostgreSQL)
   - `JWT_SECRET_KEY` 
   - `ADMIN_EMAIL`
   - `ADMIN_PASSWORD_HASH`

2. **Vercel/Other platforms**: Add the same variables in your platform's environment variable settings

## Step 3: Generate Secure JWT Secret

For production, generate a strong JWT secret:

```bash
# Using Python
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Using OpenSSL
openssl rand -base64 32
```

Copy the output and set it as `JWT_SECRET_KEY` in your environment variables.

## Security Best Practices

### Password Requirements
- ✅ Minimum 12 characters
- ✅ Mix of uppercase and lowercase letters
- ✅ Include numbers
- ✅ Include special characters (!@#$%^&*)
- ❌ Don't use common words or patterns
- ❌ Don't reuse passwords from other services

### Production Checklist
- [ ] Generated strong admin password
- [ ] Set `ADMIN_PASSWORD_HASH` in environment variables
- [ ] Generated and set secure `JWT_SECRET_KEY` (min 32 characters)
- [ ] Configured correct `ADMIN_EMAIL`
- [ ] Set up `DATABASE_URL` with secure credentials
- [ ] Enabled HTTPS for production deployment
- [ ] Restricted CORS origins (update `backend/api_v2.py`)
- [ ] Never committed `.env` files to version control

### CORS Configuration

By default, the API allows all origins (`allow_origins=["*"]`). For production, restrict this:

**Edit `backend/api_v2.py`:**

```python
# Replace this:
allow_origins=["*"],

# With your actual frontend domain(s):
allow_origins=[
    "https://your-frontend-domain.com",
    "https://www.your-frontend-domain.com",
],
```

## Testing Authentication

Test that authentication works correctly:

```bash
# Start the backend
uvicorn backend.api_v2:app --reload

# In another terminal, test login
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"your-admin@example.com","password":"YourSecurePassword123"}'
```

**Expected response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "email": "your-admin@example.com"
}
```

## Troubleshooting

### Error: "Admin password not configured"
- You forgot to set `ADMIN_PASSWORD_HASH` in environment variables
- Solution: Generate hash and add to `.env` or hosting platform

### Error: "Invalid email or password"
- Check that `ADMIN_EMAIL` matches the email you're using
- Verify you generated the hash with the correct password
- Ensure the hash is complete (starts with `$2b$12$`)

### Backend fails to start
- Check all required environment variables are set
- Verify database connection (`DATABASE_URL`)
- Check logs for specific error messages

## Password Rotation

To change the admin password:

1. Generate a new hash with the new password
2. Update `ADMIN_PASSWORD_HASH` in environment variables
3. Restart the application
4. Existing JWT tokens will remain valid until expiration (8 hours)

## What Changed?

### Before (INSECURE ❌)
```python
def authenticate_admin(email: str, password: str):
    if email != ADMIN_EMAIL:
        return None
    # Accept ANY password - SECURITY VULNERABILITY!
    return {"email": email, "role": "admin"}
```

### After (SECURE ✅)
```python
def authenticate_admin(email: str, password: str):
    if email != ADMIN_EMAIL:
        return None
    if not ADMIN_PASSWORD_HASH:
        raise HTTPException(status_code=500, detail="Password not configured")
    # Verify password using bcrypt
    if not verify_password(password, ADMIN_PASSWORD_HASH):
        return None
    return {"email": email, "role": "admin"}
```

## Support

If you encounter issues, check:
1. This documentation
2. Main README.md
3. Create a GitHub issue with details

---

**Last Updated**: 2025-11-08  
**Security Level**: Production-Ready with Bcrypt
