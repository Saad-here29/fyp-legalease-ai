You are now acting as a Senior Software Architect, Senior MERN Stack Engineer, AI Systems Engineer, UI/UX Designer, DevOps Engineer, Database Architect, QA Engineer, and Technical Documentation Expert.

PROJECT CONTEXT:
I am rebuilding my Final Year Project (FYP-1) from scratch in a professional way because our previous implementation had:

* weak UI/UX design
* poor folder structure
* inconsistent backend logic
* API failures
* incomplete AI chatbot module
* poor architecture understanding
* missing iteration 2 modules
* weak integration between frontend/backend
* weak testing implementation

The project is:
“LegalEase AI – AI-Powered Online Lawyer Management and Legal Assistance Platform”

IMPORTANT:
You MUST first analyze ALL attached files, documents, reports, diagrams, screenshots, PDFs, images, and FYP-related materials inside the project folder before generating anything.

CRITICAL RULE:
The FINAL REPORT is the PRIMARY SOURCE OF TRUTH.
If there are conflicts between Mid Report and Final Report:

* ALWAYS follow the FINAL REPORT.
* Treat the Mid Report only as historical reference.

====================================================
YOUR FIRST TASK
===============

STEP 1:
Analyze all uploaded files and extract:

* Project overview
* Problem statement
* Existing Pakistani legal domain problems
* Proposed solution
* Functional requirements
* Non-functional requirements
* Unit testing requirements
* Architecture
* Layered architecture
* Domain model
* ERD
* Class diagram
* Use cases
* User roles
* Module descriptions
* Tech stack
* APIs
* AI features
* Database design
* Security requirements
* Iteration commitments
* Testing strategy
* Algorithms
* Datasets
* AI model requirements
* OCR requirements
* AI Legal Research requirements
* Chatbot requirements
* Constraints
* UI expectations
* Deployment expectations

Then generate a COMPLETE SYSTEM UNDERSTANDING DOCUMENT.

====================================================
CURRENT PROJECT STATUS
======================

Iteration 1 committed modules:

1. AI Chatbot
2. Case Management

Reality:

* AI chatbot incomplete
* APIs unstable
* logic issues
* poor UI
* poor architecture
* weak backend integration

Iteration 2 committed modules:
3. AI Legal Research
4. OCR & Document Analysis

Reality:

* Not implemented yet

NOW THE GOAL:
We need to rebuild and properly implement ALL FOUR MODULES professionally before demo.

====================================================
MAIN OBJECTIVE
==============

Rebuild the ENTIRE system professionally with:

* enterprise-level folder structure
* scalable architecture
* modular backend
* professional UI/UX
* reusable components
* proper API handling
* AI integrations
* clean database design
* secure authentication
* role-based dashboards
* unit testing
* proper GitHub commit workflow
* documentation alignment with Final Report

====================================================
PHASE 1 — SYSTEM RESTRUCTURING
==============================

Your FIRST implementation task:

Create a PROFESSIONAL project structure that:

* any non-technical person can understand
* follows enterprise MERN practices
* separates concerns properly
* supports scalability
* supports future deployment
* supports AI services cleanly

Use:
Frontend:

* React
* Vite
* TailwindCSS
* Framer Motion
* React Router
* Zustand or Redux Toolkit
* Axios
* React Query
* ShadCN/UI

Backend:

* Node.js
* Express.js
* MongoDB
* Mongoose
* JWT Authentication
* Role-Based Access Control
* Multer
* OCR services
* OpenAI/Claude-compatible AI layer
* Vector database support if needed

Testing:

* Jest
* React Testing Library
* Supertest

Dev Tools:

* ESLint
* Prettier
* Husky
* dotenv
* nodemon

====================================================
FOLDER STRUCTURE REQUIREMENTS
=============================

Create:

1. frontend/
2. backend/
3. docs/
4. testing/
5. assets/
6. ai-services/
7. scripts/

Inside frontend:

* components/
* pages/
* layouts/
* hooks/
* services/
* api/
* store/
* utils/
* animations/
* routes/
* constants/
* styles/
* dashboard/
* auth/
* chatbot/
* legal-research/
* ocr/
* case-management/

Inside backend:

* config/
* controllers/
* routes/
* middlewares/
* services/
* repositories/
* models/
* validators/
* utils/
* uploads/
* ai/
* ocr/
* legal-research/
* chatbot/
* case-management/
* tests/

You MUST explain WHY each folder exists.

====================================================
PHASE 2 — UI/UX REDESIGN
========================

We need a PREMIUM FINAL YEAR PROJECT UI.

Design philosophy:

* modern SaaS legal-tech platform
* animated but professional
* dark elegant theme
* glassmorphism where appropriate
* legal-tech inspired colors
* modern typography
* smooth transitions
* responsive everywhere
* polished spacing
* premium dashboard feel

Use:

* Framer Motion
* TailwindCSS animations
* gradient backgrounds
* animated cards
* hover effects
* loading skeletons
* modern charts
* reusable UI components

====================================================
LANDING PAGE REQUIREMENTS
=========================

Create:

* Hero section
* Animated legal AI assistant visualization
* Lawyer & client illustrations
* Statistics section
* AI capabilities section
* Features showcase
* Legal services section
* Testimonials
* Workflow section
* Call-to-action sections
* Beautiful footer

Must feel like:
“startup-level legal AI platform”

====================================================
AUTHENTICATION PAGES
====================

Build:

1. Welcome selection page
2. Login page
3. Signup page
4. Forgot password
5. OTP verification
6. Role selection

Roles:

* Client
* Lawyer
* Admin

Each role should have:

* separate dashboard
* separate sidebar
* separate permissions
* separate navbar options

