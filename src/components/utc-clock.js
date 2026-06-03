export function createUtcClock() {
  const root = document.createElement("div");
  root.className = "utc-clock";

  function render() {
    root.textContent = new Date().toISOString().replace(".000Z", " UTC");
  }

  render();
  window.setInterval(render, 1000);

  return { root };
}
