# Geeetech M1 Klipper setup and SWD flashing

This procedure is tested on one Geeetech M1 mainboard marked with an
STM32F103/APM32E103 VET6-class MCU and an `8.000` MHz crystal. Confirm that your
board matches before proceeding. The configuration is experimental and the
stock LCD is not supported.

## 1. Make a rollback backup first

Do not flash until you have made and verified a full 512 KiB readout. The
vendor `GTM32Source.bin` begins at offset `0x7000`; it does not contain the
complete bootloader and board state.

The labeled 2x3 mainboard header has these signals:

| Board label | SWD probe signal |
| --- | --- |
| `DIO` | `SWDIO` |
| `CLK` | `SWCLK` |
| `RST` | `NRST` |
| `GND` | `GND` |
| `3.3V` | `VTref` only |

Use the labels, not an assumed connector pin order. Power the mainboard from the
printer normally. Connect `3.3V` only as the probe's target-voltage reference;
do not use the probe to power the printer. Keep clear of mains and 24 V wiring.

The commands below use a CMSIS-DAP probe and OpenOCD. Substitute the correct
interface configuration if using an ST-Link or another supported probe.

```sh
openocd \
  -f interface/cmsis-dap.cfg \
  -f target/stm32f1x.cfg \
  -c "adapter speed 1000" \
  -c "init; reset halt; dump_image geeetech-m1-stock-full.bin 0x08000000 0x80000; shutdown"

sha256sum geeetech-m1-stock-full.bin
```

Make a second readout and compare it byte-for-byte before trusting the backup:

```sh
openocd \
  -f interface/cmsis-dap.cfg \
  -f target/stm32f1x.cfg \
  -c "adapter speed 1000" \
  -c "init; reset halt; dump_image geeetech-m1-stock-full.verify.bin 0x08000000 0x80000; shutdown"

cmp geeetech-m1-stock-full.bin geeetech-m1-stock-full.verify.bin
```

Keep the first dump, its SHA-256, and a copy on another device. Do not continue
unless `cmp` succeeds and both files are exactly 524288 bytes.

## 2. Build Klipper for the stock bootloader and USB-UART bridge

In a current Klipper checkout, run `make menuconfig` and select:

- Enable extra low-level configuration options
- Micro-controller architecture: `STMicroelectronics STM32`
- Processor model: `STM32F103`
- Bootloader offset: `28KiB bootloader`
- Clock reference: `8 MHz crystal`
- Communication interface: `Serial (on USART1 PA10/PA9)`

Then build:

```sh
make clean
make
```

The 28 KiB selection links the Klipper application for `0x08007000`, matching
the recovered stock application start. The serial connection runs through the
printer's CH340 bridge; the supplied config uses 250000 baud.

## 3. Flash only the application region over SWD

Stop the Klipper service on the host if it is already running. With the target
powered and the SWD probe connected, flash the raw binary at the application
address:

```sh
openocd \
  -f interface/cmsis-dap.cfg \
  -f target/stm32f1x.cfg \
  -c "adapter speed 1000" \
  -c "init; reset halt; flash write_image erase out/klipper.bin 0x08007000 bin; verify_image out/klipper.bin 0x08007000 bin; reset run; shutdown"
```

Run this from the Klipper checkout, or replace `out/klipper.bin` with its full
path. Do not issue a mass-erase command: the lower `0x7000` bytes contain the
stock bootloader that this workflow intentionally preserves.

## 4. Install and personalize the configuration

Copy both the sample and macro directory into the Klipper configuration
directory, then rename the sample:

```sh
cp printer.cfg.sample ~/printer_data/config/printer.cfg
cp -r macros ~/printer_data/config/
```

Edit `printer.cfg` and replace both placeholders:

- Find the CH340 path with `ls /dev/serial/by-id/` and set `[mcu] serial`.
- Set `[virtual_sdcard] path` to the host's actual G-code directory.

The sample deliberately contains no saved bed mesh or machine-specific probe
offset. On first connection, verify every input and output before moving or
heating:

1. Confirm temperatures are plausible at room temperature.
2. Run `QUERY_ENDSTOPS` and manually actuate each endstop.
3. Test each axis at low speed and be ready to cut power.
4. Verify heater temperature rises on the matching sensor and stop immediately
   if it does not.
5. Verify the load-cell probe triggers reliably, then run `PROBE_CALIBRATE` and
   `SAVE_CONFIG`.
6. Run the normal Klipper PID and motion calibrations for your own machine.
7. Test the wipe and purge locations cautiously before starting a print.

The sample homes against physical endstops and leaves the recovered X/Y
TMC2209 UART sections disabled. Stock Marlin confirmed communication with both
drivers, but no retained evidence confirms the UART mapping under Klipper. It
is not required for homing or normal standalone driver operation.

The supplied `START_PRINT` performs a hot wipe, cool load-cell mesh, reheat,
and purge. The wipe height is the recovered vendor value of 0.5 mm; the default
stroke count is reduced from 12 to 6. The purge speed is reduced from 6.5 to
3 mm/s to avoid Klipper's maximum volumetric extrusion limit.

## 5. Roll back to the captured stock image

Use only your own verified full-flash dump. With the printer halted and attached
over SWD:

```sh
openocd \
  -f interface/cmsis-dap.cfg \
  -f target/stm32f1x.cfg \
  -c "adapter speed 1000" \
  -c "init; reset halt; flash write_image erase geeetech-m1-stock-full.bin 0x08000000 bin; verify_image geeetech-m1-stock-full.bin 0x08000000 bin; reset run; shutdown"
```

Verify the backup's recorded SHA-256 again before restoring it. A vendor
`GTM32Source.bin` alone is not a substitute for this full image.
