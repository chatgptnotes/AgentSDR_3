"""
Celery Background Tasks for Email Automation
InboxAI - Lindy AI-like Email Automation Platform
"""

import os
from datetime import datetime, timedelta
from typing import List, Dict, Any

from agentsdr.celery_config import celery_app
from agentsdr.email.gmail_service import GmailService
from agentsdr.core.supabase_client import get_supabase_client


@celery_app.task(name='agentsdr.email.tasks.fetch_user_emails')
def fetch_user_emails(user_id: str, org_id: str, credentials: Dict[str, Any]) -> Dict[str, Any]:
    """
    Fetch emails for a specific user

    Args:
        user_id: User ID
        org_id: Organization ID
        credentials: Gmail OAuth credentials

    Returns:
        Result dictionary with count and status
    """
    try:
        # Initialize Gmail service
        gmail = GmailService(credentials=credentials)

        # Fetch emails from last 24 hours
        after_date = datetime.now() - timedelta(hours=24)
        emails = gmail.fetch_emails(
            max_results=100,
            after_date=after_date
        )

        # Store emails in database
        supabase = get_supabase_client()
        stored_count = 0

        for email_data in emails:
            try:
                # Check if email already exists
                existing = supabase.table('emails').select('id').eq(
                    'gmail_message_id', email_data['gmail_message_id']
                ).eq('user_id', user_id).execute()

                if not existing.data:
                    # Add user and org IDs
                    email_data['user_id'] = user_id
                    email_data['org_id'] = org_id

                    # Store email
                    supabase.table('emails').insert(email_data).execute()
                    stored_count += 1

                    # Trigger classification task
                    classify_email.delay(
                        email_id=email_data.get('id'),
                        user_id=user_id
                    )

            except Exception as e:
                print(f"Error storing email: {e}")
                continue

        return {
            'status': 'success',
            'fetched': len(emails),
            'stored': stored_count,
            'user_id': user_id
        }

    except Exception as e:
        return {
            'status': 'error',
            'error': str(e),
            'user_id': user_id
        }


@celery_app.task(name='agentsdr.email.tasks.fetch_all_user_emails')
def fetch_all_user_emails() -> Dict[str, Any]:
    """
    Fetch emails for all users with Gmail connected

    Returns:
        Summary of fetch operations
    """
    try:
        supabase = get_supabase_client()

        # Get all organizations with Gmail credentials
        # This is a simplified version - in production you'd store credentials securely
        orgs = supabase.table('organizations').select('*').execute()

        total_fetched = 0
        total_stored = 0
        errors = []

        for org in orgs.data:
            # Get org members
            members = supabase.table('organization_members').select(
                'user_id'
            ).eq('org_id', org['id']).execute()

            for member in members.data:
                # Get user credentials (stored securely)
                # In production, retrieve encrypted credentials
                user_id = member['user_id']

                # TODO: Implement secure credential retrieval
                # For now, skip if no credentials
                credentials = {}  # Placeholder

                if credentials:
                    result = fetch_user_emails.delay(
                        user_id=user_id,
                        org_id=org['id'],
                        credentials=credentials
                    )

        return {
            'status': 'success',
            'total_fetched': total_fetched,
            'total_stored': total_stored,
            'errors': errors
        }

    except Exception as e:
        return {
            'status': 'error',
            'error': str(e)
        }


@celery_app.task(name='agentsdr.email.tasks.classify_email')
def classify_email(email_id: str, user_id: str) -> Dict[str, Any]:
    """
    Classify an email using AI

    Args:
        email_id: Email ID
        user_id: User ID

    Returns:
        Classification result
    """
    try:
        from agentsdr.email.ai_service import AIService

        supabase = get_supabase_client()

        # Get email
        email = supabase.table('emails').select('*').eq('id', email_id).single().execute()

        if not email.data:
            return {'status': 'error', 'error': 'Email not found'}

        # Classify with AI
        ai_service = AIService()
        classification = ai_service.classify_email(
            subject=email.data.get('subject'),
            body=email.data.get('body_plain'),
            from_email=email.data.get('from_email'),
            user_id=user_id
        )

        # Store classification
        classification['email_id'] = email_id
        classification['user_id'] = user_id

        result = supabase.table('email_classifications').insert(classification).execute()

        # Deduct credits
        supabase.rpc('deduct_credits', {
            'p_user_id': user_id,
            'p_org_id': email.data.get('org_id'),
            'p_credits': 1,
            'p_action_type': 'email_classification',
            'p_description': f'Classified email: {email.data.get("subject")}'
        }).execute()

        # If urgent, trigger draft response
        if classification.get('category') == 'urgent':
            draft_email_response.delay(email_id=email_id, user_id=user_id)

        return {
            'status': 'success',
            'classification': classification
        }

    except Exception as e:
        return {
            'status': 'error',
            'error': str(e)
        }


