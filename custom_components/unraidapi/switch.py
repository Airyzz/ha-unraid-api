from datetime import timedelta
import logging

import async_timeout

from homeassistant.components.light import LightEntity
from homeassistant.exceptions import ConfigEntryAuthFailed

from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
    UpdateFailed,
)

from homeassistant.helpers.entity_registry import (
    async_get_registry,
)

from homeassistant.helpers.entity import Entity
from homeassistant.components.switch import SwitchEntity

from homeassistant.core import CALLBACK_TYPE, callback

from .const import *

from . import UnraidAPI

_LOGGER = logging.getLogger(__name__)

async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Set up platform."""
    #config = hass.data[DOMAIN][config_entry.entry_id]

    config = hass.data[DOMAIN]

    entity_registry = await async_get_registry(hass)

    credentials = dict()

    for server in config["servers"]:
        ip = config["servers"][server]["host"]
        credentials[ip] = config["servers"][server]

    api = UnraidAPI.Unraid(config[CONF_HOST], config[CONF_PORT], credentials)

    entities = None
    ids = None
    coordinator = None

    async def async_update_data():
        data = await api.get_servers()

        
        if entities is not None:
            
            removed_entities = list()

            #remove any stale dockers / vms
            for entity in entities:

                if isinstance(entity, DockerEntity):
                    if not entity.id in data["servers"][entity.server]["docker"]["details"]["containers"]:
                        #docker not found in server
                        _LOGGER.warning("Docker " + entity.name + " removed")
                        entity_registry.async_remove(entity.entity_id)
                        removed_entities.append(entity)

                if isinstance(entity, VMEntity):
                    if not entity.id in data["servers"][entity.server]["vm"]["details"]:
                        #VM not found in server
                        _LOGGER.warning("VM " + entity.name + " removed")
                        entity_registry.async_remove(entity.entity_id)
                        removed_entities.append(entity)
            
            #get rid of references to deleted entities
            for entity in removed_entities:
                entities.remove(entity)

            #add any new dockers found
            for server in data["servers"]:
                for docker in data["servers"][server]["docker"]["details"]["containers"]:
                    if not docker in ids:
                        ids.add(docker)
                        entity = DockerEntity(coordinator, server, docker, api, data)
                        entities.append(entity)
                        _LOGGER.warning("Docker " + entity.name + " added")
                        async_add_entities([entity])

                for vm in data["servers"][server]["vm"]["details"]:
                    if not vm in ids:
                        ids.add(vm)
                        entity = VMEntity(coordinator, server, vm, api, data)
                        entities.append(entity)
                        _LOGGER.warning("VM " + entity.name + " added")
                        async_add_entities([entity])

        return data

    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        # Name of the data. For logging purposes.
        name="sensor",
        update_method=async_update_data,
        # Polling interval. Will only be polled if there are subscribers.
        update_interval=timedelta(seconds=30),
    )

    await coordinator.async_refresh()

    entities = list()
    ids = set()

    for server in coordinator.data["servers"]:
        for docker in coordinator.data["servers"][server]["docker"]["details"]["containers"]:
            entities.append(DockerEntity(coordinator, server, docker, api, coordinator.data))
            ids.add(docker)

        for vm in coordinator.data["servers"][server]["vm"]["details"]:
            entities.append(VMEntity(coordinator, server, vm, api, coordinator.data))
            ids.add(vm)


    async_add_entities(
        entities
    )





class DockerEntity(CoordinatorEntity, SwitchEntity):

    def __init__(self, coordinator, server, id, api, data):

        super().__init__(coordinator)

        self.api = api
        self.id = id
        self.server = server

        self._attr_is_on = data["servers"][self.server]["docker"]["details"]["containers"][self.id]["status"] == "started"

        self.server_name = data["servers"][self.server]["serverDetails"]["title"]
        self.server_name_safe = self.server_name.lower().translate({ord(c): "_" for c in "!@#$%^&*()[]{};:,./<>?\|`~-=_+"})
        
        self._attr_name = data["servers"][self.server]["docker"]["details"]["containers"][self.id]["name"]
        self.docker_name_safe = self.name.lower().translate({ord(c): "_" for c in "!@#$%^&*()[]{};:,./<>?\|`~-=_+"})
        self.entity_id = "switch.unraid_" + self.server_name_safe + "_docker_" + self.docker_name_safe


    @property
    def device_state_attributes(self):
        attributes = self.coordinator.data["servers"][self.server]["docker"]["details"]["containers"][self.id]
        attributes["entity_picture"] = self.api.url() + attributes["imageUrl"]

        return attributes

    @property
    def unique_id(self):
        return self._attr_name

    async def async_turn_on(self, **kwargs):
        """Turn the entity on."""
        self._attr_is_on = True

        self.async_write_ha_state()

        await self.api.docker_status(self.server, self.id, "domain-start")

    async def async_turn_off(self, **kwargs):
        """Turn the entity off."""

        self._attr_is_on = False

        self.async_write_ha_state()

        await self.api.docker_status(self.server, self.id, "domain-stop")

    @callback
    def _handle_coordinator_update(self) -> None:
        try:
            self._attr_is_on = self.coordinator.data["servers"][self.server]["docker"]["details"]["containers"][self.id]["status"] == "started"
        except:
            self._attr_is_on = False
        self.async_write_ha_state()





class VMEntity(CoordinatorEntity, SwitchEntity):

    def __init__(self, coordinator, server, id, api, data):

        super().__init__(coordinator)

        self.api = api
        self.id = id
        self.server = server

        self._attr_is_on = data["servers"][self.server]["vm"]["details"][self.id]["status"] == "started"

        self.server_name = data["servers"][self.server]["serverDetails"]["title"]

        self.server_name_safe = self.server_name.lower().translate({ord(c): "_" for c in "!@#$%^&*()[]{};:,./<>?\|`~-=_+"})
        
        self._attr_name = data["servers"][self.server]["vm"]["details"][self.id]["name"]
        self.docker_name_safe = self.name.lower().translate({ord(c): "_" for c in "!@#$%^&*()[]{};:,./<>?\|`~-=_+"})
        self.entity_id = "switch.unraid_" + self.server_name_safe + "_vm_" + self.docker_name_safe

    @property
    def device_state_attributes(self):
        attributes = self.coordinator.data["servers"][self.server]["vm"]["details"][self.id]
        attributes["entity_picture"] = self.api.url() + attributes["icon"]

        return attributes

    @property
    def unique_id(self):
        return self.id

    async def async_turn_on(self, **kwargs):
        """Turn the entity on."""
        self._attr_is_on = True

        self.async_write_ha_state()

        await self.api.vm_status(self.server, self.id, "domain-start")

    async def async_turn_off(self, **kwargs):
        """Turn the entity off."""
        self._attr_is_on = False

        self.async_write_ha_state()

        await self.api.vm_status(self.server, self.id, "domain-stop")

    @callback
    def _handle_coordinator_update(self) -> None:

        self._attr_is_on = self.coordinator.data["servers"][self.server]["vm"]["details"][self.id]["status"] == "started"
        
        self.async_write_ha_state()