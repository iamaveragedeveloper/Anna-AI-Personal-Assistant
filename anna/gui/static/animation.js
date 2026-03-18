/**
 * Anna — Circle Animation Engine
 * 
 * States:
 *   idle      — Gentle breathing pulse (soft blue)
 *   active    — Strong pulse + glow (wake word detected)
 *   listening — Audio-reactive (user speaking)
 *   speaking  — Expressive emotional animation
 * 
 * Also draws a subtle ambient particle field on a secondary canvas.
 */

// ─── Particle System ─────────────────────────────────────────
class ParticleField {
    constructor(canvas) {
        this.canvas = canvas;
        this.ctx = canvas.getContext('2d');
        this.particles = [];
        this.resize();
        window.addEventListener('resize', () => this.resize());
        this.spawnInitial();
        this.loop();
    }

    resize() {
        this.canvas.width = window.innerWidth;
        this.canvas.height = window.innerHeight;
    }

    spawnInitial() {
        const count = Math.floor((window.innerWidth * window.innerHeight) / 18000);
        for (let i = 0; i < count; i++) {
            this.particles.push(this.newParticle(true));
        }
    }

    newParticle(random = false) {
        return {
            x: Math.random() * this.canvas.width,
            y: random ? Math.random() * this.canvas.height : this.canvas.height + 4,
            vx: (Math.random() - 0.5) * 0.15,
            vy: -(Math.random() * 0.3 + 0.1),
            r: Math.random() * 1.2 + 0.3,
            alpha: Math.random() * 0.5 + 0.1,
            life: 0,
            maxLife: Math.random() * 400 + 200
        };
    }

    loop() {
        const ctx = this.ctx;
        ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);

        for (let i = this.particles.length - 1; i >= 0; i--) {
            const p = this.particles[i];
            p.x += p.vx;
            p.y += p.vy;
            p.life++;

            const lifeRatio = p.life / p.maxLife;
            const fade = lifeRatio < 0.1 ? lifeRatio / 0.1
                       : lifeRatio > 0.8 ? (1 - lifeRatio) / 0.2
                       : 1;

            ctx.globalAlpha = p.alpha * fade;
            ctx.fillStyle = `hsl(210, 100%, 70%)`;
            ctx.beginPath();
            ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
            ctx.fill();

            if (p.life >= p.maxLife) {
                this.particles[i] = this.newParticle();
            }
        }
        ctx.globalAlpha = 1;
        requestAnimationFrame(() => this.loop());
    }
}


// ─── Anna Circle ─────────────────────────────────────────────
class AnnaCircle {
    constructor() {
        this.canvas     = document.getElementById('annaCircle');
        this.ctx        = this.canvas.getContext('2d');
        this.statusText = document.getElementById('statusText');
        this.transcriptBox = document.getElementById('transcriptBox');
        this.transcript = document.getElementById('transcript');
        this.connStatus = document.getElementById('connectionStatus');
        this.connLabel  = document.getElementById('connectionLabel');

        // Responsive sizing
        this.baseRadius = Math.min(window.innerWidth, window.innerHeight) * 0.1;
        this.baseRadius = Math.max(60, Math.min(this.baseRadius, 100));

        this.resize();
        window.addEventListener('resize', () => this.resize());

        // Circle physics
        this.currentRadius  = this.baseRadius;
        this.targetRadius   = this.baseRadius;
        this.opacity        = 0.55;
        this.targetOpacity  = 0.55;
        this.glowSize       = 0;
        this.targetGlowSize = 0;
        this.ripples        = [];     // [{r, alpha}]

        // State
        this.state         = 'idle';
        this.t             = 0;
        this.audioLevel    = 0;

        // Color palette (HSL)
        this.palette = {
            idle:      { h: 214, s: 85, l: 55 },
            active:    { h: 207, s: 100, l: 60 },
            listening: { h: 190, s: 100, l: 58 },
            speaking:  { h: 205, s: 100, l: 62 },
        };

        // WebSocket
        this.ws              = null;
        this.reconnectDelay  = 1500;
        this.connect();

        // Animation loop
        this.animate();
    }

