# Aircraft market engine filter exact DB values

This patch makes the Buy new aircraft engine filter use `aircraft_models.engine_type` as the only source of truth.

The filter no longer renders a generic `JET` option. It uses exact DB values:

- TURBOFAN
- TURBOPROP
- PISTON
- TURBOSHAFT
- SUPERSONIC

The catalog endpoint returns `engine_type`, and market table rows receive `data-engine-type` attributes.
