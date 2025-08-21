from flask import render_template, redirect, url_for, flash, request, jsonify, current_app
from flask_login import login_required, current_user
from agentsdr.orgs import orgs_bp
from agentsdr.core.supabase_client import get_supabase, get_service_supabase
from agentsdr.core.rbac import require_org_admin, require_org_member, is_org_admin
from agentsdr.core.email import get_email_service
from agentsdr.core.models import CreateOrganizationRequest, UpdateOrganizationRequest, CreateInvitationRequest
from agentsdr.services.gmail_service import fetch_and_summarize_emails

from datetime import datetime, timedelta
import uuid
import secrets

@orgs_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create_organization():
    if request.method == 'POST':
        try:
            # Handle both JSON and form data
            if request.is_json:
                data = request.get_json()
            else:
                data = request.form.to_dict()

            current_app.logger.info(f"Creating organization with data: {data}")
            current_app.logger.info(f"Current user: {current_user.id} ({current_user.email})")

            # Remove CSRF token from data before validation
            org_data = {k: v for k, v in data.items() if k != 'csrf_token'}
            current_app.logger.info(f"Filtered organization data: {org_data}")

            try:
                org_request = CreateOrganizationRequest(**org_data)
                current_app.logger.info(f"Validation successful: name={org_request.name}, slug={org_request.slug}")
            except Exception as validation_error:
                current_app.logger.error(f"Validation error: {validation_error}")
                raise validation_error

            supabase = get_service_supabase()

            # Check if slug is unique
            existing_org = supabase.table('organizations').select('id').eq('slug', org_request.slug).execute()
            if existing_org.data:
                current_app.logger.warning(f"Organization slug already exists: {org_request.slug}")
                return jsonify({'error': 'Organization slug already exists'}), 400

            # Create organization
            org_data = {
                'id': str(uuid.uuid4()),
                'name': org_request.name,
                'slug': org_request.slug,
                'owner_user_id': current_user.id,
                'created_at': datetime.utcnow().isoformat(),
                'updated_at': datetime.utcnow().isoformat()
            }

            current_app.logger.info(f"Inserting organization data: {org_data}")
            org_response = supabase.table('organizations').insert(org_data).execute()

            if org_response.data:
                current_app.logger.info("Organization created successfully")

                # Add creator as admin
                member_data = {
                    'id': str(uuid.uuid4()),
                    'org_id': org_data['id'],
                    'user_id': current_user.id,
                    'role': 'admin',
                    'joined_at': datetime.utcnow().isoformat()
                }

                current_app.logger.info(f"Adding organization member: {member_data}")
                member_response = supabase.table('organization_members').insert(member_data).execute()

                if member_response.data:
                    current_app.logger.info("Organization member added successfully")
                    flash('Organization created successfully!', 'success')
                    return jsonify({
                        'success': True,
                        'message': 'Organization created successfully!',
                        'redirect': url_for('main.dashboard')  # Redirect to dashboard for now
                    })
                else:
                    current_app.logger.error("Failed to add organization member")
                    return jsonify({'error': 'Failed to add organization member'}), 500
            else:
                current_app.logger.error("Failed to create organization")
                return jsonify({'error': 'Failed to create organization'}), 500

        except Exception as e:
            current_app.logger.error(f"Error creating organization: {e}")
            import traceback
            traceback.print_exc()

            # Handle Pydantic validation errors specifically
            if hasattr(e, 'errors'):
                validation_errors = []
                for error in e.errors():
                    field = error.get('loc', ['unknown'])[0]
                    message = error.get('msg', 'Invalid value')
                    validation_errors.append(f"{field}: {message}")
                return jsonify({'error': f'Validation error: {", ".join(validation_errors)}'}), 400

            return jsonify({'error': f'Error creating organization: {str(e)}'}), 500

    return render_template('orgs/create.html')

@orgs_bp.route('/<org_slug>/edit', methods=['GET', 'POST'])
@require_org_admin('org_slug')
def edit_organization(org_slug):
    try:
        supabase = get_supabase()

        # Get organization
        org_response = supabase.table('organizations').select('*').eq('slug', org_slug).execute()
        if not org_response.data:
            flash('Organization not found.', 'error')
            return redirect(url_for('main.dashboard'))

        organization = org_response.data[0]

        if request.method == 'POST':
            try:
                data = request.get_json()
                update_request = UpdateOrganizationRequest(**data)

                update_data = {}
                if update_request.name:
                    update_data['name'] = update_request.name
                if update_request.slug:
                    # Check if new slug is unique
                    if update_request.slug != org_slug:
                        existing_org = supabase.table('organizations').select('id').eq('slug', update_request.slug).execute()
                        if existing_org.data:
                            return jsonify({'error': 'Organization slug already exists'}), 400
                    update_data['slug'] = update_request.slug

                if update_data:
                    update_data['updated_at'] = datetime.utcnow().isoformat()
                    supabase.table('organizations').update(update_data).eq('id', organization['id']).execute()

                flash('Organization updated successfully!', 'success')
                return jsonify({'redirect': url_for('main.org_dashboard', org_slug=update_data.get('slug', org_slug))})

            except Exception as e:
                return jsonify({'error': str(e)}), 400

        return render_template('orgs/edit.html', organization=organization)

    except Exception as e:
        flash('Error loading organization.', 'error')
        return redirect(url_for('main.dashboard'))
