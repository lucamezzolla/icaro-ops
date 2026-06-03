import { createUtcClock } from "../components/utc-clock.js";

export function createAppShell() {
  const root = document.createElement("div");
  root.className = "app-shell";

  const topBar = document.createElement("header");
  topBar.className = "top-bar";

  const brand = document.createElement("div");
  brand.className = "brand";
  brand.innerHTML = `
    <div class="brand-mark">IO</div>
    <strong>Icaro Ops</strong>
  `;

  const clock = createUtcClock();

  const content = document.createElement("main");
  content.className = "main-content";

  topBar.append(brand, clock.root);
  root.append(topBar, content);

  return {
    root,
    setContent(view) {
      content.replaceChildren(view.root);
    }
  };
}
