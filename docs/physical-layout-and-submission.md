# TinyTMR physical organization and shuttle submission

**ICMOS engineering note — 2026-10-19.** This note distinguishes observations from the first successful hardening run from proposed radiation-aware layout practices.

## Current hardened macro

- SKY130 user macro DIEAREA in the committed DEF: `(0 0) (161000 111520)` at 1000 DEF units/µm, i.e. **161 × 111.52 µm**.
- 39 standard-cell placement rows.
- First post-synthesis report: **441 mapped standard cells** including four voter instances; **4,790.8448 µm²** mapped logic cell area; 39 sequential cells.
- Local LibreLane run completed 80/80 flow stages, setup/hold checks showed no violations with the current constraints, LVS passed, Magic DRC reported zero violations. Note max-slew violations at hot/slow/low-voltage corners; KLayout DRC is disabled in the default config. These remain issues requiring sign-off review.
- The OpenROAD screenshot shows upper-region clustering of functional logic; this is a **qualitative visual observation, not a placement audit**. It does not prove A/B/C separation nor FF1-to-FF2 synchronizer proximity.
- Evidence: `reports/latest/final/def/tt_um_jeffadickson_tinytmr.def`, `reports/latest/06-yosys-synthesis/reports/stat.rpt`, `reports/latest/62-magic-drc/reports/drc.magic.rpt`.

## Two physical implementations worth comparing

### Version 0: unconstrained reference (as implemented)

Flat global timing/area-oriented placement. Contains independently described TMR storage, three feedback majority voters, and synchronous command controllers, but no enforced physical exclusion regions for the replica domains. As a result, adjacency/correlated-upset susceptibility is unknown.

### Version 1: triplicated physical lane template (proposed, not implemented)

1. Design and characterize **one fault-containment lane**: eight local state bits, lane controller, its local repair voter, and dedicated local control and clock/reset endpoints.
2. Establish a repeatable floorplan for this lane. Harden/place/route it under a fixed interface contract and verify timing, hold, area, signal integrity and power.
3. Instantiate three copies as separate physically controlled regions, with meaningful **spatial separation** and routing corridors. Duplicate lane macros if supported by the shuttle/tool flow, otherwise use floorplan regions and cell-placement constraints rather than assuming hard macros are accepted.
4. Add the cross-lane fan-in network required by each majority voter. Each lane's voter must sample A, B, and C but repair **only its own** bank. Keep independent cone logic and analyze correlated upset risk on shared long wires.
5. Integrate a common input boundary, output voter, and handshake path explicitly as documented **common-mode vulnerabilities** (or design additional protection in a later iteration).
6. Constrain FF1 and FF2 **near each other**, with FF1 near the receiving macro input if practical. Keep a timed FF1-Q→FF2-D route; do not force timing false paths across both stages. Separate the three fault-containment lanes, **not** the two stages of one synchronizer.
7. Audit final DEF/ODB and netlists: identify each A/B/C register pair's physical distance, inter-lane minimum clearance, three independently implemented feedback voters, FF1→FF2 distance/delay, common reset/clock and routed crossover topology.
8. Compare PPA and routed delays against Version 0 and record repeatable experiments. Timing or routing might make strict identical lane cloning impractical; preserve electrical correctness first.

This is a **design proposal**, not radiation assurance. Physical separation distances cannot be chosen quantitatively without process- and radiation-environment-specific evidence. Even a physically isolated lane can share sensitive upstream control, pads, power and clocks.

## Current submission path (Tiny Tapeout SKY130)

1. Ensure the repository follows the selected **TTSKY26d Verilog template**, especially `info.yaml`, `docs/info.md`, `src/config.json` and GitHub Actions for GDS/docs. A successful local hardening run is **not** the same as passing the Tiny Tapeout portal's automated checks.
2. Before submission: review unresolved max-slew violations, missing KLayout DRC, physical TMR separation, synchronizer placement and complete documented testing. Do not mark the design radiation-qualified.
3. In https://app.tinytapeout.com/projects/create sign in with GitHub, **Create a new project**, supply `https://github.com/jeffadickson/TinyTMR`, choose the **TTSKY26d** shuttle and complete any checkout/coupon step.
4. After creating the project, explicitly select **Submit a new revision**. To use later source changes, let GDS/docs finish and submit an updated revision before the shuttle closes.
5. As listed by Tiny Tapeout on 2026-10-19, **TTSKY26d closes 2026-11-30**; check the portal for availability, exact deadline and current fees. Tiny Tapeout expects submitted design documentation to become public, so confirm how the present private GitHub repository must be handled before submitting.

Official references:
- https://tinytapeout.com/guides/advanced-workshop/submit-your-design/
- https://tinytapeout.com/chips/
- https://tinytapeout.com/terms/
