from openai import OpenAI
from utils.config_loader import load_config


class OpenAIService:
    def __init__(self, api_key, model="gpt-4"):
        self.model = model
        self.client = OpenAI(
            api_key=api_key,
        )

    def chat_completion_with_function(self, messages, functions, function_call):
        response = self.client.chat.completions.create(
            model=self.model,
            temperature=0.7,
            messages=messages,
            functions=functions,
            function_call=function_call,
        )
        return response.choices[0].message

    def summarize_notes_and_identify_tasks(self, notes):
        prompt = f"""
Given the provided journal entries, please generate an easy-to-read daily journal in Markdown format, which captures all the knowledge, links, and facts from the journal entries for future reference. 
Following the summary, enumerate any actionable items identified within the journal entries. 
Conclude with a list of relevant tags, formatted in snake-case, that categorize the content or themes of the notes.

Example:
Journal entry: "[2024-05-21 02:38:09 PM] The team discussed the upcoming project launch, [focusing on the marketing strategy](http://www.link.com), budget allocations, and the final review of the product design. Tasks were assigned to finalize the promotional materials and secure additional funding."

Summary: "[02:38:09 PM] Discussed upcoming product launch, [marketing strategies](http://www.link.com), budgeting, and product design finalization."

Actionable Items:
1. Finalize promotional materials.
2. Secure additional funding.

Tags: project_launch, marketing_strategy, budget_allocation, product_design

Journal entries:\n{notes}"""
        messages = [
            {
                "role": "system",
                "content": "You are a helpful assistant and a genius summarizer.",
            },
            {"role": "user", "content": prompt},
        ]
        functions = [
            {
                "name": "summarize_notes_and_tasks",
                "description": "Provide a summary of the notes, list action items, and relevant tags",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "summary": {"type": "string"},
                        "tasks": {"type": "array", "items": {"type": "string"}},
                        "tags": {"type": "array", "items": {"type": "string"}},
                    },
                    "required": ["summary", "tasks", "tags"],
                },
            }
        ]
        function_call = {"name": "summarize_notes_and_tasks"}

        response = self.chat_completion_with_function(
            messages, functions, function_call
        )
        arguments = eval(response.function_call.arguments)

        return {
            "summary": arguments["summary"],
            "tasks": arguments["tasks"],
            "tags": arguments["tags"],
        }

    def generate_meeting_notes(self, notes):
        prompt = f"""
From the following journal entries, identify and extract details to create meeting notes in Markdown format based on this template:
# {{date}} Meeting Notes - {{meeting_subject}}
## Tags
{{tags}}
## Participants
- {{participant_1}}
- {{participant_2}}
## Meeting notes
{{meeting_notes}}
## Decisions
## Action items
## References

Example:
Journal entry: "[2024-05-22 01:00:00 PM] Meeting on Project X. Participants: Alice, Bob. Discussed project timelines, potential risks, and mitigation strategies. Decisions made to accelerate phase 1 and review phase 2 next week. Action items: Alice to draft phase 1 report, Bob to set up a client meeting. Reference: [Project docs](http://www.link.com)."

# 2024-05-22 Meeting Notes - Project X
## Tags
project_x, timeline, risks
## Participants
- Alice
- Bob
## Meeting notes
Discussed project timelines, potential risks, and mitigation strategies.
## Decisions
Accelerate phase 1 and review phase 2 next week.
## Action items
- Alice to draft phase 1 report.
- Bob to set up a client meeting.
## References
[Project docs](http://www.link.com)

Journal entries:\n{notes}"""
        messages = [
            {
                "role": "system",
                "content": "You are a helpful assistant and a genius summarizer.",
            },
            {"role": "user", "content": prompt},
        ]
        functions = [
            {
                "name": "create_meeting_notes",
                "description": "Generate meeting notes from provided journal entries",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "date": {"type": "string"},
                        "meeting_subject": {"type": "string"},
                        "tags": {"type": "string"},
                        "participants": {"type": "array", "items": {"type": "string"}},
                        "meeting_notes": {"type": "string"},
                        "decisions": {"type": "string"},
                        "action_items": {"type": "array", "items": {"type": "string"}},
                        "references": {"type": "string"},
                    },
                    "required": [
                        "date",
                        "meeting_subject",
                        "tags",
                        "participants",
                        "meeting_notes",
                    ],
                },
            }
        ]
        function_call = {"name": "create_meeting_notes"}

        response = self.chat_completion_with_function(
            messages, functions, function_call
        )
        return eval(response.function_call.arguments)

    def generate_weekly_summary(self, notes):
        prompt = f"""
From the following week's journal entries, generate a weekly summary in Markdown format. The summary should capture key points, any important discussions, and major events.

Example:
Journal entry: "[2024-05-20] Started phase 1 of Project Y. [2024-05-21] Team discussed marketing strategies for Product Z. [2024-05-22] Meeting on Project X."

Summary:
- Started phase 1 of Project Y.
- Discussed marketing strategies for Product Z.
- Held a meeting on Project X.

Weekly journal entries:\n{notes}"""
        messages = [
            {
                "role": "system",
                "content": "You are a helpful assistant and a genius summarizer.",
            },
            {"role": "user", "content": prompt},
        ]
        functions = [
            {
                "name": "generate_weekly_summary",
                "description": "Create a summary of the week's journal entries",
                "parameters": {"type": "string"},
            }
        ]
        function_call = {"name": "generate_weekly_summary"}

        response = self.chat_completion_with_function(
            messages, functions, function_call
        )
        return response.function_call.arguments

    def identify_accomplishments(self, notes):
        prompt = f"""
From the following week's journal entries, list all accomplishments in a concise manner.

Example:
Journal entry: "[2024-05-20] Started phase 1 of Project Y. Completed initial design draft. [2024-05-21] Achieved 10% increase in sales. [2024-05-22] Successful client presentation."

Accomplishments:
- Started phase 1 of Project Y.
- Completed initial design draft.
- Achieved 10% increase in sales.
- Successful client presentation.

Weekly journal entries:\n{notes}"""
        messages = [
            {
                "role": "system",
                "content": "You are a helpful assistant and a genius summarizer.",
            },
            {"role": "user", "content": prompt},
        ]
        functions = [
            {
                "name": "identify_accomplishments",
                "description": "Identify accomplishments from provided journal entries",
                "parameters": {
                    "type": "array",
                    "items": {"type": "string"},
                },
            }
        ]
        function_call = {"name": "identify_accomplishments"}

        response = self.chat_completion_with_function(
            messages, functions, function_call
        )
        return eval(response.function_call.arguments)

    def identify_learnings(self, notes):
        prompt = f"""
From the following week's journal entries, list all notable learnings in a concise manner.

Example:
Journal entry: "[2024-05-20] Learned about the new marketing automation tool. [2024-05-21] Team discussed best practices for remote work. [2024-05-22] Realized the importance of early client feedback in the development phase."

Learnings:
- Learned about the new marketing automation tool.
- Discussed best practices for remote work.
- Realized the importance of early client feedback.

Weekly journal entries:\n{notes}"""
        messages = [
            {
                "role": "system",
                "content": "You are a helpful assistant and a genius summarizer.",
            },
            {"role": "user", "content": prompt},
        ]
        functions = [
            {
                "name": "identify_learnings",
                "description": "Identify notable learnings from provided journal entries",
                "parameters": {
                    "type": "array",
                    "items": {"type": "string"},
                },
            }
        ]
        function_call = {"name": "identify_learnings"}

        response = self.chat_completion_with_function(
            messages, functions, function_call
        )
        return eval(response.function_call.arguments)
