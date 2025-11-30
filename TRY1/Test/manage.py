#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys


def main():
    """Run administrative tasks."""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Test.settings')
    try:
        from django.core.management import execute_from_command_line, call_command
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc

    # --- AUTO RUN generate_quiz WHEN STARTING runserver (OPTIONAL) ---
    # Set AUTO_GENERATE_QUIZ=1 (or true) to enable; optional GENERATE_QUIZ_COUNT controls number.
    if 'runserver' in sys.argv and os.getenv('AUTO_GENERATE_QUIZ', '').lower() in ('1', 'true', 'yes'):
        try:
            count = int(os.getenv('GENERATE_QUIZ_COUNT', '10'))
            print(f"[startup] AUTO_GENERATE_QUIZ detected — running management command: generate_quiz --count {count}")
            call_command('generate_quiz', count=count)
        except Exception as e:
            # Ne bloque pas le démarrage du serveur si la génération échoue
            print(f"[startup] Error running generate_quiz: {e}")

    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()