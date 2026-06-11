# RetailVision AI - Production Deployment Checklist

## Pre-Deployment

- [ ] Update `.env` with production values
- [ ] Set `ENVIRONMENT=production` and `DEBUG=False`
- [ ] Configure secure JWT secret
- [ ] Set strong PostgreSQL password
- [ ] Configure Redis authentication
- [ ] Update CORS origins with production domain
- [ ] Configure CCTV stream URLs
- [ ] Validate shelf zone configurations
- [ ] Set up SSL/TLS certificates
- [ ] Configure reverse proxy (Nginx/Traefik)
- [ ] Set up monitoring and logging
- [ ] Configure backup strategy for PostgreSQL
- [ ] Enable Redis persistence

## Infrastructure

- [ ] Set up production database backups
- [ ] Configure log rotation
- [ ] Set up monitoring dashboard
- [ ] Configure alerts for critical metrics
- [ ] Enable security scanning
- [ ] Set up rate limiting
- [ ] Configure DDoS protection

## Security

- [ ] Enable HTTPS only
- [ ] Configure HSTS headers
- [ ] Enable CORS restrictions
- [ ] Configure database encryption
- [ ] Set up secrets management (e.g., HashiCorp Vault)
- [ ] Enable API authentication
- [ ] Implement API rate limiting
- [ ] Set up Web Application Firewall (WAF)

## Performance

- [ ] Enable Redis caching
- [ ] Configure database connection pooling
- [ ] Enable CDN for static assets
- [ ] Set up auto-scaling if applicable
- [ ] Configure health checks
- [ ] Set up load balancing

## Deployment Commands

```bash
# Build production images
docker-compose build

# Start production services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down

# Backup database
docker exec retailvision_postgres pg_dump -U retailvision retailvision_db > backup.sql

# Restore database
docker exec -i retailvision_postgres psql -U retailvision retailvision_db < backup.sql
```

## Post-Deployment

- [ ] Verify all services are running
- [ ] Test API endpoints
- [ ] Test frontend dashboard
- [ ] Verify video ingestion
- [ ] Monitor performance metrics
- [ ] Check application logs
- [ ] Verify database connectivity
- [ ] Test Redis streams
- [ ] Verify backup process
- [ ] Set up monitoring alerts
