(() => {
  "use strict";

  const bank = window.PIXELFX_SOUND_BANK;
  const panel = document.querySelector("#sound-panel");
  const toggle = document.querySelector("#sound-toggle");
  const preview = document.querySelector("#sound-preview");
  const volume = document.querySelector("#sound-volume");
  const status = document.querySelector("#sound-status");
  const viewer = document.querySelector("#viewer");
  const bufferCache = new Map();
  const activeNodes = new Set();
  const fired = new Set();
  let current = null;
  let context = null;
  let master = null;
  let enabled = false;
  let state = "muted";
  let version = 0;
  let buffers = null;
  let lastTime = null;
  let lastRate = null;

  function updateControls() {
    panel.hidden = !current;
    toggle.disabled = !current;
    preview.disabled = !current || state === "loading";
    toggle.textContent = enabled ? "关闭音效" : "开启音效";
    toggle.setAttribute("aria-pressed", String(enabled));
    const label = current?.audioName || "";
    status.textContent = {
      muted: "候选侧静音",
      loading: "正在准备" + label + "音效",
      ready: label + " · 音效已开启",
      error: "音效启用失败，可点击重试",
    }[state];
    viewer.dataset.soundState = current ? state : "none";
  }

  function adjustVolume() {
    if (!master) return;
    const level = Math.min(1, Math.max(0, Number(volume.value) / 100));
    master.gain.setTargetAtTime(level * .82, context.currentTime, .018);
  }

  function reset() {
    if (context) {
      const now = context.currentTime;
      for (const { node, gain } of activeNodes) {
        gain.gain.cancelScheduledValues(now);
        gain.gain.setTargetAtTime(0, now, .002);
        node.stop(now + .009);
      }
    }
    activeNodes.clear();
    fired.clear();
    lastTime = null;
    lastRate = null;
    viewer.dataset.soundCue = "";
  }

  function decode(id) {
    if (!bufferCache.has(id)) {
      const raw = Uint8Array.from(atob(bank[id].wav), char => char.charCodeAt(0));
      const pending = context.decodeAudioData(raw.buffer).catch(error => {
        bufferCache.delete(id);
        throw error;
      });
      bufferCache.set(id, pending);
      if (bufferCache.size > 24) bufferCache.delete(bufferCache.keys().next().value);
    }
    return bufferCache.get(id);
  }

  async function prepare() {
    const generation = ++version;
    state = "loading";
    updateControls();
    try {
      const ids = [...new Set(current.audioCues.map(cue => cue.id))];
      const pairs = await Promise.all(ids.map(async id => [id, await decode(id)]));
      if (generation !== version || !enabled) return false;
      buffers = new Map(pairs);
      state = "ready";
      updateControls();
      return true;
    } catch (error) {
      if (generation !== version) return false;
      enabled = false;
      state = "error";
      updateControls();
      console.warn("Spell audio could not be decoded", error);
      return false;
    }
  }

  function setCase(caseData) {
    ++version;
    reset();
    buffers = null;
    current = caseData?.audioCues?.length ? caseData : null;
    state = "muted";
    if (current && enabled && context) void prepare();
    else updateControls();
  }

  async function enable() {
    if (!current) return false;
    try {
      if (!context) {
        const AudioEngine = window.AudioContext || window.webkitAudioContext;
        context = new AudioEngine({ latencyHint: "interactive" });
        master = context.createGain();
        master.gain.value = Number(volume.value) / 100 * .82;
        master.connect(context.destination);
      }
      const chosen = current;
      const request = ++version;
      await context.resume();
      if (request !== version || chosen !== current) return false;
      enabled = true;
      return await prepare();
    } catch (error) {
      enabled = false;
      state = "error";
      updateControls();
      console.warn("Spell audio could not be started", error);
      return false;
    }
  }

  function disable() {
    ++version;
    enabled = false;
    state = "muted";
    reset();
    updateControls();
  }

  function playCue(cue, elapsed, rate) {
    const buffer = buffers.get(cue.id);
    const remaining = Math.min(cue.duration, buffer.duration) - elapsed;
    if (remaining < .012) return;
    const node = context.createBufferSource();
    const gain = context.createGain();
    const now = context.currentTime;
    const end = now + remaining / rate;
    const fade = Math.min(.018, (end - now) * .25);
    const entry = { node, gain };
    node.buffer = buffer;
    node.playbackRate.value = rate;
    gain.gain.setValueAtTime(0, now);
    gain.gain.linearRampToValueAtTime(cue.gain, now + Math.min(.005, fade));
    gain.gain.setValueAtTime(cue.gain, end - fade);
    gain.gain.linearRampToValueAtTime(0, end);
    node.connect(gain);
    gain.connect(master);
    node.onended = () => {
      activeNodes.delete(entry);
      node.disconnect();
      gain.disconnect();
    };
    activeNodes.add(entry);
    node.start(now, elapsed);
    node.stop(end);
    viewer.dataset.soundCue = cue.id;
  }

  function advance(time, rate) {
    if (!enabled || !buffers || context.state !== "running") return;
    if (lastTime !== null && (time < lastTime || time - lastTime > .16 || rate !== lastRate)) reset();
    lastTime = time;
    lastRate = rate;
    for (const cue of current.audioCues) {
      if (cue.at > time || fired.has(cue)) continue;
      fired.add(cue);
      const elapsed = Math.max(0, time - cue.at);
      if (elapsed < cue.duration) playCue(cue, elapsed, rate);
    }
  }

  toggle.addEventListener("click", () => {
    if (enabled) disable();
    else void enable();
  });
  volume.addEventListener("input", adjustVolume);
  window.PIXELFX_SPELL_AUDIO = { setCase, enable, reset, advance };
})();
