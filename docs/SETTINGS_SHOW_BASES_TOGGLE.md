# Settings: show bases on map

This patch adds a Settings panel to the operations map.

## Feature

In `Settings` there is a switch:

```text
Show bases on map
```

When enabled:

- player bases are visible
- virtual rival bases are visible

When disabled:

- base markers disappear from the map
- selected base data in the sidebar remains available
- airport search still works

The preference is saved in:

```text
localStorage["icaro_ops_show_bases_on_map"]
```

## Apply

```bash
cd /home/luca/Documenti/html/icaro-ops
unzip -o /home/luca/Scaricati/icaro-ops-settings-show-bases-toggle-patch.zip
```

Then append the Settings CSS:

```bash
cat >> src/css/dashboard.css <<'EOF'

.settings-panel {
  position: absolute;
  top: 56px;
  right: 16px;
  z-index: 680;
  width: min(360px, calc(100% - 32px));
  padding: 16px;
  border: 1px solid rgba(255,255,255,0.18);
  border-radius: 18px;
  background: rgba(7, 16, 29, 0.94);
  backdrop-filter: blur(12px);
  box-shadow: 0 18px 42px rgba(0,0,0,0.34);
}

.settings-panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 14px;
}

.settings-panel h2 {
  margin: 0;
  font-size: 1.05rem;
}

.settings-panel-header button {
  width: 32px;
  height: 32px;
  border: 0;
  border-radius: 50%;
  color: var(--text);
  background: var(--blue);
  font-size: 1.25rem;
  line-height: 1;
  cursor: pointer;
}

.switch-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  color: var(--text);
}

.switch-row span {
  display: grid;
  gap: 3px;
}

.switch-row small {
  color: var(--muted);
  line-height: 1.35;
}

.switch-row input {
  appearance: none;
  flex: 0 0 auto;
  width: 52px;
  height: 30px;
  border-radius: 999px;
  background: rgba(255,255,255,0.18);
  border: 1px solid rgba(255,255,255,0.24);
  position: relative;
  cursor: pointer;
  transition: background 0.18s ease;
}

.switch-row input::before {
  content: "";
  position: absolute;
  width: 24px;
  height: 24px;
  top: 2px;
  left: 2px;
  border-radius: 50%;
  background: #ffffff;
  transition: transform 0.18s ease;
}

.switch-row input:checked {
  background: var(--blue);
}

.switch-row input:checked::before {
  transform: translateX(22px);
}
EOF
```

## Test

Open:

```text
http://127.0.0.1:8080/
```

Click `Settings` and toggle `Show bases on map`.
