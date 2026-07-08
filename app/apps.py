"""
CardeTrade Django App Configuration

This module configures the 'app' Django application.
It's responsible for:
- Setting the app name
- Configuring the default auto field type
- Loading signals when the app is ready

The ready() method is called when Django starts up.
It imports signals to ensure they are connected.
"""

from django.apps import AppConfig


class AppConfig(AppConfig):
    """
    Main application configuration for CardeTrade.

    Attributes:
        default_auto_field: Use BigAutoField for primary keys (recommended)
        name: The app name as used in INSTALLED_APPS
    """
    default_auto_field = 'django.db.models.BigAutoField'  # Use 64-bit integers for PKs
    name = 'app'  # App name matches the app directory

    def ready(self):
        """
        Called when Django starts up.

        This method imports signals to ensure they are connected.
        Signals must be imported here (not at module level) to avoid
        circular import issues.
        """
        import app.signals  # Connect signal handlers
