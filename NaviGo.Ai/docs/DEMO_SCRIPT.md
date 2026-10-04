# NaviGo — Hackathon Presentation & Live Demo Script

**Theme:** Multimodal AI Tourism Platform for Northern Pakistan  
**Duration:** 3–5 minutes  
**Goal:** Demonstrate voice, multimodal vision, real-time road reporting, safety replanning, and grounded local marketplace without any hardware dependencies.

---

## Act 1: The Problem & The Voice Request (0:00 – 1:00)

1. **Opening Statement**:
   > *"Planning a trip to Northern Pakistan is broken. Tourists jump between scattered Facebook groups, outdated blogs, and WhatsApp rumors just to figure out if roads are open, weather is safe, or what a trip really costs."*

2. **Action — Voice Input**:
   - Navigate to the **Plan Trip** page.
   - Click the **Microphone button** 🎤 on the preferences card.
   - Speak in Urdu or English:
     > *"Mujhe Lahore se 3 din ke liye Naran jana hai, budget 40 hazar hai"*
   - **Show the Audience**: NaviGo's AI automatically parses the speech:
     - **Origin**: Lahore
     - **Destination**: Naran
     - **Duration**: 3 Days
     - **Budget**: Rs. 40,000 (normalizing *"40 hazar"* into `40000`).

---

## Act 2: AI Itinerary Generation & Deterministic Budget (1:00 – 2:00)

1. **Action — Generate My Trip**:
   - Click **✨ Generate My Trip**.
   - Watch the **4-step SSE live animation**:
     1. *Understanding your preferences*
     2. *Selecting destinations in Naran*
     3. *Checking live weather and road hazards*
     4. *Preparing your plan & calculating budget*
2. **Key Talking Point**:
   > *"Notice how the LLM doesn't invent places or do mental arithmetic. Stops reference real verified coordinates in Naran (Saif-ul-Malook, Lulusar, Babusar Top). Our deterministic budget engine calculates exact fuel, hotel, and food costs against real market prices."*
3. **Show Budget Card**:
   - Highlight: **Total: Rs. 29,500** with the green **🟢 Within Budget** badge.
   - Click **📄 Download PDF Itinerary** to show the downloadable trip voucher generated via ReportLab.

---

## Act 3: Multimodal Road Photo Reporter (Hero Feature) (2:00 – 3:15)

1. **Action — Navigate to Road Reports**:
   - Click **Road Reports** in the navbar.
2. **Action — Upload Road Photo**:
   - Click the upload dropzone and select a road photo (e.g. mud, standing water, or landslide).
   - Click **Analyze Photo**.
3. **Show Vision AI Results**:
   - AI detects: `Mud`, `Standing Water`, `Severity: Caution`, `Confidence: 88%`.
   - **Crucial Honesty Badge**:
     > *"Notice our honesty disclaimer: 'Possible issue detected — AI suggestion, please confirm. Road status is community-reported and advisory.' NaviGo never claims a road is guaranteed safe."*
4. **Action — Submit Report**:
   - Confirm location: *"Naran – Kaghan Road"* and click **📢 Submit Official Community Report**.
   - Watch the report appear instantly in the **Community Road Reports** feed with live timestamp ("Just now").
   - Click **👍 Still There** to show community verification voting in action.

---

## Act 4: Interactive Tourism Map & "What's Around Me?" (3:15 – 4:00)

1. **Action — Explore Page**:
   - Click **Explore** in the navbar.
   - Show the interactive **Leaflet map** with custom category pins.
   - Filter by **Hotels**, **Attractions**, **Fuel**, and **Emergency**.
2. **Action — What's Around Me?**:
   - Click the **📍 What's Around Me?** button.
   - The map centers on the tourist's current location, drops a pulsing marker, calculates distances in kilometers, and displays emergency hotlines (*Rescue 1122, Police 15, KPK Tourism Police 1422*).

---

## Act 5: Grounded Tourism Chatbot & Verified Marketplace (4:00 – 5:00)

1. **Action — AI Assistant**:
   - Navigate to **AI Assistant**.
   - Click the quick chip: **🌤️ Weather**.
   - NaviGo queries Open-Meteo in real time and renders live temperature, wind speed, and rich summary cards.
   - Ask in Roman Urdu: *"Kalam mein ghumne ke liye kya hai?"*
   - NaviGo replies in Roman Urdu citing verified spots from the database.
2. **Action — Verified Partners**:
   - Open the **Destination** page for Naran.
   - Show the **Verified Hotels & Guides** section:
     - *Pine Park Hotel* & *Tariq Mehmood (Certified Alpine Guide)*.
     - Highlight: **✓ Verified Business · Last verified: September 2026**.
     - AI Review Summary highlighting top pros and cons.

---

## Summary & Closing:
> *"NaviGo combines multimodal AI, deterministic travel budgets, live weather rules, and community road safety to empower travelers across Pakistan while supporting verified local businesses."*
