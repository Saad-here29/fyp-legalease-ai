"""Repositories — the data access layer.

Repositories own the SQLAlchemy queries. Services should NEVER write raw
queries directly; they go through a repository so query logic stays testable
and swappable.
"""
