// Copyright (c) 2025, Tati and contributors
// For license information, please see license.txt

frappe.ui.form.on('Google Event', {
    join_meet: function(frm) {
        if(frm.doc.google_meet_link) {
            let match = frm.doc.google_meet_link.match(/href="([^"]+)"/);
            let url = match ? match[1] : frm.doc.google_meet_link;
            window.open(url, '_blank');
        } else {
            frappe.msgprint("No Google Meet link available for this event.");
        }
    }
});


