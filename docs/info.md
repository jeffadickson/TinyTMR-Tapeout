# TinyTMR — technical design notes

**Revision:** triplicated synchronous command controllers with independent
feedback voters and shared request/data CDC. Read
[architecture.md](architecture.md) for the threat model, block diagram,
protocol constraints, fault-injection command table, acceptance criteria and
outstanding verification cases. Read [cdc.md](cdc.md) for timing requirements.

## Datapath

Storage is 3 x 8-bit separately declared register banks with separate write,
injection and scrub enables. Each bank has a distinct 2-of-3 majority voter for
scrubbing. An additional, shared output voter drives `uo_out[7:0]` except during
idle diagnostic selection. All three bank voting functions are logically the
same, but must survive synthesis as physically independent instances.

## Command path

`req_meta` and `req_sync` synchronize the asynchronous REQ input into `clk`.
Three controller instances each contain a completion flip-flop and separate
command decode. Each lane's controls are connected only to that lane's
register, and ACK is a 2-of-3 vote over the completion states.
The producers' input data and command bits are bundled data; they are not
individually synchronized and must remain stable through the handshake.

The default build has independent voters. Defining
`TINYTMR_SHARED_FEEDBACK` selects the shared feedback-voter comparison.
The optional selector-4/5/6 commands emulate a faulty controller's decoding
with a wrong lane-local action at one edge.

## Telemetry

The idle diagnostic selector is `bank=3,selector=7,REQ=0`, returning
`{mismatch_cycles[3:0],last_outliers[2:0],sticky}`. The counter records
clock cycles of disagreement (not radiation strikes) and saturates at 15.
Telemetry, diagnostic mux, output voter and ACK voter are **not** triplicated.
`uio[7]` is ACK; there is no dedicated live mismatch pin.

## Assurance and limitations

- TMR masks one replica error per bit as long as majority logic is correct.
- Multiple concurrent upsets can defeat majority and corrupt a scrub.
- Common CDC, input data, reset, clock, output voter and pad remain vulnerable.
- An upset in a controller's `done` flop can lead to repeated execution in that
  lane while REQ stays high; ACK voting does not establish a single-commit
  guarantee during faults.
- Synthetic fault injection is a functional test aid, not particle-level SET
  pulse, metastability, SEU cross-section or system FIT-rate characterization.
- RTL, synthesis, timing/CDC, physical separation, DRC/LVS and power tests
  must all be checked before fabrication. The implemented RTL is not yet
  validated by executing the HDL simulation suite in this environment.
