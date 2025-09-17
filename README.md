# Django Cinema Backend

[![Thumnail.jpg](https://i.postimg.cc/44p56HMS/Thumnail.jpg)](https://postimg.cc/RqVK9hv7)

A production-grade backend for a subscription-based video streaming platform. It exposes REST APIs for content management (titles, seasons, episodes), authentication and user subscriptions, payments (Stripe), and chunked file uploads to AWS S3 — with background jobs via Celery and Redis.

>[**Read Documentation**](https://deepwiki.com/h0pers/django-cinema-backend/1-overview)

---

## Features

- **Django + DRF** REST API with OpenAPI schema and interactive docs.
- **Domain-oriented apps:** `cinema`, `payments`, `uploads`, `custom_user`, and shared `core`.
- **Auth:** JWT (cookie-based), `django-allauth` integration, object-level permissions via `django-guardian`.
- **Payments:** Stripe checkout, subscriptions, webhooks, and transaction history.
- **Uploads:** Multipart/chunked direct-to-S3 uploads with presigned URLs and file search.
- **Background jobs:** Celery with Redis (broker + result backend).
- **Containers:** Dockerized for dev and prod, Nginx in front for static/media and proxying.
- **Security:** HSTS, optional SSL redirect, CORS/CSRF controls, reverse-proxy headers.

---

## Tech Stack

- **Core:** Python 3.11, Django 4.2, Django REST Framework, drf-spectacular
- **Storage:** PostgreSQL (prod), SQLite (dev fallback), Redis
- **Infra:** Docker, docker-compose, Nginx, Gunicorn
- **External:** AWS S3 + CloudFront, Stripe
- **Async:** Celery, Flower (dev monitoring)

---

## Quick Start

> **Requirements:** Docker & Docker Compose installed.

### Development
Start the full local stack in debug mode and rebuild images when needed. Ideal for day-to-day development with hot reload, verbose logs, and developer-friendly defaults.
```bash
docker compose -f docker-compose.debug.yml up --build
```

### Testing
Run the project’s test suite in an ephemeral container built from the image. No state is kept between runs, which makes this suitable for CI.
```bash
docker run --rm django-docker-template:master ./pytest.sh
```
### Production
Launch the production stack with Traefik and automatic Let’s Encrypt certificates. Replace your.domain.com with your actual domain (ensure DNS points to the host) and verify your .env is configured.
```bash
MY_DOMAIN=your.domain.com docker compose -f docker-compose.yml -f docker-compose.tls.yml up --build -d
```