@orgs_bp.route('/<org_slug>/manage', methods=['GET'])
@require_org_admin('org_slug')
def manage_organization(org_slug):
    """Organization admin overview page with management actions"""
    try:
        supabase = get_service_supabase()

        # Get organization
        org_response = supabase.table('organizations').select('*').eq('slug', org_slug).execute()
        if not org_response.data:
            flash('Organization not found.', 'error')
            return redirect(url_for('main.dashboard'))
        organization = org_response.data[0]

        # Counts and recent
        members_count = supabase.table('organization_members').select('id', count='exact').eq('org_id', organization['id']).execute()
        records_count = supabase.table('records').select('id', count='exact').eq('org_id', organization['id']).execute()
        invites_count = supabase.table('invitations').select('id', count='exact').eq('org_id', organization['id']).execute()

        recent_records = supabase.table('records').select('*').eq('org_id', organization['id']).order('created_at', desc=True).limit(5).execute()
        # Agents count may fail if table not yet migrated
        try:
            agents_count_resp = supabase.table('agents').select('id', count='exact').eq('org_id', organization['id']).execute()
            agents_count_val = agents_count_resp.count or 0
        except Exception:
            agents_count_val = 0

        return render_template('orgs/manage.html',
                               organization=organization,
                               members_count=members_count.count or 0,
                               records_count=records_count.count or 0,
                               invites_count=invites_count.count or 0,
                               agents_count=agents_count_val,
                               recent_records=recent_records.data or [])
    except Exception as e:
        flash('Error loading organization.', 'error')
        return redirect(url_for('main.dashboard'))


@orgs_bp.route('/<org_slug>', methods=['DELETE'])
@require_org_admin('org_slug')
def delete_organization(org_slug):
    """Delete organization and related data (admin only)."""
    try:
        supabase = get_service_supabase()
        org_resp = supabase.table('organizations').select('id').eq('slug', org_slug).execute()
        if not org_resp.data:
            return jsonify({'error': 'Organization not found'}), 404
        org_id = org_resp.data[0]['id']

        # Delete related rows first (basic cascade)
        supabase.table('organization_members').delete().eq('org_id', org_id).execute()
        supabase.table('invitations').delete().eq('org_id', org_id).execute()
        supabase.table('records').delete().eq('org_id', org_id).execute()

        # Delete organization
        supabase.table('organizations').delete().eq('id', org_id).execute()

        flash('Organization deleted successfully.', 'success')
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@orgs_bp.route('/<org_slug>/agents', methods=['POST'])
@require_org_admin('org_slug')
def create_agent(org_slug):
    """Create an agent for the organization. Types: email_summarizer | hubspot_data | custom"""
    try:
        current_app.logger.info(f"Creating agent for org: {org_slug}")
        current_app.logger.info(f"Request content type: {request.content_type}")
        current_app.logger.info(f"Request is_json: {request.is_json}")

        # Accept JSON or form-encoded payloads robustly
        if request.is_json:
            data = request.get_json(silent=True) or {}
        else:
            data = request.form.to_dict() or {}

        current_app.logger.info(f"Received data: {data}")

        name = (data.get('name') or '').strip()
        agent_type = (data.get('type') or '').strip()

        current_app.logger.info(f"Parsed name: '{name}', agent_type: '{agent_type}'")

        if not name or not agent_type:
            current_app.logger.error(f"Missing required fields: name='{name}', type='{agent_type}'")
            return jsonify({'error': 'Name and type are required'}), 400
        if agent_type not in ['email_summarizer', 'hubspot_data', 'custom']:
            current_app.logger.error(f"Invalid agent type: '{agent_type}'")
            return jsonify({'error': 'Invalid agent type'}), 400

        supabase = get_service_supabase()
        # Resolve slug -> id
        org_resp = supabase.table('organizations').select('id').eq('slug', org_slug).limit(1).execute()
        if not org_resp.data:
            current_app.logger.error(f"Organization not found: {org_slug}")
            return jsonify({'error': 'Organization not found'}), 404
        org_id = org_resp.data[0]['id']
        current_app.logger.info(f"Found organization ID: {org_id}")

        # Create agent record
        import json, uuid
        now = datetime.utcnow().isoformat()
        agent = {
            'id': str(uuid.uuid4()),
            'org_id': org_id,
            'name': name,
            'agent_type': agent_type,
            'config': {},
            'created_by': current_user.id,
            'created_at': now,
            'updated_at': now
        }
        current_app.logger.info(f"Creating agent: {agent}")

        result = supabase.table('agents').insert(agent).execute()
        current_app.logger.info(f"Agent created successfully: {result}")

        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@orgs_bp.route('/<org_slug>/agents', methods=['GET'])
