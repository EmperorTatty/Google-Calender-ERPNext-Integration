# 🗓️ Google Calendar ERPNext Integration

## Overview  
**Google Calendar ERPNext** is a standalone app that seamlessly integrates Google Calendar events into your ERPNext instance.  
It allows you to **create, manage, and sync Google Meet events** directly from ERPNext — perfect for scheduling meetings, online classes, or project check-ins.

---

## 🚀 Features
- 🔄 Create Google Calendar events directly from ERPNext  
- 📅 Auto-generate Google Meet links  
- 👥 Add multiple event participants with RSVP tracking  
- 🕓 Sync event details such as start and end times  
- 📍 Join meeting directly from ERPNext  
- 🧠 (Coming Soon) Two-way sync: reflect event updates from Google Calendar back into ERPNext  

---

## 🧩 Doctypes

### 1️⃣ Google Event
Stores event details and integrates with Google Calendar.  
**Key fields:**
- **Event Name**
- **Start Time / End Time**
- **Google Meet Link**
- **Event ID** (from Google)
- **Participants** (child table)
- **Join Meet Button** (for quick access)

### 2️⃣ Participants (Child Table)
Stores information about each attendee.  
**Fields:**
- **Name**
- **Email**
- **Response** (Accepted / Declined)

---

## ⚙️ Setup Instructions

### 1️⃣ Enable Google Cloud API
1. Go to [Google Cloud Console](https://console.cloud.google.com/).  
2. Create a new project and enable the **Google Calendar API**.  
3. Create **OAuth 2.0 Client Credentials**:
   - Application type: **Desktop App**
   - Download the credentials JSON file.

### 2️⃣ Add Credentials to ERPNext Site
Place your credentials file inside your site directory, e.g.:
/sites/mysite.local/google_credentials.json


### 3️⃣ Authentication Flow
When you create your first event, the app will:
- Prompt Google OAuth login  
- Save the token as `token.json` in your site folder  
- Automatically reuse and refresh the token on subsequent requests  

### 4️⃣ Install the App
```bash
cd $PATH_TO_YOUR_BENCH
bench get-app https://github.com/yourusername/google-calender-erpnext.git
bench install-app calendererpnext




Example Usage

Once installed, create a Google Event document in ERPNext:

Enter Event Name, Start Time, and End Time

Add participant names and emails under Event Participants

Click Create Google Event

The system will:

Create the event in Google Calendar

Generate a Google Meet link

Save it in your document

Allow you to join directly with the Join Meet button