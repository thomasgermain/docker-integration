"""multimatic integration constants."""

DOMAIN = "docker_monitor"

# list of platforms into entity are created
PLATFORMS = ["sensor", "binary_sensor", "button"]

# default values for configuration
DEFAULT_SCAN_INTERVAL = 30

# keys
COORDINATOR = "coordinator"
EVENTS_LISTENER = "events_listener"