    resize() {
        // Always full viewport
        this.canvas.width  = window.innerWidth;
        this.canvas.height = window.innerHeight;
        this.cx = this.canvas.width  / 2;
        this.cy = this.canvas.height / 2;
    }

    // ── WebSocket ──────────────────────────────────────────────
    connect() {
        const proto = location.protocol === 'https:' ? 'wss:' : 'ws:';
        this.ws = new WebSocket(`${proto}//${location.host}/ws`);

        this.ws.onopen = () => {
            console.info('[Anna] WebSocket connected');
            this.setConnectionState(true);
            this.applyState('idle');
            this.updateStatus("Say 'Anna' to begin");
        };

        this.ws.onmessage = (evt) => {
            try {
                this.handleMessage(JSON.parse(evt.data));
            } catch (e) {
                console.warn('[Anna] Bad message:', evt.data);
            }
        };

        this.ws.onclose = () => {
            console.warn('[Anna] disconnected – retrying in', this.reconnectDelay, 'ms');
            this.setConnectionState(false);
            this.applyState('idle');
            this.updateStatus('Reconnecting...');
            setTimeout(() => this.connect(), this.reconnectDelay);
            this.reconnectDelay = Math.min(this.reconnectDelay * 1.5, 10000);
        };

        this.ws.onerror = () => {
            this.ws.close();
        };
    }

    setConnectionState(online) {
        this.connStatus.className = 'dot-indicator ' + (online ? 'online' : 'offline');
        this.connLabel.textContent = online ? 'Online' : 'Offline';
        if (online) this.reconnectDelay = 1500;
    }

    handleMessage(data) {
        switch (data.type) {
            case 'wakeword_detected':
                this.spawnRipple();
                this.applyState('active');
                this.updateStatus('Listening...');
                this.clearTranscript();
                break;

            case 'listening':
                this.applyState('listening');
                if (data.transcript) this.showTranscript(data.transcript);
                if (data.audioLevel !== undefined) this.audioLevel = data.audioLevel;
                break;

            case 'processing':
                this.applyState('active');
                this.updateStatus('Thinking...');
                break;

            case 'speaking':
                this.applyState('speaking');
                if (data.text) this.showTranscript(data.text);
                break;

            case 'idle':
                this.applyState('idle');
                this.updateStatus("Say 'Anna' to begin");
                setTimeout(() => this.clearTranscript(), 3000);
                break;

            case 'ping':
                break; // keep-alive, ignore

            default:
                console.log('[Anna] Unknown message type:', data.type);
        }
    }

    // ── State machine ───────────────────────────────────────────
    applyState(newState) {
        this.state = newState;

        // Body class for CSS state hooks
        document.body.className = 'state-' + newState;

        switch (newState) {
            case 'idle':
                this.targetRadius  = this.baseRadius;
                this.targetOpacity = 0.55;
                this.targetGlowSize = 0;
                break;

            case 'active':
                this.targetRadius  = this.baseRadius * 1.18;
                this.targetOpacity = 0.95;
                this.targetGlowSize = 35;
                break;

            case 'listening':
                this.targetRadius  = this.baseRadius * 1.08;
                this.targetOpacity = 0.9;
                this.targetGlowSize = 22;
                break;

            case 'speaking':
                this.targetRadius  = this.baseRadius * 1.28;
                this.targetOpacity = 1.0;
                this.targetGlowSize = 48;
                break;
        }
    }

    updateStatus(msg) {
        this.statusText.textContent = msg;
    }

    showTranscript(text) {
        this.transcript.textContent = text;
        this.transcriptBox.classList.add('visible');
    }

    clearTranscript() {
        this.transcriptBox.classList.remove('visible');
        setTimeout(() => { this.transcript.textContent = ''; }, 400);
    }

    spawnRipple() {
        this.ripples.push({ r: this.currentRadius, alpha: 0.7 });
    }


