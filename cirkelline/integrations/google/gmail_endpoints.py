"""
Google Gmail Integration Endpoints
===================================
Handles Gmail email operations (list, detail, send, reply, mark read, archive, delete).
"""

from fastapi import APIRouter, Request, HTTPException

from cirkelline.config import logger
from cirkelline.integrations.google.google_oauth import get_user_google_credentials

# Create router
router = APIRouter()

# ═══════════════════════════════════════════════════════════════
# GMAIL LIST ENDPOINT
# ═══════════════════════════════════════════════════════════════

@router.get("/api/google/emails")
async def get_emails(request: Request, count: int = 20, page_token: str = None):
    """
    Get list of user's emails from Gmail

    Query params:
    - count: Number of emails to fetch (default 20, max 100)
    - page_token: For pagination

    Returns list of emails with id, from, subject, snippet, date
    """
    try:
        # Get user_id from JWT middleware
        user_id = getattr(request.state, 'user_id', None)
        if not user_id or user_id == 'anonymous' or user_id.startswith('anon-'):
            raise HTTPException(status_code=401, detail="Authentication required")

        # Check if user has Google connected
        google_creds = await get_user_google_credentials(user_id)
        if not google_creds:
            raise HTTPException(status_code=403, detail="Google account not connected")

        # Initialize Gmail tools
        from agno.tools.gmail import GmailTools
        gmail_tools = GmailTools(creds=google_creds)

        # Limit count to reasonable maximum
        count = min(count, 100)

        # Get emails using Gmail tools
        # Note: GmailTools.get_latest_emails returns formatted string, not structured data
        # We need to use the Gmail API directly for structured data
        from googleapiclient.discovery import build
        service = build('gmail', 'v1', credentials=google_creds)

        # List messages
        results = service.users().messages().list(
            userId='me',
            maxResults=count,
            pageToken=page_token
        ).execute()

        messages = results.get('messages', [])
        next_page_token = results.get('nextPageToken')

        # Get details for each message
        emails = []
        for msg in messages:
            msg_data = service.users().messages().get(userId='me', id=msg['id'], format='metadata').execute()

            # Extract headers
            headers = {header['name']: header['value'] for header in msg_data.get('payload', {}).get('headers', [])}

            emails.append({
                'id': msg['id'],
                'thread_id': msg_data.get('threadId'),
                'from': headers.get('From', ''),
                'to': headers.get('To', ''),
                'subject': headers.get('Subject', '(No Subject)'),
                'snippet': msg_data.get('snippet', ''),
                'date': headers.get('Date', ''),
                'labels': msg_data.get('labelIds', []),
                'is_unread': 'UNREAD' in msg_data.get('labelIds', [])
            })

        return {
            'emails': emails,
            'next_page_token': next_page_token,
            'total_fetched': len(emails)
        }

    except HTTPException as he:
        raise
    except Exception as e:
        logger.error(f"Get emails error: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Failed to fetch emails: {str(e)}")

logger.info("✅ Google emails list endpoint configured")

