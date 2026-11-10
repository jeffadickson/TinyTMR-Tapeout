# TinyTMR 40 MHz macro timing contract. Units are ns and fF in configuration.
# Use the standard constraint implementation from the pinned LibreLane version.
# CLOCK_PERIOD=25, IO_DELAY_CONSTRAINT=20 means 5 ns input/output delay budgets.
# The input driver is sky130_fd_sc_hd__inv_2/Y; output loading is 33.442 fF.
# Clock uncertainty is 0.25 ns, clock transition 0.15 ns, timing derating 5%.
# These are macro-interface assumptions, not measured package/board timings.
# No false paths or multicycle exceptions are introduced: in particular the
# request/reset synchronizer first-to-second-stage paths remain fully timed.
# REQ remains asynchronous at the first stage; STA does not establish its MTBF.
source $::env(FALLBACK_SDC)
