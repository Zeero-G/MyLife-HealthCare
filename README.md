<br/><div align="center">
# 🏥 MYLIFE — Patient-Owned Healthcare Platform

**A privacy-first, interoperable health record system built for Sri Lanka**

[![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/Frontend-React%2FNext.js-61DAFB?logo=react&logoColor=black)](https://react.dev/)
[![Supabase](https://img.shields.io/badge/Database-Supabase-3ECF8E?logo=supabase&logoColor=white)](https://supabase.com/)
[![Railway/Render](https://img.shields.io/badge/Hosting-Railway%2FRender-Black?logo=railway&logoColor=white)](https://railway.app/)
[![Docker](https://img.shields.io/badge/Container-Docker-2496ED?logo=docker&logoColor=white)](https://docker.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

> **Give patients absolute control over their medical records.** MYLIFE connects patients, doctors, pharmacies, and laboratories in a single secure, interoperable ecosystem — with AI-powered record processing and full offline-first capability.

<img src="logos/logo.png" alt="MYLIFE Logo" width="200" />

</div>

---

See [architecture.md](architecture.md) for the full system architecture design, encompassing the platform's backend microservices built with FastAPI, React frontend, and Supabase integration.

---

## ✨ Key Features

- **Patient Ownership First:** Users retain full control over who sees which records and for how long via QR sharing and robust permission systems.
- **AI Processing:** Upload unstructured medical documents (images, PDFs) and let the Claude API automatically extract structured data and generate summaries.
- **Microservices Architecture:** 5 purpose-built, independent services managed over simple REST APIs for rapid development and scalable deployments without over-engineering.
- **Emergency Profiles:** Offline-accessible medical emergency data so first responders have the critical information they need instantly.
- **Family Accounts:** Centrally manage care for elderly parents or children with linked profiles, role-based access, and care-giver permissions.
- **Women's Health Tracking:** Built-in menstrual and pregnancy cycle tracking.
- **Fully Containerized:** Easy to deploy with Docker, managed locally via Docker Compose. No complicated Kubernetes or separate message brokers needed for MVP.

## 🚀 Getting Started

### Prerequisites

Make sure you have the following installed on your machine:
- [Docker & Docker Compose](https://www.docker.com/)
- [Node.js 18+](https://nodejs.org/) (for frontend development)
- [Python 3.10+](https://www.python.org/) (for extending microservices locally)
- A [Supabase](https://supabase.com) account (for DB, Auth, and Storage)

### Running Locally

1. **Clone the repository:**
   ```bash
   git clone https://github.com/your-username/mylife-healthcare.git
   cd mylife-healthcare
   ```

2. **Set up Environment Variables:**
   Copy the example environment files and fill in your Supabase connection strings, Claude API keys, etc.
   ```bash
   cp .env.example .env
   ```

3. **Start the Backend Microservices:**
   The entire backend stack is containerized. This spins up the NGINX API gateway and all 5 backend microservices natively.
   ```bash
   docker-compose up --build -d
   ```
   *The API Gateway will now be available on `http://localhost:80` routing specific paths (e.g. `/auth`, `/records`) to their respective microservices.*

4. **Start the Frontend:**
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

## 📁 Project Structure

```text
mylife/
├── frontend/               # React.js application
├── services/               # Microservices
│   ├── auth-service/       # Identity, JWT, role mgmt (Port 8001)
│   ├── medical-service/    # Medical records, QR sharing (Port 8002)
│   ├── family-service/     # Caregiver & tracked profiles (Port 8003)
│   ├── ai-service/         # Medical document extraction (Port 8004)
│   └── notification-service/# Emails & Push Notifications (Port 8005)
├── gateway/                # NGINX configuration (Port 80)
├── docker-compose.yml      # Orchestrates all backend services
└── architecture.md         # Full architecture and deployment plan
```

## ☁️ Deployment Strategy

For the MVP, we favor simplicity over complex orchestration:
- **Frontend** is deployed automatically to **Vercel** with native CI/CD.
- **Backend Microservices** are deployed via **Docker** on **Railway** or **Render**, linked together securely and scaled seamlessly. 
- **Database, Auth & Storage** are all handled by **Supabase**.

## 🤝 Contributing

We welcome contributions! Please check our [Issues](issues) board or open a pull request to submit bugs or suggest new features. Ensure you follow our code style guidelines for both Python (pep8/black) and TypeScript (Prettier/ESLint).

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.