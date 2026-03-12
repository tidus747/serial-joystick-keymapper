# Serial Protocol

The firmware transmits a single ASCII line per report:

```text
T,<b1>,<b2>,<b3>,<b4>,<s1x>,<s1y>,<s2x>,<s2y>\n
```

Example:

```text
T,1,0,0,1,512,501,1012,8
```

## Fields

- `T`: frame type marker
- `b1..b4`: digital button states (`0` or `1`)
- `s1x`: stick 1 X raw ADC value (`0..1023`)
- `s1y`: stick 1 Y raw ADC value (`0..1023`)
- `s2x`: stick 2 X raw ADC value (`0..1023`)
- `s2y`: stick 2 Y raw ADC value (`0..1023`)

## Design Rationale

The protocol is intentionally human-readable:

- easy to inspect in the Arduino Serial Monitor
- easy to log and replay
- easy to parse in Python
- sufficient for the required throughput
