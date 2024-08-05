from openai import OpenAI
from utils.config_loader import load_config
import os
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np


class OpenAIService:
    def __init__(self, api_key, model="gpt-4o-mini"):
        self.model = model
        self.client = OpenAI(api_key=api_key)

    def generate_learning_title(self, learning):
        prompt = f"Generate a concise short title for the following learning. Do not use quotation marks in the title:\n\n{learning}"
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=50,
        )
        title = response.choices[0].message.content.strip()
        # Remove any remaining quotation marks, just in case
        return title.replace('"', "").replace("'", "")

    def generate_learning_tags(self, learning):
        prompt = f"Generate relevant tags for the following learning, formatted in snake-case, each tag should be prefixed with a #-sign, split the tags with a , :\n\n{learning}"
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=50,
        )
        return [tag.strip() for tag in response.choices[0].message.content.split(",")]

    def identify_related_learnings(self, learning, learnings_dir, max_candidates=10):
        learnings = []
        for filename in os.listdir(learnings_dir):
            if filename.endswith(".md"):
                with open(os.path.join(learnings_dir, filename), "r") as file:
                    content = file.read()
                    learnings.append({"filename": filename, "content": content})

        if not learnings:
            print("No existing learnings found to relate to.")
            return []

        # Step 1: Use TF-IDF and cosine similarity to find potential candidates
        vectorizer = TfidfVectorizer(stop_words="english")
        tfidf_matrix = vectorizer.fit_transform(
            [learning] + [l["content"] for l in learnings]
        )
        cosine_similarities = cosine_similarity(
            tfidf_matrix[0:1], tfidf_matrix[1:]
        ).flatten()
        related_docs_indices = cosine_similarities.argsort()[-max_candidates:][::-1]

        candidates = [learnings[i] for i in related_docs_indices]

        # Step 2: Use OpenAI to rank the candidates
        prompt = f"Given the following learning:\n\n{learning}\n\nRank the following learnings by relevance (most relevant first), returning only the numbers of the relevant ones:\n\n"
        for i, l in enumerate(candidates):
            prompt += f"{i+1}. {l['content'][:200]}...\n\n"

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=50,
        )

        try:
            related_indices = [
                int(index.strip())
                for index in response.choices[0].message.content.split(",")
                if index.strip().isdigit()
            ]
        except ValueError:
            print("No valid related learnings identified.")
            return []

        return [
            {
                "filename": candidates[i - 1]["filename"],
                "title": candidates[i - 1]["content"].split("\n")[0][2:],
            }
            for i in related_indices
            if 1 <= i <= len(candidates)
        ][:3]  # Limit to top 3 related learnings

    def chat_completion_with_function(self, messages, functions, function_call):
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                temperature=0.6,
                messages=messages,
                functions=functions,
                function_call=function_call,
            )
            return response.choices[0].message
        except Exception as e:
            print(f"An error occurred: {e}")
            return None

    def summarize_notes_and_identify_tasks(self, notes):
        prompt = f"""
        Given the provided journal entries, please generate an easy-to-read daily journal in Markdown format, which captures all the knowledge, links, and facts from the journal entries for future reference. 
        Following the summary, enumerate any actionable items identified within the journal entries that are actionable by the owner of the notes. 
        Conclude with a list of relevant tags, formatted in snake-case, that categorize the content or themes of the notes.
        
        Example:
        Journal entry: "[2024-05-21 02:38:09 PM] The team discussed the upcoming project launch, [focusing on the marketing strategy](http://www.link.com), budget allocations, and the final review of the product design. Tasks were assigned to finalize the promotional materials and secure additional funding."
        
        Summary: "[02:38:09 PM] Discussed upcoming product launch, [marketing strategies](http://www.link.com), budgeting, and product design finalization."
        
        Actionable Items:
        1. Finalize promotional materials.
        2. Secure additional funding.
        
        Tags: project_launch, marketing_strategy, budget_allocation, product_design
        
        Journal entries:\\n{notes}"""

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
                "description": "Create meeting notes from the journal entries.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "summary": {"type": "string"},
                        "actionable_items": {
                            "type": "array",
                            "items": {"type": "string"},
                        },
                        "tags": {"type": "array", "items": {"type": "string"}},
                    },
                    "required": ["summary", "actionable_items", "tags"],
                },
            }
        ]
        function_call = {"name": "create_meeting_notes"}

        response = self.chat_completion_with_function(
            messages, functions, function_call
        )
        if response:
            meeting_notes_list = eval(response.function_call.arguments)
            return meeting_notes_list
        else:
            return None

    def generate_weekly_summary(self, notes):
        prompt = f"""
        Given the provided journal entries, please generate an easy-to-read weekly journal in Markdown format, which captures all the knowledge, links, and facts from the journal entries for future reference. 
        Following the summary, create a section that enumerates accomplishments based on the journal entries. 
        Following the accomplishments, create a section called Learnings, and list any learnings identified within the journal entries.
        
        Conclude with a list of links extracted from the journal entries, formatted in Markdown and infer a title for each link based on the URL or context in which the link was originally found.
        
        Example:
        Journal entry: "[2024-05-21 02:38:09 PM] The team discussed the upcoming project launch, [focusing on the marketing strategy](http://www.link.com), budget allocations, and the final review of the product design. Tasks were assigned to finalize the promotional materials and secure additional funding."
        
        Summary: 
        - [2024-05-21 02:38:09 PM] Discussed upcoming product launch, focusing on the marketing strategy, budget allocations, and product design finalization.
        
        Accomplishments:
        - Finalized promotional materials.
        - Secured additional funding.
        
        Learnings:
        - Importance of clear communication in marketing strategies.
        - Budget allocation challenges.
        
        Links:
        - [Marketing Strategy](http://www.link.com)
        
        Weekly journal entries:
        {notes}
        """

        messages = [
            {
                "role": "system",
                "content": "You are a helpful assistant and a genius summarizer.",
            },
            {"role": "user", "content": prompt},
        ]

        try:
            response = self.client.chat.completions.create(
                model=self.model, messages=messages, max_tokens=1500
            )
            print(response)
            return response.choices[0].message.content
        except Exception as e:
            print(f"An error occurred: {e}")
            return None

    def generate_meeting_notes(self, notes):
        prompt = f"""
From the following journal entries, infer which entries may have been taken during a meeting or call. For each meeting or call, extract details to create meeting notes in Markdown format based on this template:
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
Journal entry: "[2024-05-22 04:00:00 PM] Call on Project Y. Participants: John. Discussed project budget, marketing strategies. Decisions made to accelerate phase 1 and review phase 2 next week. Action items: Alice to draft phase 1 report, Bob to set up a client meeting. Reference: [Project docs](http://www.link.com)."

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

# 2024-05-22 Meeting Notes - Project Y
## Tags
project_y, marketing, budget
## Participants
- John
## Meeting notes
Discussed project budget, marketing strategies.
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
                        "meetings": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "date": {"type": "string"},
                                    "meeting_subject": {"type": "string"},
                                    "tags": {"type": "string"},
                                    "participants": {
                                        "type": "array",
                                        "items": {"type": "string"},
                                    },
                                    "meeting_notes": {"type": "string"},
                                    "decisions": {"type": "string"},
                                    "action_items": {
                                        "type": "array",
                                        "items": {"type": "string"},
                                    },
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
                    },
                    "required": ["meetings"],
                },
            }
        ]
        function_call = {"name": "create_meeting_notes"}

        response = self.chat_completion_with_function(
            messages, functions, function_call
        )

        # Extract the arguments from the response function call
        meeting_notes_list = eval(response.function_call.arguments)

        return meeting_notes_list
