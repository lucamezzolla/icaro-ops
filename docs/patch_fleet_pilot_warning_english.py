#!/usr/bin/env python3
from pathlib import Path

path = Path("src/js/fleet.js")
text = path.read_text(encoding="utf-8")

old_block = '''    if (code === "INSUFFICIENT_QUALIFIED_PILOTS") {
      lines.push("Pilot coverage is not sufficient for this purchase.");
      lines.push("Pilots are a qualified company pool, not assigned permanently to a single aircraft.");
    } else {
      lines.push(body?.message || code || `Request failed: ${response.status}`);
    }

    if (body?.required_pilots_after_purchase !== undefined) {
      lines.push(`Required qualified pilots after purchase: ${body.required_pilots_after_purchase}`);
    }

    if (body?.current_qualified_pilots !== undefined) {
      lines.push(`Current qualified pilots: ${body.current_qualified_pilots}`);
    }

    if (body?.required_license) {
      lines.push(`Required aircraft qualification: ${body.required_license}`);
    }'''

new_block = '''    if (code === "INSUFFICIENT_QUALIFIED_PILOTS") {
      lines.push("Pilot coverage is not sufficient for this purchase.");

      if (
        body?.required_pilots_after_purchase !== undefined &&
        body?.current_qualified_pilots !== undefined
      ) {
        const missingPilots = Math.max(
          0,
          Number(body.required_pilots_after_purchase) - Number(body.current_qualified_pilots)
        );

        lines.push(`You need ${missingPilots} more qualified pilots to buy this aircraft.`);
      }

      if (body?.required_license) {
        lines.push(`Required aircraft qualification: ${body.required_license}`);
      }
    } else {
      lines.push(body?.message || code || `Request failed: ${response.status}`);
    }'''

italian_block = '''    if (code === "INSUFFICIENT_QUALIFIED_PILOTS") {
      lines.push("Pilot coverage is not sufficient for this purchase.");

      if (
        body?.required_pilots_after_purchase !== undefined &&
        body?.current_qualified_pilots !== undefined
      ) {
        const missingPilots = Math.max(
          0,
          Number(body.required_pilots_after_purchase) - Number(body.current_qualified_pilots)
        );

        lines.push(`Ho bisogno di altri ${missingPilots} per comprare questo velivolo`);
      }

      if (body?.required_license) {
        lines.push(`Required aircraft qualification: ${body.required_license}`);
      }
    } else {
      lines.push(body?.message || code || `Request failed: ${response.status}`);
    }'''

if old_block in text:
    text = text.replace(old_block, new_block)
elif italian_block in text:
    text = text.replace(italian_block, new_block)
elif "You need ${missingPilots} more qualified pilots to buy this aircraft." in text:
    print("OK: Fleet pilot coverage warning is already in English.")
else:
    raise SystemExit(
        "Could not find the expected pilot warning block. "
        "Run: grep -n \"INSUFFICIENT_QUALIFIED_PILOTS\\|required_pilots_after_purchase\\|current_qualified_pilots\" src/js/fleet.js"
    )

path.write_text(text, encoding="utf-8")
print("OK: Fleet pilot coverage warning is now concise and in English.")
