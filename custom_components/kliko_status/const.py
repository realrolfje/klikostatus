"""Constants for the Kliko Container Manager integration."""

DOMAIN = "kliko_status"

SOURCE_KLIKO_MANAGER = "kliko_manager"
SOURCE_SPAARNELANDEN = "spaarnelanden"

LOGIN_TYPE_ADDRESS = "ADDRESS"
LOGIN_TYPE_ADDRESS_AND_CARDNUMBER = "ADDRESS-AND-CARDNUMBER"
LOGIN_TYPE_NONE = "NONE"
LOGIN_TYPE_PASSWORD = "PASSWORD"

CLIENTS = {
    "landvancuijk": {
        "name": "Land van Cuijk",
        "login_type": LOGIN_TYPE_PASSWORD,
    },
    "maassluis": {
        "name": "Maassluis",
        "login_type": LOGIN_TYPE_ADDRESS,
    },
    "oudeijsselstreek": {
        "name": "Oude IJsselstreek",
        "login_type": LOGIN_TYPE_ADDRESS,
    },
    "ouderamstel": {
        "name": "Ouder Amstel",
        "login_type": LOGIN_TYPE_PASSWORD,
    },
    "uithoorn": {
        "name": "Uithoorn",
        "login_type": LOGIN_TYPE_PASSWORD,
    },
    "spaarnelanden": {
        "name": "Spaarnelanden",
        "login_type": LOGIN_TYPE_NONE,
        "source": SOURCE_SPAARNELANDEN,
        "containers_url": "https://inzameling.spaarnelanden.nl/",
    },
}

SUPPORTED_CLIENTS = {client_id: client["name"] for client_id, client in CLIENTS.items()}

DEFAULT_SCAN_INTERVAL_MINUTES = 60
MIN_SCAN_INTERVAL_MINUTES = 30

CONF_APP = "app"
CONF_CARD_NUMBER = "card_number"
CONF_CLIENT = "client"
CONF_CLIENT_NAME = "client_name"
CONF_CONTAINER_NUMBER = "container_number"
CONF_CONTAINER_NUMBERS = "container_numbers"
CONF_CONTAINERS_URL = "containers_url"
CONF_LOGIN_TYPE = "login_type"
CONF_LOGIN_URL = "login_url"
CONF_SCAN_INTERVAL_MINUTES = "scan_interval_minutes"
CONF_SOURCE = "source"
CONF_STREET_NUMBER = "street_number"
CONF_STREET_NUMBER_ADDITION = "street_number_addition"
CONF_ZIP_CODE = "zip_code"

ATTR_CONTAINER_NUMBER = "container_number"
ATTR_DISTRICT = "district"
