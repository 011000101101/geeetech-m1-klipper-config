# Experimental Klipper configuration for the Geeetech M1

This repository contains an independently reverse-engineered, community Klipper
configuration for the Geeetech M1 mini 3D printer. It has completed real prints
on one stock machine and is useful for further testing, but it remains
**experimental**. Hardware revisions may differ, and a wrong pin or heater
setting can damage a printer or create a fire hazard.

This project is not affiliated with, endorsed by, or supported by the Klipper
project or Geeetech. Do not request support for this configuration from the
Klipper maintainers.

## How this port was developed

This port combines several forms of reverse engineering and validation:

- AI-assisted analysis of the stock firmware image, including strings,
  peripheral data structures, pin tables, and candidate code paths
- Live serial and SWD probing of the stock firmware, including register
  inspection and reversible input/output correlation
- Manual continuity tracing of mainboard and load-cell daughterboard signals
- Incremental hardware tests followed by calibration and complete test prints

AI assistance was used to accelerate firmware analysis and organize competing
hypotheses; it was not treated as evidence by itself. Published pin mappings
and behavior are based on recovered binary/runtime evidence, physical tracing,
or tests on the printer. Remaining uncertainty is called out explicitly.

## Tested status

The following have been exercised on the author's printer:

- Cartesian motion, homing, heaters, thermistors, and fans
- X/Y/Z endstops and filament runout sensing
- Load-cell probing with daughterboard zeroing
- Bed meshing and complete prints
- Start, wipe, purge, pause/resume, cancel, and end-print macros

The stock parallel TFT and its rotary controls are not supported. Calibration
values are not portable between printers; in particular, do not reuse another
machine's probe Z offset, bed mesh, PID results, pressure advance, or input
shaper results without checking them.

X and Y use physical endstops. Stock Marlin reported successful communication
with both TMC2209 drivers, and the shared UART bus and addresses were recovered
from that firmware. No retained evidence confirms the interface under Klipper,
so it is disabled in the sample. UART is optional here and is not used for
homing.

## Before installing

Secure a verified full-flash SWD backup first. The vendor `GTM32Source.bin` is
only an application image and is not a complete rollback backup. The tested
Klipper build preserves the stock 28 KiB bootloader by placing Klipper at
`0x08007000`, but the initial installation still requires SWD.

Read [the complete setup and rollback guide](docs/setup.md) before connecting a
probe or writing flash.

## Configuration files

- `printer.cfg.sample` is the reusable, tested hardware configuration. Copy it
  to `printer.cfg`, replace the serial and virtual-SD placeholders, and perform
  the required calibrations.
- `macros/m1_startup_macros.cfg` contains the tested print lifecycle, load-cell,
  wipe, and purge macros. Keep the same relative path or adjust the include.

For OrcaSlicer, the intended start and end G-code is:

```gcode
START_PRINT BED_TEMP=[first_layer_bed_temperature] EXTRUDER_TEMP=[first_layer_temperature]
```

```gcode
END_PRINT
```

`END_PRINT` parks at maximum Y so the bed moves forward and presents the
finished print.

## License

The original configuration, macros, and documentation in this repository are
available under the [MIT License](LICENSE). Klipper is a separate project,
distributed under GPL-3.0; it is not bundled here and must be obtained from its
own project.
