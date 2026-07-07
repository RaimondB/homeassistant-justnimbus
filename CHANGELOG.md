# Changelog

## [0.2.0](https://github.com/RaimondB/homeassistant-justnimbus/compare/homeassistant-justnimbus-v0.1.0...homeassistant-justnimbus-v0.2.0) (2026-06-24)


### Features

* default water-flow sensors to 0 (not unknown) ([3223755](https://github.com/RaimondB/homeassistant-justnimbus/commit/32237551a11daefb3fa1367eb76bb1d3378b4bfb))
* default water-flow sensors to 0 instead of unknown ([fe0fbac](https://github.com/RaimondB/homeassistant-justnimbus/commit/fe0fbac88197bedd3fab404ae516878a77521ed4))
* initial JustNimbus MQTT integration ([7929467](https://github.com/RaimondB/homeassistant-justnimbus/commit/7929467a920cac16c701c3c761ca81c6c61f5c95))
* map remaining device topics (pump stats, system, actuators) ([48d5cda](https://github.com/RaimondB/homeassistant-justnimbus/commit/48d5cdafbcaf4e6a35f0335d54d4508458b58951))
* map remaining device topics (pump stats, system, actuators) ([027f319](https://github.com/RaimondB/homeassistant-justnimbus/commit/027f319050802acf143dd89eb357b4e133d32eda))
* reservoir fill % + full indicator with preset-prefilled options ([145a188](https://github.com/RaimondB/homeassistant-justnimbus/commit/145a1887412b21016c28b9ca06b94757a66d1ad8))
* reservoir fill % + full indicator with preset-prefilled options ([4166272](https://github.com/RaimondB/homeassistant-justnimbus/commit/4166272ae5a6c349ccdbf3ecf892674489a393f8))
* reservoir in add-device flow + "Unknown" option ([5d58c4d](https://github.com/RaimondB/homeassistant-justnimbus/commit/5d58c4dccc5f81163f3366180e63fc6ac548207f))
* reservoir in add-device flow + Unknown option ([091b31a](https://github.com/RaimondB/homeassistant-justnimbus/commit/091b31ac65a15c0ab32d4a33f549ef9427c737e8))
* restore state across restart + clean Sensor/Diagnostic split ([10cbbaf](https://github.com/RaimondB/homeassistant-justnimbus/commit/10cbbafcb91457e4f37d50ad6f42c3287d7d4ed1))
* restore state across restart + clean Sensor/Diagnostic split ([aafda63](https://github.com/RaimondB/homeassistant-justnimbus/commit/aafda63668fb985313b38a4109100eb60be9c307))
* **scripts:** add standalone MQTT probe for out-of-HASS device testing ([c07d4b6](https://github.com/RaimondB/homeassistant-justnimbus/commit/c07d4b620a15a57dfc54f7cbaa0e9a53433f7cc3))
* **sensor:** throttle fast MEASUREMENT sensors to cut stored data ([#23](https://github.com/RaimondB/homeassistant-justnimbus/issues/23)) ([372924b](https://github.com/RaimondB/homeassistant-justnimbus/commit/372924b349ffd7abc3f0ff8d498647af8060ec81))
* switch to direct aiomqtt with configurable MQTT host/port ([f79b1cf](https://github.com/RaimondB/homeassistant-justnimbus/commit/f79b1cf9c2ccc183cd34beacdbd8ac3692d53ddb))
* switch to direct aiomqtt with configurable MQTT host/port ([0f258c3](https://github.com/RaimondB/homeassistant-justnimbus/commit/0f258c37eb2357be6a078c9abcb59dc422ffb91f))


### Bug Fixes

* add translations/en.json so entity names render in the UI ([5bd1027](https://github.com/RaimondB/homeassistant-justnimbus/commit/5bd1027075fcec1d96e093a1f7174db5bd9059d4))
* correct device/state class for water totals and reservoir volume ([2c17986](https://github.com/RaimondB/homeassistant-justnimbus/commit/2c1798651c621cf8f589aec163f998da49227bfd))
* derive entity_ids from the stable key, not the device_class ([c2543fa](https://github.com/RaimondB/homeassistant-justnimbus/commit/c2543fa7b0d44d778546d43d152adcbed8fe68eb))
* deterministic, readable entity_ids (no device_class number postfixes) ([6994f53](https://github.com/RaimondB/homeassistant-justnimbus/commit/6994f53ee0548a6750db950e1c86aba6452f4db7))
* entity names, water dashboard classification + standalone MQTT probe ([774479b](https://github.com/RaimondB/homeassistant-justnimbus/commit/774479b9c985f8574a8ddbe9c47f91062a2f1412))
* hold own config_entry ref in options flow (500 on load) ([a362e58](https://github.com/RaimondB/homeassistant-justnimbus/commit/a362e58e42ba1149eff725aa827b9344d9ec9d66))
* move selector translations to top level for hassfest ([f7f1dc6](https://github.com/RaimondB/homeassistant-justnimbus/commit/f7f1dc66e15589f8ff655be5b777605109a02d84))
* options flow 500 on load (hold own config_entry ref) ([a14a9b8](https://github.com/RaimondB/homeassistant-justnimbus/commit/a14a9b82a422d16c106a56cbb0d4546c41f88028))
* options form schema must be frontend-serializable (500 on load) ([6832a27](https://github.com/RaimondB/homeassistant-justnimbus/commit/6832a274110e7d73ad6f8aaa14f722453b323b53))
* options form schema must be frontend-serializable (the real 500) ([0a45fb7](https://github.com/RaimondB/homeassistant-justnimbus/commit/0a45fb7f81dd511f9fb12f1eb4785b618b7384e0))
* **sensor:** ignore non-finite (nan/inf) stat payloads ([#22](https://github.com/RaimondB/homeassistant-justnimbus/issues/22)) ([832668a](https://github.com/RaimondB/homeassistant-justnimbus/commit/832668ad197cab98d3948f54a35fe9640e0af38a))
* single-step options flow (extra-keys error + missing custom boxes) ([92aeccd](https://github.com/RaimondB/homeassistant-justnimbus/commit/92aeccd9ae0ed87539eda1d0df527b600f5ae8c7))
* single-step options flow (fixes 'extra keys' + missing custom boxes) ([a8959ad](https://github.com/RaimondB/homeassistant-justnimbus/commit/a8959adfee2b554b34a7065c799ec31b30039022))
* **tests:** add autouse MQTT client patch to prevent teardown hangs ([3835caa](https://github.com/RaimondB/homeassistant-justnimbus/commit/3835caabd025390ccc8bb470159382dd373c5445))
