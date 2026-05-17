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
        return JustNimbusMqttOptionsFlow()


def _positive_int(value: object) -> int:
    """Coerce to an int and reject non-positive reservoir dimensions."""
    ivalue = int(value)  # type: ignore[arg-type]
    if ivalue <= 0:
        raise vol.Invalid("must be a positive number")
    return ivalue


class JustNimbusMqttOptionsFlow(OptionsFlow):
    """Configure the physical reservoir ("zak") so fill % can be derived.

    Step 1 picks a standard bag (or "custom"); step 2 shows the four
    dimensions prefilled from that choice so users rarely type anything.
    """

    def __init__(self) -> None:
        self._prefill: dict[str, int] = {}

    async def async_step_init(self, user_input: dict | None = None) -> ConfigFlowResult:
        """Choose a standard reservoir preset (or custom)."""
        if user_input is not None:
            preset = user_input[CONF_RESERVOIR_PRESET]
            self._prefill = RESERVOIR_PRESETS.get(preset, {})
            return await self.async_step_dimensions()

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_RESERVOIR_PRESET, default=PRESET_CUSTOM
                    ): SelectSelector(
                        SelectSelectorConfig(
                            options=[*RESERVOIR_PRESETS, PRESET_CUSTOM],
                            translation_key="reservoir_preset",
                            mode=SelectSelectorMode.LIST,
                        )
                    )
                }
            ),
        )

    async def async_step_dimensions(
        self, user_input: dict | None = None
    ) -> ConfigFlowResult:
        """Confirm or adjust the reservoir dimensions."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        opts = self.config_entry.options

        def _default(key: str, fallback: int) -> int:
            return self._prefill.get(key, opts.get(key, fallback))

        return self.async_show_form(
            step_id="dimensions",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_RESERVOIR_LENGTH,
                        default=_default(
                            CONF_RESERVOIR_LENGTH, DEFAULT_RESERVOIR_LENGTH
                        ),
                    ): _positive_int,
                    vol.Required(
                        CONF_RESERVOIR_WIDTH,
                        default=_default(CONF_RESERVOIR_WIDTH, DEFAULT_RESERVOIR_WIDTH),
                    ): _positive_int,
                    vol.Required(
                        CONF_RESERVOIR_HEIGHT,
                        default=_default(
                            CONF_RESERVOIR_HEIGHT, DEFAULT_RESERVOIR_HEIGHT
                        ),
                    ): _positive_int,
                    vol.Required(
                        CONF_RESERVOIR_VOLUME,
                        default=_default(
                            CONF_RESERVOIR_VOLUME, DEFAULT_RESERVOIR_VOLUME
                        ),
                    ): _positive_int,
                }
            ),
        )
