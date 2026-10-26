# LOQED Extras

Adds an **Open house mode** switch (NL: *Touwtje uit de brievenbus*) to your LOQED Touch
Smart Lock in Home Assistant. It complements the core `loqed` integration (keep that one
installed) and attaches the switch to the same device.

## Install
1. Copy `custom_components/loqed_extras` into your HA `config/custom_components/`, or add this repo to HACS as a custom repository.
2. Restart HA, then Settings → Devices & services → Add integration → **LOQED Extras**.
3. Paste a personal access token from https://integrations.production.loqed.com/personal-access-tokens (admin account).

## How it works
- Writes: `POST /api/locks/{id}/setting` with `{"setting_name": "open_house_mode", "setting_value": 0|1}` (documented by LOQED).
- Reads: polls `GET /api/locks/` every 5 minutes. The state key is **not documented**; the switch reads `guest_access_mode` (confirmed to be Open House Mode), then `open_house_mode`. If neither exists in your payload it shows the last value set from HA. Enable debug logging for `custom_components.loqed_extras` to see your payload and adjust `OPEN_HOUSE_STATE_KEYS` in `const.py`.
- Because the mode is also changed from the LOQED app, state set elsewhere only shows up if the list payload reports it.

## Status
Untested against a real lock.
