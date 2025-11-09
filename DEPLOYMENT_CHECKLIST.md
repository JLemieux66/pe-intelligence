# 🚀 Production Deployment Checklist

## Pre-Deployment Setup

### Environment Variables
- [ ] Set `OPENAI_API_KEY` in production environment
- [ ] Generate secure `JWT_SECRET_KEY` (32+ characters)
- [ ] Create admin password hash: `python -c "from backend.auth import hash_password; print(hash_password('your-password'))"`
- [ ] Set `DATABASE_URL` for production database
- [ ] Configure `ALLOWED_ORIGINS` with your frontend domain

### Database Setup
- [ ] Create production PostgreSQL database
- [ ] Run database migrations/setup
- [ ] Verify database connectivity

### Security
- [ ] Review CORS settings in `backend/main.py`
- [ ] Ensure JWT secret is secure and unique
- [ ] Verify admin credentials are properly hashed
- [ ] Check that sensitive data is not in version control

## Deployment Steps

### Backend (Railway)
```bash
# Railway deployment is configured via railway.json
git push origin main
```

### Frontend (Vercel)
```bash
# Vercel deployment is configured via vercel.json
# Update API_BASE_URL in frontend to point to production backend
```

### Post-Deployment Verification
- [ ] Test authentication endpoints
- [ ] Verify similar companies API works
- [ ] Check frontend loads and connects to backend
- [ ] Test company search and modal functionality
- [ ] Verify similar companies tab displays correctly

## Monitoring & Maintenance
- [ ] Set up error monitoring (Sentry recommended)
- [ ] Configure logging levels
- [ ] Set up database backups
- [ ] Monitor API usage and costs (OpenAI)
- [ ] Set up health checks

## Performance Optimization
- [ ] Enable database connection pooling
- [ ] Configure caching for similar companies results
- [ ] Optimize frontend bundle size
- [ ] Set up CDN for static assets