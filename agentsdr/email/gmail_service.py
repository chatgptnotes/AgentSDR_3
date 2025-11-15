"""
Gmail API Integration Service
InboxAI - Lindy AI-like Email Automation Platform
"""

import os
import base64
import email
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from bs4 import BeautifulSoup
import email_reply_parser


class GmailService:
    """Gmail API service for fetching and sending emails"""

    SCOPES = [
        'https://www.googleapis.com/auth/gmail.readonly',
        'https://www.googleapis.com/auth/gmail.send',
        'https://www.googleapis.com/auth/gmail.modify',
    ]

    def __init__(self, credentials: Optional[Dict[str, Any]] = None):
        """
        Initialize Gmail service

        Args:
            credentials: OAuth2 credentials dictionary
        """
        self.credentials = credentials
        self.service = None
        if credentials:
            self._build_service()

    def _build_service(self):
        """Build Gmail API service"""
        try:
            creds = Credentials.from_authorized_user_info(
                self.credentials,
                self.SCOPES
            )
            self.service = build('gmail', 'v1', credentials=creds)
        except Exception as e:
            print(f"Error building Gmail service: {e}")
            raise

    def fetch_emails(
        self,
        max_results: int = 50,
        query: str = None,
        after_date: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """
        Fetch emails from Gmail

        Args:
            max_results: Maximum number of emails to fetch
            query: Gmail search query
            after_date: Fetch emails after this date

        Returns:
            List of parsed email dictionaries
        """
        if not self.service:
            raise ValueError("Gmail service not initialized")

        try:
            # Build query
            if not query:
                query = "in:inbox"

            if after_date:
                date_str = after_date.strftime("%Y/%m/%d")
                query = f"{query} after:{date_str}"

            # Fetch message IDs
            results = self.service.users().messages().list(
                userId='me',
                q=query,
                maxResults=max_results
            ).execute()

            messages = results.get('messages', [])

            if not messages:
                return []

            # Fetch full message details
            emails = []
            for msg in messages:
                try:
                    email_data = self._fetch_email_by_id(msg['id'])
                    if email_data:
                        emails.append(email_data)
                except Exception as e:
                    print(f"Error fetching email {msg['id']}: {e}")
                    continue

            return emails

        except HttpError as error:
            print(f"Gmail API error: {error}")
            raise

    def _fetch_email_by_id(self, message_id: str) -> Optional[Dict[str, Any]]:
        """
        Fetch a single email by ID and parse it

        Args:
            message_id: Gmail message ID

        Returns:
            Parsed email dictionary
        """
        try:
            message = self.service.users().messages().get(
                userId='me',
                id=message_id,
                format='full'
            ).execute()

            return self._parse_email(message)

        except HttpError as error:
            print(f"Error fetching email {message_id}: {error}")
            return None

    def _parse_email(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse Gmail message into structured format

        Args:
            message: Raw Gmail message

        Returns:
            Parsed email dictionary
        """
        headers = {h['name']: h['value'] for h in message['payload']['headers']}

        # Extract basic info
        email_data = {
            'gmail_message_id': message['id'],
            'gmail_thread_id': message['threadId'],
            'subject': headers.get('Subject', ''),
            'from_email': self._extract_email(headers.get('From', '')),
            'from_name': self._extract_name(headers.get('From', '')),
            'to_email': self._extract_email(headers.get('To', '')),
            'cc_emails': self._parse_email_list(headers.get('Cc', '')),
            'bcc_emails': self._parse_email_list(headers.get('Bcc', '')),
            'received_at': self._parse_date(headers.get('Date', '')),
            'labels': message.get('labelIds', []),
            'is_read': 'UNREAD' not in message.get('labelIds', []),
            'is_starred': 'STARRED' in message.get('labelIds', []),
            'raw_data': message,
        }

        # Extract body
        body_plain, body_html = self._extract_body(message['payload'])
        email_data['body_plain'] = body_plain
        email_data['body_html'] = body_html

        # Check for attachments
        email_data['has_attachments'] = self._has_attachments(message['payload'])
        email_data['attachment_count'] = self._count_attachments(message['payload'])

        return email_data

    def _extract_body(self, payload: Dict[str, Any]) -> tuple:
        """
        Extract plain text and HTML body from email payload

        Args:
            payload: Email payload

        Returns:
            Tuple of (plain_text, html)
        """
        plain_text = None
        html = None

        if 'body' in payload and payload['body'].get('data'):
            # Simple email body
            data = payload['body']['data']
            text = base64.urlsafe_b64decode(data).decode('utf-8')
            plain_text = text
        elif 'parts' in payload:
            # Multipart email
            for part in payload['parts']:
                if part['mimeType'] == 'text/plain':
                    if part['body'].get('data'):
                        data = part['body']['data']
                        plain_text = base64.urlsafe_b64decode(data).decode('utf-8')
                elif part['mimeType'] == 'text/html':
                    if part['body'].get('data'):
                        data = part['body']['data']
                        html = base64.urlsafe_b64decode(data).decode('utf-8')
                elif 'parts' in part:
                    # Nested parts
                    p_text, p_html = self._extract_body(part)
                    if not plain_text:
                        plain_text = p_text
                    if not html:
                        html = p_html

        # If we only have HTML, convert to plain text
        if not plain_text and html:
            soup = BeautifulSoup(html, 'html.parser')
            plain_text = soup.get_text()

        return plain_text, html

    def _extract_email(self, email_str: str) -> str:
        """Extract email address from string like 'Name <email@example.com>'"""
        if '<' in email_str and '>' in email_str:
            return email_str[email_str.find('<') + 1:email_str.find('>')]
        return email_str.strip()

    def _extract_name(self, email_str: str) -> str:
        """Extract name from string like 'Name <email@example.com>'"""
        if '<' in email_str:
            return email_str[:email_str.find('<')].strip().strip('"')
        return ''

    def _parse_email_list(self, email_list_str: str) -> List[str]:
        """Parse comma-separated email list"""
        if not email_list_str:
            return []
        emails = []
        for email_str in email_list_str.split(','):
            emails.append(self._extract_email(email_str))
        return emails

    def _parse_date(self, date_str: str) -> datetime:
        """Parse email date string to datetime"""
        try:
            from email.utils import parsedate_to_datetime
            return parsedate_to_datetime(date_str)
        except Exception:
            return datetime.now()

    def _has_attachments(self, payload: Dict[str, Any]) -> bool:
        """Check if email has attachments"""
        if 'parts' in payload:
            for part in payload['parts']:
                if part.get('filename'):
                    return True
                if 'parts' in part:
                    if self._has_attachments(part):
                        return True
        return False

    def _count_attachments(self, payload: Dict[str, Any]) -> int:
        """Count number of attachments"""
        count = 0
        if 'parts' in payload:
            for part in payload['parts']:
                if part.get('filename'):
                    count += 1
                if 'parts' in part:
                    count += self._count_attachments(part)
        return count

    def send_email(
        self,
        to: str,
        subject: str,
        body: str,
        cc: Optional[List[str]] = None,
        bcc: Optional[List[str]] = None,
        html: bool = False,
        in_reply_to: Optional[str] = None,
        thread_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Send an email via Gmail

        Args:
            to: Recipient email
            subject: Email subject
            body: Email body
            cc: CC recipients
            bcc: BCC recipients
            html: Whether body is HTML
            in_reply_to: Message ID to reply to
            thread_id: Thread ID for threading

        Returns:
            Sent message data
        """
        if not self.service:
            raise ValueError("Gmail service not initialized")

        try:
            # Create message
            message = MIMEMultipart() if html else MIMEText(body)

            if html:
                message.attach(MIMEText(body, 'html'))

            message['to'] = to
            message['subject'] = subject

            if cc:
                message['cc'] = ', '.join(cc)
            if bcc:
                message['bcc'] = ', '.join(bcc)
            if in_reply_to:
                message['In-Reply-To'] = in_reply_to
                message['References'] = in_reply_to

            # Encode message
            raw = base64.urlsafe_b64encode(message.as_bytes()).decode()

            # Send message
            send_body = {'raw': raw}
            if thread_id:
                send_body['threadId'] = thread_id

            sent_message = self.service.users().messages().send(
                userId='me',
                body=send_body
            ).execute()

            return sent_message

        except HttpError as error:
            print(f"Error sending email: {error}")
            raise

    def mark_as_read(self, message_id: str) -> bool:
        """Mark email as read"""
        try:
            self.service.users().messages().modify(
                userId='me',
                id=message_id,
                body={'removeLabelIds': ['UNREAD']}
            ).execute()
            return True
        except HttpError as error:
            print(f"Error marking email as read: {error}")
            return False

    def archive_email(self, message_id: str) -> bool:
        """Archive email (remove from inbox)"""
        try:
            self.service.users().messages().modify(
                userId='me',
                id=message_id,
                body={'removeLabelIds': ['INBOX']}
            ).execute()
            return True
        except HttpError as error:
            print(f"Error archiving email: {error}")
            return False

    def star_email(self, message_id: str) -> bool:
        """Star an email"""
        try:
            self.service.users().messages().modify(
                userId='me',
                id=message_id,
                body={'addLabelIds': ['STARRED']}
            ).execute()
            return True
        except HttpError as error:
            print(f"Error starring email: {error}")
            return False

    def create_label(self, label_name: str) -> Optional[str]:
        """
        Create a Gmail label

        Args:
            label_name: Name of the label

        Returns:
            Label ID if successful
        """
        try:
            label = self.service.users().labels().create(
                userId='me',
                body={
                    'name': label_name,
                    'labelListVisibility': 'labelShow',
                    'messageListVisibility': 'show'
                }
            ).execute()
            return label['id']
        except HttpError as error:
            print(f"Error creating label: {error}")
            return None

    def add_label(self, message_id: str, label_id: str) -> bool:
        """Add label to email"""
        try:
            self.service.users().messages().modify(
                userId='me',
                id=message_id,
                body={'addLabelIds': [label_id]}
            ).execute()
            return True
        except HttpError as error:
            print(f"Error adding label: {error}")
            return False