@router.get("/api/google/emails/{email_id}")
async def get_email_detail(request: Request, email_id: str):
    """
    Get full details of a specific email

    Returns email with full body content (text and HTML)
    """
    try:
        # Get user_id from JWT middleware
        user_id = getattr(request.state, 'user_id', None)
        if not user_id or user_id == 'anonymous' or user_id.startswith('anon-'):
            raise HTTPException(status_code=401, detail="Authentication required")

        # Check if user has Google connected
        google_creds = await get_user_google_credentials(user_id)
        if not google_creds:
            raise HTTPException(status_code=403, detail="Google account not connected")

        # Build Gmail service
        from googleapiclient.discovery import build
        import base64
        service = build('gmail', 'v1', credentials=google_creds)

        # Get full message
        msg_data = service.users().messages().get(userId='me', id=email_id, format='full').execute()

        # Extract headers
        headers = {header['name']: header['value'] for header in msg_data.get('payload', {}).get('headers', [])}

        # Extract body
        def get_body(payload):
            """Recursively extract email body from payload"""
            body_text = ""
            body_html = ""

            if 'parts' in payload:
                for part in payload['parts']:
                    if part.get('mimeType') == 'text/plain' and 'data' in part.get('body', {}):
                        body_text = base64.urlsafe_b64decode(part['body']['data']).decode('utf-8')
                    elif part.get('mimeType') == 'text/html' and 'data' in part.get('body', {}):
                        body_html = base64.urlsafe_b64decode(part['body']['data']).decode('utf-8')
                    elif 'parts' in part:
                        # Recursive for nested parts
                        text, html = get_body(part)
                        body_text = body_text or text
                        body_html = body_html or html
            elif 'data' in payload.get('body', {}):
                # Single part message
                decoded = base64.urlsafe_b64decode(payload['body']['data']).decode('utf-8')
                if payload.get('mimeType') == 'text/plain':
                    body_text = decoded
                elif payload.get('mimeType') == 'text/html':
                    body_html = decoded

            return body_text, body_html

        body_text, body_html = get_body(msg_data.get('payload', {}))

        return {
            'id': email_id,
            'thread_id': msg_data.get('threadId'),
            'from': headers.get('From', ''),
            'to': headers.get('To', ''),
            'cc': headers.get('Cc', ''),
            'bcc': headers.get('Bcc', ''),
            'subject': headers.get('Subject', '(No Subject)'),
            'date': headers.get('Date', ''),
            'body_text': body_text,
            'body_html': body_html,
            'snippet': msg_data.get('snippet', ''),
            'labels': msg_data.get('labelIds', []),
            'is_unread': 'UNREAD' in msg_data.get('labelIds', [])
        }

    except HTTPException as he:
        raise
    except Exception as e:
        logger.error(f"Get email detail error: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Failed to fetch email: {str(e)}")

logger.info("✅ Google email detail endpoint configured")

@router.post("/api/google/emails/send")
async def send_email(request: Request):
    """
    Send a new email via Gmail

    Request body:
    {
        "to": "recipient@email.com",
        "subject": "Subject line",
        "body": "Email body content"
    }
    """
    try:
        # Get user_id from JWT middleware
        user_id = getattr(request.state, 'user_id', None)
        if not user_id or user_id == 'anonymous' or user_id.startswith('anon-'):
            raise HTTPException(status_code=401, detail="Authentication required")

        # Parse request body
        data = await request.json()
        to = data.get('to')
        subject = data.get('subject', '(No Subject)')
        body = data.get('body', '')

        if not to:
            raise HTTPException(status_code=400, detail="Recipient email required")

        # Check if user has Google connected
        google_creds = await get_user_google_credentials(user_id)
        if not google_creds:
            raise HTTPException(status_code=403, detail="Google account not connected")

        # Use Gmail tools to send email
        from agno.tools.gmail import GmailTools
        gmail_tools = GmailTools(creds=google_creds)

        # send_email method signature: send_email(to: str, subject: str, body: str)
        result = gmail_tools.send_email(to=to, subject=subject, body=body)

        return {
            'success': True,
            'message': 'Email sent successfully',
            'to': to,
            'subject': subject
        }

    except HTTPException as he:
        raise
    except Exception as e:
        logger.error(f"Send email error: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Failed to send email: {str(e)}")

logger.info("✅ Google send email endpoint configured")

@router.post("/api/google/emails/{email_id}/reply")
async def reply_to_email(request: Request, email_id: str):
    """
    Reply to an email

    Request body:
    {
        "body": "Reply content",
        "reply_all": false (optional)
    }
    """
    try:
        # Get user_id from JWT middleware
        user_id = getattr(request.state, 'user_id', None)
        if not user_id or user_id == 'anonymous' or user_id.startswith('anon-'):
            raise HTTPException(status_code=401, detail="Authentication required")

        # Parse request body
        data = await request.json()
        reply_body = data.get('body', '')
        reply_all = data.get('reply_all', False)

        if not reply_body:
            raise HTTPException(status_code=400, detail="Reply body required")

        # Check if user has Google connected
        google_creds = await get_user_google_credentials(user_id)
        if not google_creds:
            raise HTTPException(status_code=403, detail="Google account not connected")

        # Build Gmail service
        from googleapiclient.discovery import build
        import base64
        from email.mime.text import MIMEText
        service = build('gmail', 'v1', credentials=google_creds)

        # Get original email to extract headers
        original = service.users().messages().get(userId='me', id=email_id, format='metadata').execute()
        headers = {header['name']: header['value'] for header in original.get('payload', {}).get('headers', [])}

        # Prepare reply
        to = headers.get('From', '')  # Reply to sender
        subject = headers.get('Subject', '')
        if not subject.startswith('Re: '):
            subject = f"Re: {subject}"

        # Create message
        message = MIMEText(reply_body)
        message['to'] = to
        message['subject'] = subject
        message['In-Reply-To'] = headers.get('Message-ID', '')
        message['References'] = headers.get('Message-ID', '')

        # If reply all, add CC recipients
        if reply_all:
            cc = headers.get('Cc', '')
            if cc:
                message['cc'] = cc

        # Encode and send
        raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
        send_message = service.users().messages().send(
            userId='me',
            body={'raw': raw, 'threadId': original.get('threadId')}
        ).execute()

        return {
            'success': True,
            'message': 'Reply sent successfully',
            'message_id': send_message.get('id')
        }

    except HTTPException as he:
        raise
    except Exception as e:
        logger.error(f"Reply email error: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Failed to reply: {str(e)}")

