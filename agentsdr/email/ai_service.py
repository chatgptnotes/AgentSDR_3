"""
AI Service for Email Classification and Response Drafting
InboxAI - Lindy AI-like Email Automation Platform
"""

import os
import re
from typing import Dict, Any, List, Optional
from openai import OpenAI

from agentsdr.email.models import EmailCategory, Sentiment


class AIService:
    """AI-powered email processing service using OpenAI GPT-4"""

    def __init__(self):
        """Initialize OpenAI client"""
        self.client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        self.model = os.getenv('OPENAI_MODEL', 'gpt-4')
        self.temperature = float(os.getenv('OPENAI_TEMPERATURE', '0.7'))
        self.max_tokens = int(os.getenv('OPENAI_MAX_TOKENS', '2000'))

    def classify_email(
        self,
        subject: str,
        body: str,
        from_email: str,
        user_id: str,
        user_preferences: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Classify an email using AI

        Args:
            subject: Email subject
            body: Email body (plain text)
            from_email: Sender email address
            user_id: User ID for personalization
            user_preferences: Optional user classification preferences

        Returns:
            Classification result dictionary
        """
        # Prepare classification prompt
        prompt = self._build_classification_prompt(
            subject, body, from_email, user_preferences
        )

        try:
            # Call OpenAI API
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert email triage assistant. Classify emails as Urgent, FYI, or Archive based on content, sender, and context. Provide confidence scores, reasoning, keywords, sentiment analysis, and actionability."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=self.temperature,
                max_tokens=1000,
                response_format={"type": "json_object"}
            )

            # Parse response
            result = eval(response.choices[0].message.content)

            # Structure the classification
            classification = {
                "category": result.get("category", "fyi").lower(),
                "confidence_score": float(result.get("confidence", 0.8)),
                "reasoning": result.get("reasoning", ""),
                "priority_score": int(result.get("priority", 50)),
                "keywords": result.get("keywords", []),
                "sentiment": result.get("sentiment", "neutral").lower(),
                "action_required": result.get("action_required", False),
                "estimated_response_time": result.get("estimated_response_time", ""),
                "ai_model": self.model,
                "entities": result.get("entities", {}),
            }

            return classification

        except Exception as e:
            print(f"Error classifying email: {e}")
            # Return default classification
            return {
                "category": "fyi",
                "confidence_score": 0.5,
                "reasoning": f"Classification failed: {str(e)}",
                "priority_score": 50,
                "keywords": [],
                "sentiment": "neutral",
                "action_required": False,
                "ai_model": self.model,
            }

    def _build_classification_prompt(
        self,
        subject: str,
        body: str,
        from_email: str,
        user_preferences: Optional[Dict[str, Any]] = None
    ) -> str:
        """Build the classification prompt"""

        # Truncate body if too long
        max_body_length = 2000
        truncated_body = body[:max_body_length] if body else ""
        if len(body or "") > max_body_length:
            truncated_body += "... [truncated]"

        prompt = f"""Classify this email into one of three categories: Urgent, FYI, or Archive.

Email Details:
- From: {from_email}
- Subject: {subject}
- Body: {truncated_body}

Classification Criteria:
- **Urgent**: Requires immediate attention, action items, time-sensitive, from important contacts, requests for response
- **FYI**: Informational, newsletters, updates, no immediate action needed, read later
- **Archive**: Promotional, spam, irrelevant, automated notifications, unimportant

"""

        if user_preferences:
            prompt += f"\nUser Preferences:\n{user_preferences}\n"

        prompt += """
Respond in JSON format with:
{
    "category": "urgent" | "fyi" | "archive",
    "confidence": 0.0-1.0,
    "reasoning": "brief explanation",
    "priority": 0-100,
    "keywords": ["keyword1", "keyword2"],
    "entities": {"people": [], "organizations": [], "dates": []},
    "sentiment": "positive" | "neutral" | "negative",
    "action_required": true | false,
    "estimated_response_time": "24 hours" | "within 1 week" | ""
}
"""

        return prompt

    def draft_response(
        self,
        subject: str,
        body: str,
        from_email: str,
        user_id: str,
        tone: str = "professional",
        key_points: Optional[List[str]] = None,
        custom_instructions: Optional[str] = None,
        user_writing_samples: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Draft an email response using AI

        Args:
            subject: Original email subject
            body: Original email body
            from_email: Sender email
            user_id: User ID
            tone: Response tone (professional, friendly, formal, casual)
            key_points: Key points to include in response
            custom_instructions: Custom drafting instructions
            user_writing_samples: Sample emails to match writing style

        Returns:
            Draft response dictionary
        """
        # Build draft prompt
        prompt = self._build_draft_prompt(
            subject, body, from_email, tone, key_points,
            custom_instructions, user_writing_samples
        )

        try:
            # Call OpenAI API
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": f"You are an expert email response writer. Draft {tone} email responses that match the user's writing style. Be concise, clear, and actionable."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=self.temperature,
                max_tokens=self.max_tokens,
            )

            # Extract draft
            draft_text = response.choices[0].message.content.strip()

            # Calculate tokens used
            tokens_used = response.usage.total_tokens

            # Extract subject and body from draft
            draft_subject, draft_body = self._parse_draft(draft_text, subject)

            draft = {
                "draft_subject": draft_subject,
                "draft_body": draft_body,
                "tone": tone,
                "style_match_score": 0.85,  # Placeholder - would calculate from samples
                "ai_model": self.model,
                "tokens_used": tokens_used,
            }

            return draft

        except Exception as e:
            print(f"Error drafting email: {e}")
            return {
                "draft_subject": f"Re: {subject}",
                "draft_body": f"Error generating draft: {str(e)}",
                "tone": tone,
                "ai_model": self.model,
                "tokens_used": 0,
            }

    def _build_draft_prompt(
        self,
        subject: str,
        body: str,
        from_email: str,
        tone: str,
        key_points: Optional[List[str]],
        custom_instructions: Optional[str],
        user_writing_samples: Optional[List[str]]
    ) -> str:
        """Build the draft response prompt"""

        # Truncate body if too long
        max_body_length = 1500
        truncated_body = body[:max_body_length] if body else ""
        if len(body or "") > max_body_length:
            truncated_body += "... [truncated]"

        prompt = f"""Draft a {tone} email response to the following email:

Original Email:
From: {from_email}
Subject: {subject}
Body:
{truncated_body}

"""

        if key_points:
            prompt += f"\nKey Points to Address:\n"
            for i, point in enumerate(key_points, 1):
                prompt += f"{i}. {point}\n"

        if custom_instructions:
            prompt += f"\nCustom Instructions:\n{custom_instructions}\n"

        if user_writing_samples:
            prompt += f"\nWriting Style Reference (match this style):\n"
            for i, sample in enumerate(user_writing_samples[:2], 1):
                prompt += f"\nSample {i}:\n{sample[:300]}...\n"

        prompt += f"""
Requirements:
- Tone: {tone}
- Be concise and clear (2-4 paragraphs max)
- Address all key points mentioned in the original email
- Include appropriate greeting and closing
- Professional and courteous
- Actionable and specific

Format your response as:
Subject: [proposed subject line]

[email body including greeting, content, and closing]
"""

        return prompt

    def _parse_draft(self, draft_text: str, original_subject: str) -> tuple:
        """Parse draft text to extract subject and body"""

        # Try to extract subject line
        subject_match = re.search(r'Subject:\s*(.+?)\n', draft_text, re.IGNORECASE)

        if subject_match:
            draft_subject = subject_match.group(1).strip()
            # Remove subject line from body
            draft_body = re.sub(r'Subject:.+?\n\n?', '', draft_text, count=1, flags=re.IGNORECASE).strip()
        else:
            draft_subject = f"Re: {original_subject}"
            draft_body = draft_text.strip()

        return draft_subject, draft_body

    def analyze_sentiment(self, text: str) -> str:
        """
        Analyze sentiment of text

        Args:
            text: Text to analyze

        Returns:
            Sentiment: positive, neutral, or negative
        """
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "Analyze the sentiment of the text. Respond with only one word: positive, neutral, or negative."
                    },
                    {
                        "role": "user",
                        "content": text[:500]  # Limit to 500 chars
                    }
                ],
                temperature=0.3,
                max_tokens=10,
            )

            sentiment = response.choices[0].message.content.strip().lower()

            if sentiment in ["positive", "neutral", "negative"]:
                return sentiment

            return "neutral"

        except Exception as e:
            print(f"Error analyzing sentiment: {e}")
            return "neutral"

    def extract_entities(self, text: str) -> Dict[str, List[str]]:
        """
        Extract entities from text (people, organizations, dates)

        Args:
            text: Text to analyze

        Returns:
            Dictionary of entities
        """
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "Extract people, organizations, and dates from the text. Return as JSON: {\"people\": [], \"organizations\": [], \"dates\": []}"
                    },
                    {
                        "role": "user",
                        "content": text[:1000]  # Limit to 1000 chars
                    }
                ],
                temperature=0.3,
                max_tokens=200,
                response_format={"type": "json_object"}
            )

            entities = eval(response.choices[0].message.content)
            return entities

        except Exception as e:
            print(f"Error extracting entities: {e}")
            return {"people": [], "organizations": [], "dates": []}
