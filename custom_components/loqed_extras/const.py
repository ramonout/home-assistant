"""Constants for LOQED Extras."""

DOMAIN = "loqed_extras"
CORE_LOQED_DOMAIN = "loqed"

CONF_API_TOKEN = "api_token"
CONF_LOCK_ID = "lock_id"

CLOUD_BASE_URL = "https://integrations.production.loqed.com"

# Setting name used by POST /api/locks/{id}/setting
SETTING_OPEN_HOUSE_MODE = "open_house_mode"

# Keys that may carry the open house state in GET /api/locks/ (first match wins).
# The list payload reports Open House Mode as "guest_access_mode" (confirmed by user).
OPEN_HOUSE_STATE_KEYS = ("guest_access_mode", "open_house_mode")

UPDATE_INTERVAL_MINUTES = 5