logger.info("✅ Google reply email endpoint configured")

@router.post("/api/google/emails/{email_id}/mark-read")
async def mark_email_as_read(request: Request, email_id: str):
    """
    Mark an email as read (remove UNREAD label)
    """
    try:
        # Get user_id from JWT middleware
        user_id = getattr(request.state, 'user_id', None)
        if not user_id or user_id == 'anonymous' or user_id.startswith('anon-'):
            raise HTTPException(status_code=401, detail="Authentication required")

        # Check if user has Google connected
        google_creds = await get_user_google_credentials(user_id)
        if not google_creds:
            raise HTTPException(status_code=403, detail="Google account not connected")

        # Build Gmail service
        from googleapiclient.discovery import build
        service = build('gmail', 'v1', credentials=google_creds)

        # Remove UNREAD label (marks email as read)
        service.users().messages().modify(
            userId='me',
            id=email_id,
            body={'removeLabelIds': ['UNREAD']}
        ).execute()

        return {
            'success': True,
            'message': 'Email marked as read successfully'
        }

    except HTTPException as he:
        raise
    except Exception as e:
        logger.error(f"Mark email as read error: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Failed to mark email as read: {str(e)}")

logger.info("✅ Google mark email as read endpoint configured")

@router.post("/api/google/emails/{email_id}/archive")
async def archive_email(request: Request, email_id: str):
    """
    Archive an email (remove from INBOX label)
    """
    try:
        # Get user_id from JWT middleware
        user_id = getattr(request.state, 'user_id', None)
        if not user_id or user_id == 'anonymous' or user_id.startswith('anon-'):
            raise HTTPException(status_code=401, detail="Authentication required")

        # Check if user has Google connected
        google_creds = await get_user_google_credentials(user_id)
        if not google_creds:
            raise HTTPException(status_code=403, detail="Google account not connected")

        # Build Gmail service
        from googleapiclient.discovery import build
        service = build('gmail', 'v1', credentials=google_creds)

        # Remove INBOX label (archives the email)
        service.users().messages().modify(
            userId='me',
            id=email_id,
            body={'removeLabelIds': ['INBOX']}
        ).execute()

        return {
            'success': True,
            'message': 'Email archived successfully'
        }

    except HTTPException as he:
        raise
    except Exception as e:
        logger.error(f"Archive email error: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Failed to archive email: {str(e)}")

logger.info("✅ Google archive email endpoint configured")

@router.delete("/api/google/emails/{email_id}")
async def delete_email(request: Request, email_id: str):
    """
    Delete an email permanently
    """
    try:
        # Get user_id from JWT middleware
        user_id = getattr(request.state, 'user_id', None)
        if not user_id or user_id == 'anonymous' or user_id.startswith('anon-'):
            raise HTTPException(status_code=401, detail="Authentication required")

        # Check if user has Google connected
        google_creds = await get_user_google_credentials(user_id)
        if not google_creds:
            raise HTTPException(status_code=403, detail="Google account not connected")

        # Build Gmail service
        from googleapiclient.discovery import build
        service = build('gmail', 'v1', credentials=google_creds)

        # Delete the email
        service.users().messages().delete(userId='me', id=email_id).execute()

        return {
            'success': True,
            'message': 'Email deleted successfully'
        }

    except HTTPException as he:
        raise
    except Exception as e:
        logger.error(f"Delete email error: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Failed to delete email: {str(e)}")

logger.info("✅ Google delete email endpoint configured")


logger.info("✅ Gmail integration endpoints loaded")
