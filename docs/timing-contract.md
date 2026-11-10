# Forty MHz macro timing contract

The baseline clock period is 25 ns. `src/timing.sdc` explicitly selects the standard constraints supplied by the pinned LibreLane version; it introduces no false paths or multicycle exceptions. The configuration fixes the previously implicit assumptions: 5 ns input and output delay budgets (20% of the period), an `inv_2/Y` input driver, 33.442 fF output loading, 0.25 ns clock uncertainty, 0.15 ns clock transition and 5% timing derating.

These assumptions describe the user macro. They do not characterize the shuttle pad ring, package, controller or PCB. Integration must meet the macro timing/load contract. Input command/data coherence still depends on the bundled-data handshake documented in `cdc.md`.

REQ is asynchronous to `clk`. The first capture stage can become metastable; setup/hold STA does not establish a metastability failure rate. Both request synchronizer stages and both reset-release stages are preserved, and their inter-stage paths remain timed. Layout audits report their cell-origin distances, without claiming a numerical MTBF or radiation qualification.

All configured timing corners are checked. Slow-corner electrical repair is combined with conservative hold margins, and fast-corner hold violations remain fatal. No transition limit is widened to obtain a passing report. The rejected experiments and the final candidate evidence distinguish flow completion from electrical signoff.
