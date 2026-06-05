#!/usr/bin/env python3
from pathlib import Path

path = Path("src/js/routes.js")
text = path.read_text(encoding="utf-8")

if "let lastSuggestedTicketPrice" not in text:
    text = text.replace("let routes = [];", "let routes = [];\nlet lastSuggestedTicketPrice = null;")

text = text.replace('document.querySelector("#ticketPrice").value = "250.00";', 'document.querySelector("#ticketPrice").value = "0.00";')
text = text.replace('document.querySelector("#ticketPrice").value = "250";', 'document.querySelector("#ticketPrice").value = "0.00";')

text = text.replace('''  document.querySelector("#previewRouteButton")?.addEventListener("click", previewRoute);
  document.querySelector("#routeForm")?.addEventListener("submit", saveRoute);
  await loadRoutes();''', '''  document.querySelector("#previewRouteButton")?.addEventListener("click", previewRoute);
  document.querySelector("#routeForm")?.addEventListener("submit", saveRoute);
  setupTicketSuggestion();
  await loadRoutes();''')

text = text.replace('''  document.querySelector("#previewRouteButton")?.addEventListener("click", previewRoute);
  document.querySelector("#saveRouteButton")?.addEventListener("click", saveRoute);
  await loadRoutes();''', '''  document.querySelector("#previewRouteButton")?.addEventListener("click", previewRoute);
  document.querySelector("#saveRouteButton")?.addEventListener("click", saveRoute);
  setupTicketSuggestion();
  await loadRoutes();''')

text = text.replace("async function previewRoute() {", "async function previewRoute(options = {}) {")
text = text.replace("  const payload = routeFormPayload();", "  const payload = routeFormPayload();\n  const silent = Boolean(options.silent);", 1)

text = text.replace('''  error.hidden = true;
  panel.hidden = false;
  content.textContent = "Calculating preview...";''', '''  error.hidden = true;

  if (!silent) {
    panel.hidden = false;
    content.textContent = "Calculating preview...";
  }''')

text = text.replace('''    const preview = await postJson(API.preview, payload);
    content.innerHTML = renderPreview(preview);''', '''    const preview = await postJson(API.preview, payload);
    lastSuggestedTicketPrice = Number(preview.suggested_ticket_price || 0);

    if (Number(payload.ticket_price || 0) <= 0 && lastSuggestedTicketPrice > 0) {
      document.querySelector("#ticketPrice").value = lastSuggestedTicketPrice.toFixed(2);
    }

    if (!silent) {
      panel.hidden = false;
      content.innerHTML = renderPreview(preview);
    }''')

text = text.replace('''  } catch (err) {
    panel.hidden = true;
    error.hidden = false;
    error.textContent = err.message || "Unable to preview route.";
  }''', '''  } catch (err) {
    if (!silent) {
      panel.hidden = true;
      error.hidden = false;
      error.textContent = err.message || "Unable to preview route.";
    }
  }''')

helper = r'''
function setupTicketSuggestion() {
  const origin = document.querySelector("#originAirport");
  const destination = document.querySelector("#destinationAirport");
  const ticket = document.querySelector("#ticketPrice");

  if (!origin || !destination || !ticket || ticket.dataset.suggestionBound) {
    return;
  }

  ticket.dataset.suggestionBound = "true";

  const maybeSuggest = debounce(async () => {
    const originValue = origin.value.trim().toUpperCase();
    const destinationValue = destination.value.trim().toUpperCase();

    if (originValue.length !== 4 || destinationValue.length !== 4 || originValue === destinationValue) {
      return;
    }

    if (Number(ticket.value || 0) > 0) {
      return;
    }

    await previewRoute({ silent: true });
  }, 450);

  origin.addEventListener("input", maybeSuggest);
  destination.addEventListener("input", maybeSuggest);
  origin.addEventListener("blur", maybeSuggest);
  destination.addEventListener("blur", maybeSuggest);
}

function debounce(callback, waitMs) {
  let timeoutId = null;

  return (...args) => {
    window.clearTimeout(timeoutId);
    timeoutId = window.setTimeout(() => callback(...args), waitMs);
  };
}
'''

if "function setupTicketSuggestion(" not in text:
    marker = "async function getJson("
    pos = text.find(marker)
    if pos != -1:
        text = text[:pos] + helper + "\n\n" + text[pos:]
    else:
        text += "\n" + helper + "\n"

path.write_text(text, encoding="utf-8")
print("OK: routes JS patched.")
