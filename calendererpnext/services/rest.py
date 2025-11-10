import os
import json
from datetime import datetime, timedelta
import frappe
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
import pytz

SCOPES = ['https://www.googleapis.com/auth/calendar']
LOCAL_TZ = pytz.timezone("Africa/Nairobi")


# -------------------------
# 1. AUTHENTICATE SERVICE
# -------------------------
def get_calendar_service():
    """Authenticate and return Google Calendar API service."""
    creds = None
    creds_file = frappe.get_site_path('google_credentials.json')
    token_file = frappe.get_site_path('token.json')

    if os.path.exists(token_file):
        creds = Credentials.from_authorized_user_file(token_file, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(creds_file, SCOPES)
            creds = flow.run_local_server(port=8080)
        with open(token_file, 'w') as token:
            token.write(creds.to_json())

    return build('calendar', 'v3', credentials=creds)


# -------------------------
# 2. CREATE GOOGLE MEET EVENT
# -------------------------
@frappe.whitelist()
def create_google_meet_event(summary, start_time, end_time, attendees=None):
    """Create a Google Meet event in Google Calendar."""
    try:
        service = get_calendar_service()
        event = {
            'summary': summary,
            'description': 'Automatically generated event via ERPNext',
            'start': {'dateTime': start_time.isoformat(), 'timeZone': 'Africa/Nairobi'},
            'end': {'dateTime': end_time.isoformat(), 'timeZone': 'Africa/Nairobi'},
            'conferenceData': {
                'createRequest': {
                    'requestId': f"meet-{int(datetime.now().timestamp())}",
                    'conferenceSolutionKey': {'type': 'hangoutsMeet'}
                }
            },
        }
        if attendees:
            event['attendees'] = attendees

        created_event = service.events().insert(
            calendarId='primary',
            body=event,
            conferenceDataVersion=1
        ).execute()

        meet_link = created_event.get('hangoutLink') or created_event['conferenceData']['entryPoints'][0]['uri']
        return {'event_id': created_event['id'], 'meet_link': meet_link}

    except Exception as e:
        frappe.log_error(str(e)[:1000], "Google Meet Integration")
        return {"error": str(e)}


from datetime import datetime, timedelta, timezone
import frappe
from calendererpnext.services.rest import get_calendar_service

# Set your local timezone offset for Nairobi (UTC+3)
LOCAL_TZ = timezone(timedelta(hours=3))

@frappe.whitelist(allow_guest=True)
def google_webhook():
    """Sync only events updated or created in the last 10 minutes."""
    try:
        headers = frappe.local.request.headers
        resource_state = headers.get("X-Goog-Resource-State")
        resource_id = headers.get("X-Goog-Resource-ID")

        # Log minimal info safely
        frappe.log_error(
            f"Webhook received: state={resource_state}, resource_id={resource_id}",
            "Google Webhook Debug"
        )

        service = get_calendar_service()

        # -----------------------------
        # Handle deleted events
        # -----------------------------
        if resource_state == "deleted":
            existing = frappe.get_all("Google Event", filters={"event_id": resource_id})
            if existing:
                frappe.delete_doc("Google Event", existing[0].name, ignore_permissions=True)
            return "Deleted"

        # -----------------------------
        # Handle created/updated events
        # -----------------------------
        if resource_state == "exists":
            ten_minutes_ago = datetime.utcnow().replace(tzinfo=timezone.utc) - timedelta(minutes=10)

            events_result = service.events().list(
                calendarId='primary',
                maxResults=2500,
                singleEvents=True,
                orderBy='updated',
                timeMin=ten_minutes_ago.isoformat()
            ).execute()

            for event in events_result.get('items', []):
                event_id = event.get("id")
                start_time = event["start"].get("dateTime")
                end_time = event["end"].get("dateTime")
                if not start_time or not end_time:
                    continue

                # Convert Google datetime string to naive local datetime
                def parse_google_datetime(dt_str):
                    dt = datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
                    dt_local = dt.astimezone(LOCAL_TZ)
                    return dt_local.replace(tzinfo=None)

                # Safe summary
                event_summary = event.get("summary", "Untitled Event").strip()
                if len(event_summary) > 140:
                    event_summary = event_summary[:140]

                existing = frappe.get_all("Google Event", filters={"event_id": event_id})
                if existing:
                    doc = frappe.get_doc("Google Event", existing[0].name)
                else:
                    doc = frappe.new_doc("Google Event")
                    if hasattr(doc, "event_participants"):
                        doc.event_participants = []

                doc._from_google_webhook = True
                doc.db_set({
                    "event_name": event_summary,
                    "start_time": parse_google_datetime(start_time),
                    "end_time": parse_google_datetime(end_time),
                    "event_id": event_id,
                    "google_meet_link": (
                        f'<a href="{event.get("hangoutLink")}" target="_blank">Join Google Meet</a>'
                        if event.get("hangoutLink") else None
                    )
                })
                frappe.log_error(f"Synced Google Event: {event_id}", "Google Webhook Sync")

        return "OK"

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Google Webhook Error")
        return str(e)


# -------------------------
# 4. SETUP WATCH
# -------------------------
@frappe.whitelist()
def setup_google_watch():
    """Subscribe to Google Calendar push notifications."""
    try:
        service = get_calendar_service()
        request = {
            "id": f"erpnext-channel-{frappe.generate_hash(length=8)}",
            "type": "web_hook",
            "address": "https://24fa0a170085.ngrok-free.app/api/method/calendererpnext.services.rest.google_webhook"
        }

        response = service.events().watch(calendarId='primary', body=request).execute()
        frappe.log_error(message=frappe.as_json(response), title="Google Watch Setup Response")
        return response
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Google Watch Setup Failed")
        return str(e)
