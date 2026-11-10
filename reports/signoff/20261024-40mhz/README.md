# TinyTMR 40 MHz engineering acceptance — 24 October 2026

Local acceptance passes for run `baseline40mhz-drc-20261024T2359352729859Z`. This is an experimental macro candidate, not silicon measurement or radiation qualification. The hosted Tiny Tapeout GDS/docs/precheck/gate jobs and the portal revision remain separate acceptance steps.

| Check | Result |
|---|---|
| Clock period / metadata | 25 ns / 40 MHz |
| Placement target density | 60% |
| Worst extracted setup slack | +9.365132 ns |
| Worst extracted hold slack | +0.147036 ns |
| Maximum slew violations | 0 across configured signoff corners |
| Magic DRC / KLayout DRC / LVS | Pass, zero reported errors |
| RTL / gate-level public-pin tests | 9/9 and 9/9 at the 25 ns test clock |
| Local Tiny Tapeout precheck | 15/15 |
| Replica preservation | 24 storage flops; three named 16-cell feedback-voter cones |

The electrical correction excludes undersized buffer/delay-cell choices identified by pin-level diagnostics, repairs at the slow corner and reserves 1 ns hold-repair margin. All signoff corners remain checked; no transition limit, timing check or DRC check was relaxed. The exact macro-interface assumptions are in `docs/timing-contract.md` and `src/timing.sdc`.

Hardening uses LibreLane 3.0.14 and SKY130 revision `8afc8346a57fe1ab7934ba5a6056ea8b43078e71`. Local precheck uses support-tools revision `01d5d2814fa9dd61e9d211e0b235a4a592a9316a` and the shuttle precheck PDK revision `0536d02d875c8f67dd7cca3902ac457e62f20005`. Native Magic/KLayout execute through the C# adapter using the pinned LibreLane image. The precheck Python environment uses `tt/precheck/requirements.txt`.

`run.json` records the experiment's starting HEAD and actual source hashes, including uncommitted configuration changes. `verified-inputs.json` confirms the frozen design/configuration/test/workflow content matches those inputs, with only Windows checkout line-ending normalization where applicable. The containing Git commit identifies this reviewed snapshot. Hosted CI must rebuild that commit to produce the official stamped submission artifact.

Evidence: final `metrics.json`, `input-config.json`, `layout-audit.json`, `gate-results.xml`, precheck XML/Markdown, RTL coverage and build/test log excerpts. Raw runs, PDK assets and physical databases remain outside Git. GDS/LEF/powered netlist are exported locally as `candidate-layout`; this folder is not represented as the official Tiny Tapeout submission artifact.

RTL coverage from Verilator 5.048 reports line 28/28, branch 48/48, toggle 734/826 and expression 41/43 points. Coverage-point definitions differ from source-line annotation: only 100/147 annotated lines have every attached coverage point hit. Gate simulation uses functional standard-cell models without SDF; extracted multi-corner STA supplies timing evidence separately. The mapped register/voter audit and synchronizer distances do not establish MTBF, correlated-strike immunity or radiation tolerance.

Traceability: `docs/requirements.sdoc` (`TMR-FAB-001` through `TMR-FAB-004`) and `tools/ICMOS.PhysicalReview/requirements.sdoc`. Helper coverage, seeded property tests, malformed-input tests, manual mutation checks and limitations are documented in the helper's `verification.txt`.
