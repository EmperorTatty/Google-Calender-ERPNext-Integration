# Copyright (c) 2025, Tati and contributors
# For license information, please see license.txt

from calendererpnext.services.rest import create_google_meet_event, get_calendar_service
import frappe
from frappe.model.document import Document
from datetime import datetime, timezone

class GoogleEvent(Document):
    def before_save(self):
        """
        Automatically create Google Meet for ERPNext-created events.
        Updates Google Calendar event if ERPNext record is updated.
        Ensures summary/title is not empty and <=140 characters.
        """
        try:
            if isinstance(self.start_time, str):
                self.start_time = datetime.fromisoformat(self.start_time)
            if isinstance(self.end_time, str):
                self.end_time = datetime.fromisoformat(self.end_time)

            attendees = []
            if hasattr(self, "event_participants"):
                for p in self.event_participants:
                    if p.email:
                        attendees.append({"email": p.email})

            # Skip creating/updating Google Meet for events coming from Google webhook
            if getattr(self, "_from_google_webhook", False):
                return

            # Safe summary handling
            summary = (self.event_name.strip() if self.event_name else "Untitled Event")
            if len(summary) > 140:
                summary = summary[:140]

            service = get_calendar_service()

            if not self.event_id:
                # Create Google Meet event
                event = create_google_meet_event(
                    summary=summary,
                    start_time=self.start_time,
                    end_time=self.end_time,
                    attendees=attendees
                )
                if event.get("error"):
                    frappe.throw(f"Error creating Google Meet: {event['error']}")
                self.event_id = event.get("event_id")
                self.google_meet_link = f'<a href="{event.get("meet_link")}" target="_blank">Join Google Meet</a>'
            else:
                # Update existing Google Calendar event
                event_body = {
                    'summary': summary,
                    'start': {'dateTime': self.start_time.isoformat(), 'timeZone': 'Africa/Nairobi'},
                    'end': {'dateTime': self.end_time.isoformat(), 'timeZone': 'Africa/Nairobi'},
                    'attendees': attendees
                }
                service.events().update(
                    calendarId='primary',
                    eventId=self.event_id,
                    body=event_body
                ).execute()

        except Exception as e:
            frappe.log_error(str(e)[:1000], "Google Meet Integration")
            frappe.throw(f"Error creating/updating Google Meet: {str(e)}")


    def on_trash(self):
        """Delete event from Google Calendar when deleted in ERPNext."""
        try:
            if self.event_id:
                service = get_calendar_service()
                service.events().delete(calendarId='primary', eventId=self.event_id).execute()
        except Exception as e:
            frappe.log_error(str(e), "Google Event Deletion Failed")