@require_org_member('org_slug')
def list_agents(org_slug):
    """List agents for an organization (records tagged as agents)."""
    try:
        supabase = get_service_supabase()
        org_resp = supabase.table('organizations').select('*').eq('slug', org_slug).limit(1).execute()
        if not org_resp.data:
            flash('Organization not found.', 'error')
            return redirect(url_for('main.dashboard'))
        organization = org_resp.data[0]

        # For now: agents are records whose content JSON has agent_type
        agents_resp = supabase.table('agents').select('*').eq('org_id', organization['id']).order('created_at', desc=True).execute()
        agents = agents_resp.data or []
        return render_template('orgs/agents.html', organization=organization, agents=agents)
    except Exception as e:
        flash('Error loading agents.', 'error')
        return redirect(url_for('main.dashboard'))



@orgs_bp.route('/<org_slug>/members')
@require_org_member('org_slug')
def list_members(org_slug):
    try:
        supabase = get_supabase()
        # Get organization
        org_response = supabase.table('organizations').select('*').eq('slug', org_slug).execute()
        if not org_response.data:
            flash('Organization not found.', 'error')
            return redirect(url_for('main.dashboard'))
        organization = org_response.data[0]

        # Get members
        members_response = supabase.table('organization_members').select('user_id, role, joined_at').eq('org_id', organization['id']).execute()
        members = []
        for member in members_response.data:
            user_response = supabase.table('users').select('email, display_name').eq('id', member['user_id']).execute()
            if user_response.data:
                user_data = user_response.data[0]
                members.append({
                    'user_id': member['user_id'],
                    'email': user_data['email'],
                    'display_name': user_data.get('display_name'),
                    'role': member['role'],
                    'joined_at': member['joined_at']
                })

        return render_template('orgs/members.html', organization=organization, members=members)

    except Exception as e:
        flash('Error loading members.', 'error')
        return redirect(url_for('main.dashboard'))


@orgs_bp.route('/<org_slug>/agents/<agent_id>', methods=['PATCH'])
@require_org_admin('org_slug')
def update_agent(org_slug, agent_id):
    try:
        data = request.get_json() or {}
        updates = {}
        if 'name' in data and data['name']:
            updates['name'] = data['name']
        if not updates:
            return jsonify({'error': 'No changes provided'}), 400
        updates['updated_at'] = datetime.utcnow().isoformat()
        supabase = get_service_supabase()
        supabase.table('agents').update(updates).eq('id', agent_id).execute()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@orgs_bp.route('/<org_slug>/agents/<agent_id>', methods=['GET'])
@require_org_member('org_slug')
def view_agent(org_slug, agent_id):
    """View individual agent details and handle Email Summarizer functionality"""
    try:
        current_app.logger.info(f"Viewing agent: org_slug={org_slug}, agent_id={agent_id}")
        supabase = get_service_supabase()

        # Get organization
        org_resp = supabase.table('organizations').select('*').eq('slug', org_slug).limit(1).execute()
        if not org_resp.data:
            flash('Organization not found.', 'error')
            return redirect(url_for('main.dashboard'))
        organization = org_resp.data[0]

        # Get agent
        agent_resp = supabase.table('agents').select('*').eq('id', agent_id).eq('org_id', organization['id']).execute()
        if not agent_resp.data:
            flash('Agent not found.', 'error')
            return redirect(url_for('orgs.list_agents', org_slug=org_slug))
        agent = agent_resp.data[0]

        # Check if Gmail is connected for email_summarizer agents
        gmail_connected = False
        if agent['agent_type'] == 'email_summarizer':
            config = agent.get('config', {})
            gmail_connected = bool(config.get('gmail_refresh_token'))

        return render_template('orgs/agent_detail.html',
                             organization=organization,
                             agent=agent,
                             gmail_connected=gmail_connected)

    except Exception as e:
        current_app.logger.error(f"Error viewing agent: {e}")
        flash('Error loading agent.', 'error')
        return redirect(url_for('orgs.list_agents', org_slug=org_slug))

@orgs_bp.route('/<org_slug>/agents/<agent_id>/gmail/auth')
@require_org_member('org_slug')
def gmail_auth(org_slug, agent_id):
    """Initiate Gmail OAuth flow"""
    try:
        from urllib.parse import urlencode
        import os

        # Gmail OAuth configuration
        client_id = os.getenv('GMAIL_CLIENT_ID')
        if not client_id:
            flash('Gmail OAuth not configured. Please contact administrator.', 'error')
            return redirect(url_for('orgs.view_agent', org_slug=org_slug, agent_id=agent_id))

        # OAuth parameters - use a fixed callback URL
        redirect_uri = url_for('orgs.gmail_callback_handler', _external=True)
        current_app.logger.info(f"Gmail OAuth redirect URI: {redirect_uri}")
        params = {
            'client_id': client_id,
            'redirect_uri': redirect_uri,
            'scope': 'https://www.googleapis.com/auth/gmail.readonly',
            'response_type': 'code',
            'access_type': 'offline',
            'prompt': 'consent',
            'state': f"{org_slug}:{agent_id}"
        }

        auth_url = f"https://accounts.google.com/o/oauth2/auth?{urlencode(params)}"
        return redirect(auth_url)

    except Exception as e:
        current_app.logger.error(f"Error initiating Gmail auth: {e}")
        flash('Error connecting to Gmail.', 'error')
        return redirect(url_for('orgs.view_agent', org_slug=org_slug, agent_id=agent_id))

