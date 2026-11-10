# TinyTMR Tapeout

An 8-bit triple-modular-redundant register and I/O demonstrator prepared as a **Tiny Tapeout TTSKY26d** submission candidate.

TinyTMR stores each logical bit in three independent register banks and uses majority voting for the output and feedback paths. It supports controlled fault injection, scrubbing, disagreement telemetry, and a four-phase request/acknowledge interface.

> This repository is an engineering submission snapshot. It is not radiation-qualified, and creating it does not submit a Tiny Tapeout revision or purchase a shuttle.

## Candidate status

The checked-in candidate is the verified **40 MHz** SKY130 configuration:

- Tiny Tapeout: TTSKY26d
- Macro size: 1 × 1 tile
- Top module: `tt_um_jeffadickson_tinytmr`
- Language: Verilog
- Clock target: 40 MHz (`25 ns`)
- RTL and gate-level signoff evidence: 9/9 tests
- Local Tiny Tapeout precheck evidence: 15/15 checks
- Timing, slew, DRC and LVS evidence: see [`reports/signoff/20261024-40mhz/`](reports/signoff/20261024-40mhz/)

## Interface

| Signal | Direction | Description |
| --- | --- | --- |
| `ui_in[7:0]` | input | Command and payload data |
| `uo_out[7:0]` | output | Majority-voted data or diagnostic status |
| `uio[0]` | input | Four-phase request (`REQ`) |
| `uio[1]` | input | Command kind: `1` = load, `0` = inject/scrub |
| `uio[3:2]` | input | Replica bank selection |
| `uio[6:4]` | input | Bit or diagnostic selector |
| `uio[7]` | output | Acknowledgement (`ACK`) |

The external transaction protocol is:

1. Drive the command and payload.
2. Assert `REQ` and hold all inputs stable.
3. Wait for `ACK` to assert.
4. Deassert `REQ`.
5. Wait for `ACK` to deassert before starting the next transaction.

See [`docs/cdc.md`](docs/cdc.md) for the complete protocol and clock-domain limitations.

## Commands

- **LOAD** — load all three replica banks from `ui_in`.
- **INJECT** — toggle a selected bit in one replica bank.
- **SCRUB** — repair all replicas from their independent majority values.
- **VOTER SET** — inject a controlled fault into one feedback voter for experiments.
- **DIAGNOSTIC READ** — read disagreement and outlier telemetry while idle.

Fault injection is controlled synchronous logic; it does not model a physical radiation strike.

## Run the RTL simulation

From a Linux environment with Icarus Verilog and Python available:

```sh
python -m pip install -r test/requirements.txt
make -C test
```

To exercise the comparative shared-feedback build:

```sh
make -C test TINYTMR_SHARED_FEEDBACK=1
```

The testbench and dependencies are in [`test/`](test/).

## Repository layout

```text
src/project.v                         RTL implementation
src/config.json                       Tiny Tapeout hardening configuration
src/timing.sdc                        40 MHz timing contract
info.yaml                             Tiny Tapeout project metadata and pinout
test/                                 cocotb and Icarus Verilog tests
docs/                                 Architecture, CDC, timing and submission notes
reports/signoff/20261024-40mhz/      Verified candidate evidence
```

## Provenance and scope

This is a clean, independent-history snapshot of [`jeffadickson/TinyTMR`](https://github.com/jeffadickson/TinyTMR) at verified commit [`cc4f5272020733c8f3eff60ede09454bd3a1dcb1`](https://github.com/jeffadickson/TinyTMR/commit/cc4f5272020733c8f3eff60ede09454bd3a1dcb1).

The snapshot keeps the fabrication inputs, required tests, relevant documentation, and 40 MHz signoff evidence. Sweep reports, unrelated experiments, historical repository history, and nonessential engineering tools are intentionally excluded. See [`SUBMISSION-SNAPSHOT.md`](SUBMISSION-SNAPSHOT.md) for the inclusion boundary.

## License

Released under the [MIT License](LICENSE).
