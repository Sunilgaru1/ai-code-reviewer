# 🤖 AI Code Reviewer (GitHub App Microservice)

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/)
[![Django](https://img.shields.io/badge/Django-5.0-092E20.svg)](https://www.djangoproject.com/)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED.svg)](https://www.docker.com/)
[![Celery](https://img.shields.io/badge/Celery-Distributed_Task_Queue-37814A.svg)](https://docs.celeryq.dev/)
[![Redis](https://img.shields.io/badge/Redis-Message_Broker-DC382D.svg)](https://redis.io/)
[![Google Gemini](https://img.shields.io/badge/AI-Google_Gemini_API-FFA000.svg)](https://ai.google.dev/)

An automated, asynchronous GitHub App that intercepts push and Pull Request webhooks to provide real-time, AI-driven code reviews using the Google Gemini LLM. 

![Project Demo](https://via.placeholder.com/800x400.png?text=Replace+this+image+with+a+GIF+of+your+bot+commenting+on+GitHub)
*(**Note:** Watch the 2-minute video demonstration of the bot in action [here](#).)*

## 🏗️ System Architecture & Engineering Decisions

When building webhook-driven applications, GitHub enforces a strict **10-second timeout**. Processing code through a Large Language Model (LLM) often takes 15–30 seconds, which would normally cause the webhook to fail. 

To solve this, I designed a **distributed microservices architecture**:
1. **API Gateway (Django + Gunicorn):** Instantly receives the GitHub payload, cryptographically verifies the `X-Hub-Signature-256`, and returns a `202 Accepted` response to GitHub within milliseconds.
2. **Message Broker (Redis):** The payload is serialized and pushed into a Redis queue.
3. **Background Workers (Celery):** An asynchronous worker picks up the task, generates a JWT using RSA Private Keys, exchanges it for a GitHub Installation Token, fetches the code diffs, and communicates with the Gemini API.
4. **Data Persistence (MySQL):** Stores webhook logs, metadata, and review history.

All services are fully containerized using **Docker Compose** for seamless local development and cloud deployment.

---

## ✨ Features
- **Zero-Friction Integration:** Acts as a native GitHub App. Developers never leave their repository; the AI comments directly on their commits and PRs.
- **Enterprise-Grade Security:** Utilizes `.pem` Private Key JWT authentication for GitHub API access. Validates all incoming payloads using HMAC-SHA256 signatures.
- **Production Ready:** Configured following the 12-Factor App methodology. Runs on a multi-threaded Gunicorn WSGI server with containerized database health checks.

---

## 🚀 Local Development Setup

Because the entire stack is containerized, getting the project running on your local machine takes less than 2 minutes.

### 1. Prerequisites
- Docker & Docker Compose installed.
- A GitHub App created in your GitHub Developer Settings.
- A Google Gemini API Key.

### 2. Environment Variables
Clone the repository and set up your environment variables:
```bash
git clone [https://github.com/Sunilgaru1/ai-code-reviewer.git](https://github.com/Sunilgaru1/ai-code-reviewer.git)
cd ai-code-reviewer
cp .env.example .env