@orgs_bp.route('/<org_slug>/agents/<agent_id>/gmail/callback')
@require_org_member('org_slug')
def gmail_callback(org_slug, agent_id):
    """Handle Gmail OAuth callback"""
    try:
        import requests
        import os

        code = request.args.get('code')
        state = request.args.get('state')
        error = request.args.get('error')

        if error:
            flash(f'Gmail authorization failed: {error}', 'error')
            return redirect(url_for('orgs.view_agent', org_slug=org_slug, agent_id=agent_id))

        if not code:
            flash('No authorization code received.', 'error')
            return redirect(url_for('orgs.view_agent', org_slug=org_slug, agent_id=agent_id))

        # Verify state parameter
        expected_state = f"{org_slug}:{agent_id}"
        if state != expected_state:
            flash('Invalid state parameter.', 'error')
            return redirect(url_for('orgs.view_agent', org_slug=org_slug, agent_id=agent_id))

        # Exchange code for tokens
        client_id = os.getenv('GMAIL_CLIENT_ID')
        client_secret = os.getenv('GMAIL_CLIENT_SECRET')

        redirect_uri = url_for('orgs.gmail_callback_handler', _external=True)
        current_app.logger.info(f"Token exchange redirect URI: {redirect_uri}")
        token_data = {
            'client_id': client_id,
            'client_secret': client_secret,
            'code': code,
            'grant_type': 'authorization_code',
            'redirect_uri': redirect_uri
        }

        token_response = requests.post('https://oauth2.googleapis.com/token', data=token_data)
        token_json = token_response.json()

        if 'error' in token_json:
            flash(f'Token exchange failed: {token_json["error"]}', 'error')
            return redirect(url_for('orgs.view_agent', org_slug=org_slug, agent_id=agent_id))

        # Store refresh token in agent config
        supabase = get_service_supabase()
        config_update = {
            'gmail_refresh_token': token_json.get('refresh_token'),
            'gmail_access_token': token_json.get('access_token'),
            'gmail_connected_at': datetime.utcnow().isoformat()
        }

        supabase.table('agents').update({
            'config': config_update,
            'updated_at': datetime.utcnow().isoformat()
        }).eq('id', agent_id).execute()

        flash('Gmail connected successfully!', 'success')
        return redirect(url_for('orgs.view_agent', org_slug=org_slug, agent_id=agent_id))

    except Exception as e:
        current_app.logger.error(f"Error in Gmail callback: {e}")
        flash('Error connecting Gmail account.', 'error')
        return redirect(url_for('orgs.view_agent', org_slug=org_slug, agent_id=agent_id))

@orgs_bp.route('/gmail/callback')
def gmail_callback_handler():
    """Fixed Gmail OAuth callback handler"""
    try:
        import requests
        import os

        code = request.args.get('code')
        state = request.args.get('state')
        error = request.args.get('error')

        if error:
            flash(f'Gmail authorization failed: {error}', 'error')
            return redirect(url_for('main.dashboard'))

        if not code or not state:
            flash('Invalid OAuth response.', 'error')
            return redirect(url_for('main.dashboard'))

        # Parse state to get org_slug and agent_id
        try:
            org_slug, agent_id = state.split(':', 1)
        except ValueError:
            flash('Invalid state parameter.', 'error')
            return redirect(url_for('main.dashboard'))

        # Exchange code for tokens
        client_id = os.getenv('GMAIL_CLIENT_ID')
        client_secret = os.getenv('GMAIL_CLIENT_SECRET')

        redirect_uri = url_for('orgs.gmail_callback_handler', _external=True)
        current_app.logger.info(f"Main callback redirect URI: {redirect_uri}")
        token_data = {
            'client_id': client_id,
            'client_secret': client_secret,
            'code': code,
            'grant_type': 'authorization_code',
            'redirect_uri': redirect_uri
        }

        token_response = requests.post('https://oauth2.googleapis.com/token', data=token_data)
        token_json = token_response.json()

        if 'error' in token_json:
            flash(f'Token exchange failed: {token_json["error"]}', 'error')
            return redirect(url_for('orgs.view_agent', org_slug=org_slug, agent_id=agent_id))

        # Store refresh token in agent config
        supabase = get_service_supabase()
        config_update = {
            'gmail_refresh_token': token_json.get('refresh_token'),
            'gmail_access_token': token_json.get('access_token'),
            'gmail_connected_at': datetime.utcnow().isoformat()
        }

        supabase.table('agents').update({
            'config': config_update,
            'updated_at': datetime.utcnow().isoformat()
        }).eq('id', agent_id).execute()

        flash('Gmail connected successfully!', 'success')
        return redirect(url_for('orgs.view_agent', org_slug=org_slug, agent_id=agent_id))

    except Exception as e:
        current_app.logger.error(f"Error in Gmail callback: {e}")
        flash('Error connecting Gmail account.', 'error')
        return redirect(url_for('main.dashboard'))





