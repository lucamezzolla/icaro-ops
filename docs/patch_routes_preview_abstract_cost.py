#!/usr/bin/env python3
from pathlib import Path

path = Path("src/js/routes.js")
text = path.read_text(encoding="utf-8")

old = '''function renderPreview(p) {
  return `
    <div class="detail-grid">
      ${section("Route", [
        ["Route", `${p.origin_airport_icao_code} → ${p.destination_airport_icao_code}`],
        ["Distance", `${p.planned_distance_km} km`],
        ["Duration", `${p.planned_duration_minutes} min`],
        ["Aircraft", `${p.aircraft.manufacturer} ${p.aircraft.model_name}`]
      ])}
      ${section("Passengers", [
        ["Capacity", p.passenger_capacity],
        ["Low estimate", `${p.estimates.low.passengers} pax · ${money(p.estimates.low.revenue)} ${p.currency_code}`],
        ["Expected", `${p.estimates.expected.passengers} pax · ${money(p.estimates.expected.revenue)} ${p.currency_code}`],
        ["High estimate", `${p.estimates.high.passengers} pax · ${money(p.estimates.high.revenue)} ${p.currency_code}`]
      ])}
      ${section("Expected economics", [
        ["Revenue", `${money(p.estimates.expected.revenue)} ${p.currency_code}`],
        ["Fuel cost", `${money(p.costs.fuel_cost)} ${p.currency_code}`],
        ["Maintenance cost", `${money(p.costs.maintenance_cost)} ${p.currency_code}`],
        ["Staff cost", `${money(p.costs.staff_cost)} ${p.currency_code}`],
        ["Total cost", `${money(p.costs.total_operating_cost)} ${p.currency_code}`],
        ["Expected profit", `${money(p.estimates.expected.profit)} ${p.currency_code}`]
      ])}
      ${section("Notes", [
        ["Fuel burn", `${p.aircraft.fuel_burn_kg_per_hour} kg/h`],
        ["Cruise speed", `${p.aircraft.cruise_speed_kmh} km/h`],
        ["Break-even pax", p.break_even_passengers],
        ["Recommendation", p.recommendation]
      ])}
    </div>
  `;
}'''

new = '''function renderPreview(p) {
  return `
    <div class="detail-grid">
      ${section("Route", [
        ["Route", `${p.origin_airport_icao_code} → ${p.destination_airport_icao_code}`],
        ["Distance", `${p.planned_distance_km} km`],
        ["Duration", `${p.planned_duration_minutes} min`],
        ["Block hours", `${p.block_hours} h`],
        ["Aircraft", `${p.aircraft.manufacturer} ${p.aircraft.model_name}`]
      ])}
      ${section("Passengers", [
        ["Capacity", p.passenger_capacity],
        ["Low estimate", `${p.estimates.low.passengers} pax · revenue ${money(p.estimates.low.revenue)} · profit ${money(p.estimates.low.profit)} ${p.currency_code}`],
        ["Expected", `${p.estimates.expected.passengers} pax · revenue ${money(p.estimates.expected.revenue)} · profit ${money(p.estimates.expected.profit)} ${p.currency_code}`],
        ["High estimate", `${p.estimates.high.passengers} pax · revenue ${money(p.estimates.high.revenue)} · profit ${money(p.estimates.high.profit)} ${p.currency_code}`]
      ])}
      ${section("Expected economics", [
        ["Revenue", `${money(p.estimates.expected.revenue)} ${p.currency_code}`],
        ["Fuel cost", `${money(p.costs.fuel_cost)} ${p.currency_code}`],
        ["Maintenance reserve", `${money(p.costs.maintenance_cost)} ${p.currency_code}`],
        ["Crew allocated cost", `${money(p.costs.staff_cost)} ${p.currency_code}`],
        ["Total cost", `${money(p.costs.total_operating_cost)} ${p.currency_code}`],
        ["Expected profit", `${money(p.estimates.expected.profit)} ${p.currency_code}`]
      ])}
      ${section("Pricing", [
        ["Current ticket", `${money(p.ticket_price)} ${p.currency_code}`],
        ["Suggested ticket", `${money(p.suggested_ticket_price)} ${p.currency_code}`],
        ["Break-even pax", p.break_even_passengers],
        ["Recommendation", p.recommendation]
      ])}
      ${section("Cost model", [
        ["Crew formula", p.cost_model?.crew_cost_formula || "-"],
        ["Crew base before share", `${money(p.cost_model?.crew_base_cost_before_revenue_share || 0)} ${p.currency_code}`],
        ["Daily retainer", p.cost_model?.daily_retainer_note || "-"],
        ["Fuel burn", `${p.aircraft.fuel_burn_kg_per_hour} kg/h`],
        ["Cruise speed", `${p.aircraft.cruise_speed_kmh} km/h`]
      ])}
    </div>
  `;
}'''

if old in text:
    text = text.replace(old, new)
else:
    raise SystemExit("renderPreview block not found exactly. Manual update may be needed.")

path.write_text(text, encoding="utf-8")
print("OK: routes.js preview updated.")
