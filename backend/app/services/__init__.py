"""Service layer — business logic.

Each service orchestrates repositories, runs business rules, validates state
transitions, and writes audit logs. Controllers (API routers) should be thin
wrappers that delegate to a service.
"""
