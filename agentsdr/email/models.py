"""
Email Automation Data Models
InboxAI - Lindy AI-like Email Automation Platform
"""

from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class EmailCategory(str, Enum):
    """Email classification categories"""
    URGENT = "urgent"
    FYI = "fyi"
    ARCHIVE = "archive"


class FollowUpType(str, Enum):
    """Types of follow-up actions"""
    REMINDER = "reminder"
    CHECK_IN = "check_in"
    CLOSING = "closing"
    CUSTOM = "custom"


class Sentiment(str, Enum):
    """Email sentiment analysis"""
    POSITIVE = "positive"
    NEUTRAL = "neutral"
    NEGATIVE = "negative"


class SubscriptionTier(str, Enum):
    """User subscription tiers"""
    FREE = "free"
    PRO = "pro"
    BUSINESS = "business"


class Email(BaseModel):
    """Email model"""
    id: str
    org_id: str
    user_id: str
    gmail_message_id: str
    gmail_thread_id: str
    subject: Optional[str] = None
    from_email: str
    from_name: Optional[str] = None
    to_email: str
    cc_emails: Optional[List[str]] = None
    bcc_emails: Optional[List[str]] = None
    body_plain: Optional[str] = None
    body_html: Optional[str] = None
    received_at: datetime
    labels: Optional[List[str]] = None
    is_read: bool = False
    is_starred: bool = False
    has_attachments: bool = False
    attachment_count: int = 0
    raw_data: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime


class EmailClassification(BaseModel):
    """AI-powered email classification"""
    id: str
    email_id: str
    user_id: str
    category: EmailCategory
    confidence_score: float = Field(ge=0, le=1)
    reasoning: Optional[str] = None
    ai_model: str = "gpt-4"
    priority_score: Optional[int] = Field(None, ge=0, le=100)
    keywords: Optional[List[str]] = None
    entities: Optional[Dict[str, Any]] = None
    sentiment: Optional[Sentiment] = None
    action_required: bool = False
    estimated_response_time: Optional[str] = None
    created_at: datetime


class EmailDraft(BaseModel):
    """AI-generated email draft"""
    id: str
    email_id: str
    user_id: str
    draft_subject: Optional[str] = None
    draft_body: str
    tone: str = "professional"
    style_match_score: Optional[float] = Field(None, ge=0, le=1)
    ai_model: str = "gpt-4"
    tokens_used: Optional[int] = None
    is_sent: bool = False
    sent_at: Optional[datetime] = None
    is_edited: bool = False
    edit_history: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime


class SenderResearch(BaseModel):
    """Researched sender information"""
    id: str
    email_address: str
    user_id: str
    full_name: Optional[str] = None
    company: Optional[str] = None
    job_title: Optional[str] = None
    linkedin_url: Optional[str] = None
    twitter_url: Optional[str] = None
    website: Optional[str] = None
    bio: Optional[str] = None
    location: Optional[str] = None
    social_profiles: Optional[Dict[str, Any]] = None
    company_info: Optional[Dict[str, Any]] = None
    interaction_history: Optional[Dict[str, Any]] = None
    research_data: Optional[Dict[str, Any]] = None
    last_researched_at: datetime
    research_source: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class FollowUpSchedule(BaseModel):
    """Scheduled follow-up"""
    id: str
    email_id: str
    user_id: str
    org_id: str
    scheduled_time: datetime
    follow_up_type: FollowUpType
    template_message: Optional[str] = None
    is_completed: bool = False
    completed_at: Optional[datetime] = None
    is_cancelled: bool = False
    cancelled_at: Optional[datetime] = None
    cancellation_reason: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3
    created_at: datetime
    updated_at: datetime


class UserCredits(BaseModel):
    """User credit balance"""
    id: str
    user_id: str
    org_id: str
    total_credits: int = 0
    used_credits: int = 0
    available_credits: int = 0
    subscription_tier: SubscriptionTier
    credits_reset_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


class CreditTransaction(BaseModel):
    """Credit usage transaction"""
    id: str
    user_id: str
    org_id: str
    action_type: str
    credits_used: int
    description: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    created_at: datetime


class WorkflowAutomation(BaseModel):
    """No-code workflow automation"""
    id: str
    org_id: str
    user_id: str
    name: str
    description: Optional[str] = None
    is_active: bool = True
    trigger_type: str
    trigger_conditions: Optional[Dict[str, Any]] = None
    actions: Dict[str, Any]
    execution_count: int = 0
    last_executed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


class WorkflowExecutionLog(BaseModel):
    """Workflow execution log"""
    id: str
    workflow_id: str
    email_id: Optional[str] = None
    status: str
    execution_time_ms: Optional[int] = None
    error_message: Optional[str] = None
    actions_executed: Optional[Dict[str, Any]] = None
    created_at: datetime


# Request models for API endpoints

class ClassifyEmailRequest(BaseModel):
    """Request to classify an email"""
    email_id: str
    user_preferences: Optional[Dict[str, Any]] = None


class DraftEmailResponseRequest(BaseModel):
    """Request to draft an email response"""
    email_id: str
    tone: str = "professional"
    key_points: Optional[List[str]] = None
    custom_instructions: Optional[str] = None


class ResearchSenderRequest(BaseModel):
    """Request to research an email sender"""
    email_address: EmailStr
    deep_research: bool = False


class CreateFollowUpRequest(BaseModel):
    """Request to create a follow-up schedule"""
    email_id: str
    scheduled_time: datetime
    follow_up_type: FollowUpType
    template_message: Optional[str] = None


class CreateWorkflowRequest(BaseModel):
    """Request to create a workflow automation"""
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    trigger_type: str
    trigger_conditions: Optional[Dict[str, Any]] = None
    actions: Dict[str, Any]


class UpdateWorkflowRequest(BaseModel):
    """Request to update a workflow automation"""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    is_active: Optional[bool] = None
    trigger_conditions: Optional[Dict[str, Any]] = None
    actions: Optional[Dict[str, Any]] = None


# Credit pricing constants (credits per action)
CREDIT_COSTS = {
    "email_classification": 1,
    "email_draft_short": 3,
    "email_draft_long": 7,
    "sender_research_basic": 2,
    "sender_research_deep": 5,
    "follow_up_schedule": 1,
    "workflow_execution": 1,
}

# Subscription tier limits
TIER_LIMITS = {
    "free": {
        "monthly_credits": 400,
        "max_workflows": 3,
        "max_follow_ups": 10,
    },
    "pro": {
        "monthly_credits": 5000,
        "max_workflows": 50,
        "max_follow_ups": 100,
    },
    "business": {
        "monthly_credits": 30000,
        "max_workflows": 500,
        "max_follow_ups": 1000,
    },
}