@orgs_bp.route('/<org_slug>/agents/<agent_id>/emails/test', methods=['POST'])
@require_org_member('org_slug')
def test_gmail_connection(org_slug, agent_id):
    """Test Gmail connection without full email processing"""
    try:
        current_app.logger.info(f"Testing Gmail connection for agent {agent_id}")
        supabase = get_service_supabase()

        # Get agent and verify it's an email_summarizer
        agent_resp = supabase.table('agents').select('*').eq('id', agent_id).execute()
        if not agent_resp.data:
            return jsonify({'error': 'Agent not found'}), 404

        agent = agent_resp.data[0]
        if agent['agent_type'] != 'email_summarizer':
            return jsonify({'error': 'Agent is not an email summarizer'}), 400

        config = agent.get('config', {})
        refresh_token = config.get('gmail_refresh_token')

        if not refresh_token:
            return jsonify({'error': 'Gmail not connected'}), 400

        # Just test the connection by getting basic profile info
        from agentsdr.services.gmail_service import GmailService
        gmail_service = GmailService()
        service = gmail_service.build_gmail_service(refresh_token)
        
        # Test with a simple profile call
        profile = service.users().getProfile(userId='me').execute()
        
        return jsonify({
            'success': True,
            'message': 'Gmail connection working',
            'email': profile.get('emailAddress'),
            'total_messages': profile.get('messagesTotal', 0)
        })

    except Exception as e:
        current_app.logger.error(f"Error testing Gmail connection: {e}")
        import traceback
        current_app.logger.error(f"Full traceback: {traceback.format_exc()}")
        return jsonify({'error': str(e)}), 500


@orgs_bp.route('/<org_slug>/agents/<agent_id>/emails/summarize', methods=['POST'])
@require_org_member('org_slug')
def summarize_emails(org_slug, agent_id):
    """Fetch and summarize emails based on criteria"""
    try:
        current_app.logger.info(f"Email summarize request: org_slug={org_slug}, agent_id={agent_id}")

        data = request.get_json()
        if not data:
            current_app.logger.error("No JSON data received, using defaults")
            data = {'type': 'last_24_hours', 'count': 10}

        # Normalize inputs coming from the UI (which may be strings)
        criteria_type = str(data.get('type', 'last_24_hours')).strip() or 'last_24_hours'
        try:
            count = int(data.get('count', 10))
        except (ValueError, TypeError):
            count = 10
        # Keep count within a reasonable range for Gmail API
        if count <= 0:
            count = 10
        if count > 100:
            count = 100
        current_app.logger.info(f"Raw data received: {data}")
        current_app.logger.info(f"Criteria: type={criteria_type}, count={count}")

        supabase = get_service_supabase()

        # Get agent and verify it's an email_summarizer
        agent_resp = supabase.table('agents').select('*').eq('id', agent_id).execute()
        if not agent_resp.data:
            return jsonify({'error': 'Agent not found'}), 404

        agent = agent_resp.data[0]
        if agent['agent_type'] != 'email_summarizer':
            return jsonify({'error': 'Agent is not an email summarizer'}), 400

        config = agent.get('config', {})
        refresh_token = config.get('gmail_refresh_token')

        if not refresh_token:
            return jsonify({'error': 'Gmail not connected'}), 400

        # Check required environment variables
        import os
        if not os.getenv('GMAIL_CLIENT_ID'):
            return jsonify({'error': 'Gmail OAuth not configured (missing GMAIL_CLIENT_ID)'}), 500
        if not os.getenv('GMAIL_CLIENT_SECRET'):
            return jsonify({'error': 'Gmail OAuth not configured (missing GMAIL_CLIENT_SECRET)'}), 500
        if not os.getenv('OPENAI_API_KEY'):
            return jsonify({'error': 'OpenAI API not configured. Please set the OPENAI_API_KEY environment variable.'}), 500

        # Fetch and summarize emails
        try:
            current_app.logger.info(f"Starting email summarization for agent {agent_id}")
            summaries = fetch_and_summarize_emails(refresh_token, criteria_type, count)
            
            current_app.logger.info(f"Email summarization completed successfully with {len(summaries)} summaries")

            current_app.logger.info(f"Returning {len(summaries)} summaries directly")

            return jsonify({
                'success': True,
                'summaries': summaries,
                'criteria_type': criteria_type,
                'count': len(summaries)
            })
            
        except Exception as fetch_error:
            current_app.logger.error(f"Error in email fetching/summarization: {fetch_error}")
            # Check if it's a token-related error
            if 'token' in str(fetch_error).lower() or 'auth' in str(fetch_error).lower():
                return jsonify({'error': 'Gmail authentication failed. Please reconnect your Gmail account.'}), 401
            elif 'quota' in str(fetch_error).lower() or 'insufficient' in str(fetch_error).lower():
                return jsonify({'error': 'OpenAI API quota exceeded. Please add credits to your OpenAI account.'}), 429
            elif 'rate' in str(fetch_error).lower():
                return jsonify({'error': 'Rate limit exceeded. Please try again in a few minutes.'}), 429
            else:
                return jsonify({'error': f'Failed to fetch emails: {str(fetch_error)}'}), 500

    except Exception as e:
        current_app.logger.error(f"Error in summarize_emails endpoint: {e}")
        import traceback
        current_app.logger.error(f"Full traceback: {traceback.format_exc()}")
        return jsonify({'error': 'An unexpected error occurred. Please try again.'}), 500


