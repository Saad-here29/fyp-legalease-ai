"""Pydantic schemas — request bodies and response DTOs.

Naming convention:
    UserCreate    -> request body for POST /users
    UserUpdate    -> request body for PUT/PATCH /users/{id}
    UserRead      -> response body shape
    UserInDB      -> internal shape that includes hashed_password etc.
"""
