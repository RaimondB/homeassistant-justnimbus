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
    RESERVOIR_PRESETS,
)


class JustNimbusMqttConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for JustNimbus MQTT."""

    VERSION = 1

    async def async_step_user(self, user_input: dict | None = None) -> ConfigFlowResult:
        """Handle the initial step."""
        if user_input is not None:
            await self.async_set_unique_id(
                f"{user_input[CONF_HOST]}:{user_input[CONF_PORT]}"
                f":{user_input[CONF_TOPIC_PREFIX]}"
            )
            self._abort_if_unique_id_configured()
            return self.async_create_entry(
                title=user_input[CONF_DEVICE_NAME],
                data=user_input,
            )

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

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: ConfigEntry,
    ) -> JustNimbusMqttOptionsFlow:
        """Return the options flow for reservoir ("zak") dimensions."""
        return JustNimbusMqttOptionsFlow(config_entry)


# A serializable positive-mm/litre input. A bare callable here is NOT
# JSON-serializable for the frontend (voluptuous_serialize), which made the
# options form fail to load ("config flow could not be loaded"); selectors
# serialize cleanly.
def _dimension() -> NumberSelector:
    return NumberSelector(
        NumberSelectorConfig(min=1, step=1, mode=NumberSelectorMode.BOX)
    )


_PRESET_LABELS: dict[str, str] = {
    "standard_3000": "Standard 3,000 L (~2.6 x 2.6 x 0.5 m)",
    "standard_4500": "Standard 4,500 L (~3.5 x 2.6 x 0.5 m)",
    PRESET_CUSTOM: "Custom (use the values entered below)",
}


class JustNimbusMqttOptionsFlow(OptionsFlow):
    """Configure the physical reservoir ("zak") so fill % can be derived.

    Single step: a preset radio plus the four dimension boxes. Picking a
    standard bag uses its values; "custom" uses whatever is in the boxes
    (always visible, so there is never a hidden/blocked sub-step).
    """

    def __init__(self, config_entry: ConfigEntry) -> None:
        # Hold our own reference rather than relying on the framework's
        # self.config_entry, whose availability at form-build time varies
        # across HA versions (caused a 500 when loading the options flow).
        self._entry = config_entry

    async def async_step_init(self, user_input: dict | None = None) -> ConfigFlowResult:
        """Show preset + dimensions and store the resolved values."""
        if user_input is not None:
            preset = user_input[CONF_RESERVOIR_PRESET]
            if preset in RESERVOIR_PRESETS:
                resolved = dict(RESERVOIR_PRESETS[preset])
            else:
                # NumberSelector yields floats; store ints.
                resolved = {
                    CONF_RESERVOIR_LENGTH: int(user_input[CONF_RESERVOIR_LENGTH]),
                    CONF_RESERVOIR_WIDTH: int(user_input[CONF_RESERVOIR_WIDTH]),
                    CONF_RESERVOIR_HEIGHT: int(user_input[CONF_RESERVOIR_HEIGHT]),
                    CONF_RESERVOIR_VOLUME: int(user_input[CONF_RESERVOIR_VOLUME]),
                }
            resolved[CONF_RESERVOIR_PRESET] = preset
            return self.async_create_entry(title="", data=resolved)

        opts = self._entry.options

        def _default(key: str, fallback: int) -> int:
            return opts.get(key, fallback)

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_RESERVOIR_PRESET,
                        default=opts.get(CONF_RESERVOIR_PRESET, PRESET_CUSTOM),
                    ): SelectSelector(
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
                        default=_default(
                            CONF_RESERVOIR_LENGTH, DEFAULT_RESERVOIR_LENGTH
                        ),
                    ): _dimension(),
                    vol.Required(
                        CONF_RESERVOIR_WIDTH,
                        default=_default(CONF_RESERVOIR_WIDTH, DEFAULT_RESERVOIR_WIDTH),
                    ): _dimension(),
                    vol.Required(
                        CONF_RESERVOIR_HEIGHT,
                        default=_default(
                            CONF_RESERVOIR_HEIGHT, DEFAULT_RESERVOIR_HEIGHT
                        ),
                    ): _dimension(),
                    vol.Required(
                        CONF_RESERVOIR_VOLUME,
                        default=_default(
                            CONF_RESERVOIR_VOLUME, DEFAULT_RESERVOIR_VOLUME
                        ),
                    ): _dimension(),
                }
            ),
        )