@celery_app.task(name='agentsdr.email.tasks.draft_email_response')
def draft_email_response(
    email_id: str,
    user_id: str,
    tone: str = 'professional',
    custom_instructions: str = None
) -> Dict[str, Any]:
    """
    Draft an AI-generated email response

    Args:
        email_id: Email ID
        user_id: User ID
        tone: Response tone
        custom_instructions: Custom instructions

    Returns:
        Draft result
    """
    try:
        from agentsdr.email.ai_service import AIService

        supabase = get_supabase_client()

        # Get email
        email = supabase.table('emails').select('*').eq('id', email_id).single().execute()

        if not email.data:
            return {'status': 'error', 'error': 'Email not found'}

        # Generate draft
        ai_service = AIService()
        draft = ai_service.draft_response(
            subject=email.data.get('subject'),
            body=email.data.get('body_plain'),
            from_email=email.data.get('from_email'),
            user_id=user_id,
            tone=tone,
            custom_instructions=custom_instructions
        )

        # Store draft
        draft['email_id'] = email_id
        draft['user_id'] = user_id
        draft['tone'] = tone

        result = supabase.table('email_drafts').insert(draft).execute()

        # Deduct credits
        credits_cost = 3 if len(draft.get('draft_body', '')) < 500 else 7
        supabase.rpc('deduct_credits', {
            'p_user_id': user_id,
            'p_org_id': email.data.get('org_id'),
            'p_credits': credits_cost,
            'p_action_type': 'email_draft',
            'p_description': f'Drafted response for: {email.data.get("subject")}'
        }).execute()

        return {
            'status': 'success',
            'draft': draft
        }

    except Exception as e:
        return {
            'status': 'error',
            'error': str(e)
        }


@celery_app.task(name='agentsdr.email.tasks.research_sender')
def research_sender(email_address: str, user_id: str, deep_research: bool = False) -> Dict[str, Any]:
    """
    Research an email sender

    Args:
        email_address: Sender email
        user_id: User ID
        deep_research: Whether to perform deep research

    Returns:
        Research result
    """
    try:
        from agentsdr.email.research_service import ResearchService

        supabase = get_supabase_client()

        # Check if already researched recently
        existing = supabase.table('sender_research').select('*').eq(
            'email_address', email_address
        ).eq('user_id', user_id).execute()

        # If researched in last 7 days, return cached data
        if existing.data:
            last_researched = datetime.fromisoformat(existing.data[0]['last_researched_at'])
            if datetime.now() - last_researched < timedelta(days=7):
                return {
                    'status': 'success',
                    'research': existing.data[0],
                    'cached': True
                }

        # Perform research
        research_service = ResearchService()
        research_data = research_service.research_sender(
            email_address=email_address,
            deep_research=deep_research
        )

        # Store research
        research_data['email_address'] = email_address
        research_data['user_id'] = user_id
        research_data['last_researched_at'] = datetime.now().isoformat()

        if existing.data:
            # Update
            result = supabase.table('sender_research').update(research_data).eq(
                'id', existing.data[0]['id']
            ).execute()
        else:
            # Insert
            result = supabase.table('sender_research').insert(research_data).execute()

        # Deduct credits
        credits_cost = 5 if deep_research else 2
        supabase.rpc('deduct_credits', {
            'p_user_id': user_id,
            'p_org_id': user_id,  # Simplified - should get from context
            'p_credits': credits_cost,
            'p_action_type': 'sender_research',
            'p_description': f'Researched sender: {email_address}'
        }).execute()

        return {
            'status': 'success',
            'research': research_data,
            'cached': False
        }

    except Exception as e:
        return {
            'status': 'error',
            'error': str(e)
        }


@celery_app.task(name='agentsdr.email.tasks.process_follow_ups')
def process_follow_ups() -> Dict[str, Any]:
    """
    Process scheduled follow-ups

    Returns:
        Summary of processed follow-ups
    """
    try:
        supabase = get_supabase_client()

        # Get follow-ups that are due
        now = datetime.now().isoformat()
        follow_ups = supabase.table('follow_up_schedules').select('*').lte(
            'scheduled_time', now
        ).eq('is_completed', False).eq('is_cancelled', False).execute()

        processed = 0
        errors = []

        for follow_up in follow_ups.data:
            try:
                # Send follow-up email
                # TODO: Implement actual sending
                # For now, just mark as completed

                supabase.table('follow_up_schedules').update({
                    'is_completed': True,
                    'completed_at': datetime.now().isoformat()
                }).eq('id', follow_up['id']).execute()

                processed += 1

            except Exception as e:
                errors.append({'follow_up_id': follow_up['id'], 'error': str(e)})

        return {
            'status': 'success',
            'processed': processed,
            'errors': errors
        }

    except Exception as e:
        return {
            'status': 'error',
            'error': str(e)
        }


@celery_app.task(name='agentsdr.email.tasks.reset_monthly_credits')
def reset_monthly_credits() -> Dict[str, Any]:
    """
    Reset monthly credits for all users

    Returns:
        Summary of reset operation
    """
    try:
        supabase = get_supabase_client()

        # Get all user credits
        credits = supabase.table('user_credits').select('*').execute()

        reset_count = 0

        for credit in credits.data:
            tier = credit.get('subscription_tier', 'free')

            # Get tier limits
            from agentsdr.email.models import TIER_LIMITS
            monthly_credits = TIER_LIMITS[tier]['monthly_credits']

            # Reset credits
            supabase.table('user_credits').update({
                'total_credits': monthly_credits,
                'used_credits': 0,
                'available_credits': monthly_credits,
                'credits_reset_at': datetime.now().isoformat()
            }).eq('id', credit['id']).execute()

            reset_count += 1

        return {
            'status': 'success',
            'reset_count': reset_count
        }

    except Exception as e:
        return {
            'status': 'error',
            'error': str(e)
        }
