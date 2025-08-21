from flask import render_template, redirect, url_for, flash, request, session, current_app, jsonify
from flask_login import login_required, current_user
from agentsdr.calendar import calendar_bp
import os
import json
from datetime import datetime, timedelta
import requests
from urllib.parse import urlencode

@calendar_bp.route('/connect')
@login_required
def connect_calendar():
    """Initiate Google Calendar OAuth flow"""
    try:
        # Build OAuth URL
        auth_url = "https://accounts.google.com/o/oauth2/auth"
        params = {
            'client_id': current_app.config['GOOGLE_CALENDAR_CLIENT_ID'],
            'redirect_uri': current_app.config['GOOGLE_CALENDAR_REDIRECT_URI'],
            'scope': 'https://www.googleapis.com/auth/calendar.readonly',
            'response_type': 'code',
            'access_type': 'offline',
            'prompt': 'consent',
            'state': f"{current_user.id}:{session.get('current_org_id')}"  # Include user and org info
        }
        
        oauth_url = f"{auth_url}?{urlencode(params)}"
        return redirect(oauth_url)
        
    except Exception as e:
        current_app.logger.error(f"Calendar connect error: {e}")
        flash('Failed to connect to Google Calendar. Please try again.', 'error')
        return redirect(url_for('orgs.manage_org'))

@calendar_bp.route('/callback')
@login_required
def calendar_callback():
    """Handle Google Calendar OAuth callback"""
    try:
        code = request.args.get('code')
        state = request.args.get('state')
        error = request.args.get('error')
        
        if error:
            flash(f'Calendar connection failed: {error}', 'error')
            return redirect(url_for('orgs.manage_org'))
        
        if not code:
            flash('No authorization code received.', 'error')
            return redirect(url_for('orgs.manage_org'))
        
        # Exchange code for tokens
        token_url = "https://oauth2.googleapis.com/token"
        token_data = {
            'client_id': current_app.config['GOOGLE_CALENDAR_CLIENT_ID'],
            'client_secret': current_app.config['GOOGLE_CALENDAR_CLIENT_SECRET'],
            'code': code,
            'grant_type': 'authorization_code',
            'redirect_uri': current_app.config['GOOGLE_CALENDAR_REDIRECT_URI']
        }
        
        response = requests.post(token_url, data=token_data)
        token_info = response.json()
        
        if 'access_token' not in token_info:
            flash('Failed to get access token from Google.', 'error')
            return redirect(url_for('orgs.manage_org'))
        
        # Store tokens (you'll need to implement this based on your database structure)
        # For now, we'll store in session for demo
        session['google_calendar_tokens'] = {
            'access_token': token_info['access_token'],
            'refresh_token': token_info.get('refresh_token'),
            'expires_at': datetime.now() + timedelta(seconds=token_info.get('expires_in', 3600))
        }
        
        flash('Google Calendar connected successfully!', 'success')
        return redirect(url_for('calendar.calendar_dashboard'))
        
    except Exception as e:
        current_app.logger.error(f"Calendar callback error: {e}")
        flash('Failed to complete calendar connection.', 'error')
        return redirect(url_for('orgs.manage_org'))

@calendar_bp.route('/dashboard')
@login_required
def calendar_dashboard():
    """Calendar dashboard showing events and options"""
    try:
        # Check if user has connected calendar
        tokens = session.get('google_calendar_tokens')
        if not tokens:
            flash('Please connect your Google Calendar first.', 'info')
            return redirect(url_for('calendar.connect_calendar'))
        
        # Get calendar events
        events = get_calendar_events(tokens['access_token'])
        
        return render_template('calendar/dashboard.html', events=events)
        
    except Exception as e:
        current_app.logger.error(f"Calendar dashboard error: {e}")
        flash('Error loading calendar dashboard.', 'error')
        return redirect(url_for('orgs.manage_org'))

@calendar_bp.route('/events')
@login_required
def get_events():
    """API endpoint to get calendar events"""
    try:
        tokens = session.get('google_calendar_tokens')
        if not tokens:
            return jsonify({'error': 'Calendar not connected'}), 401
        
        events = get_calendar_events(tokens['access_token'])
        return jsonify({'events': events})
        
    except Exception as e:
        current_app.logger.error(f"Get events error: {e}")
        return jsonify({'error': 'Failed to fetch events'}), 500

def get_calendar_events(access_token, max_results=10):
    """Fetch events from Google Calendar API"""
    try:
        # Get events from primary calendar
        calendar_url = "https://www.googleapis.com/calendar/v3/calendars/primary/events"
        headers = {'Authorization': f'Bearer {access_token}'}
        
        # Get events for the next 7 days
        time_min = datetime.now().isoformat() + 'Z'
        time_max = (datetime.now() + timedelta(days=7)).isoformat() + 'Z'
        
        params = {
            'timeMin': time_min,
            'timeMax': time_max,
            'maxResults': max_results,
            'singleEvents': True,
            'orderBy': 'startTime'
        }
        
        response = requests.get(calendar_url, headers=headers, params=params)
        
        if response.status_code == 200:
            calendar_data = response.json()
            events = []
            
            for item in calendar_data.get('items', []):
                event = {
                    'id': item.get('id'),
                    'summary': item.get('summary', 'No Title'),
                    'description': item.get('description', ''),
                    'start': item.get('start', {}).get('dateTime') or item.get('start', {}).get('date'),
                    'end': item.get('end', {}).get('dateTime') or item.get('end', {}).get('date'),
                    'location': item.get('location', ''),
                    'attendees': [attendee.get('email') for attendee in item.get('attendees', [])]
                }
                events.append(event)
            
            return events
        else:
            current_app.logger.error(f"Calendar API error: {response.status_code} - {response.text}")
            return []
            
    except Exception as e:
        current_app.logger.error(f"Error fetching calendar events: {e}")
        return []

@calendar_bp.route('/disconnect')
@login_required
def disconnect_calendar():
    """Disconnect Google Calendar"""
    try:
        # Remove tokens from session
        session.pop('google_calendar_tokens', None)
        
        # Here you would also remove from database if stored there
        
        flash('Google Calendar disconnected successfully.', 'success')
        return redirect(url_for('orgs.manage_org'))
        
    except Exception as e:
        current_app.logger.error(f"Calendar disconnect error: {e}")
        flash('Error disconnecting calendar.', 'error')
        return redirect(url_for('orgs.manage_org'))
