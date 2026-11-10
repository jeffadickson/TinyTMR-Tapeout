# TinyTMR RTL and true SKY130 gate-level simulation.
SIM ?= icarus
TOPLEVEL_LANG = verilog
TOPLEVEL = tb
COCOTB_TEST_MODULES = test
SRC_DIR := $(abspath $(CURDIR)/../src)
ifeq ($(GATES),yes)
SIM_BUILD = sim_build/gates
COMPILE_ARGS += -DGL_TEST -DFUNCTIONAL -DUSE_POWER_PINS -DSIM -DUNIT_DELAY=\#1
VERILOG_SOURCES = $(PDK_ROOT)/sky130A/libs.ref/sky130_fd_sc_hd/verilog/primitives.v
VERILOG_SOURCES += $(PDK_ROOT)/sky130A/libs.ref/sky130_fd_sc_hd/verilog/sky130_fd_sc_hd.v
VERILOG_SOURCES += $(abspath $(CURDIR)/gate_level_netlist.v)
export TINYTMR_GATES = 1
else
SIM_BUILD = sim_build/rtl
VERILOG_SOURCES = $(SRC_DIR)/project.v
export TINYTMR_GATES = 0
endif
ifeq ($(TINYTMR_SHARED_FEEDBACK),1)
COMPILE_ARGS += -DTINYTMR_SHARED_FEEDBACK
export TINYTMR_TEST_SHARED = 1
endif
VERILOG_SOURCES += $(abspath $(CURDIR)/tb.v)
include $(shell cocotb-config --makefiles)/Makefile.sim