@orgs_bp.route('/<org_slug>/agents/<agent_id>/summaries', methods=['GET'])
@require_org_member('org_slug')
def view_summaries(org_slug, agent_id):
    """View email summaries page"""
    try:
        supabase = get_service_supabase()

        # Get organization
        org_resp = supabase.table('organizations').select('*').eq('slug', org_slug).limit(1).execute()
        if not org_resp.data:
            flash('Organization not found.', 'error')
            return redirect(url_for('main.dashboard'))
        organization = org_resp.data[0]

        # Get agent
        agent_resp = supabase.table('agents').select('*').eq('id', agent_id).eq('org_id', organization['id']).execute()
        if not agent_resp.data:
            flash('Agent not found.', 'error')
            return redirect(url_for('orgs.list_agents', org_slug=org_slug))
        agent = agent_resp.data[0]

        # Check if Gmail is connected for email_summarizer agents
        gmail_connected = False
        if agent['agent_type'] == 'email_summarizer':
            config = agent.get('config', {})
            gmail_connected = bool(config.get('gmail_refresh_token'))

        # Get summaries from database using session ID
        from flask import session
        session_id = session.get(f'summaries_{agent_id}')
        
        if session_id:
            # Retrieve from database
            supabase = get_service_supabase()
            record_resp = supabase.table('records').select('*').eq('session_id', session_id).eq('record_type', 'email_summaries').limit(1).execute()
            
            if record_resp.data:
                record = record_resp.data[0]
                summaries_data = record['data']
                summaries = summaries_data.get('summaries', [])
                criteria_type = summaries_data.get('criteria_type', 'last_24_hours')
                
                current_app.logger.info(f"Retrieved {len(summaries)} summaries from database for agent {agent_id}")
                current_app.logger.info(f"Session ID: {session_id}")
                if summaries:
                    current_app.logger.info(f"First summary sender: {summaries[0].get('sender', 'Unknown')}")
                    current_app.logger.info(f"Last summary sender: {summaries[-1].get('sender', 'Unknown')}")
            else:
                current_app.logger.warning(f"No record found for session_id: {session_id}")
                summaries = []
                criteria_type = 'last_24_hours'
        else:
            current_app.logger.warning(f"No session_id found for agent {agent_id}")
            summaries = []
            criteria_type = 'last_24_hours'

        return render_template('orgs/email_summaries.html',
                             organization=organization,
                             agent=agent,
                             gmail_connected=gmail_connected,
                             summaries=summaries,
                             criteria_type=criteria_type)

    except Exception as e:
        current_app.logger.error(f"Error viewing summaries: {e}")
        flash('Error loading summaries.', 'error')
        return redirect(url_for('orgs.view_agent', org_slug=org_slug, agent_id=agent_id))


@orgs_bp.route('/<org_slug>/agents/<agent_id>/schedule', methods=['GET', 'POST'])
@require_org_member('org_slug')
def manage_schedule(org_slug, agent_id):
    """Get or create/update agent schedule"""
    try:
        current_app.logger.info(f"Managing schedule for org: {org_slug}, agent: {agent_id}")
        supabase = get_service_supabase()

        # Get organization
        org_resp = supabase.table('organizations').select('*').eq('slug', org_slug).limit(1).execute()
        if not org_resp.data:
            current_app.logger.error(f"Organization not found: {org_slug}")
            return jsonify({'error': 'Organization not found'}), 404
        organization = org_resp.data[0]
        current_app.logger.info(f"Found organization: {organization['id']}")

        # Get agent
        agent_resp = supabase.table('agents').select('*').eq('id', agent_id).eq('org_id', organization['id']).execute()
        if not agent_resp.data:
            current_app.logger.error(f"Agent not found: {agent_id}")
            return jsonify({'error': 'Agent not found'}), 404
        agent = agent_resp.data[0]
        current_app.logger.info(f"Found agent: {agent['name']}")

        if request.method == 'GET':
            # Get current schedule
            try:
                schedule_resp = supabase.table('agent_schedules').select('*').eq('agent_id', agent_id).limit(1).execute()
                schedule = schedule_resp.data[0] if schedule_resp.data else None
                current_app.logger.info(f"Retrieved schedule: {schedule}")
                
                return jsonify({
                    'success': True,
                    'schedule': schedule
                })
            except Exception as e:
                current_app.logger.error(f"Error getting schedule: {e}")
                return jsonify({'error': f'Failed to get schedule: {str(e)}'}), 500
        
        elif request.method == 'POST':
            data = request.get_json()
            current_app.logger.info(f"Received schedule data: {data}")
            
            schedule_time = data.get('schedule_time')
            recipient_email = data.get('recipient_email')
            criteria_type = data.get('criteria_type', 'last_24_hours')
            
            if not schedule_time or not recipient_email:
                current_app.logger.error("Missing required fields")
                return jsonify({'error': 'Schedule time and recipient email are required'}), 400
            
            # Check if schedule exists
            try:
                existing_resp = supabase.table('agent_schedules').select('*').eq('agent_id', agent_id).limit(1).execute()
                current_app.logger.info(f"Existing schedules: {existing_resp.data}")
                
                if existing_resp.data:
                    # Update existing schedule
                    schedule_id = existing_resp.data[0]['id']
                    update_data = {
                        'schedule_time': schedule_time,
                        'recipient_email': recipient_email,
                        'criteria_type': criteria_type,
                        'updated_at': datetime.utcnow().isoformat()
                    }
                    
                    current_app.logger.info(f"Updating schedule {schedule_id} with data: {update_data}")
                    result = supabase.table('agent_schedules').update(update_data).eq('id', schedule_id).execute()
                    current_app.logger.info(f"Update result: {result}")
                else:
                    # Create new schedule
                    schedule_data = {
                        'agent_id': agent_id,
                        'org_id': organization['id'],
                        'schedule_time': schedule_time,
                        'recipient_email': recipient_email,
                        'criteria_type': criteria_type,
                        'created_by': g.user['id'],
                        'is_active': True
                    }
                    
                    current_app.logger.info(f"Creating new schedule with data: {schedule_data}")
                    result = supabase.table('agent_schedules').insert(schedule_data).execute()
                    current_app.logger.info(f"Insert result: {result}")
                
                return jsonify({
                    'success': True,
                    'message': 'Schedule saved successfully'
                })
                
            except Exception as e:
                current_app.logger.error(f"Error saving schedule: {e}")
                return jsonify({'error': f'Failed to save schedule: {str(e)}'}), 500
    
    except Exception as e:
        current_app.logger.error(f"Error managing schedule: {e}")
        return jsonify({'error': f'Failed to manage schedule: {str(e)}'}), 500


