"""Support for the Geofency device tracker platform."""
import logging

from homeassistant.core import callback
from homeassistant.components.device_tracker import SOURCE_TYPE_GPS
from homeassistant.components.device_tracker.config_entry import (
    DeviceTrackerEntity
)
from homeassistant.helpers.dispatcher import async_dispatcher_connect

from . import DOMAIN as GF_DOMAIN, TRACKER_UPDATE

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up Geofency config entry."""
    @callback
    def _receive_data(device, gps, location_name, attributes):
        """Fire HA event to set location."""
        if device in hass.data[GF_DOMAIN]['devices']:
            return

        hass.data[GF_DOMAIN]['devices'].add(device)

        async_add_entities([GeofencyEntity(
            device, gps, location_name, attributes
        )])

    hass.data[GF_DOMAIN]['unsub_device_tracker'][config_entry.entry_id] = \
        async_dispatcher_connect(hass, TRACKER_UPDATE, _receive_data)

    return True


class GeofencyEntity(DeviceTrackerEntity):
    """Represent a tracked device."""

    def __init__(self, device, gps, location_name, attributes):
        """Set up Geofency entity."""
        self._attributes = attributes
        self._name = device
        self._location_name = location_name
        self._gps = gps
        self._unsub_dispatcher = None

    @property
    def device_state_attributes(self):
        """Return device specific attributes."""
        return self._attributes

    @property
    def latitude(self):
        """Return latitude value of the device."""
        return self._gps[0]

    @property
    def longitude(self):
        """Return longitude value of the device."""
        return self._gps[1]

    @property
    def location_name(self):
        """Return a location name for the current location of the device."""
        return self._location_name

    @property
    def name(self):
        """Return the name of the device."""
        return self._name

    @property
    def should_poll(self):
        """No polling needed."""
        return False

    @property
    def source_type(self):
        """Return the source type, eg gps or router, of the device."""
        return SOURCE_TYPE_GPS

    async def async_added_to_hass(self):
        """Register state update callback."""
        self._unsub_dispatcher = async_dispatcher_connect(
            self.hass, TRACKER_UPDATE, self._async_receive_data)

    async def async_will_remove_from_hass(self):
        """Clean up after entity before removal."""
        self._unsub_dispatcher()

    @callback
    def _async_receive_data(self, device, gps, location_name, attributes):
        """Mark the device as seen."""
        if device != self.name:
            return

        self._attributes.update(attributes)
        self._location_name = location_name
        self._gps = gps
        self.async_write_ha_state()
