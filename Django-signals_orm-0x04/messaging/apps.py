from django.apps import AppConfig

class MessagingConfig(AppConfig):
    name = 'messaging'
    verbose_name = "Messaging"

    def ready(self):
        # Import signals so they are registered when Django starts
        import messaging.signals  # noqa: F401

