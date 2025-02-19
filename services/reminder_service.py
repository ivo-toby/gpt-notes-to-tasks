"""
Reminder service for macOS.

This module provides functionality to interact with the macOS Reminders app,
allowing the addition of tasks to the default Work list.
"""

import applescript


class ReminderService:
    """
    Service for managing reminders in macOS Reminders app.

    This service provides methods to add tasks to the Reminders app
    with user confirmation.
    """

    @staticmethod
    def add_to_reminders(task: str) -> bool:
        """
        Add a task to the Work list in Reminders app with user confirmation.

        Args:
            task (str): Task description to add as a reminder

        Returns:
            bool: True if task was added successfully, False otherwise
        """
        try:
            user_input = input(
                f"Do you want to add the task '{task}' to reminders? (y/n): "
            ).lower()

            if user_input != "y":
                print("Task not added to reminders.")
                return False

            script = f"""
            tell application "Reminders"
                try
                    set mylist to list "Work"
                    tell mylist
                        make new reminder with properties {{name:"{task}"}}
                    end tell
                    return true
                on error errMsg
                    return false
                end try
            end tell
            """

            result = applescript.run(script)
            if result:
                print(f"Task '{task}' added to Work list in Reminders.")
                return True
            else:
                print("Failed to add task to Reminders.")
                return False

        except Exception as e:
            print(f"Error adding reminder: {str(e)}")
            return False
