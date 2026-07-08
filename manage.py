#!/usr/bin/env python
"""
CardeTrade Django Management Script

This is the command-line utility for administrative tasks.
It's the entry point for Django management commands.

Usage:
    python manage.py <command> [options]

Common Commands:
    python manage.py runserver          # Start development server
    python manage.py makemigrations     # Create database migrations
    python manage.py migrate            # Apply database migrations
    python manage.py createsuperuser    # Create admin user
    python manage.py test               # Run tests
    python manage.py shell              # Open Django shell
    python manage.py collectstatic      # Collect static files

This script sets up the Django environment and executes the requested command.
"""
import os
import sys


def main():
    """
    Run administrative tasks.

    This function:
    1. Sets the Django settings module
    2. Imports Django's command-line executor
    3. Executes the requested management command
    """
    # Set the settings module (default: cardetrade.settings)
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cardetrade.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    # Execute the management command from command line arguments
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    # Run main function when script is executed directly
    main()
