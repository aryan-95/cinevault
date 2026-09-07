// CineVault video player: HLS.js fallback, resume-from-position, periodic progress saving.

document.addEventListener("DOMContentLoaded", () => {
  const video = document.getElementById("cvPlayer");
  if (!video) return;

  const movieId = video.dataset.movieId;
  const resumeAt = parseFloat(video.dataset.resumeAt || "0");
  const mediaType = video.dataset.mediaType;
  const source = video.querySelector("source");
  const src = source ? source.getAttribute("src") : null;

  // Use HLS.js for .m3u8 sources on browsers without native HLS support (e.g. Chrome/Firefox).
  if (mediaType === "application/x-mpegURL" && src && window.Hls && Hls.isSupported()) {
    const hls = new Hls();
    hls.loadSource(src);
    hls.attachMedia(video);
  }

  video.addEventListener("loadedmetadata", () => {
    if (resumeAt > 5 && resumeAt < video.duration - 5) {
      video.currentTime = resumeAt;
    }
  });

  function getCsrfToken() {
    const meta = document.querySelector('input[name="csrf_token"]');
    return meta ? meta.value : "";
  }

  function saveProgress() {
    if (!video.duration || Number.isNaN(video.duration)) return;
    fetch(`/watch/${movieId}/progress`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        progress_seconds: video.currentTime,
        duration_seconds: video.duration,
      }),
    }).catch(() => {
      // Silently ignore network errors; progress will be saved on next tick.
    });
  }

  // Save progress every 10 seconds while playing, and once more on pause/unload.
  let progressInterval = null;
  video.addEventListener("play", () => {
    if (!progressInterval) {
      progressInterval = setInterval(saveProgress, 10000);
    }
  });
  video.addEventListener("pause", () => {
    saveProgress();
    if (progressInterval) {
      clearInterval(progressInterval);
      progressInterval = null;
    }
  });
  window.addEventListener("beforeunload", saveProgress);
});
