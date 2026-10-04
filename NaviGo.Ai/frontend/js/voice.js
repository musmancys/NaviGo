/**
 * NaviGo Voice Assistant Controller (Web Speech API + MediaRecorder)
 * Parses spoken Urdu, Roman Urdu, and English travel requests into structured parameters.
 */

let mediaRecorder = null;
let audioChunks = [];
let isRecording = false;
let activeVoiceTarget = 'plan'; // 'plan' or 'chat'

function isSecureContextSafe() {
  return window.isSecureContext || window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1';
}

function toggleVoicePlanInput() {
  activeVoiceTarget = 'plan';
  toggleVoiceRecording(document.getElementById('planMicBtn'));
}
window.toggleVoicePlanInput = toggleVoicePlanInput;

function toggleVoiceChat() {
  activeVoiceTarget = 'chat';
  toggleVoiceRecording(document.getElementById('chatMicBtn'));
}
window.toggleVoiceChat = toggleVoiceChat;

async function toggleVoiceRecording(btnEl) {
  if (!isSecureContextSafe()) {
    alert("Microphone access requires HTTPS or localhost. Please ensure you are running on a secure domain.");
    return;
  }

  if (isRecording) {
    stopRecording(btnEl);
  } else {
    startRecording(btnEl);
  }
}

async function startRecording(btnEl) {
  audioChunks = [];

  // Check if MediaRecorder is available
  if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      mediaRecorder = new MediaRecorder(stream);

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) audioChunks.push(event.data);
      };

      mediaRecorder.onstop = async () => {
        const audioBlob = new Blob(audioChunks, { type: 'audio/webm' });
        await sendAudioToVoiceAPI(audioBlob);
        stream.getTracks().forEach(track => track.stop());
      };

      mediaRecorder.start();
      isRecording = true;
      if (btnEl) btnEl.classList.add('recording');
      updateVoiceStatus("🎤 Listening... Speak now (e.g. 'Mujhe Lahore se Hunza jana hai' or 'Karachi se Swat trip')");
      return;
    } catch (err) {
      console.warn("MediaRecorder permission denied or unavailable, trying Web Speech API:", err);
    }
  }

  // Fallback: Web Speech API
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (SpeechRecognition) {
    const recognition = new SpeechRecognition();
    recognition.lang = 'ur-PK, en-US';
    recognition.interimResults = false;

    recognition.onstart = () => {
      isRecording = true;
      if (btnEl) btnEl.classList.add('recording');
      updateVoiceStatus("🎤 Listening via Web Speech...");
    };

    recognition.onresult = async (event) => {
      const transcript = event.results[0][0].transcript;
      await sendTranscriptToVoiceAPI(transcript);
    };

    recognition.onerror = (event) => {
      console.error("Speech recognition error:", event.error);
      stopRecording(btnEl);
      toast("Voice recognition failed");
    };

    recognition.onend = () => {
      stopRecording(btnEl);
    };

    recognition.start();
  } else {
    // Demo Mode Simulation Prompt
    const demoPrompt = prompt("Voice demo: Enter your spoken request in Urdu or English:", "Mujhe Karachi se 4 din ke liye Swat jana hai, budget 60 hazar hai");
    if (demoPrompt) {
      sendTranscriptToVoiceAPI(demoPrompt);
    }
  }
}

function stopRecording(btnEl) {
  isRecording = false;
  if (btnEl) btnEl.classList.remove('recording');
  if (mediaRecorder && mediaRecorder.state !== 'inactive') {
    mediaRecorder.stop();
  }
  updateVoiceStatus("");
}

function updateVoiceStatus(msg) {
  const el = document.getElementById('voiceStatusMsg');
  if (el) {
    if (msg) {
      el.textContent = msg;
      el.style.display = 'block';
    } else {
      el.style.display = 'none';
    }
  }
}

async function sendAudioToVoiceAPI(audioBlob) {
  toast("Processing your voice with AI...");
  const formData = new FormData();
  formData.append('file', audioBlob, 'voice_input.webm');

  try {
    const res = await api.upload('/voice/parse', formData);
    applyExtractedParameters(res);
  } catch (err) {
    console.error("Voice parse failed:", err);
    toast("Could not process audio. Try typing.");
  }
}

async function sendTranscriptToVoiceAPI(transcriptText) {
  toast("Extracting trip preferences...");
  const formData = new FormData();
  formData.append('transcript', transcriptText);

  try {
    const res = await api.upload('/voice/parse', formData);
    applyExtractedParameters(res);
  } catch (err) {
    console.error("Transcript parse failed:", err);
    toast("Could not understand voice command.");
  }
}

function applyExtractedParameters(res) {
  const p = res.params || {};

  if (activeVoiceTarget === 'plan') {
    if (p.origin && document.getElementById('planOrigin')) {
      document.getElementById('planOrigin').value = p.origin;
    }
    if (p.destination && document.getElementById('planDest')) {
      document.getElementById('planDest').value = p.destination;
    }
    if (p.duration_days && document.getElementById('planDuration')) {
      document.getElementById('planDuration').value = p.duration_days.toString();
    }
    if (p.travelers && document.getElementById('planTravelers')) {
      document.getElementById('planTravelers').value = p.travelers.toString();
    }
    if (p.budget_pkr && document.getElementById('planBudget')) {
      document.getElementById('planBudget').value = p.budget_pkr;
    }

    toast(`Understood: ${p.duration_days} days to ${(p.destination || '').toUpperCase()}, Budget Rs. ${(p.budget_pkr || 0).toLocaleString()}`);
  } else if (activeVoiceTarget === 'chat') {
    const chatInput = document.getElementById('chatInput');
    if (chatInput) {
      chatInput.value = res.transcript;
      if (window.sendMessage) window.sendMessage();
    }
  }
}
