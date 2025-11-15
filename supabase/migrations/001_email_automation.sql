-- Email Automation System Schema Extension
-- Version: 1.0
-- Date: 2025-11-16

-- Create emails table to store fetched emails
CREATE TABLE IF NOT EXISTS public.emails (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    org_id UUID NOT NULL REFERENCES public.organizations(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    gmail_message_id TEXT UNIQUE NOT NULL,
    gmail_thread_id TEXT NOT NULL,
    subject TEXT,
    from_email TEXT NOT NULL,
    from_name TEXT,
    to_email TEXT NOT NULL,
    cc_emails TEXT[],
    bcc_emails TEXT[],
    body_plain TEXT,
    body_html TEXT,
    received_at TIMESTAMP WITH TIME ZONE NOT NULL,
    labels TEXT[],
    is_read BOOLEAN DEFAULT FALSE,
    is_starred BOOLEAN DEFAULT FALSE,
    has_attachments BOOLEAN DEFAULT FALSE,
    attachment_count INTEGER DEFAULT 0,
    raw_data JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create email_classifications table for AI triaging
CREATE TABLE IF NOT EXISTS public.email_classifications (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email_id UUID NOT NULL REFERENCES public.emails(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    category TEXT NOT NULL CHECK (category IN ('urgent', 'fyi', 'archive')),
    confidence_score DECIMAL(3, 2) CHECK (confidence_score >= 0 AND confidence_score <= 1),
    reasoning TEXT,
    ai_model TEXT DEFAULT 'gpt-4',
    priority_score INTEGER CHECK (priority_score >= 0 AND priority_score <= 100),
    keywords TEXT[],
    entities JSONB,
    sentiment TEXT CHECK (sentiment IN ('positive', 'neutral', 'negative')),
    action_required BOOLEAN DEFAULT FALSE,
    estimated_response_time TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(email_id, user_id)
);

-- Create email_drafts table for AI-generated responses
CREATE TABLE IF NOT EXISTS public.email_drafts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email_id UUID NOT NULL REFERENCES public.emails(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    draft_subject TEXT,
    draft_body TEXT NOT NULL,
    tone TEXT DEFAULT 'professional',
    style_match_score DECIMAL(3, 2) CHECK (style_match_score >= 0 AND style_match_score <= 1),
    ai_model TEXT DEFAULT 'gpt-4',
    tokens_used INTEGER,
    is_sent BOOLEAN DEFAULT FALSE,
    sent_at TIMESTAMP WITH TIME ZONE,
    is_edited BOOLEAN DEFAULT FALSE,
    edit_history JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create sender_research table for researched sender information
CREATE TABLE IF NOT EXISTS public.sender_research (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email_address TEXT NOT NULL,
    user_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    full_name TEXT,
    company TEXT,
    job_title TEXT,
    linkedin_url TEXT,
    twitter_url TEXT,
    website TEXT,
    bio TEXT,
    location TEXT,
    social_profiles JSONB,
    company_info JSONB,
    interaction_history JSONB,
    research_data JSONB,
    last_researched_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    research_source TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(email_address, user_id)
);

-- Create follow_up_schedules table for smart follow-ups
CREATE TABLE IF NOT EXISTS public.follow_up_schedules (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email_id UUID NOT NULL REFERENCES public.emails(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    org_id UUID NOT NULL REFERENCES public.organizations(id) ON DELETE CASCADE,
    scheduled_time TIMESTAMP WITH TIME ZONE NOT NULL,
    follow_up_type TEXT CHECK (follow_up_type IN ('reminder', 'check_in', 'closing', 'custom')),
    template_message TEXT,
    is_completed BOOLEAN DEFAULT FALSE,
    completed_at TIMESTAMP WITH TIME ZONE,
    is_cancelled BOOLEAN DEFAULT FALSE,
    cancelled_at TIMESTAMP WITH TIME ZONE,
    cancellation_reason TEXT,
    retry_count INTEGER DEFAULT 0,
    max_retries INTEGER DEFAULT 3,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create user_credits table for credit-based billing
CREATE TABLE IF NOT EXISTS public.user_credits (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    org_id UUID NOT NULL REFERENCES public.organizations(id) ON DELETE CASCADE,
    total_credits INTEGER DEFAULT 0,
    used_credits INTEGER DEFAULT 0,
    available_credits INTEGER DEFAULT 0,
    subscription_tier TEXT CHECK (subscription_tier IN ('free', 'pro', 'business')),
    credits_reset_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(user_id, org_id)
);

-- Create credit_transactions table for tracking usage
CREATE TABLE IF NOT EXISTS public.credit_transactions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    org_id UUID NOT NULL REFERENCES public.organizations(id) ON DELETE CASCADE,
    action_type TEXT NOT NULL,
    credits_used INTEGER NOT NULL,
    description TEXT,
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create workflow_automations table for no-code workflows
CREATE TABLE IF NOT EXISTS public.workflow_automations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    org_id UUID NOT NULL REFERENCES public.organizations(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    description TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    trigger_type TEXT NOT NULL,
    trigger_conditions JSONB,
    actions JSONB NOT NULL,
    execution_count INTEGER DEFAULT 0,
    last_executed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create workflow_execution_logs table
CREATE TABLE IF NOT EXISTS public.workflow_execution_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    workflow_id UUID NOT NULL REFERENCES public.workflow_automations(id) ON DELETE CASCADE,
    email_id UUID REFERENCES public.emails(id) ON DELETE SET NULL,
    status TEXT CHECK (status IN ('success', 'failure', 'partial')),
    execution_time_ms INTEGER,
    error_message TEXT,
    actions_executed JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_emails_org_id ON public.emails(org_id);
CREATE INDEX IF NOT EXISTS idx_emails_user_id ON public.emails(user_id);
CREATE INDEX IF NOT EXISTS idx_emails_gmail_message_id ON public.emails(gmail_message_id);
CREATE INDEX IF NOT EXISTS idx_emails_gmail_thread_id ON public.emails(gmail_thread_id);
CREATE INDEX IF NOT EXISTS idx_emails_from_email ON public.emails(from_email);
CREATE INDEX IF NOT EXISTS idx_emails_received_at ON public.emails(received_at DESC);

CREATE INDEX IF NOT EXISTS idx_email_classifications_email_id ON public.email_classifications(email_id);
CREATE INDEX IF NOT EXISTS idx_email_classifications_user_id ON public.email_classifications(user_id);
CREATE INDEX IF NOT EXISTS idx_email_classifications_category ON public.email_classifications(category);

CREATE INDEX IF NOT EXISTS idx_email_drafts_email_id ON public.email_drafts(email_id);
CREATE INDEX IF NOT EXISTS idx_email_drafts_user_id ON public.email_drafts(user_id);
CREATE INDEX IF NOT EXISTS idx_email_drafts_is_sent ON public.email_drafts(is_sent);

CREATE INDEX IF NOT EXISTS idx_sender_research_email ON public.sender_research(email_address);
CREATE INDEX IF NOT EXISTS idx_sender_research_user_id ON public.sender_research(user_id);

CREATE INDEX IF NOT EXISTS idx_follow_up_schedules_email_id ON public.follow_up_schedules(email_id);
CREATE INDEX IF NOT EXISTS idx_follow_up_schedules_user_id ON public.follow_up_schedules(user_id);
CREATE INDEX IF NOT EXISTS idx_follow_up_schedules_scheduled_time ON public.follow_up_schedules(scheduled_time);
CREATE INDEX IF NOT EXISTS idx_follow_up_schedules_is_completed ON public.follow_up_schedules(is_completed);

CREATE INDEX IF NOT EXISTS idx_user_credits_user_id ON public.user_credits(user_id);
CREATE INDEX IF NOT EXISTS idx_user_credits_org_id ON public.user_credits(org_id);

CREATE INDEX IF NOT EXISTS idx_credit_transactions_user_id ON public.credit_transactions(user_id);
CREATE INDEX IF NOT EXISTS idx_credit_transactions_org_id ON public.credit_transactions(org_id);
CREATE INDEX IF NOT EXISTS idx_credit_transactions_created_at ON public.credit_transactions(created_at DESC);

CREATE INDEX IF NOT EXISTS idx_workflow_automations_org_id ON public.workflow_automations(org_id);
CREATE INDEX IF NOT EXISTS idx_workflow_automations_user_id ON public.workflow_automations(user_id);
CREATE INDEX IF NOT EXISTS idx_workflow_automations_is_active ON public.workflow_automations(is_active);

CREATE INDEX IF NOT EXISTS idx_workflow_execution_logs_workflow_id ON public.workflow_execution_logs(workflow_id);
CREATE INDEX IF NOT EXISTS idx_workflow_execution_logs_email_id ON public.workflow_execution_logs(email_id);

-- Enable Row Level Security (RLS)
ALTER TABLE public.emails ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.email_classifications ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.email_drafts ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.sender_research ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.follow_up_schedules ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.user_credits ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.credit_transactions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.workflow_automations ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.workflow_execution_logs ENABLE ROW LEVEL SECURITY;

-- RLS Policies for emails
CREATE POLICY "Users can view their own emails" ON public.emails
    FOR SELECT USING (user_id = auth.uid());

CREATE POLICY "Users can insert their own emails" ON public.emails
    FOR INSERT WITH CHECK (user_id = auth.uid());

CREATE POLICY "Users can update their own emails" ON public.emails
    FOR UPDATE USING (user_id = auth.uid());

-- RLS Policies for email_classifications
CREATE POLICY "Users can view their own classifications" ON public.email_classifications
    FOR SELECT USING (user_id = auth.uid());

CREATE POLICY "Users can create classifications" ON public.email_classifications
    FOR INSERT WITH CHECK (user_id = auth.uid());

CREATE POLICY "Users can update their classifications" ON public.email_classifications
    FOR UPDATE USING (user_id = auth.uid());

-- RLS Policies for email_drafts
CREATE POLICY "Users can view their own drafts" ON public.email_drafts
    FOR SELECT USING (user_id = auth.uid());

CREATE POLICY "Users can create drafts" ON public.email_drafts
    FOR INSERT WITH CHECK (user_id = auth.uid());

CREATE POLICY "Users can update their drafts" ON public.email_drafts
    FOR UPDATE USING (user_id = auth.uid());

-- RLS Policies for sender_research
CREATE POLICY "Users can view their sender research" ON public.sender_research
    FOR SELECT USING (user_id = auth.uid());

CREATE POLICY "Users can create sender research" ON public.sender_research
    FOR INSERT WITH CHECK (user_id = auth.uid());

CREATE POLICY "Users can update their sender research" ON public.sender_research
    FOR UPDATE USING (user_id = auth.uid());

-- RLS Policies for follow_up_schedules
CREATE POLICY "Users can view their follow-ups" ON public.follow_up_schedules
    FOR SELECT USING (user_id = auth.uid());

CREATE POLICY "Users can create follow-ups" ON public.follow_up_schedules
    FOR INSERT WITH CHECK (user_id = auth.uid());

CREATE POLICY "Users can update their follow-ups" ON public.follow_up_schedules
    FOR UPDATE USING (user_id = auth.uid());

-- RLS Policies for user_credits
CREATE POLICY "Users can view their own credits" ON public.user_credits
    FOR SELECT USING (user_id = auth.uid());

CREATE POLICY "System can update credits" ON public.user_credits
    FOR ALL USING (true);

-- RLS Policies for credit_transactions
CREATE POLICY "Users can view their transactions" ON public.credit_transactions
    FOR SELECT USING (user_id = auth.uid());

CREATE POLICY "System can create transactions" ON public.credit_transactions
    FOR INSERT WITH CHECK (true);

-- RLS Policies for workflow_automations
CREATE POLICY "Users can view org workflows" ON public.workflow_automations
    FOR SELECT USING (public.is_org_member(org_id) OR public.is_super_admin());

CREATE POLICY "Users can create workflows" ON public.workflow_automations
    FOR INSERT WITH CHECK (public.is_org_member(org_id));

CREATE POLICY "Users can update their workflows" ON public.workflow_automations
    FOR UPDATE USING (user_id = auth.uid() OR public.is_org_admin(org_id));

-- RLS Policies for workflow_execution_logs
CREATE POLICY "Users can view workflow logs" ON public.workflow_execution_logs
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM public.workflow_automations wa
            WHERE wa.id = workflow_id AND (wa.user_id = auth.uid() OR public.is_org_admin(wa.org_id))
        )
    );

-- Create triggers for updated_at timestamps
CREATE TRIGGER update_emails_updated_at BEFORE UPDATE ON public.emails
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_email_drafts_updated_at BEFORE UPDATE ON public.email_drafts
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_sender_research_updated_at BEFORE UPDATE ON public.sender_research
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_follow_up_schedules_updated_at BEFORE UPDATE ON public.follow_up_schedules
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_user_credits_updated_at BEFORE UPDATE ON public.user_credits
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_workflow_automations_updated_at BEFORE UPDATE ON public.workflow_automations
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Function to deduct credits
CREATE OR REPLACE FUNCTION deduct_credits(
    p_user_id UUID,
    p_org_id UUID,
    p_credits INTEGER,
    p_action_type TEXT,
    p_description TEXT DEFAULT NULL,
    p_metadata JSONB DEFAULT NULL
)
RETURNS BOOLEAN AS $$
DECLARE
    v_available_credits INTEGER;
BEGIN
    -- Get current available credits
    SELECT available_credits INTO v_available_credits
    FROM public.user_credits
    WHERE user_id = p_user_id AND org_id = p_org_id;

    -- Check if enough credits
    IF v_available_credits IS NULL OR v_available_credits < p_credits THEN
        RETURN FALSE;
    END IF;

    -- Deduct credits
    UPDATE public.user_credits
    SET used_credits = used_credits + p_credits,
        available_credits = available_credits - p_credits,
        updated_at = NOW()
    WHERE user_id = p_user_id AND org_id = p_org_id;

    -- Log transaction
    INSERT INTO public.credit_transactions (user_id, org_id, action_type, credits_used, description, metadata)
    VALUES (p_user_id, p_org_id, p_action_type, p_credits, p_description, p_metadata);

    RETURN TRUE;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Function to add credits
CREATE OR REPLACE FUNCTION add_credits(
    p_user_id UUID,
    p_org_id UUID,
    p_credits INTEGER,
    p_description TEXT DEFAULT 'Credit added'
)
RETURNS BOOLEAN AS $$
BEGIN
    UPDATE public.user_credits
    SET total_credits = total_credits + p_credits,
        available_credits = available_credits + p_credits,
        updated_at = NOW()
    WHERE user_id = p_user_id AND org_id = p_org_id;

    IF NOT FOUND THEN
        INSERT INTO public.user_credits (user_id, org_id, total_credits, available_credits, subscription_tier)
        VALUES (p_user_id, p_org_id, p_credits, p_credits, 'free');
    END IF;

    INSERT INTO public.credit_transactions (user_id, org_id, action_type, credits_used, description)
    VALUES (p_user_id, p_org_id, 'credit_added', -p_credits, p_description);

    RETURN TRUE;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;
