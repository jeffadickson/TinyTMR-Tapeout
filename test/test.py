"""TinyTMR cocotb tests for CDC four-phase bundled-data handshake."""
import os
import cocotb
from cocotb.triggers import Timer

async def tick(dut):
    # 40 MHz baseline: 12 ns low + 12 ns high + 1 ns settling after falling edge.
    dut.clk.value = 0
    await Timer(12, unit="ns")
    dut.clk.value = 1
    await Timer(12, unit="ns")
    dut.clk.value = 0
    await Timer(1, unit="ns")

async def setup(dut):
    dut.clk.value = 0
    dut.ena.value = 1
    dut.ui_in.value = 0
    dut.uio_in.value = 0
    dut.rst_n.value = 0
    await tick(dut)
    dut.rst_n.value = 1
    for _ in range(5):
        await tick(dut)
    assert int(dut.uio_oe.value) == 0x80
    assert int(dut.uio_out.value) == 0

async def send(dut, controls, data=0, hold=0):
    """Controls bit 0 is reserved for the asynchronous request."""
    dut.ui_in.value = data
    dut.uio_in.value = controls & ~1
    await tick(dut)  # Establish data before request.
    dut.uio_in.value = controls | 1
    for n in range(10):
        await tick(dut)
        if int(dut.uio_out.value) & 0x80:
            break
    else:
        raise AssertionError("No acknowledgment of request")
    for _ in range(hold):
        await tick(dut)
        assert int(dut.uio_out.value) & 0x80
    dut.uio_in.value = controls & ~1
    for n in range(10):
        await tick(dut)
        if not (int(dut.uio_out.value) & 0x80):
            break
    else:
        raise AssertionError("ACK did not clear after request returned low")

async def load(dut, value):
    await send(dut, 0x02, value)

async def inject(dut, bank, bit):
    await send(dut, (bank << 2) | (bit << 4))

async def scrub(dut, selector=0, bit=0):
    await send(dut, 0x0c | (selector << 4), bit)

async def read_idle_page(dut, select):
    """Read diagnostic/scan page without triggering the REQ handshake."""
    saved = int(dut.ui_in.value)
    dut.ui_in.value = select
    dut.uio_in.value = 0x7c  # bank=3, index=7, REQ=0
    await Timer(1, unit="ns")
    value = int(dut.uo_out.value)
    dut.uio_in.value = 0
    dut.ui_in.value = saved
    await Timer(1, unit="ns")
    return value

async def diag(dut):
    return await read_idle_page(dut, 0x00)

async def scan(dut):
    """Capture and read four bytes: physical A/B/C, majority snapshot."""
    await send(dut, 0x7c, 0)
    return [await read_idle_page(dut, 0x30 + i) for i in range(4)]

@cocotb.test()
async def single_fault_masks_and_scrubs(dut):
    await setup(dut)
    await load(dut, 0xa5)
    for bank in range(3):
        for bit in range(8):
            await inject(dut, bank, bit)
            assert int(dut.uo_out.value) == 0xa5
            telemetry = await diag(dut)
            assert telemetry & 1
            assert ((telemetry >> 1) & 7) == (1 << bank)
            await scrub(dut)
            assert int(dut.uo_out.value) == 0xa5
            await load(dut, 0xa5)

@cocotb.test()
async def double_fault_scrub_cements_bad_majority(dut):
    await setup(dut)
    await load(dut, 0)
    await inject(dut, 0, 4)
    await inject(dut, 1, 4)
    assert int(dut.uo_out.value) == 0x10
    await scrub(dut)
    assert int(dut.uo_out.value) == 0x10

@cocotb.test()
async def held_request_only_executes_once_and_rearms(dut):
    await setup(dut)
    await load(dut, 0)
    # A ten-clock held request must not toggle the same fault twice.
    await send(dut, 0x00, 0, hold=10)
    assert await scan(dut) == [1, 0, 0, 0]
    await inject(dut, 0, 0)
    assert await scan(dut) == [0, 0, 0, 0]
    await load(dut, 0x96)
    assert int(dut.uo_out.value) == 0x96

