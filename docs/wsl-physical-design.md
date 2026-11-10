# Ubuntu WSL2 build, timing, and CDC physical implementation

## Supported target and provenance

Target for this script: **SKY130 Tiny Tapeout** with the current project `info.yaml` and standard `tt-support-tools`/LibreLane flow. Always confirm shuttle-specific versions and configuration before submission. The template's `src/config.json` (generated in the local flow) governs clock, CTS, tile outline, routing and CTS; don't casually replace its floorplan/PDN settings. Official flow: https://tinytapeout.com/guides/local-hardening/ . Current guide shows LibreLane 3.0.3 as of October 2026, but pins may change.

## Prerequisites

- Windows 11 + WSL2 Ubuntu 24.04 recommended (Python >= 3.11), and Docker Desktop configured for WSL integration **or** working native Docker Engine.
- Place repo in a Linux path such as `~/src/TinyTMR`, not `/mnt/c`.
- Make sure `docker info` works from Ubuntu before running setup.

```bash
bash scripts/setup-wsl.sh
bash scripts/build-wsl.sh all
bash scripts/build-wsl.sh gui    # OpenROAD GUI; requires GUI/display support
```

Individual stages: `rtl`, `harden`, `gate`, `reports`.

Note: gate-level cocotb simulation depends on the PDK being enabled; if PDK cell models are missing, follow the official guide's `ciel ls` and `ciel enable <installed-hash>` instructions. The scripts do not silently enable a different PDK revision.

## Stages and signoff scope

1. **RTL**: Icarus + cocotb. Ensure both feedback architectures and controller-fault tests pass; `TINYTMR_SHARED_FEEDBACK=1` can be used with `make -C test` separately.
2. **Synthesis**: inspect inferred flops, whether the three per-lane controllers/feedback voters remain independent, and optimizations/shared nets. Unique instance names alone do not establish physical independence.
3. **Floorplan/placement**: inspect tile-edge pin locations (`ui_in`, `uio_in`, `clk`, `rst_n`) and two-FF synchronizer cells. Inspect whether the FF1-to-FF2 connection remains short and has no intervening combinational fanout. Check clock-tree and reset distribution.
4. **Routing/parasitics/STA**: inspect setup and hold slack (WNS/TNS), unconstrained paths, interstage FF1/Q -> FF2/D max and min timing and wirelength, clock skew, fanout, and DRC/LVS results. Use routed parasitics if available. Check that no false-path exception unintentionally masks the FF1->FF2 timing path.
5. **Macro artifacts**: inspect final DEF/ODB (coordinates), SPEF, gate netlist, GDS/LEF. The TT integration team then connects the tile's boundary pins to shared mux and actual I/O pads on the shuttle die.

## CDC implementation rules and placement

- `REQ` is asynchronous to `clk`, so its **first-stage D input is asynchronous**. Do not place ordinary synchronous setup/hold requirements on external REQ as if it were clocked by `clk`.
- **FF1/Q -> FF2/D remains timed** for setup and hold; maximize the available metastability settling interval by keeping the stages near each other. Apply any CDC-specific constraints only to the asynchronous input path, never `FF1 -> FF2`.
- Neither RTL attributes nor standard automatic placement guarantee proximity, and a general FF-to-FF short route is not equivalent to an MTBF guarantee. Establish identifiable instance/cell names in the *mapped* netlist. Inspect coordinates/routed path in DEF/ODB and timing reports, then introduce flow-version-compatible placement constraints or custom OpenROAD steps if needed. Don't use hard-coded coordinates from a different floorplan; TT may change tile pin positions.
- FF1 Q should drive **only FF2 D**. Preserve the synchronizer flops through synthesis and physical optimizations; avoid scan-style or retiming modifications unless verified.
- Put FF1 reasonably near the **tile input pin**, not necessarily the package pad. The package pad's location and multiplexing are controlled by the shuttle top-level build, not by the user macro. FF1/FF2 adjacency is usually more important than proximity to the tile pin.
- `rst_n` asynchronous assertion / synchronized deassertion must also be assessed for reset-domain crossing. Ordinary two-FF synchronizers are **not radiation hard**; residual SET/SEU and common-mode failures must be documented.
- Handshake bundles (`ui_in`, command pins) must be held stable through REQ acceptance per `docs/cdc.md`; no independent bitwise bus synchronizers. An asynchronous sender must synchronize returned ACK on its side.
- The synchronizer must be assessed using *technology-specific* metastability parameters for any quantitative MTBF claim; ordinary STA by itself does not measure metastability probability.

## Functional and silicon checks before claiming readiness

- All cocotb tests pass in RTL and where practical at gate level.
- No unexpected inferred latches and no loss of TMR independence during synthesis.
- Every synchronous setup and hold path passes at specified operating conditions; clock/unconstrained-path reports are reviewed.
- Measured post-route FF1-to-FF2 timing and coordinates recorded for design review; no async-source fanout into control beyond FF1.
- Tile routing/DRC/LVS succeed; the complete shuttle's external I/O timing and pad frame are **not** independently signed off by this project.
- The current 1x1 tile fits by **actual** synthesis/placement metrics, not assumptions from RTL source count.
