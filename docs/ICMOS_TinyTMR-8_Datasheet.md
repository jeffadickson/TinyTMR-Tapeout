# ICMOS | TinyTMR-8
## Eight-Bit Triple Modular Redundancy I/O Demonstrator

**PRELIMINARY DATASHEET — ENGINEERING EVALUATION ONLY**  
**ICMOS-TMR8-DS-001 | Revision C | 24 October 2026**

### Product overview
TinyTMR-8 is an experimental eight-bit triple-modular-redundancy (TMR) storage and I/O demonstrator for a Tiny Tapeout SKY130 user macro. Three banks of eight flip-flops hold the logical value. Three separately instantiated majority voters feed independent repair paths, and a fourth majority voter drives the output. Three separate synchronous command controllers sit behind one shared request synchronizer. A four-phase request/acknowledge bundled-data protocol supports loads, deliberate fault injection, scrubbing, and readback.

**Qualification restriction:** No fabricated, packaged, or radiation-characterized part is claimed. Silicon electrical limits, radiation cross section, TID, SEL immunity, metastability MTBF, power, and maximum frequency are not established. Mapped replica/voter preservation and placement have been audited; geometric distances do not establish radiation independence.

### Key features
- 8-bit logical register implemented by 24 physical storage flip-flops in three banks.
- Three feedback majority-voter instances plus one nonredundant output voter.
- Three independently instantiated synchronous command controllers; ACK uses 2-of-3 completion voting.
- Two-flop REQ synchronizer; bundled-data four-phase handshake.
- Storage-bit SEU injection, feedback-voter transient emulation, and wrong-command injection.
- Majority-based scrubbing, sticky mismatch status, four-bit saturating mismatch-cycle counter.
- Build option `TINYTMR_SHARED_FEEDBACK` for shared-voter comparison.

### Functional architecture

```text
ui_in[7:0] + command bits ----+---- shared command/data bus ----+
                              |                                 |
uio[0] REQ --> 2-FF CDC -----+-- Controller A ---> Bank A -----+
                              +-- Controller B ---> Bank B -----+--> output majority --> uo_out[7:0]
                              +-- Controller C ---> Bank C -----+
                                   |      |      |
                           feedback voter A/B/C each repairs its own bank
controller A/B/C completion --> 2-of-3 ACK majority --> uio[7]
```

Common-mode interfaces include the external data/command bus, synchronizer, reset, clock, enable, ACK voter, output voter, shared shuttle mux and pad frame.

### External interface

| Signal | Direction | Description |
|---|---|---|
| `clk` | In | Single rising-edge receiving clock |
| `rst_n` | In | Active-low asynchronously asserted reset; internal synchronized release |
| `ena` | In | Command-execution enable |
| `ui_in[7:0]` | In | LOAD byte; `ui_in[2:0]` selects bit for special injected faults |
| `uo_out[7:0]` | Out | Voted output or idle diagnostic byte |
| `uio[0]` | In | Asynchronous REQ level |
| `uio[1]` | In | KIND, 1=LOAD, 0=INJECT/SCRUB/TEST |
| `uio[3:2]` | In | BANK selector 0=A, 1=B, 2=C, 3=special |
| `uio[6:4]` | In | Bit address or special selector |
| `uio[7]` | Out | ACK, majority-voted controller completion |
| `uio_oe[7:0]` | Out-control | Constant `8'h80`; only UIO[7] is driven by this macro |

Physical package pin positions are defined by the Tiny Tapeout shuttle and are not user-macro pin locations.

### Command encoding

| KIND | BANK | SEL | Action |
|---|---|---|---|
| 1 | Any | Any | Load same byte into banks A/B/C; clear telemetry |
| 0 | 0–2 | 0–7 | Flip selected bit in bank A/B/C |
| 0 | 3 | 0 | Scrub all banks using separate feedback voter outputs |
| 0 | 3 | 1–3 | Scrub with emulated feedback-voter fault in lane A/B/C; bit from `ui_in[2:0]` |
| 0 | 3 | 4–6 | Emulate wrong command in controller A/B/C: chosen bank flips `ui_in[2:0]` bit, others scrub |
| 0 | 3 | 7 | Reserved transaction; diagnostic output selection with REQ idle |

**Diagnostic readback:** When synchronized REQ is low, BANK=3, SEL=7 (control bits `uio_in[6:0]=7'h7c`), output is `{mismatch_cycles[3:0],last_outliers[2:0],sticky}`. Outlier bit 0 denotes bank A. The mismatch counter saturates at 15 and counts cycles with mismatches, **not discrete events**. Sticky and counter clear on reset or LOAD.

### Four-phase REQ/ACK protocol

1. Drive stable `ui_in` and command pins `uio[6:1]` before raising REQ.
2. Assert REQ as a **level**, not a short pulse. The two-flop receiving-clock synchronizer delivers REQ to all three synchronous controllers. They execute if `ena=1`.
3. Keep data and command unchanged until ACK is high. An asynchronous sender must synchronize ACK in its own clock domain.
4. Drop REQ, wait for ACK to return low, then change payload/start another request.

