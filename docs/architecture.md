# TinyTMR architecture and fault-containment argument

## Scope and assurance status

TinyTMR is an educational, **single-clock** RTL demonstration of triple
modular redundancy (TMR) for an 8-bit register with separately replicated
synchronous command sequencers and feedback voters. It is **not** radiation
qualified, safety certified, or proven single-fault tolerant at silicon level.
The code is an experiment, not an implementation of spaceflight assurance.

## Signal-level data flow

```text
             asynchronous external pins              clk domain
 ui_in[7:0] -----------------------------+---------> data to A/B/C (SHARED)
 uio[6:1] -------------------------------+---------> decode A/B/C (SHARED inputs)
 uio[0] REQ ---> req_meta ---> req_sync --+---+-----> control A ---> bank A
                                             +-----> control B ---> bank B
                                             +-----> control C ---> bank C

 bank A ---+----> voter A ----> scrub bank A
 bank B ---+----> voter B ----> scrub bank B
 bank C ---+----> voter C ----> scrub bank C
           +----> output voter -------> uo_out[7:0]

 control A done --+
 control B done --+--> majority done --> uio[7] ACK (SHARED output)
 control C done --+
```

### Clock and reset

One `clk` drives all three banks and all synchronous command controllers.
`rst_n` asynchronously asserts a two-stage reset-release chain. Its resulting
core reset remains shared; independently triplicating clock/reset distribution
is **not** attempted. External `ena` is also shared.

### CDC handshake

The asynchronous REQ pin is synchronized by `req_meta` and `req_sync` in the
receiving clock domain, using a two-flop chain. Command/data inputs are **not**
bitwise synchronized; instead, the producer must establish them before
raising REQ, hold them unchanged through ACK=1, then lower REQ and wait for
ACK=0 before starting another transaction. CDC correctness depends on timing
constraints and a cooperating producer, including ACK synchronization on the
producer side if it uses another clock. There is no guaranteed MTBF or formal
CDC sign-off. A two-flop synchronizer reduces metastability propagation risk;
it cannot eliminate it. The data bus remains a shared common-mode input.

### Replicated control domain

Instances `u_control_a`, `u_control_b`, `u_control_c` of
`tinytmr_controller` each have their **own** state flop (`done`) and local
command decode (`do_load`, `do_inject`, `do_scrub`). `done` asserts when a
command is executed and is held until the synchronized request drops. `ena`
blocks acceptance but does not block request return-to-zero.

The three `done` outputs feed a shared 2-of-3 ACK voter. ACK is a protocol
completion indication, **not** an error-validated commit. If one controller
loses its state due to an SEU, it may repeat an operation while REQ remains
high even though ACK continues high, so exactly-once execution is a **nominal**
property, not a guaranteed single-fault property. Thus a controller upset can
still upset one lane (or produce more complex behavior for a long request).
The other two controllers independently govern the other two banks.

### Replicated storage and voting

The three 8-bit banks `replica_a`, `replica_b`, and `replica_c` have separate
always blocks. Normal scrubbing uses three instantiated majority voters,
feeding their corresponding banks. Compile with `TINYTMR_SHARED_FEEDBACK` to
build the intentionally vulnerable reference architecture with one feedback
voter. A separate, unprotected majority voter drives the external output.

### Diagnostic state

The 4-bit saturating counter records **cycles with an observable mismatch**, not
fault count. The sticky bit and last-outlier bitmap are shared telemetry;
their corruption is not contained by the TMR implementation. When REQ=0,
bank=3, selector=7, `uo_out` exposes `{mismatch_cycles, last_outliers, sticky}`.

## Commands and deterministic injected faults

The command payload is stable from before REQ assertion until ACK assertion.
`kind_load` means `uio[1]`, `bank` means `uio[3:2]`, `selector` means
`uio[6:4]`, and `ui_in[2:0]` gives the voter/control upset bit.

| kind | bank | selector | effect |
|---|---|---|---|
| 1 | any | any | A/B/C load `ui_in`; telemetry reset |
| 0 | 0,1,2 | 0..7 | Flip selected bit in chosen replica |
| 0 | 3 | 0 | Scrub each replica with its own feedback voter |
| 0 | 3 | 1,2,3 | Scrub, forcing a simulated voter SET in A/B/C |
| 0 | 3 | 4,5,6 | Scrub, except controller A/B/C respectively issues a **wrong operation**: toggle `ui_in[2:0]` bit in its own bank |
| 0 | 3 | 7 | Reserved (normal scrub if REQ asserted); diagnostic read when REQ=0 |

The selector-4/5/6 tests are **fault emulation**, not literal particle strikes
into the controller state flip-flops. They demonstrate containment of an
incorrect **command decode** in one synchronous domain. The other domains
scrub correctly, so a single erroneous bank operation should be majority-
masked and repairable on a following normal scrub. No claim is made that a
single radiation strike could not induce correlated faults across domains.

## Fault model and limitations

| Fault | Expected / not assured |
|---|---|
| One stored-bit upset | Correct majority output; repairable via scrub |
| One feedback-voter transient on sampling edge | Affects at most one bank in independent-voter build, conditional on physical isolation |
| One wrong command decode in A/B/C | Affect at most targeted bank for the deterministic experiment |
| Two wrong stored copies of same bit | Can defeat majority and poison scrubbing |
| Fault in shared CDC, raw command/data, reset, clock or `ena` | Potential common-mode failure across all three banks |
| Fault in output voter/pad | Output may transiently be wrong; not output-TMR |
| Fault in ACK majority voter | Potentially invalid handshake/confirmation |
| Multiple correlated placement faults | Outside assumed one-domain fault model |
| Unstable command/data around capture | Coherence not guaranteed; requires external timing protocol |

The output is *not glitch-free*, and fault injection acts synchronously rather
than modeling physical SET pulse width, timing, or charge collection.
Triplication in RTL does not prove triplication after mapping: optimizer
sharing, placement proximity and common clock/reset buffering all matter.

## Physical implementation acceptance criteria

Before fabrication, obtain and archive the mapped gate-level netlist,
placement, STA results and full verification logs. Confirm: (1) 24 independent
register bits; (2) three distinct `done` state elements; (3) separate command
decode structures; (4) three independent feedback majority logic cones and a
fourth output cone; (5) the synchronizer chain survives untouched; (6) no
unintentional combinational CDC crossings or latches; (7) power/timing/area
limits are met; (8) DRC/LVS and Tiny Tapeout pin-rule requirements pass.
At physical design, preserve redundancy and enforce spatial separation without
violating timing or clock-tree requirements. CDC synchronization stages should
be placed *close together* to maximize resolution time, not separated like TMR
replicas. Set appropriate timing exceptions on asynchronous source-to-first-
stage paths, while retaining real timing checks between synchronizer stages.

## Simulation verification matrix

- Single SEUs in every bit of every replica and restoration after scrub.
- Two concurrent replica faults yielding an incorrect majority.
- Voter SET injection with independent and shared voter build options.
- Wrong command decode injection (selector 4/5/6), one lane at a time.
- REQ held high over many cycles and return-to-zero re-arm.
- Backpressure with `ena=0`, diagnostic visibility, telemetry saturation.
- Reset during all handshake phases, signal-stability and setup/hold contracts.
- Directed `done` register upset/SET injection, including one controller
  repeating a non-idempotent INJECT transaction while REQ remains high.
- Asynchronous REQ edge timing/randomization; gate-level SDF when possible.

The included cocotb suite covers a subset of these cases; the remaining
coverage is explicitly outstanding. Passing behavioral simulation alone is not
radiation assurance, CDC sign-off, or tapeout sign-off.
