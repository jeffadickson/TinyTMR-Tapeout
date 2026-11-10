# TinyTMR CDC command interface

The design has one internal clock. An external controller may be asynchronous.
Use a **four-phase return-to-zero bundled-data handshake**:

1. Drive `ui_in[7:0]` and the command bits `uio_in[6:1]`; keep them stable.
2. Raise `uio_in[0]` (REQ) after data/command settle.
3. Wait for `uio_out[7]` (ACK) to become high. The receiver has nominally executed the request in all three lanes; ACK is the majority of three completion states. Exactly-once is **not** guaranteed if a controller state flop is upset.
4. Lower REQ and wait for ACK low before another transfer; only then change command/data.

`REQ` traverses two serial `(* async_reg *)` flip-flops, then triggers independently decoded operations in three synchronous controller instances. Each controller holds its own completion state until synchronized REQ goes low, and ACK is the majority of those states. Data is not synchronized per bit; its stability across the two-FF latency is guaranteed by the sender's handshake. The sender must allow sufficient setup margin before raising REQ and must not modify the bus until after ACK has been observed. With unsynchronized asynchronous inputs, no design can offer a mathematical guarantee against metastability; this scheme makes the risk small when properly timed and constrained.

`rst_n` has asynchronous assertion and internally synchronized release. `ena=0` prevents operations and stalls ACK assertion for pending commands; sender must continue holding inputs until ACK high. ACK deassertion is clocked, even when `ena=0`. `ACK` is a clk-domain output, so an asynchronous controller needs to synchronize ACK in **its own domain** (or otherwise satisfy timing), and maintain data stability for the full protocol.

The protocol is not a pulse synchronizer and cannot accept a momentary request pulse; mechanical switches also require debounce. The unprotected synchronizer and ACK voter, shared raw command/data bus, shared clock/reset, and physical proximity of replicas remain single-point/common-mode risks. This is a functional CDC demonstration, not a quantified MTBF analysis or a radiation-qualified interface.
