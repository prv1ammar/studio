# 🗓️ Google Calendar Node — Configuration Guide for Clinic Booking

> **Tyboo Studio v3.0.0**
> Last updated: 2026-02-25

---

## Table of Contents

1. [Prerequisites](#1-prerequisites)
2. [Step 1 — Create a Google Cloud Project](#2-step-1--create-a-google-cloud-project)
3. [Step 2 — Get Your OAuth Tokens](#3-step-2--get-your-oauth-tokens)
4. [Step 3 — Save the Credential in Tyboo Studio](#4-step-3--save-the-credential-in-tyboo-studio)
5. [Step 4 — Configure the Google Calendar Nodes](#5-step-4--configure-the-google-calendar-nodes)
   - [Node 1: Check Availability (List Events)](#node-1-check-availability-list-events)
   - [Node 2: Book Appointment (Create Event)](#node-2-book-appointment-create-event)
   - [Node 3: Confirm / Manage Booking (Get / Update Event)](#node-3-confirm--manage-booking-get--update-event)
6. [How to Connect the Nodes](#6-how-to-connect-the-nodes)
7. [Troubleshooting](#7-troubleshooting)

---

## 1. Prerequisites

| Requirement | Details |
|---|---|
| Google Account | A Google Workspace or personal Gmail account |
| Google Cloud Console | Access to [console.cloud.google.com](https://console.cloud.google.com) |
| Tyboo Studio | Running locally with backend + frontend active |
| Credential Manager | Accessible via the 🔑 icon in Tyboo Studio header |

---

## 2. Step 1 — Create a Google Cloud Project

1. Go to **[Google Cloud Console](https://console.cloud.google.com)**.
2. Click **"Select a Project"** → **"New Project"**.
3. Name it: `Clinic Booking System` → Click **Create**.
4. Once created, select the project.

### Enable the Google Calendar API

5. Go to **APIs & Services** → **Library**.
6. Search for **"Google Calendar API"**.
7. Click on it → Click **"ENABLE"**.

### Create OAuth 2.0 Credentials

8. Go to **APIs & Services** → **Credentials**.
9. Click **"+ CREATE CREDENTIALS"** → **"OAuth Client ID"**.
10. If prompted, configure the **OAuth Consent Screen** first:
    - User Type: **External** (or Internal if Google Workspace)
    - App Name: `Clinic Booking`
    - User Support Email: your email
    - Save and continue through all steps
11. Back in Credentials, click **"+ CREATE CREDENTIALS"** → **"OAuth Client ID"**:
    - Application Type: **Web application**
    - Name: `Clinic Booking OAuth`
    - Authorized Redirect URIs: add `https://developers.google.com/oauthplayground`
12. Click **Create**.
13. **Copy and save** the:
    - ✅ **Client ID** (e.g., `387512345-abc.apps.googleusercontent.com`)
    - ✅ **Client Secret** (e.g., `GOCSPX-xxxxxxxxxxxxxx`)

---

## 3. Step 2 — Get Your OAuth Tokens

### Using Google OAuth Playground

1. Go to **[OAuth Playground](https://developers.google.com/oauthplayground/)**.
2. Click the ⚙️ **gear icon** (top right) → Check **"Use your own OAuth credentials"**.
3. Enter your **Client ID** and **Client Secret** from Step 1.
4. In the left panel, expand **"Google Calendar API v3"**.
5. Select the scope: `https://www.googleapis.com/auth/calendar`
6. Click **"Authorize APIs"** → Sign in with your Google account → Allow.
7. Click **"Exchange authorization code for tokens"**.
8. **Copy and save** the:
    - ✅ **Access Token** (starts with `ya29.`)
    - ✅ **Refresh Token** (starts with `1//`)

> ⚠️ **Important**: Access tokens expire after ~1 hour. For production, use the
> Refresh Token to auto-renew. For testing, you can re-generate from the Playground.

---

## 4. Step 3 — Save the Credential in Tyboo Studio

1. Open Tyboo Studio in your browser.
2. Click the **🔑 Key icon** in the header bar to open the **Secure Credential Manager**.
3. Click **"+ Add New Credential"**.
4. Fill in:

| Field | Value |
|---|---|
| **Unique ID** | `clinic_google_calendar` |
| **Display Name** | `Clinic Google Calendar` |
| **Service Type** | `Google OAuth` |
| **Client ID** | `387512345-abc.apps.googleusercontent.com` (your value) |
| **Client Secret** | `GOCSPX-xxxxxxxxxxxxxx` (your value) |
| **Access Token** | `ya29.a0AfH6SM...` (your value) |
| **Refresh Token** | `1//0eXyz...` (your value, optional) |

5. Click **"Save Encrypted"** ✅

> Your credential is now securely stored with AES-256 encryption and ready to use.

---

## 5. Step 4 — Configure the Google Calendar Nodes

Drag **3 Google Calendar nodes** from the sidebar onto the canvas. Configure each one differently:

---

### Node 1: Check Availability (List Events)

**Purpose**: The AI agent calls this tool to see if a time slot is free before booking.

| Field | Value | Notes |
|---|---|---|
| **Google Calendar Auth** | Select: `Clinic Google Calendar` | The credential you just created |
| **Action** | `list_events` | Lists upcoming events |
| **Calendar ID** | `primary` | Or your specific calendar email (e.g., `clinic@gmail.com`) |
| **Summary** | *(leave empty)* | Not needed for listing |
| **Description** | *(leave empty)* | Not needed for listing |
| **Start Time** | *(leave empty)* | Not needed — defaults to upcoming events |
| **End Time** | *(leave empty)* | Not needed |
| **Event ID** | *(leave empty)* | Not needed |
| **Attendees** | *(leave empty)* | Not needed |

**What it returns**: A list of the next 10 upcoming events with their times, so the agent can check if the requested slot is available.

---

### Node 2: Book Appointment (Create Event)

**Purpose**: The AI agent creates a new calendar event when the patient confirms a slot.

| Field | Value | Notes |
|---|---|---|
| **Google Calendar Auth** | Select: `Clinic Google Calendar` | Same credential |
| **Action** | `create_event` | Creates a new event |
| **Calendar ID** | `primary` | Or your specific calendar email |
| **Summary** | *(The agent fills this dynamically)* | e.g., `Dental Checkup - Ahmed` |
| **Description** | *(The agent fills this dynamically)* | e.g., `Patient: Ahmed, Phone: +213...` |
| **Start Time** | *(The agent fills this dynamically)* | ISO 8601 format: `2026-03-01T10:00:00Z` |
| **End Time** | *(The agent fills this dynamically)* | ISO 8601 format: `2026-03-01T11:00:00Z` |
| **Event ID** | *(leave empty)* | Auto-generated by Google |
| **Attendees** | *(The agent fills this dynamically)* | e.g., `patient@email.com, doctor@clinic.com` |

> 💡 **Note**: When this node is connected as a **Tool** to the Agent, the agent
> dynamically fills in Summary, Description, Start/End Time, and Attendees based
> on the patient conversation. You can leave these fields empty in the node config.

**What it returns**: The created event object including the Google Meet link (if enabled) and the event ID.

---

### Node 3: Confirm / Manage Booking (Get / Update Event)

**Purpose**: The AI agent retrieves event details for confirmation, or updates/cancels an existing booking.

#### For Getting Event Details:

| Field | Value | Notes |
|---|---|---|
| **Google Calendar Auth** | Select: `Clinic Google Calendar` | Same credential |
| **Action** | `get_event` | Retrieves a specific event |
| **Calendar ID** | `primary` | Same calendar |
| **Event ID** | *(The agent fills this dynamically)* | From the create_event result |
| *(all other fields)* | *(leave empty)* | Not needed for get |

#### For Updating/Cancelling:

| Field | Value | Notes |
|---|---|---|
| **Action** | `update_event` or `delete_event` | Change or cancel the appointment |
| **Event ID** | *(Required — from previous result)* | The event to modify |
| **Summary** | *(New title if updating)* | e.g., `CANCELLED: Dental Checkup` |

---

## 6. How to Connect the Nodes

### Visual Layout

```
                    ┌──────────────────┐
                    │   Tyboo LiteLLM  │
                    │  (LLM Provider)  │
                    └───────┬──────────┘
                            │ LLM
                            ▼
┌────────────┐     ┌────────────────────┐     ┌─────────────┐
│ Chat Input │────▶│  Configurable      │────▶│ Chat Output │
│            │     │  Agent (LangChain) │     │             │
└────────────┘     └──┬─────────────┬───┘     └─────────────┘
                      │ Tools       │ Tools
                      ▼             ▼
          ┌───────────────┐  ┌──────────────┐
          │ Google Cal #1 │  │ Google Cal #2│
          │ (list_events) │  │(create_event)│
          └───────────────┘  └──────────────┘
```

### Connection Steps

1. **Chat Input** → drag from its output to the **Agent**'s `User Question` input handle
2. **Tyboo LiteLLM** → drag from its `response` output to the **Agent**'s `LLM` input handle
3. **Google Calendar #1** (list_events) → drag from its `Tool` output to the **Agent**'s `Tools` input handle
4. **Google Calendar #2** (create_event) → drag from its `Tool` output to the **Agent**'s `Tools` input handle
5. **Agent** → drag from its output to **Chat Output**'s input handle

> 💡 **Tip**: You can connect multiple tools to the same Agent `Tools` port.
> The agent decides which tool to call based on the conversation context.

---

## 7. Troubleshooting

### ❌ "Google Access Token required"
- Your credential doesn't have an `access_token` field.
- Go to the Credential Manager → delete and re-create the credential.
- Make sure you select **"Google OAuth"** as the Service Type.
- Paste the Access Token from the OAuth Playground.

### ❌ "401 Unauthorized" from Google
- Your Access Token has expired (they last ~1 hour).
- Go back to the [OAuth Playground](https://developers.google.com/oauthplayground/).
- Re-generate a new Access Token.
- Update the credential in the Credential Manager.

### ❌ "403 Forbidden / Insufficient Permission"
- You didn't select the correct scope in OAuth Playground.
- Make sure you selected: `https://www.googleapis.com/auth/calendar` (full access).
- Not the read-only scope.

### ❌ "Calendar ID not found"
- Use `primary` for your default calendar.
- Or find your calendar ID: Google Calendar → Settings → click on your calendar → "Integrate calendar" → Calendar ID.

### ❌ Node not showing in sidebar
- Refresh the browser page (Ctrl+F5).
- Check that the backend is running.

### ❌ Credential not appearing in dropdown
- Make sure you are logged in to Tyboo Studio.
- Refresh the page after creating a credential.
- Check browser console for errors.

---

## Quick Reference — Field Summary

| Field | list_events | create_event | get_event | update_event | delete_event |
|---|:---:|:---:|:---:|:---:|:---:|
| Google Calendar Auth | ✅ Required | ✅ Required | ✅ Required | ✅ Required | ✅ Required |
| Calendar ID | ✅ `primary` | ✅ `primary` | ✅ `primary` | ✅ `primary` | ✅ `primary` |
| Summary | — | ✅ Event title | — | ✅ New title | — |
| Description | — | ✅ Details | — | ✅ New details | — |
| Start Time | — | ✅ ISO 8601 | — | ✅ New time | — |
| End Time | — | ✅ ISO 8601 | — | ✅ New time | — |
| Event ID | — | — | ✅ Required | ✅ Required | ✅ Required |
| Attendees | — | ✅ Emails | — | ✅ New emails | — |

---

*Guide created for Tyboo Studio v3.0.0 — Clinic Booking System*
