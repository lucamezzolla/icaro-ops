# Aircraft market filters restore

Restores the Buy new aircraft filter bar and makes the Engine filter use only `aircraft_models.engine_type` values.

Supported engine values:

- TURBOFAN
- TURBOPROP
- PISTON
- TURBOSHAFT
- SUPERSONIC

The generic `JET` value is intentionally removed because it is not present in the database.
