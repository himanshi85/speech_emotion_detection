/**
 * AURA | Voice Emotion & Behaviour AI
 * Main Client Application Controller
 */

document.addEventListener('DOMContentLoaded', () => {
  // UI Elements
  const modelSelect = document.getElementById('model-select');
  const tabMic = document.getElementById('tab-mic');
  const tabUpload = document.getElementById('tab-upload');
  const paneMic = document.getElementById('pane-mic');
  const paneUpload = document.getElementById('pane-upload');

  const micBtn = document.getElementById('mic-btn');
  const recordTimer = document.getElementById('record-timer');
  const recordHint = document.getElementById('record-hint');
  const dropzone = document.getElementById('dropzone');
  const fileInput = document.getElementById('file-input');
  const filePreview = document.getElementById('file-preview');
  const fileNameDisplay = document.getElementById('file-name');
  const sampleChipsContainer = document.getElementById('sample-chips');
  const analyzeBtn = document.getElementById('analyze-btn');

  // Results UI Elements
  const emptyState = document.getElementById('empty-state');
  const resultsContainer = document.getElementById('results-container');
  const emotionTitle = document.getElementById('emotion-title');
  const emotionPill = document.getElementById('emotion-pill');
  const emotionSubtitle = document.getElementById('emotion-subtitle');
  const gaugeFill = document.getElementById('gauge-fill');
  const gaugeVal = document.getElementById('gauge-val');
  const probBarsContainer = document.getElementById('prob-bars');

  // 4 Metric Tiles
  const metricSpeedVal = document.getElementById('metric-speed-val');
  const metricSpeedSub = document.getElementById('metric-speed-sub');
  const metricPauseVal = document.getElementById('metric-pause-val');
  const metricPauseSub = document.getElementById('metric-pause-sub');
  const metricEnergyVal = document.getElementById('metric-energy-val');
  const metricEnergySub = document.getElementById('metric-energy-sub');
  const metricPitchVal = document.getElementById('metric-pitch-val');
  const metricPitchSub = document.getElementById('metric-pitch-sub');

  // Behaviour Synthesis
  const behaviourHeroTitle = document.getElementById('behaviour-hero-title');
  const behaviourHeroDesc = document.getElementById('behaviour-hero-desc');
  const reportTextarea = document.getElementById('report-textarea');
  const copyReportBtn = document.getElementById('copy-report-btn');
  const downloadJsonBtn = document.getElementById('download-json-btn');

  // Audio & State
  let visualizer = null;
  try {
    visualizer = new AudioVisualizer('canvas-visualizer');
  } catch (e) {
    console.warn('Canvas visualizer disabled:', e);
  }

  let mediaRecorder = null;
  let audioChunks = [];
  let recordInterval = null;
  let recordSeconds = 0;
  let activeAudioBlob = null;
  let activeAudioFilename = 'sample.wav';
  let lastAnalysisResult = null;

  // Emotion Color Themes
  const EMOTION_THEMES = {
    neutral: { color: '#06B6D4', bg: 'rgba(6, 182, 212, 0.15)', glow: '0 0 25px rgba(6, 182, 212, 0.35)' },
    calm: { color: '#38BDF8', bg: 'rgba(56, 189, 248, 0.15)', glow: '0 0 25px rgba(56, 189, 248, 0.35)' },
    happy: { color: '#10B981', bg: 'rgba(16, 185, 129, 0.15)', glow: '0 0 25px rgba(16, 185, 129, 0.35)' },
    sad: { color: '#818CF8', bg: 'rgba(129, 140, 248, 0.15)', glow: '0 0 25px rgba(129, 140, 248, 0.35)' },
    angry: { color: '#EF4444', bg: 'rgba(239, 68, 68, 0.15)', glow: '0 0 25px rgba(239, 68, 68, 0.35)' },
    fear: { color: '#F59E0B', bg: 'rgba(245, 158, 11, 0.15)', glow: '0 0 25px rgba(245, 158, 11, 0.35)' },
    fearful: { color: '#F59E0B', bg: 'rgba(245, 158, 11, 0.15)', glow: '0 0 25px rgba(245, 158, 11, 0.35)' },
    disgust: { color: '#A855F7', bg: 'rgba(168, 85, 247, 0.15)', glow: '0 0 25px rgba(168, 85, 247, 0.35)' },
  };

  // 1. Fetch Models
  async function loadModels() {
    try {
      const res = await fetch('/api/models');
      const data = await res.json();
      modelSelect.innerHTML = '';
      data.models.forEach(m => {
        const opt = document.createElement('option');
        opt.value = m.id;
        opt.textContent = `${m.name} (${m.accuracy})`;
        if (m.recommended) opt.selected = true;
        modelSelect.appendChild(opt);
      });
    } catch (err) {
      console.error('Error fetching models:', err);
    }
  }

  // 2. Fetch Sample Clips
  async function loadSamples() {
    try {
      const res = await fetch('/api/samples');
      const data = await res.json();
      sampleChipsContainer.innerHTML = '';
      data.samples.forEach(s => {
        const chip = document.createElement('button');
        chip.className = 'sample-chip';
        chip.innerHTML = `
          <span>${s.name}</span>
          <span class="sample-badge">${s.expected}</span>
        `;
        chip.addEventListener('click', async () => {
          chip.style.opacity = '0.6';
          try {
            const audioRes = await fetch(s.url);
            const blob = await audioRes.blob();
            activeAudioBlob = blob;
            activeAudioFilename = `${s.id}.wav`;
            enableAnalysis(s.name);
          } catch (e) {
            console.error('Failed loading sample clip:', e);
          } finally {
            chip.style.opacity = '1';
          }
        });
        sampleChipsContainer.appendChild(chip);
      });
    } catch (err) {
      console.error('Error loading samples:', err);
    }
  }

  // 3. Tab Navigation
  tabMic.addEventListener('click', () => {
    tabMic.classList.add('active');
    tabUpload.classList.remove('active');
    paneMic.classList.add('active');
    paneUpload.classList.remove('active');
  });

  tabUpload.addEventListener('click', () => {
    tabUpload.classList.add('active');
    tabMic.classList.remove('active');
    paneUpload.classList.add('active');
    paneMic.classList.remove('active');
  });

  /**
   * Encodes an AudioBuffer into standard 16-bit Mono PCM RIFF/WAVE Blob.
   */
  function encodePcmWav(audioBuffer) {
    const channelData = audioBuffer.getChannelData(0);
    const sampleRate = audioBuffer.sampleRate;
    const numSamples = channelData.length;
    const buffer = new ArrayBuffer(44 + numSamples * 2);
    const view = new DataView(buffer);

    function writeString(offset, string) {
      for (let i = 0; i < string.length; i++) {
        view.setUint8(offset + i, string.charCodeAt(i));
      }
    }

    // RIFF identifier
    writeString(0, 'RIFF');
    // File length minus RIFF identifier and length (36 + data size)
    view.setUint32(4, 36 + numSamples * 2, true);
    // RIFF type
    writeString(8, 'WAVE');
    // Format chunk identifier
    writeString(12, 'fmt ');
    // Format chunk length (16 for PCM)
    view.setUint32(16, 16, true);
    // Audio format (1 = PCM)
    view.setUint16(20, 1, true);
    // Number of channels (1 = Mono)
    view.setUint16(22, 1, true);
    // Sample rate (16000)
    view.setUint32(24, sampleRate, true);
    // Byte rate (sampleRate * numChannels * bitsPerSample / 8)
    view.setUint32(28, sampleRate * 2, true);
    // Block align (numChannels * bitsPerSample / 8)
    view.setUint16(32, 2, true);
    // Bits per sample
    view.setUint16(34, 16, true);
    // Data chunk identifier
    writeString(36, 'data');
    // Data chunk length
    view.setUint32(40, numSamples * 2, true);

    // Write 16-bit signed PCM samples with clipping
    let offset = 44;
    for (let i = 0; i < numSamples; i++) {
      const s = Math.max(-1, Math.min(1, channelData[i]));
      view.setInt16(offset, s < 0 ? s * 0x8000 : s * 0x7FFF, true);
      offset += 2;
    }

    return new Blob([view], { type: 'audio/wav' });
  }

  /**
   * Decodes an arbitrary audio blob using Web Audio API and resamples to 16 kHz Mono PCM WAV.
   */
  async function convertBlobToPcmWav(blob, targetSampleRate = 16000) {
    const arrayBuffer = await blob.arrayBuffer();
    const AudioCtxClass = window.AudioContext || window.webkitAudioContext;
    if (!AudioCtxClass) {
      throw new Error('AudioContext not supported in this browser.');
    }
    const audioCtx = new AudioCtxClass();
    let audioBuffer;
    try {
      audioBuffer = await audioCtx.decodeAudioData(arrayBuffer);
    } finally {
      if (audioCtx.state !== 'closed') {
        audioCtx.close();
      }
    }

    const OfflineCtxClass = window.OfflineAudioContext || window.webkitOfflineAudioContext;
    if (!OfflineCtxClass) {
      return encodePcmWav(audioBuffer);
    }

    const targetLength = Math.max(1, Math.ceil(audioBuffer.duration * targetSampleRate));
    const offlineCtx = new OfflineCtxClass(1, targetLength, targetSampleRate);
    const source = offlineCtx.createBufferSource();
    source.buffer = audioBuffer;
    source.connect(offlineCtx.destination);
    source.start(0);

    const renderedBuffer = await offlineCtx.startRendering();
    return encodePcmWav(renderedBuffer);
  }

  // 4. Microphone Recording
  micBtn.addEventListener('click', async () => {
    if (mediaRecorder && mediaRecorder.state === 'recording') {
      stopRecording();
    } else {
      await startRecording();
    }
  });

  async function startRecording() {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      audioChunks = [];
      mediaRecorder = new MediaRecorder(stream);

      if (visualizer) visualizer.connectMediaStream(stream);

      mediaRecorder.ondataavailable = (e) => {
        if (e.data.size > 0) audioChunks.push(e.data);
      };

      mediaRecorder.onstop = async () => {
        stream.getTracks().forEach(track => track.stop());
        if (visualizer) visualizer.stop();

        recordHint.textContent = 'Encoding recording into 16 kHz PCM WAV...';
        const rawMime = mediaRecorder.mimeType || 'audio/webm';
        const rawBlob = new Blob(audioChunks, { type: rawMime });

        try {
          activeAudioBlob = await convertBlobToPcmWav(rawBlob, 16000);
          activeAudioFilename = 'microphone_recording.wav';
          recordHint.textContent = 'Audio recorded & encoded as 16 kHz PCM WAV! Ready to analyze.';
        } catch (convErr) {
          console.warn('Browser PCM conversion fallback:', convErr);
          activeAudioBlob = rawBlob;
          const ext = rawMime.includes('mp4') ? '.mp4' : (rawMime.includes('ogg') ? '.ogg' : '.webm');
          activeAudioFilename = `microphone_recording${ext}`;
          recordHint.textContent = 'Audio recorded. Ready to analyze.';
        }

        enableAnalysis('Microphone Recording');
      };

      mediaRecorder.start(100);
      micBtn.classList.add('recording');
      recordHint.textContent = 'Recording in progress... Click again to finish.';
      recordSeconds = 0;
      updateTimer();
      recordInterval = setInterval(() => {
        recordSeconds++;
        updateTimer();
      }, 1000);
    } catch (err) {
      console.error('Microphone access denied:', err);
      alert('Microphone access was denied or is not supported in this browser.');
    }
  }

  function stopRecording() {
    if (mediaRecorder && mediaRecorder.state === 'recording') {
      mediaRecorder.stop();
    }
    clearInterval(recordInterval);
    micBtn.classList.remove('recording');
  }

  function updateTimer() {
    const mins = String(Math.floor(recordSeconds / 60)).padStart(2, '0');
    const secs = String(recordSeconds % 60).padStart(2, '0');
    recordTimer.textContent = `${mins}:${secs}`;
  }

  // 5. File Upload & Dropzone
  dropzone.addEventListener('dragover', (e) => {
    e.preventDefault();
    dropzone.classList.add('dragover');
  });

  dropzone.addEventListener('dragleave', () => {
    dropzone.classList.remove('dragover');
  });

  dropzone.addEventListener('drop', (e) => {
    e.preventDefault();
    dropzone.classList.remove('dragover');
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleSelectedFile(e.dataTransfer.files[0]);
    }
  });

  fileInput.addEventListener('change', () => {
    if (fileInput.files && fileInput.files[0]) {
      handleSelectedFile(fileInput.files[0]);
    }
  });

  async function handleSelectedFile(file) {
    fileNameDisplay.textContent = file.name;
    filePreview.style.display = 'flex';
    enableAnalysis(file.name);

    if (!file.name.toLowerCase().endsWith('.wav')) {
      try {
        const convertedBlob = await convertBlobToPcmWav(file, 16000);
        activeAudioBlob = convertedBlob;
        activeAudioFilename = file.name.replace(/\.[^/.]+$/, "") + ".wav";
        fileNameDisplay.textContent = `${file.name} (encoded to 16 kHz WAV)`;
      } catch (convErr) {
        console.warn('Direct client conversion skipped, sending original format to server:', convErr);
        activeAudioBlob = file;
        activeAudioFilename = file.name;
      }
    } else {
      activeAudioBlob = file;
      activeAudioFilename = file.name;
    }
  }

  function enableAnalysis(sourceName) {
    analyzeBtn.disabled = false;
    analyzeBtn.innerHTML = `
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <polygon points="5 3 19 12 5 21 5 3"></polygon>
      </svg>
      Analyze "${sourceName.length > 20 ? sourceName.slice(0, 18) + '...' : sourceName}"
    `;
  }

  // 6. Run Analysis via API
  analyzeBtn.addEventListener('click', async () => {
    if (!activeAudioBlob) return;

    analyzeBtn.disabled = true;
    analyzeBtn.innerHTML = `<span class="spinner"></span> Analyzing Acoustic Signals...`;

    let uploadBlob = activeAudioBlob;
    let uploadFilename = activeAudioFilename;

    const formData = new FormData();
    formData.append('file', uploadBlob, uploadFilename);
    formData.append('model_id', modelSelect.value);

    try {
      const response = await fetch('/api/analyze', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Analysis failed on server.');
      }

      const result = await response.json();
      lastAnalysisResult = result;
      displayResults(result);
    } catch (err) {
      console.error('Analysis error:', err);
      alert(`Audio analysis failed: ${err.message}`);
    } finally {
      analyzeBtn.disabled = false;
      analyzeBtn.innerHTML = `
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <polygon points="5 3 19 12 5 21 5 3"></polygon>
        </svg>
        Re-Analyze Audio
      `;
    }
  });

  // 7. Render Analysis Results
  function displayResults(data) {
    emptyState.style.display = 'none';
    resultsContainer.style.display = 'flex';

    // A. Hero Emotion Verdict
    const emo = data.emotion.toLowerCase();
    const theme = EMOTION_THEMES[emo] || EMOTION_THEMES.neutral;

    emotionTitle.textContent = data.emotion.toUpperCase();
    emotionPill.textContent = `${data.confidence}% CONFIDENCE`;
    emotionPill.style.background = theme.bg;
    emotionPill.style.color = theme.color;
    emotionPill.style.boxShadow = theme.glow;
    emotionSubtitle.textContent = `Predicted on ${data.duration}s recording via ${modelSelect.options[modelSelect.selectedIndex].text}`;

    // B. Circular Confidence Gauge
    const circumference = 314;
    const offset = circumference - (data.confidence / 100.0) * circumference;
    gaugeFill.style.strokeDashoffset = offset;
    gaugeVal.textContent = `${data.confidence}%`;

    // C. Probability Bars
    probBarsContainer.innerHTML = '';
    const sortedProbs = Object.entries(data.probabilities).sort((a, b) => b[1] - a[1]);

    sortedProbs.forEach(([emotionName, probVal]) => {
      const row = document.createElement('div');
      row.className = 'prob-row';
      const emoTheme = EMOTION_THEMES[emotionName.toLowerCase()] || EMOTION_THEMES.neutral;

      row.innerHTML = `
        <span class="prob-name">${emotionName}</span>
        <div class="bar-track">
          <div class="bar-fill" style="width: 0%; background: ${emoTheme.color};"></div>
        </div>
        <span class="prob-pct">${probVal}%</span>
      `;
      probBarsContainer.appendChild(row);

      // Animate width
      setTimeout(() => {
        const fill = row.querySelector('.bar-fill');
        if (fill) fill.style.width = `${probVal}%`;
      }, 50);
    });

    // D. 4 Acoustic Behaviour Metrics
    metricSpeedVal.textContent = data.speaking_speed.category;
    metricSpeedSub.textContent = `${data.speaking_speed.syllables_per_second} syll/sec • ${data.speaking_speed.words_per_minute} WPM`;

    metricPauseVal.textContent = data.pause_frequency.category;
    metricPauseSub.textContent = `${data.pause_frequency.silence_ratio}% silence • ${data.pause_frequency.pauses_per_minute} pauses/min`;

    metricEnergyVal.textContent = data.vocal_energy.category;
    metricEnergySub.textContent = `${data.vocal_energy.rms_db} dB RMS loudness`;

    metricPitchVal.textContent = data.pitch_variation.category;
    metricPitchSub.textContent = `mean: ${data.pitch_variation.mean_hz} Hz • std: ${data.pitch_variation.std_hz} Hz`;

    // E. Behaviour Diagnosis Synthesis
    behaviourHeroTitle.textContent = data.overall_behaviour;
    behaviourHeroDesc.textContent = synthesizeDiagnosticInsight(data);

    // F. Raw Report Card & Export
    reportTextarea.value = data.report_text;

    // Scroll to results on mobile
    if (window.innerWidth < 1024) {
      resultsContainer.scrollIntoView({ behavior: 'smooth' });
    }
  }

  function synthesizeDiagnosticInsight(data) {
    const emo = data.emotion.toLowerCase();
    const speed = data.speaking_speed.category;
    const energy = data.vocal_energy.category;
    const pitch = data.pitch_variation.category;

    if (data.overall_behaviour.includes('Engaged')) {
      return `Speaker demonstrates balanced speech tempo (${data.speaking_speed.syllables_per_second} syll/sec) with controlled vocal loudness and stable pitch inflection, reflecting attentive conversational engagement.`;
    } else if (data.overall_behaviour.includes('Enthusiastic') || data.overall_behaviour.includes('Assertive')) {
      return `Elevated vocal energy (${data.vocal_energy.rms_db} dB) accompanied by dynamic pitch excursion indicates high emotional activation, urgency, or strong conversational emphasis.`;
    } else if (data.overall_behaviour.includes('Hesitant') || data.overall_behaviour.includes('Cautious')) {
      return `Prolonged pause duration (${data.pause_frequency.silence_ratio}% silence) with suppressed vocal tempo indicates guarded deliberation, nervousness, or cognitive hesitation.`;
    } else {
      return `Acoustic patterns reflect steady articulation with ${energy.toLowerCase()} loudness dynamics and ${pitch.toLowerCase()} pitch modulation characteristic of ${emo} vocal expression.`;
    }
  }

  // 8. Copy Report & Download JSON
  copyReportBtn.addEventListener('click', () => {
    if (!reportTextarea.value) return;
    navigator.clipboard.writeText(reportTextarea.value).then(() => {
      const orig = copyReportBtn.innerHTML;
      copyReportBtn.textContent = 'Copied to Clipboard!';
      setTimeout(() => { copyReportBtn.innerHTML = orig; }, 2000);
    });
  });

  downloadJsonBtn.addEventListener('click', () => {
    if (!lastAnalysisResult) return;
    const dataStr = 'data:text/json;charset=utf-8,' + encodeURIComponent(JSON.stringify(lastAnalysisResult, null, 2));
    const downloadAnchor = document.createElement('a');
    downloadAnchor.setAttribute('href', dataStr);
    downloadAnchor.setAttribute('download', `aura_analysis_${Date.now()}.json`);
    document.body.appendChild(downloadAnchor);
    downloadAnchor.click();
    downloadAnchor.remove();
  });

  // Initialize
  loadModels();
  loadSamples();
});
