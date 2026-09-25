/**
 * Live HTML5 Canvas Audio Visualizer
 * Renders smooth oscilloscope waveforms and frequency spectrum bars.
 */

class AudioVisualizer {
  constructor(canvasId) {
    this.canvas = document.getElementById(canvasId);
    this.ctx = this.canvas ? this.canvas.getContext('2d') : null;
    this.audioCtx = null;
    this.analyser = null;
    this.source = null;
    this.dataArray = null;
    this.animationId = null;
    this.isActive = false;
    this.idlePhase = 0;

    this.resize();
    window.addEventListener('resize', () => this.resize());
    this.drawIdle();
  }

  resize() {
    if (!this.canvas) return;
    const rect = this.canvas.getBoundingClientRect();
    this.canvas.width = rect.width * (window.devicePixelRatio || 1);
    this.canvas.height = rect.height * (window.devicePixelRatio || 1);
    if (this.ctx) {
      this.ctx.scale(window.devicePixelRatio || 1, window.devicePixelRatio || 1);
    }
  }

  initAudioContext() {
    if (!this.audioCtx) {
      const AudioContextClass = window.AudioContext || window.webkitAudioContext;
      this.audioCtx = new AudioContextClass();
    }
    if (this.audioCtx.state === 'suspended') {
      this.audioCtx.resume();
    }
    if (!this.analyser) {
      this.analyser = this.audioCtx.createAnalyser();
      this.analyser.fftSize = 256;
      const bufferLength = this.analyser.frequencyBinCount;
      this.dataArray = new Uint8Array(bufferLength);
    }
  }

  connectMediaStream(stream) {
    this.initAudioContext();
    if (this.source) {
      try { this.source.disconnect(); } catch (e) {}
    }
    this.source = this.audioCtx.createMediaStreamSource(stream);
    this.source.connect(this.analyser);
    this.start();
  }

  connectAudioElement(audioEl) {
    this.initAudioContext();
    if (this.source) {
      try { this.source.disconnect(); } catch (e) {}
    }
    try {
      this.source = this.audioCtx.createMediaElementSource(audioEl);
      this.source.connect(this.analyser);
      this.analyser.connect(this.audioCtx.destination);
      this.start();
    } catch (e) {
      // Element may already be connected
      this.start();
    }
  }

  start() {
    this.isActive = true;
    if (this.animationId) cancelAnimationFrame(this.animationId);
    this.render();
  }

  stop() {
    this.isActive = false;
    if (this.animationId) cancelAnimationFrame(this.animationId);
    this.drawIdle();
  }

  render() {
    if (!this.isActive) return;
    this.animationId = requestAnimationFrame(() => this.render());

    if (!this.ctx || !this.analyser) return;

    this.analyser.getByteFrequencyData(this.dataArray);

    const width = this.canvas.getBoundingClientRect().width;
    const height = this.canvas.getBoundingClientRect().height;

    this.ctx.clearRect(0, 0, width, height);

    const bufferLength = this.analyser.frequencyBinCount;
    const barWidth = (width / bufferLength) * 2.2;
    let x = 0;

    for (let i = 0; i < bufferLength; i++) {
      const barHeight = (this.dataArray[i] / 255.0) * (height - 6);

      // Gradient color based on intensity
      const gradient = this.ctx.createLinearGradient(0, height, 0, height - barHeight);
      gradient.addColorStop(0, '#6366F1');
      gradient.addColorStop(1, '#06B6D4');

      this.ctx.fillStyle = gradient;
      this.ctx.beginPath();
      if (this.ctx.roundRect) {
        this.ctx.roundRect(x, height - barHeight, Math.max(barWidth - 2, 2), barHeight, [3, 3, 0, 0]);
      } else {
        this.ctx.rect(x, height - barHeight, Math.max(barWidth - 2, 2), barHeight);
      }
      this.ctx.fill();

      x += barWidth;
      if (x > width) break;
    }
  }

  drawIdle() {
    if (!this.ctx || !this.canvas) return;

    const width = this.canvas.getBoundingClientRect().width;
    const height = this.canvas.getBoundingClientRect().height;

    this.ctx.clearRect(0, 0, width, height);

    this.ctx.beginPath();
    this.ctx.moveTo(0, height / 2);

    for (let x = 0; x < width; x++) {
      const y = (height / 2) + Math.sin((x * 0.03) + this.idlePhase) * 4;
      this.ctx.lineTo(x, y);
    }

    this.ctx.strokeStyle = 'rgba(99, 102, 241, 0.25)';
    this.ctx.lineWidth = 2;
    this.ctx.stroke();

    this.idlePhase += 0.04;
    if (!this.isActive) {
      this.animationId = requestAnimationFrame(() => this.drawIdle());
    }
  }
}

window.AudioVisualizer = AudioVisualizer;
