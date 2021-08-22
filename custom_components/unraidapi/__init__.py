import asyncio
from .const import *
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import discovery
import logging

async def async_setup(hass, config):
    
    hass.data[DOMAIN] = config[DOMAIN]

    hass.async_add_job(discovery.async_load_platform(hass, 'switch', DOMAIN, {}, config))

    return True