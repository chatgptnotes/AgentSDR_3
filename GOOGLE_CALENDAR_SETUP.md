# 📅 Google Calendar Integration Setup Guide

## Overview
This guide will help you set up Google Calendar integration for your AgentSDR application. Once configured, users can connect their Google Calendar to create calendar-based agents for meeting summarization, schedule optimization, and smart reminders.

## 🔧 Step 1: Google Cloud Console Setup

### 1.1 Create/Select Google Cloud Project
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Note your project ID for reference

### 1.2 Enable Google Calendar API
1. In the Google Cloud Console, go to **"APIs & Services" > "Library"**
2. Search for **"Google Calendar API"**
3. Click on it and press **"Enable"**

### 1.3 Configure OAuth Consent Screen
1. Go to **"APIs & Services" > "OAuth consent screen"**
2. Choose **"External"** (for testing with any Google account)
3. Fill in the required information:
   - **App name**: `AgentSDR`
   - **User support email**: Your email
   - **Developer contact information**: Your email
4. **Add Scopes** (click "Add or Remove Scopes"):
   - `https://www.googleapis.com/auth/calendar.readonly` (for read-only access)
   - OR `https://www.googleapis.com/auth/calendar` (for full access)
5. **Add Test Users** (if using External):
   - Add your email and any other emails you want to test with
6. Save and continue through all steps

### 1.4 Create OAuth 2.0 Credentials
1. Go to **"APIs & Services" > "Credentials"**
2. Click **"Create Credentials" > "OAuth 2.0 Client IDs"**
3. Configure the OAuth client:
   - **Application type**: `Web application`
   - **Name**: `AgentSDR Calendar Integration`
   - **Authorized redirect URIs**: 
     - `http://localhost:5000/calendar/callback`
     - `http://127.0.0.1:5000/calendar/callback`
     - (Add your production domain when deploying)

### 1.5 Get Your Credentials
After creating the OAuth client, you'll receive:
- **Client ID**: `123456789-abcdefghijklmnop.apps.googleusercontent.com`
- **Client Secret**: `GOCSPX-abcdefghijklmnopqrstuvwxyz`

## 🔑 Step 2: Update Environment Variables

Update your `.env` file with the Google Calendar credentials:

```env
# Google Calendar OAuth Configuration
GOOGLE_CALENDAR_CLIENT_ID=your-client-id.apps.googleusercontent.com
GOOGLE_CALENDAR_CLIENT_SECRET=your-client-secret
GOOGLE_CALENDAR_REDIRECT_URI=http://localhost:5000/calendar/callback
```

**Replace the placeholder values with your actual credentials from Step 1.5**

## 🗄️ Step 3: Update Database Schema

Run this SQL in your Supabase SQL Editor to support calendar agents:

```sql
-- Update agents table to support calendar agent type
ALTER TABLE public.agents 
DROP CONSTRAINT IF EXISTS agents_agent_type_check;

ALTER TABLE public.agents 
ADD CONSTRAINT agents_agent_type_check 
CHECK (agent_type IN ('email_summarizer','hubspot_data','calendar','custom'));
```

## 🚀 Step 4: Test the Integration

1. **Restart your Flask application**:
   ```bash
   python app.py
   ```

2. **Create a Calendar Agent**:
   - Go to your organization management page
   - Click "Create Agent"
   - Select "📅 Calendar agent"
   - Give it a name and create

3. **Connect Google Calendar**:
   - Go to the calendar agent detail page
   - Click "🔗 Connect Calendar"
   - Authorize with your Google account
   - You should be redirected to the calendar dashboard

## 📋 Step 5: Available Features

Once connected, users can:

### 🤖 Calendar Agent Types
- **Meeting Summarizer**: Automatically summarize meeting notes and action items
- **Schedule Optimizer**: Analyze schedule and suggest time management improvements  
- **Smart Reminders**: Send intelligent reminders with meeting prep and context

### 📊 Calendar Dashboard
- View upcoming events (next 7 days)
- Create agents for specific events
- Access calendar analytics
- Manage calendar connection

### 🔗 API Endpoints
- `GET /calendar/dashboard` - Calendar dashboard
- `GET /calendar/connect` - Initiate OAuth flow
- `GET /calendar/callback` - OAuth callback handler
- `GET /calendar/events` - Get calendar events (JSON API)
- `GET /calendar/disconnect` - Disconnect calendar

## 🔒 Security Considerations

### OAuth Scopes
- **Read-only**: `https://www.googleapis.com/auth/calendar.readonly`
- **Full access**: `https://www.googleapis.com/auth/calendar`

Choose read-only for basic features, full access if you need to create/modify events.

### Token Storage
Currently tokens are stored in session for demo purposes. For production:
1. Store tokens in database encrypted
2. Implement token refresh logic
3. Add proper error handling for expired tokens

### Rate Limiting
Google Calendar API has rate limits:
- 1,000,000 queries per day
- 100 queries per 100 seconds per user

## 🐛 Troubleshooting

### Common Issues

1. **"redirect_uri_mismatch" error**:
   - Ensure the redirect URI in Google Console exactly matches your app
   - Check for trailing slashes, http vs https

2. **"access_blocked" error**:
   - Add your email to test users in OAuth consent screen
   - Ensure app is not in production mode unless verified

3. **"invalid_client" error**:
   - Check client ID and secret are correct
   - Ensure they're properly set in .env file

4. **Calendar events not loading**:
   - Check if user has events in the next 7 days
   - Verify API is enabled and credentials are working

### Debug Steps
1. Check Flask logs for detailed error messages
2. Verify environment variables are loaded: `echo $GOOGLE_CALENDAR_CLIENT_ID`
3. Test OAuth flow step by step
4. Use Google's OAuth 2.0 Playground for testing

## 🎯 Next Steps

1. **Set up your Google credentials** following steps 1-2
2. **Update your database** with the SQL from step 3
3. **Test the integration** following step 4
4. **Create calendar agents** and explore the features!

## 📞 Support

If you encounter issues:
1. Check the troubleshooting section above
2. Review Flask application logs
3. Verify all environment variables are set correctly
4. Ensure Google Cloud project is properly configured

Happy calendar integrating! 📅✨