@orgs_bp.route('/<org_slug>/agents/<agent_id>/schedule/toggle', methods=['POST'])
@require_org_member('org_slug')
def toggle_schedule(org_slug, agent_id):
    """Toggle schedule active/inactive"""
    try:
        supabase = get_service_supabase()

        # Get organization
        org_resp = supabase.table('organizations').select('*').eq('slug', org_slug).limit(1).execute()
        if not org_resp.data:
            return jsonify({'error': 'Organization not found'}), 404
        organization = org_resp.data[0]

        # Get current schedule
        schedule_resp = supabase.table('agent_schedules').select('*').eq('agent_id', agent_id).limit(1).execute()
        if not schedule_resp.data:
            return jsonify({'error': 'No schedule found for this agent'}), 404
        
        schedule = schedule_resp.data[0]
        new_status = not schedule['is_active']
        
        # Update schedule status
        supabase.table('agent_schedules').update({
            'is_active': new_status,
            'updated_at': datetime.utcnow().isoformat()
        }).eq('id', schedule['id']).execute()
        
        return jsonify({
            'success': True,
            'is_active': new_status,
            'message': f"Schedule {'activated' if new_status else 'paused'}"
        })
    
    except Exception as e:
        current_app.logger.error(f"Error toggling schedule: {e}")
        return jsonify({'error': 'Failed to toggle schedule'}), 500


@orgs_bp.route('/<org_slug>/agents/<agent_id>', methods=['DELETE'])
@require_org_admin('org_slug')
def delete_agent(org_slug, agent_id):
    try:
        supabase = get_service_supabase()
        supabase.table('agents').delete().eq('id', agent_id).execute()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@orgs_bp.route('/<org_slug>/members/<user_id>/remove', methods=['POST'])
@require_org_admin('org_slug')
def remove_member(org_slug, user_id):
    try:
        supabase = get_supabase()

        # Get organization
        org_response = supabase.table('organizations').select('*').eq('slug', org_slug).execute()
        if not org_response.data:
            return jsonify({'error': 'Organization not found'}), 404

        organization = org_response.data[0]

        # Check if user is trying to remove themselves
        if user_id == current_user.id:
            return jsonify({'error': 'Cannot remove yourself from the organization'}), 400

        # Remove member
        supabase.table('organization_members').delete().eq('org_id', organization['id']).eq('user_id', user_id).execute()

        flash('Member removed successfully.', 'success')
        return jsonify({'success': True})

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@orgs_bp.route('/<org_slug>/members/<user_id>/role', methods=['POST'])
@require_org_admin('org_slug')
def update_member_role(org_slug, user_id):
    try:
        data = request.get_json()
        new_role = data.get('role')

        if new_role not in ['admin', 'member']:
            return jsonify({'error': 'Invalid role'}), 400

        supabase = get_supabase()

        # Get organization
        org_response = supabase.table('organizations').select('*').eq('slug', org_slug).execute()
        if not org_response.data:
            return jsonify({'error': 'Organization not found'}), 404

        organization = org_response.data[0]

        # Update member role
        supabase.table('organization_members').update({'role': new_role}).eq('org_id', organization['id']).eq('user_id', user_id).execute()

        flash('Member role updated successfully.', 'success')
        return jsonify({'success': True})

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@orgs_bp.route('/<org_slug>/invites')
@require_org_admin('org_slug')
def list_invitations(org_slug):
    try:
        supabase = get_supabase()

        # Get organization
        org_response = supabase.table('organizations').select('*').eq('slug', org_slug).execute()
        if not org_response.data:
            flash('Organization not found.', 'error')
            return redirect(url_for('main.dashboard'))

        organization = org_response.data[0]

        # Get invitations
        invitations_response = supabase.table('invitations').select('*').eq('org_id', organization['id']).order('created_at', desc=True).execute()

        return render_template('orgs/invitations.html', organization=organization, invitations=invitations_response.data)

    except Exception as e:
        flash('Error loading invitations.', 'error')
        return redirect(url_for('main.dashboard'))

