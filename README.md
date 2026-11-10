## FPGA LED demo separated from ASIC

The Knight Rider/KITT PWM fade experiment now lives in the [portable FPGA KITT example](https://github.com/jeffadickson/fpga-starwars-kv260/tree/feature/standalone-kitt-pwm/examples/kitt-scanner). The ASIC no longer instantiates the LED scanner or reserves its output diagnostic mode. TinyTMR continues to provide triplicated registers, protected voters, controlled fault injection, upset counters, snapshot readback, and the wired-output digital comparison.

# TinyTMR

An experimental **8-bit triple-modular-redundant output register** for [Tiny Tapeout](https://tinytapeout.com/). Three independent register banks feed an output majority voter and three separately instantiated feedback voters (default build). Faults can be injected into any storage bit; a scrub command repairs all three copies using the majority value. The design provides live disagreement indication and small diagnostic telemetry.

**40 MHz candidate, 24 October 2026:** local extracted setup/hold and maximum-slew checks pass at all configured signoff corners; Magic/KLayout DRC and LVS pass. RTL and gate-level tests pass 9/9 and local Tiny Tapeout precheck passes 15/15. See [signoff evidence](reports/signoff/20261024-40mhz/README.md) and the [macro timing contract](docs/timing-contract.md). Hosted checks and portal submission remain separate steps. This experimental design is not radiation-qualified; the final pad, output voter, and shared CDC/data/reset paths are not triplicated.

## ICMOS product datasheet

[**ICMOS TinyTMR-8 — Preliminary Datasheet, Rev C**](docs/ICMOS_TinyTMR-8_Datasheet.md) covers interface, command encoding, CDC timing assumptions, fault coverage, telemetry, qualification limits and the 40 MHz verification baseline.

## Reproduce the forty MHz candidate

The repository contains the exact RTL, Tiny Tapeout metadata, timing contract, cocotb testbench and signoff evidence used for the 40 MHz candidate. The hosted workflows rebuild GDS, run Tiny Tapeout precheck, run gate-level simulation, run RTL simulation and build the documentation. Hosted checks and portal submission remain separate steps.

The GDS render is retained as a workflow artifact. No Tiny Tapeout revision has been submitted from this repository.

## CDC-protected pin interface

| Signal | Direction | Meaning |
|---|---|---|
| `ui_in[7:0]` | input | bundled command data; held stable while request active |
| `uo_out[7:0]` | output | voted result (or diagnostics) |
| `uio[0]` | input | asynchronous **REQ**, four-phase level handshake |
| `uio[1]` | input | command kind: 1=LOAD, 0=INJECT/SCRUB |
| `uio[3:2]` | input | bank select: 0/1/2 inject, 3 scrub/voter SET |
| `uio[6:4]` | input | selected bit (inject) / fault selector (scrub) |
| `uio[7]` | output | **ACK**, asserted after exactly one command execution |

`uio_oe = 8'h80`. A mismatch flag is exposed via diagnostic status, not the ACK pin.

**Transaction:** drive command/data, assert REQ, hold all command/data until ACK high, deassert REQ, wait until ACK low, then begin another transaction. See [CDC protocol](docs/cdc.md). External controllers using another clock domain must synchronize ACK on their side.

- LOAD: command kind=1; all replicas load `ui_in`, telemetry clears.
- INJECT: command kind=0, bank=0..2; toggles chosen bit exactly once per handshake.
- SCRUB: command kind=0, bank=3, selector=0; all replicas load independent majority voters.
- Voter SET experiment: bank=3, selector=1..3 to target feedback voter A/B/C, with bit from `ui_in[2:0]`.
- DIAGNOSTIC READ: when request is idle, set bank=3 and index=7 (e.g. `uio_in=8'h7c`). `uo_out={mismatch_cycles[3:0],last_outliers[2:0],sticky}`. Counter represents sampled mismatching clock cycles, not unique events.

To test with cocotb and Icarus Verilog:

```sh
python -m pip install -r test/requirements.txt
make -C test
make -C test TINYTMR_SHARED_FEEDBACK=1
```

## Triplicated synchronous controllers

Three separately instantiated `tinytmr_controller` modules now maintain independent transaction-completion state and command decoding. Their completion states feed a 2-of-3 ACK voter. Command decoding, enable generation and per-bank feedback are lane-local; the clock, reset, REQ synchronizer and input command/data bus remain shared. A single controller-state upset can cause duplicate execution during a held REQ: exactly-once semantics apply only without faults. See [architecture and fault-containment analysis](docs/architecture.md).

For a deterministic **wrong-command** experiment, send kind=0, bank=3, selector=4 (controller A), 5 (B), or 6 (C); `ui_in[2:0]` selects the bit to toggle in the affected replica while the other two replicas scrub. The voted output remains correct for a single such fault, and a subsequent normal scrub restores agreement. This fault-injection mode does not model physical strike properties.

## Protected feedback voters and intentional voter fault injection

The default build uses three independent feedback voter modules (A/B/C), each
feeding *only its corresponding register*. An optional comparative build with
`-DTINYTMR_SHARED_FEEDBACK` uses a single common voter for all three feedback
paths. The separately instantiated output voter remains outside the feedback
loop; its external output path is not radiation-hardened.

A controlled voter transient is now a single handshake command: set bank=3,
selector=1 (A), 2 (B), or 3 (C), kind=0, with `ui_in[2:0]` holding the
bit number. Independent feedback contains a single voter error to one
replica; the shared-feedback demonstration writes the erroneous bit into all
three. For example `uio_in[6:1]=0x1c` with `ui_in=5`, followed by raising
REQ, targets voter A bit 5.

The input interface uses a single shared two-FF REQ synchronizer and a four-phase ACK
handshake; see [docs/cdc.md](docs/cdc.md) for important timing and metastability
limitations. There is no CDC between the three internal replica banks.

The physical implementation must prove that the three voter module instances
have survived synthesis and are physically separated. RTL attributes alone
are not evidence of that; no PPA/tapeout sign-off is claimed.

## Share physical-design reports for review

After LibreLane hardening completes on Ubuntu/WSL, publish a **curated, tracked** snapshot of reports and physical evidence:

```bash
cd ~/TinyTMR
git pull origin main
bash scripts/publish-reports.sh
```

This collects up to 18 MB of run reports and metrics, plus selected final Verilog netlists and DEF placement files, into `reports/latest/`. It records a manifest with source commit, UTC capture time, SHA-256 checksums, and skipped oversized items. The command stages **only** `reports/latest/`, commits and pushes it to the current branch; inspect the contents before publishing if your logs may contain confidential information. The collector does not upload the raw `runs/` tree, PDK libraries, GDS, ODB, SPEF, or large/unsupported binary files. The original run remains available locally, and each Git commit preserves a historical snapshot.

To collect without pushing, run `python3 scripts/collect-reports.py` instead. Check the snapshot with `git status --short` and `git diff --stat -- reports/latest` before committing.

This is engineering-review evidence only; missing KLayout DRC data, max-slew warnings, and synchronizer geometry still require explicit examination before signoff.

## Physical layout and shuttle submission

See [ICMOS physical-lane replication strategy and Tiny Tapeout submission guide](docs/physical-layout-and-submission.md) for the current hardened macro measurements, the proposed harden-one-lane/replicate-three-times physical experiment, and the TTSKY26d portal steps. A local successful P&R build does not replace the GDS/Docs GitHub checks or a submitted shuttle revision.

## Overnight timing sweep: ICMOS C# reports

The overnight sweep uses **C#/.NET 10** for all metrics extraction, HTML generation and evidence packaging. The reporter builds XML documentation from C# `///` comments. Bash remains only the launcher for the external LibreLane and Git commands.

```bash
# Prerequisite: .NET 10 SDK installed inside Ubuntu WSL, and normal LibreLane setup.
cd ~/TinyTMR
git pull origin main
dotnet --list-sdks
# Optional: keep running after terminal disconnects:
nohup bash scripts/timing-sweep.sh > overnight-sweep.log 2>&1 < /dev/null &
echo "PID: $!"
tail -f overnight-sweep.log
```

Default overnight matrix: **16 layouts**, periods 20, 18, 15, 12, 10, 8, 6 and 5 ns at 60% placement target density, plus 20/15/10/8 ns at 50% and 70%. Each layout runs synthesis, placement, CTS, routing and signoff checks through the Tiny Tapeout hardening flow. Each case retains its own raw local run; source config is restored on exit.

After **every completed case**, including a failed hardening case, the runner refreshes `reports/sweeps/<UTC timestamp>/index.html`, `summary.csv`, `summary.json`, and bounded evidence, commits and attempts to push. It retries GitHub pushes three times and continues the sweep if GitHub is unavailable; a final push catches up any locally committed results. `SWEEP_NO_PUSH=1` disables publishing. If `dotnet build` fails, the preflight stops before consuming hours of machine time. The HTML compares requested period/frequency, area, utilization, reported setup/hold metrics, DRC/LVS, and warning summaries. Missing metrics are marked **n/r**, not silently treated as passing.

**GitHub publication requires** working Git authentication and `user.name`/`user.email`. For a manual dry run of the C# reporter: `dotnet run --project tools/ICMOS.SweepReport -c Release -- physical-sweeps/<timestamp> reports/sweeps/<timestamp>`.

**Cost note:** Tiny Tapeout's SKY130 price varies with customer category, early-bird availability and development boards. A published single-tile example was €185 including shipping (August 2026); current checkout is authoritative: https://app.tinytapeout.com/calculator .

## GitHub CI and timing sweep

The `gds`, `docs`, and `test` workflows are based on the official `ttsky26d` SKY130 template. They run on push and manually from GitHub Actions. **Workflow presence does not establish passing status**; inspect each run and address failures before submission.

The first hardening run passed reported 20 ns (50 MHz target) setup and hold constraints, but maximum operating frequency is **not measured**. Sweep clock targets and placement densities locally with:

```bash
cd ~/TinyTMR
git pull origin main
bash scripts/timing-sweep.sh
# Or choose a shorter experiment:
SWEEP_CASES="20:60 15:60 10:60 10:50 10:70" bash scripts/timing-sweep.sh
```

Each experiment captures the complete run and a build log under `physical-sweeps/<UTC timestamp>/`, plus `summary.csv`; the last run is restored to `runs/wokwi` for inspection. Experiments preserve and restore the checked-in `src/config.json`. The sweep folder is excluded from Git; publish selected reports separately, not PDK or raw GDS datasets.

**Do not interpret passing 8 ns timing as an 8 ns Fmax signoff.** Extract per-corner routed worst slack, critical path endpoints, missing constraints, and maximum-slew violations before assigning a performance rating. See [ICMOS datasheet Rev B](docs/ICMOS_TinyTMR-8_Datasheet.md).

## WSL2 ASIC hardening, placement and timing

The project now includes reproducible **Ubuntu WSL2** setup and build scripts; see [docs/wsl-physical-design.md](docs/wsl-physical-design.md).

```bash
bash scripts/setup-wsl.sh          # requires running Docker, Python >= 3.11
bash scripts/build-wsl.sh all      # cocotb RTL -> LibreLane layout/STA -> gate tests -> reports
bash scripts/build-wsl.sh gui      # inspect placed/routed cells in OpenROAD
```

**Important:** these scripts have not yet been executed against a provisioned WSL/Docker/PDK installation in this environment. Physical FF1/FF2 proximity and shuttle-pad proximity are inspection/constraint tasks, not automatic properties of the RTL. The Tiny Tapeout build produces a hardened user macro; the shuttle provider integrates the full pad ring and shared I/O multiplexer.

## PowerShell 7 build interface (Ubuntu WSL)

PowerShell 7.4+ is supported as an interactive wrapper around the established Bash/LibreLane flow. The PowerShell wrapper requires Ubuntu WSL, the Tiny Tapeout setup, and Docker Desktop WSL integration; it does **not** replace the upstream Python-based EDA tooling. Install `pwsh` in WSL and run:

```powershell
cd ~/TinyTMR
pwsh -NoProfile -File scripts/build.ps1 Test
pwsh -NoProfile -File scripts/build.ps1 Harden
pwsh -NoProfile -File scripts/build.ps1 Gate
pwsh -NoProfile -File scripts/build.ps1 Report
# Full pipeline: Test + Harden + Gate + Report
pwsh -NoProfile -File scripts/build.ps1 Build
# Explicitly commit and push curated reports to the checked-out branch:
pwsh -NoProfile -File scripts/build.ps1 Publish
```

Use `-DryRun` to inspect the exact Bash command without running it, or `-LogDirectory ~/tinytmr-logs` to override the default local log path (`~/.local/state/tinytmr/builds`). Each actual run writes a console `.log` and JSON-lines `.jsonl` event file with UTC timestamps, command arguments, duration, and exit code. Native Bash failures propagate as PowerShell errors and nonzero process exits; **Publish is never automatic**. The report publisher still invokes the existing curated collector, which uses Python internally. Do not run two hardening commands concurrently in the same checkout, because both use `runs/wokwi`.