ACK is a majority of independently stored completion state, not proof of correct or exactly-once commit. An upset in a controller completion flop can cause duplicated actions while REQ is high. Individual bus bits are **not** synchronized and require compliant stable-data timing.

### Fault-response summary

| Fault condition | Expected functional behavior | Limit |
|---|---|---|
| Single stored upset in one bank | Majority masks; scrub can restore agreement | Requires two unaffected copies and valid voter |
| Two faulty copies of same bit | Majority may become wrong; scrub can spread wrong value | Fundamental TMR limitation |
| One feedback voter transient at scrub capture | One bank can be affected in independent-voter architecture | Requires actual physical/logic independence |
| One wrong local decode | Deterministic test affects one bank | Not an arbitrary controller-state SEU model |
| Shared LOAD byte corrupted | Three banks may load identical wrong data | No common-mode protection |
| Shared clock/reset/REQ/ACK/output voter upset | May impair all lanes/transaction/output | Not internally protected |

The injected upsets are controlled synchronous digital faults; they do not characterize SET pulse widths, charge collection, MTBF, device upset cross sections, or TID.

### Timing, environmental and physical specifications

| Characteristic | Published status |
|---|---|
| Project nominal `clock_hz` | **40 MHz** |
| Current implemented clock constraint | **25 ns (40 MHz)**; extracted worst setup slack +9.365 ns, hold slack +0.147 ns across configured signoff corners |
| Payload setup/hold to REQ | Uncharacterized; payload must be stable before REQ and through ACK |
| REQ-to-ACK latency | Dependent on receiving-clock phase and `ena`; uncharacterized at pads |
| Maximum operating frequency / PVT | **Not determined**; 40 MHz is the verified macro constraint, not measured maximum Fmax |
| Max transition (slew) | **Zero reported violations** at all configured signoff corners |
| Constraint fidelity | Explicit `src/timing.sdc` and fixed macro I/O/load assumptions; see [timing contract](timing-contract.md). No false-path or multicycle exceptions |
| VDD, supply current and power | Defined by shuttle process; not characterized here |
| FF1-Q to FF2-D routed delay | Post-route measurement pending |
| SEU cross-section, SEL, TID | Not measured; no radiation rating |
| Package / external pinout | Shuttle integration responsibility |

**Physical acceptance objectives:** preserve 24 separate storage bits, independent command-control state, and three distinct feedback voter logic cones. Place the two REQ synchronizer flip-flops close together and preserve real setup/hold checks from FF1-Q to FF2-D. Spatially separate TMR banks to reduce correlated strike susceptibility. Inspect the routed DEF/ODB and timing reports; RTL attributes alone do not prove independent implementation or metastability performance.

### Verification and production status

**Current candidate (24 October 2026):** RTL and gate-level suites both pass 9/9 at the 25 ns test clock. Local Tiny Tapeout precheck passes 15/15. Magic and KLayout DRC, LVS, setup, hold and slew checks pass. The final audit finds 24 replica storage flops and three named 16-cell feedback-voter cones. REQ synchronizer cell-origin distance is 7.417 µm; reset synchronizer distance is 5.517 µm; the minimum cross-bank storage-origin distance is 8.276 µm. These are geometry inventories, not radiation or MTBF qualification. See [tracked evidence](../reports/signoff/20261024-40mhz/README.md). Gate simulation uses functional standard-cell models; extracted multi-corner STA provides timing evidence separately. The following October 19 results are retained as historical context.

**RTL behavioral verification: PASS, 7/7 tests**, using Icarus Verilog 12.0 and cocotb 2.1.0 in Ubuntu WSL2, as reported on 19 October 2026. Coverage includes single SEU fault masking, double-fault behavior, command handshake, counter saturation, voter SET emulation, local wrong-command emulation and three-controller rearming.

**Physical implementation update (19 October 2026):** LibreLane completed all 80 stages for the initial SKY130 macro. Synthesis counted 441 mapped cells, including four voter instances and 39 sequential cells, with a mapped cell area of 4,790.8448 µm². The macro DEF bounds measure 161 × 111.52 µm. LVS passed; Magic DRC reported zero violations; antenna checks passed. Reported setup and hold checks found no violations with the 20 ns constraint. Maximum slew violations remain at the hot/slow/low-voltage corners. KLayout DRC was disabled in the reference configuration; timing uses fallback constraints. Physical TMR lane separation and synchronizer interstage placement are not yet audited. Silicon measurement and radiation qualification remain outstanding. Reports: `reports/latest/`. See [architecture](architecture.md) and [CDC](cdc.md) engineering documentation.

### Document control and notice

| Item | Value |
|---|---|
| Product | ICMOS TinyTMR-8 |
| Document | ICMOS-TMR8-DS-001 |
| Revision/date | B / 19 October 2026 |
| Design top | `tt_um_jeffadickson_tinytmr` |
| Source | https://github.com/jeffadickson/TinyTMR |
| Classification | **PRELIMINARY — Engineering Evaluation Only** |

*ICMOS is the project brand requested for this datasheet. This document does not establish corporate registration, electrical guarantees, radiation assurance, or authorization for safety-critical or flight use. Specifications may change.*
