"""Domain layer initialization

WHY: The domain layer is the CORE of the application.
It contains zero infrastructure dependencies - only pure business logic.

This layer can be tested WITHOUT:
- AWS credentials
- Database connections
- Network access
- External services

If you import boto3, requests, or any infrastructure library here,
you've violated Clean Architecture.
"""
