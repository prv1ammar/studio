# 🧱 Building an Intelligent Booking Workflow (LEGO Style)

Think of Tyboo Studio like a box of digital LEGOs. To build a smart booking assistant, we need to gather our pieces (nodes), snap them together (connections), and tell them how to talk to each other (chat input/output).

Here is your exact blueprint for integrating Google Calendar, Airtable, and memory into a conversational agent.

---

## 📦 The Pieces You Need (Total: 10 Nodes)

You will need to drag **10 specific blocks** from the left sidebar onto your canvas:

1.  **[1x] Chat Input Node**: The starting point. This is where the user types their message.
2.  **[1x] Base AI Agent Node**: The brain. This block does the thinking, coordinates the tools, and decides what to reply.
3.  **[1x] Lightweight LLM Node** (e.g., `Groq Llama 3` or `OpenAI GPT-4o-mini`): The engine that gives the brain its language processing power.
4.  **[1x] Redis Buffer Memory Node**: The agent's short-term memory so it remembers what was previously said.
5.  **[3x] Google Calendar Tool Nodes**: The hands that manage the calendar. You need three separate identical blocks that we will configure for specific tasks (Get, Create, Update).
6.  **[3x] Airtable Tool Nodes**: The clipboards that log the user's booking details into your CRM. You need three separate identical blocks (Get, Create, Update).

---

## 🧩 How to Snap Them Together (Connections)

Every block has **Ports** (little dots on the sides). You draw lines (wires) between these dots to snap the LEGOs together. Just like n8n, tools generally have a single output port to provide their capability.

Here is exactly how to wire your 10 blocks:

### 1. Connect the User to the Brain (Input to Agent)
*   Find the **Chat Input Node**.
*   Click and drag a wire from the Input Node's right-side **`Message`** port...
*   ...and snap it directly into the **Base AI Agent Node**'s left-side **`User Input`** port.

### 2. Give the Brain its Engine (LLM to Agent)
*   Find the **LLM Node** (e.g., Llama 3) you dragged in.
*   Click and drag a wire from the LLM Node's right-side **`Model`** port...
*   ...and snap it into the **Base AI Agent Node**'s left-side **`LLM`** port.

### 3. Give the Brain its Memory (Redis to Agent)
*   Find the **Redis Buffer Memory Node**.
*   Click and drag a wire from the Memory Node's right-side **`Memory`** port...
*   ...and snap it into the **Base AI Agent Node**'s left-side **`Memory`** port.

### 4. Give the Brain its Tools (6 Tools to Agent)
*   The Agent Node has a special array port on its left side called **`Tools[]`**. You can snap multiple wires into this single dot.
*   Find your **3 Google Calendar Tool Nodes**. Each has exactly one dot on its right side called **`Tool`**. 
*   Drag a wire from the right-side **`Tool`** port of *each* calendar node directly into the Agent's left-side **`Tools[]`** port.
*   Find your **3 Airtable Tool Nodes**. Drag a wire from their right-side **`Tool`** port into the exact same Agent's left-side **`Tools[]`** port.

*(Your Agent now has 6 wires converging into its single `Tools[]` port!)*

---

## ⚙️ How to Configure Each Block (The Settings)

When you click on any block on your canvas, a settings panel opens on the right side of your screen. Here is exactly what to configure:

### 1. Chat Input Node & Agent Node
*   **Settings needed:** Usually none! They work directly off their incoming connections. Ensure the Agent has the System Prompt set (see blueprint below).

### 2. Lightweight LLM Node
*   **Model Name:** Select `llama3-8b` or `gpt-4o-mini`.
*   **Temperature:** Set to `0.2` or `0.3` (keeps the brain logical and prevents hallucinating fake available times).

### 3. Redis Buffer Memory Node
*   **Session ID:** Type `user_booking_session` (this acts as the unique chat history folder).
*   **Window Size:** Set to `10` (remembers only the last 10 messages).

### 4. The 3 Google Calendar Tool Nodes
Click each of the 3 calendar blocks and configure their **Action** dropdowns distinctly:
1.  **Node 1 (The Searcher):** Set Action to `Get/Check Availability`. Name it *"Check Calendar Slots"*.
2.  **Node 2 (The Maker):** Set Action to `Create Event`. Name it *"Book New Calendar Invite"*.
3.  **Node 3 (The Updater):** Set Action to `Update Event`. Name it *"Reschedule/Cancel Invite"*.

### 5. The 3 Airtable Tool Nodes
Click each of the 3 Airtable blocks and configure them distinctly:
1.  **Node 1 (The Searcher):** Set Action to `Get Records`. Enter Base ID + Table Name. Name it *"Search CRM Database"*.
2.  **Node 2 (The Maker):** Set Action to `Create Record`. Enter Base ID + Table Name. Name it *"Create CRM Lead"*.
3.  **Node 3 (The Updater):** Set Action to `Update Record`. Enter Base ID + Table Name. Name it *"Update CRM Details"*.

*(By giving them distinct actions and names, the Agent knows exactly which of the 6 single-port tools to pull out of its pocket!)*

---

## 💬 Chat Input and Output Flow

How does the conversation actually start and end? Here is the looping flow of data:

### What happens in the **Chat Input**:
When you type *"I want to book an appointment next Friday afternoon"*:
The **Chat Input Node** captures your text string and pipes it instantly into the Agent.

### What the **Agent** does:
The Agent receives *"I want to book an appointment next Friday afternoon."* 
1. It requests the chat history from the **Redis Memory** port.
2. It talks to the **LLM** engine: *"The user wants Friday PM. What tool should I use?"*
3. It decides to use the **Google Calendar 'Get' Tool** secretly in the background to look at next Friday.
4. It sees an open slot at 3:00 PM.

### What happens in the **Chat Output**:
The Agent uses the LLM to generate a human-friendly response based on the availability tool. It sends this back to the Chat interface:
> *"I have a slot available next Friday at 3:00 PM. Does that work for you? If so, what is your name and email?"*

When the user replies *"Yes, I'm John (john@example.com)"*, the LEGO loop repeats:
1. Input sends the new message to Agent.
2. Agent reads **Redis Memory** ("Ah, we were talking about Friday at 3:00 PM").
3. Agent uses the **Google Calendar "Create" Tool** to make the invite.
4. Agent uses the **Airtable "Create" Tool** to log John as a new lead.
5. Agent replies in chat: *"All set, John! Your invite is sent and you're in the CRM."*

---

## 🧭 Final Detail: The Blueprint (System Prompt)

To make this logic click, click on the **Base AI Agent Node** and paste this into its `System Prompt`:

> *"You are a helpful and polite booking assistant. Your goal is to schedule meetings. You have access to distinct tools for reading, creating, and updating data.
> 
> Step 1: Always use the 'Check Calendar Slots' tool first to find open slots when a user requests a meeting.
> Step 2: Suggest a specific time slot to the user based on availability.
> Step 3: Once they agree to a time, ask for their Name and Email.
> Step 4: Use the 'Search CRM Database' tool to see if they are already in the system.
> Step 5: Use the 'Book New Calendar Invite' tool to lock in the meeting.
> Step 6: If they are a new user, use 'Create CRM Lead'. If they already exist, use 'Update CRM Details' instead.
> 
> Never guess availability. Always rely on the tools attached to you. Be polite and concise."*