@orgs_bp.route('/<org_slug>/invites', methods=['POST'])
@require_org_admin('org_slug')
def create_invitation(org_slug):
    try:
        data = request.get_json()
        invite_request = CreateInvitationRequest(**data)

        supabase = get_supabase()

        # Get organization
        org_response = supabase.table('organizations').select('*').eq('slug', org_slug).execute()
        if not org_response.data:
            return jsonify({'error': 'Organization not found'}), 404

        organization = org_response.data[0]

        # Check if user is already a member
        existing_member = supabase.table('organization_members').select('*').eq('org_id', organization['id']).eq('user_id', invite_request.email).execute()
        if existing_member.data:
            return jsonify({'error': 'User is already a member of this organization'}), 400

        # Check if invitation already exists
        existing_invite = supabase.table('invitations').select('*').eq('org_id', organization['id']).eq('email', invite_request.email).eq('accepted_at', None).execute()
        if existing_invite.data:
            return jsonify({'error': 'Invitation already sent to this email'}), 400

        # Create invitation
        token = secrets.token_urlsafe(32)
        expires_at = datetime.utcnow() + timedelta(hours=72)

        invitation_data = {
            'id': str(uuid.uuid4()),
            'org_id': organization['id'],
            'email': invite_request.email,
            'role': invite_request.role,
            'token': token,
            'expires_at': expires_at.isoformat(),
            'invited_by': current_user.id,
            'created_at': datetime.utcnow().isoformat()
        }

        invitation_response = supabase.table('invitations').insert(invitation_data).execute()

        if invitation_response.data:
            # Send invitation email
            email_sent = get_email_service().send_invitation_email(
                invite_request.email,
                organization['name'],
                invite_request.role,
                token,
                current_user.display_name or current_user.email
            )

            if email_sent:
                flash('Invitation sent successfully!', 'success')
            else:
                flash('Invitation created but email failed to send.', 'warning')

            return jsonify({'success': True})
        else:
            return jsonify({'error': 'Failed to create invitation'}), 500

    except Exception as e:
        return jsonify({'error': str(e)}), 400

@orgs_bp.route('/<org_slug>/invites/<invitation_id>/resend', methods=['POST'])
@require_org_admin('org_slug')
def resend_invitation(org_slug, invitation_id):
    try:
        supabase = get_supabase()

        # Get invitation
        invitation_response = supabase.table('invitations').select('*').eq('id', invitation_id).execute()
        if not invitation_response.data:
            return jsonify({'error': 'Invitation not found'}), 404

        invitation = invitation_response.data[0]

        # Get organization
        org_response = supabase.table('organizations').select('*').eq('id', invitation['org_id']).execute()
        if not org_response.data:
            return jsonify({'error': 'Organization not found'}), 404

        organization = org_response.data[0]

        # Resend invitation email
        email_sent = get_email_service().send_invitation_email(
            invitation['email'],
            organization['name'],
            invitation['role'],
            invitation['token'],
            current_user.display_name or current_user.email
        )

        if email_sent:
            flash('Invitation resent successfully!', 'success')
            return jsonify({'success': True})
        else:
            return jsonify({'error': 'Failed to send invitation email'}), 500

    except Exception as e:
        return jsonify({'error': str(e)}), 400

@orgs_bp.route('/mine', methods=['GET'])
@login_required
def my_organizations():
    """List organizations where the current user is admin"""
    try:
        supabase = get_service_supabase()

        # Get memberships where user is admin
        memberships = supabase.table('organization_members').select('org_id, role').eq('user_id', current_user.id).eq('role', 'admin').execute()

        # Collect org details
        orgs = []
        for m in memberships.data or []:
            org_resp = supabase.table('organizations').select('id, name, slug, owner_user_id, created_at').eq('id', m['org_id']).execute()
            if org_resp.data:
                orgs.append({
                    'org': org_resp.data[0],
                    'role': m['role']
                })

        return render_template('orgs/mine.html', organizations=orgs)
    except Exception as e:
        flash(f'Failed to load organizations: {e}', 'error')
        return render_template('orgs/mine.html', organizations=[])



@orgs_bp.route('/<org_slug>/invites/<invitation_id>', methods=['DELETE'])
@require_org_admin('org_slug')
def revoke_invitation(org_slug, invitation_id):
    try:
        supabase = get_supabase()

        # Delete invitation
        supabase.table('invitations').delete().eq('id', invitation_id).execute()

        flash('Invitation revoked successfully.', 'success')
        return jsonify({'success': True})

    except Exception as e:
        return jsonify({'error': str(e)}), 500
