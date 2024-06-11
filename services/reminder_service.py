import applescript


class ReminderService:
    @staticmethod
    def add_to_reminders(task):
        user_input = input(
            f"Do you want to add the task '{task}' to reminders? (y/n): "
        )
        if user_input.lower() == "y":
            script = f"""
            tell application "Reminders"
                set myRemind to (current date) + 1 * days
                set the time of myRemind to 9 * hours
                make new reminder with properties {{name:"{task}", due date:myRemind}}
            end tell
            """
            applescript.run(script)
        else:
            print("Task not added to reminders.")
