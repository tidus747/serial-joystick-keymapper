# Calibration Notes

Each axis stores:

- `raw_min`
- `raw_center`
- `raw_max`
- `deadzone`
- `invert`
- `sensitivity`
- `expo`
- `negative_threshold`
- `positive_threshold`
- `hysteresis`

## Recommended Procedure

1. Connect the Arduino and start the desktop app.
2. Keep the stick at rest and capture the center.
3. Move the stick to the mechanical extremes.
4. Capture the practical minimum and maximum values.
5. Increase deadzone until idle noise disappears.
6. If the movement direction is wrong, enable inversion.
7. For keyboard-threshold mode, tune thresholds and hysteresis.
8. Save the result as a profile JSON file.