@cocotb.test()
async def enable_backpressure_and_telemetry(dut):
    await setup(dut)
    await load(dut, 0x5a)
    await inject(dut, 2, 3)
    for _ in range(20):
        await tick(dut)
    assert (await diag(dut)) >> 4 == 15
    dut.ena.value = 0
    dut.ui_in.value = 0xff
    dut.uio_in.value = 0x03  # request + load
    for _ in range(6):
        await tick(dut)
    assert int(dut.uio_out.value) == 0
    assert int(dut.uo_out.value) == 0x5a
    dut.ena.value = 1
    for _ in range(5):
        await tick(dut)
    assert int(dut.uio_out.value) == 0x80
    assert int(dut.uo_out.value) == 0xff
    dut.uio_in.value = 0x02
    for _ in range(4):
        await tick(dut)
    assert int(dut.uio_out.value) == 0

@cocotb.test()
async def voter_transient_containment(dut):
    await setup(dut)
    await load(dut, 0xff)
    await scrub(dut, selector=1, bit=5)
    shared = bool(int(os.getenv("TINYTMR_TEST_SHARED", "0")))
    expected = 0xdf if shared else 0xff
    assert int(dut.uo_out.value) == expected
    await scrub(dut)
    assert int(dut.uo_out.value) == expected

@cocotb.test()
async def triplicated_command_decode_fault_containment(dut):
    """One wrong synchronous command decoder must not overwrite all banks."""
    await setup(dut)
    for lane in range(3):
        await load(dut, 0xff)
        # selector 4,5,6 invokes wrong-command injection in A,B,C respectively.
        await scrub(dut, selector=4 + lane, bit=lane)
        assert int(dut.uo_out.value) == 0xff
        physical = (await scan(dut))[:3]
        assert physical == [0xff ^ (1 << lane) if i == lane else 0xff
                            for i in range(3)]
        assert (await diag(dut)) & 1
        await scrub(dut)
        assert (await scan(dut))[:3] == [0xff] * 3

@cocotb.test()
async def three_independent_controllers_rearm(dut):
    """Check externally visible majority ACK rearm and non-destructive scrub."""
    await setup(dut)
    await load(dut, 0x69)
    assert int(dut.uio_out.value) == 0
    await send(dut, 0x0c, 0, hold=8)
    assert int(dut.uio_out.value) == 0
    assert int(dut.uo_out.value) == 0x69
    assert await scan(dut) == [0x69] * 4


@cocotb.test()
async def output_combiner_fault_truth_table(dut):
    """Compare logical wired OR, open-drain wired AND, and majority."""
    await setup(dut)
    await load(dut, 0xff)
    dut.ui_in.value = 0x40  # combiner view, storage bit 0
    dut.uio_in.value = 0x7c
    await Timer(1, unit="ns")
    assert int(dut.uo_out.value) == 0x7e  # 0,1,1,1,1,1,1,0
    dut.uio_in.value = 0
    await inject(dut, 0, 0)  # A=0, B=C=1
    dut.ui_in.value = 0x40
    dut.uio_in.value = 0x7c
    await Timer(1, unit="ns")
    assert int(dut.uo_out.value) == 0xe6  # disagree,majority=1,OR=1,AND=0,A=0,B=C=1
    dut.uio_in.value = 0
    await inject(dut, 1, 0)  # A=B=0, C=1
    dut.ui_in.value = 0x40
    dut.uio_in.value = 0x7c
    await Timer(1, unit="ns")
    assert int(dut.uo_out.value) == 0xa2  # disagree,majority=0,OR=1,AND=0,A=B=0,C=1


@cocotb.test()
async def scan_and_upset_counters(dut):
    """Snapshot all TMR banks, distinguish episodes from injected faults."""
    await setup(dut)
    await load(dut, 0xa5)
    assert await scan(dut) == [0xa5] * 4
    await inject(dut, 0, 0)
    assert int(dut.uo_out.value) == 0xa5
    assert await read_idle_page(dut, 0x20) == 1  # one injected fault
    assert await read_idle_page(dut, 0x10) == 1  # one disagreement episode
    assert await scan(dut) == [0xa4, 0xa5, 0xa5, 0xa5]
    # Another flip while disagreement is active is a new injection but
    # not a new disagreement episode. The snapshots are nondestructive.
    await inject(dut, 0, 1)
    assert await read_idle_page(dut, 0x20) == 2
    assert await read_idle_page(dut, 0x10) == 1
    await scrub(dut)
    await tick(dut)
    await inject(dut, 2, 2)
    assert await read_idle_page(dut, 0x20) == 3
    assert await read_idle_page(dut, 0x10) == 2
    assert await scan(dut) == [0xa5, 0xa5, 0xa1, 0xa5]
    await load(dut, 0x55)
    assert await read_idle_page(dut, 0x10) == 0
    assert await read_idle_page(dut, 0x20) == 0