====================================================
DASHBOARD REQUIREMENTS
======================

CLIENT DASHBOARD:

* AI legal chatbot
* Case tracking
* OCR uploads
* Legal research
* Appointment booking
* Notifications
* Profile management

LAWYER DASHBOARD:

* Client management
* Case management
* AI assistance
* Document analysis
* Research tools
* Schedule management

ADMIN DASHBOARD:

* User management
* Lawyer verification
* Analytics
* Reports
* System monitoring
* AI usage monitoring

====================================================
PHASE 3 — BACKEND & LOGIC
=========================

Create COMPLETE backend architecture.

Implement:

* clean controllers
* service layer
* repository pattern
* middleware architecture
* centralized error handling
* logging
* validation
* authentication
* authorization
* file upload handling
* AI request handling
* OCR pipeline
* API retry mechanisms
* API fallback mechanisms

====================================================
DATABASE REQUIREMENTS
=====================

Design proper MongoDB schemas for:

* Users
* Lawyers
* Clients
* Cases
* Appointments
* Messages
* Chat history
* OCR documents
* Legal research history
* Notifications
* AI usage logs
* Reports

Generate:

* schema relationships
* indexes
* validations
* timestamps
* role-based structures

====================================================
AI MODULE REQUIREMENTS
======================

MODULE 1 — AI CHATBOT:
Features:

* legal question answering
* context memory
* chat history
* conversation persistence
* citation-ready answers
* multilingual support
* Pakistani legal context

Need:

* prompt engineering structure
* retrieval architecture
* vector storage plan
* fallback handling
* token optimization

====================================================
MODULE 2 — CASE MANAGEMENT
==========================

Features:

* create cases
* assign lawyers
* update status
* hearings
* evidence upload
* case timeline
* notifications

Need:

* secure workflows
* RBAC validation
* audit logs

====================================================
MODULE 3 — AI LEGAL RESEARCH
============================

Features:

* legal precedent search
* smart legal summarization
* keyword extraction
* citation assistance
* semantic search
* Pakistani law context

Need:

* embedding pipeline
* vector database planning
* document indexing
* RAG architecture

====================================================
MODULE 4 — OCR & DOCUMENT ANALYSIS
==================================

Features:

* upload legal documents
* OCR extraction
* summarize documents
* identify clauses
* extract important entities
* searchable document content

Need:

* OCR pipeline
* preprocessing pipeline
* document parser
* AI summarizer
* searchable storage

====================================================
AI & DATASET REQUIREMENTS
=========================

Recommend:

* best AI models
* cheapest scalable options
* APIs vs local models
* fine-tuning possibilities
* embedding models
* OCR models
* Pakistani legal dataset ideas
* legal document preprocessing methods

Explain:

* whether fine-tuning is needed
* whether RAG is better
* how embeddings will work
* how documents will be indexed
* storage strategy

====================================================
API ARCHITECTURE
================

Generate:

* complete REST API structure
* endpoint naming conventions
* request/response structures
* authentication flow
* error handling standards
* API documentation structure

====================================================
NON-FUNCTIONAL REQUIREMENTS
===========================

Implementation MUST satisfy:

* scalability
* maintainability
* reliability
* security
* performance
* responsiveness
* availability
* usability
* modularity

====================================================
TESTING REQUIREMENTS
====================

VERY IMPORTANT:
The final report includes unit testing.

So implement:

* unit testing structure
* API tests
* frontend component tests
* authentication tests
* chatbot tests
* OCR tests
* case management tests

Use:

* Jest
* Supertest
* React Testing Library

Generate:

* testing folder structure
* sample tests
* testing strategy

====================================================
GITHUB WORKFLOW REQUIREMENTS
============================

We MUST maintain GitHub history professionally.

Create:

* branch strategy
* commit strategy
* naming conventions
* PR strategy
* sprint workflow

Commit examples:

* feat(auth): implement JWT login system
* feat(chatbot): add AI conversation persistence
* fix(api): resolve retry middleware issue
* refactor(ui): improve dashboard responsiveness

====================================================
IMPORTANT DEVELOPMENT RULES
===========================

1. NEVER generate messy code.
2. Use scalable architecture.
3. Use reusable components.
4. Maintain clean coding standards.
5. Add comments where necessary.
6. Follow MERN best practices.
7. Follow production-level architecture.
8. Avoid hardcoded values.
9. Create environment variable setup.
10. Use proper error handling.
11. Maintain separation of concerns.
12. Maintain consistent naming conventions.
13. Follow final report requirements carefully.
14. Maintain responsive design everywhere.
15. Use modern typography and spacing.
16. Keep the UI beautiful and professional.
17. Ensure backend and frontend integration is stable.
18. Ensure APIs are fault-tolerant.
19. Ensure AI services are modular.
20. Ensure codebase is demo-ready.

====================================================
OUTPUT FORMAT
=============

You must work in PHASES.

PHASE 1:

* Analyze documents
* Generate system understanding
* Generate architecture plan
* Generate implementation roadmap

PHASE 2:

* Create professional folder structure
* Explain every folder

PHASE 3:

* Create UI/UX design system
* Generate theme and component architecture

PHASE 4:

* Setup backend architecture

PHASE 5:

* Implement authentication

PHASE 6:

* Implement dashboards

PHASE 7:

* Implement AI chatbot

PHASE 8:

* Implement case management

PHASE 9:

* Implement legal research

PHASE 10:

* Implement OCR module

PHASE 11:

* Testing

PHASE 12:

* Deployment readiness

Do NOT rush.
Work professionally.
Always explain architectural decisions.
Always align implementation with the Final Report.
