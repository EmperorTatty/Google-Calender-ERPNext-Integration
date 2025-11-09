# Copyright (c) 2025, Tati and contributors
# For license information, please see license.txt

from calendererpnext.services.rest import create_google_meet_event
import frappe
from frappe.model.document import Document
from datetime import datetime

class GoogleEvent(Document):
    def before_save(self):
        """Automatically create Google Meet when saving the document."""
        if self.event_id:
            return

        try:
            # Convert start_time and end_time to datetime objects if they are strings
            if isinstance(self.start_time, str):
                self.start_time = datetime.fromisoformat(self.start_time)
            if isinstance(self.end_time, str):
                self.end_time = datetime.fromisoformat(self.end_time)

            # Prepare attendees
            attendees = []
            for participant in self.event_participants:
                if participant.email:
                    attendees.append({'email': participant.email})

            event = create_google_meet_event(
                summary=self.event_name,
                start_time=self.start_time,
                end_time=self.end_time,
                attendees=attendees
            )

            if event.get("error"):
                frappe.throw(f"Error creating Google Meet: {event['error']}")

            self.event_id = event.get("event_id")
            self.google_meet_link = f'<a href="{event.get("meet_link")}" target="_blank">Join Google Meet</a>'

        except Exception as e:
            frappe.log_error(f"Google Meet Error: {str(e)}", "Google Meet Integration")
            frappe.throw(f"Error creating Google Meet: {str(e)}")
