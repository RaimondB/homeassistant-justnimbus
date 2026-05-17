"""Config flow for JustNimbus MQTT."""

from __future__ import annotations

import voluptuous as vol
from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlow,
)
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.core import callback
from homeassistant.helpers.selector import (
    NumberSelector,
    NumberSelectorConfig,
    NumberSelectorMode,
    SelectOptionDict,
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
)

from .const import (
    CONF_DEVICE_NAME,
    CONF_RESERVOIR_HEIGHT,
    CONF_RESERVOIR_LENGTH,
    CONF_RESERVOIR_PRESET,
    CONF_RESERVOIR_VOLUME,
    CONF_RESERVOIR_WIDTH,
    CONF_TOPIC_PREFIX,
    DEFAULT_DEVICE_NAME,
    DEFAULT_PORT,
    DEFAULT_RESERVOIR_HEIGHT,
    DEFAULT_RESERVOIR_LENGTH,
    DEFAULT_RESERVOIR_VOLUME,
    DEFAULT_RESERVOIR_WIDTH,
    DEFAULT_TOPIC_PREFIX,
    DOMAIN,
    PRESET_CUSTOM,
    PRESET_UNKNOWN,
    RESERVOIR_PRESETS,
)

_DIMENSION_KEYS = (
    CONF_RESERVOIR_LENGTH,
    CONF_RESERVOIR_WIDTH,
    CONF_RESERVOIR_HEIGHT,
    CONF_RESERVOIR_VOLUME,
)

# Order also drives the radio list. "Unknown" first so an unconfigured
# reservoir is the explicit, safe default.
_PRESET_LABELS: dict[str, str] = {
    PRESET_UNKNOWN: "Unknown / not set (fill level stays unavailable)",
    "standard_3000": "Standard 3,000 L (~2.6 x 2.6 x 0.5 m)",
    "standard_4500": "Standard 4,500 L (~3.5 x 2.6 x 0.5 m)",
    PRESET_CUSTOM: "Custom (use the values entered below)",
}


# A bare callable schema type is NOT JSON-serializable for the frontend
# (voluptuous_serialize) and makes the form fail to load; selectors are.
def _dimension() -> NumberSelector:
    return NumberSelector(
        NumberSelectorConfig(min=1, step=1, mode=NumberSelectorMode.BOX)
    )


def _reservoir_schema(defaults: dict, preset_default: str) -> vol.Schema:
    """Preset radio + the four dimension boxes (shared by both flows)."""
    return vol.Schema(
        {
            vol.Required(CONF_RESERVOIR_PRESET, default=preset_default): SelectSelector(
                SelectSelectorConfig(
                    options=[
                        SelectOptionDict(value=value, label=label)
                        for value, label in _PRESET_LABELS.items()
                    ],
                    mode=SelectSelectorMode.LIST,
                )
            ),
            vol.Required(
                CONF_RESERVOIR_LENGTH,
                default=defaults.get(CONF_RESERVOIR_LENGTH, DEFAULT_RESERVOIR_LENGTH),
            ): _dimension(),
            vol.Required(
                CONF_RESERVOIR_WIDTH,
                default=defaults.get(CONF_RESERVOIR_WIDTH, DEFAULT_RESERVOIR_WIDTH),
            ): _dimension(),
            vol.Required(
                CONF_RESERVOIR_HEIGHT,
                default=defaults.get(CONF_RESERVOIR_HEIGHT, DEFAULT_RESERVOIR_HEIGHT),
            ): _dimension(),
            vol.Required(
                CONF_RESERVOIR_VOLUME,
                default=defaults.get(CONF_RESERVOIR_VOLUME, DEFAULT_RESERVOIR_VOLUME),
            ): _dimension(),
        }
    )


def _resolve_reservoir(user_input: dict) -> dict:
    """Map the submitted reservoir form to the stored options dict.

    Unknown -> no dimensions (derived fill/full entities stay unknown).
    A standard preset -> its own values. Custom -> the entered boxes.
    """
    preset = user_input[CONF_RESERVOIR_PRESET]
    if preset == PRESET_UNKNOWN:
        return {CONF_RESERVOIR_PRESET: PRESET_UNKNOWN}
    if preset in RESERVOIR_PRESETS:
        resolved = dict(RESERVOIR_PRESETS[preset])
    else:  # custom — NumberSelector yields floats; store ints
        resolved = {k: int(user_input[k]) for k in _DIMENSION_KEYS}
    resolved[CONF_RESERVOIR_PRESET] = preset
    return resolved


class JustNimbusMqttConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for JustNimbus MQTT."""

    VERSION = 1

    def __init__(self) -> None:
        self._conn: dict = {}

    async def async_step_user(self, user_input: dict | None = None) -> ConfigFlowResult:
        """Step 1: broker connection."""
        if user_input is not None:
            await self.async_set_unique_id(
                f"{user_input[CONF_HOST]}:{user_input[CONF_PORT]}"
                f":{user_input[CONF_TOPIC_PREFIX]}"
            )
            self._abort_if_unique_id_configured()
            self._conn = user_input
            return await self.async_step_reservoir()

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_HOST): str,
                    vol.Required(CONF_PORT, default=DEFAULT_PORT): int,
                    vol.Required(CONF_TOPIC_PREFIX, default=DEFAULT_TOPIC_PREFIX): str,
                    vol.Required(CONF_DEVICE_NAME, default=DEFAULT_DEVICE_NAME): str,
                }
            ),
        )

    async def async_step_reservoir(
        self, user_input: dict | None = None
    ) -> ConfigFlowResult:
        """Step 2: reservoir ("zak"), stored as entry options."""
        if user_input is not None:
            return self.async_create_entry(
                title=self._conn[CONF_DEVICE_NAME],
                data=self._conn,
                options=_resolve_reservoir(user_input),
            )

        return self.async_show_form(
            step_id="reservoir",
            data_schema=_reservoir_schema({}, PRESET_UNKNOWN),
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: ConfigEntry,
    ) -> JustNimbusMqttOptionsFlow:
        """Return the options flow for reservoir ("zak") dimensions."""
        return JustNimbusMqttOptionsFlow(config_entry)


class JustNimbusMqttOptionsFlow(OptionsFlow):
    """Reconfigure the physical reservoir ("zak") after setup."""

    def __init__(self, config_entry: ConfigEntry) -> None:
        # Hold our own reference; the framework's self.config_entry
        # availability at form-build time varies across HA versions.
        self._entry = config_entry

    async def async_step_init(self, user_input: dict | None = None) -> ConfigFlowResult:
        """Show preset + dimensions and store the resolved values."""
        if user_input is not None:
            return self.async_create_entry(
                title="", data=_resolve_reservoir(user_input)
            )

        opts = self._entry.options
        return self.async_show_form(
            step_id="init",
            data_schema=_reservoir_schema(
                opts, opts.get(CONF_RESERVOIR_PRESET, PRESET_UNKNOWN)
            ),
        )