    // ── Animation loop ──────────────────────────────────────────
    animate() {
        this.t += 0.016;  // ~60 fps tick

        // Ease physics values toward targets
        this.currentRadius  = lerp(this.currentRadius,  this.targetRadius,   0.08);
        this.opacity        = lerp(this.opacity,        this.targetOpacity,  0.08);
        this.glowSize       = lerp(this.glowSize,       this.targetGlowSize, 0.08);

        const ctx = this.ctx;
        ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);

        // ── Ripples ──
        for (let i = this.ripples.length - 1; i >= 0; i--) {
            const rip = this.ripples[i];
            rip.r     += 2.5;
            rip.alpha *= 0.93;
            if (rip.alpha < 0.01) { this.ripples.splice(i, 1); continue; }

            ctx.beginPath();
            ctx.arc(this.cx, this.cy, rip.r, 0, Math.PI * 2);
            ctx.strokeStyle = `hsla(210, 100%, 70%, ${rip.alpha})`;
            ctx.lineWidth = 1.5;
            ctx.stroke();
        }

        // ── Dynamic radius offset by state ──
        let dr = 0;
        switch (this.state) {
            case 'idle':
                dr = Math.sin(this.t * 1.6) * 5;
                break;
            case 'active':
                dr = Math.sin(this.t * 4.5) * 9;
                break;
            case 'listening':
                dr = this.audioLevel * 18 + Math.sin(this.t * 3.2) * 4;
                break;
            case 'speaking':
                dr = Math.sin(this.t * 6) * 14 + Math.sin(this.t * 2.1) * 7;
                break;
        }
        const r = this.currentRadius + dr;

        const pal = this.palette[this.state] || this.palette.idle;
        const hsl = `${pal.h}, ${pal.s}%, ${pal.l}%`;

        // ── Outer glow ──
        if (this.glowSize > 1) {
            const glow = ctx.createRadialGradient(
                this.cx, this.cy, r * 0.5,
                this.cx, this.cy, r + this.glowSize
            );
            glow.addColorStop(0, `hsla(${hsl}, ${this.opacity * 0.6})`);
            glow.addColorStop(1, `hsla(${hsl}, 0)`);
            ctx.fillStyle = glow;
            ctx.beginPath();
            ctx.arc(this.cx, this.cy, r + this.glowSize, 0, Math.PI * 2);
            ctx.fill();
        }

        // ── Main filled circle ──
        const mainGrad = ctx.createRadialGradient(
            this.cx - r * 0.25, this.cy - r * 0.25, 0,
            this.cx, this.cy, r
        );
        mainGrad.addColorStop(0, `hsla(${pal.h}, ${pal.s}%, ${Math.min(pal.l + 20, 95)}%, ${this.opacity})`);
        mainGrad.addColorStop(1, `hsla(${hsl}, ${this.opacity * 0.85})`);

        ctx.fillStyle = mainGrad;
        ctx.beginPath();
        ctx.arc(this.cx, this.cy, r, 0, Math.PI * 2);
        ctx.fill();

        // ── Inner highlight (glassy sheen) ──
        const shine = ctx.createRadialGradient(
            this.cx - r * 0.3, this.cy - r * 0.35, 0,
            this.cx, this.cy, r * 0.95
        );
        shine.addColorStop(0, `rgba(255, 255, 255, ${this.opacity * 0.18})`);
        shine.addColorStop(0.5, `rgba(255, 255, 255, ${this.opacity * 0.04})`);
        shine.addColorStop(1, `rgba(255, 255, 255, 0)`);
        ctx.fillStyle = shine;
        ctx.beginPath();
        ctx.arc(this.cx, this.cy, r, 0, Math.PI * 2);
        ctx.fill();

        requestAnimationFrame(() => this.animate());
    }
}

// ─── Utilities ────────────────────────────────────────────────
function lerp(a, b, t) {
    return a + (b - a) * t;
}

// ─── Entrypoint ───────────────────────────────────────────────
window.addEventListener('DOMContentLoaded', () => {
    new ParticleField(document.getElementById('particles'));
    new AnnaCircle();
});
