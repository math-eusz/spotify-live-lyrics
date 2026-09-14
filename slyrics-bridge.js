// Local interoperability bridge. Does not request Spotify tokens or call lyric APIs.
(() => {
  const TOKEN = "__SLYRICS_LOCAL_TOKEN__";
  const ENDPOINT = "http://127.0.0.1:43829/state";
  let uri = null, lyrics = null, lastLookup = 0, lastLyricsSend = 0;
  let generation = 0;
  globalThis.__slyricsStop?.();
  let stopped = false;
  globalThis.__slyricsStop = () => { stopped = true; };

  async function cachedLyrics(trackUri) {
    const id = trackUri.split(":").pop();
    const names = (await caches.keys()).filter(n => n.startsWith("SpicyLyrics_LyricsStore"));
    // Inspect only Spicy Lyrics caches and only the currently playing track.
    for (const name of names.reverse()) {
      const cache = await caches.open(name);
      const response = await cache.match(new URL("/" + id, location.origin).href);
      if (!response) continue;
      const wrapped = await response.json();
      if (wrapped.ExpiresAt && wrapped.ExpiresAt < Date.now()) continue;
      const data = wrapped.Content;
      if (!data || !["Syllable", "Line", "Static"].includes(data.Type)) continue;
      if (data.uri && data.uri !== trackUri) continue;
      return data;
    }
    return null;
  }

  async function tick() {
    if (stopped) return;
    let delay = 100;
    try {
      const player = globalThis.Spicetify?.Player;
      if (!player?.data) { delay = 500; return; }
      const item = player.data.item;
      const currentUri = item?.uri ?? "";
      if (uri !== currentUri) {
        uri = currentUri; lyrics = null; lastLookup = 0; lastLyricsSend = 0;
        generation++;
      }
      const thisGeneration = generation;
      if (uri.startsWith("spotify:track:") && Date.now() - lastLookup > 1000) {
        lastLookup = Date.now();
        const result = await cachedLyrics(uri);
        // A song may change while Cache Storage is being read.
        if (player.data?.item?.uri !== currentUri || stopped) return;
        lyrics = result;
      }
      if (thisGeneration !== generation || stopped) return;
      const meta = item?.metadata ?? {};
      const message = {
        version: 1, uri: currentUri,
        title: item?.name ?? meta.title ?? "",
        artist: meta.artist_name ?? item?.artists?.map(a => a.name).join(", ") ?? "",
        position: player.getProgress() / 1000,
        playing: player.isPlaying(),
        duration: typeof player.getDuration === "function" && Number.isFinite(player.getDuration())
          ? Math.max(0, player.getDuration() / 1000) : 0
      };
      const sendLyrics = Date.now() - lastLyricsSend > 2000;
      if (sendLyrics) message.lyrics = lyrics;
      const controller = new AbortController();
      const timeout = setTimeout(() => controller.abort(), 1500);
      try {
        const response = await fetch(ENDPOINT, {
          method: "POST", mode: "cors", credentials: "omit",
          headers: {"Content-Type": "application/json", "X-Slyrics-Key": TOKEN},
          body: JSON.stringify(message), signal: controller.signal
        });
        if (!response.ok) throw new Error("Local bridge HTTP " + response.status);
        if (sendLyrics) lastLyricsSend = Date.now();
      } finally { clearTimeout(timeout); }
    } catch (error) {
      // The terminal normally is not running. Retry gently and resend data on reconnect.
      lastLyricsSend = 0;
      delay = 1000;
    } finally {
      if (!stopped) setTimeout(tick, delay);
    }
  }
  tick();
})();
