`default_nettype none
`timescale 1ns / 1ps
// Public-pin test harness for RTL and the actual SKY130 gate-level netlist.
// Tie power rails explicitly: without this, the powered standard-cell
// simulation produces X even for constant output-enable signals.
module tb;
    reg clk;
    reg rst_n;
    reg ena;
    reg [7:0] ui_in;
    reg [7:0] uio_in;
    wire [7:0] uo_out;
    wire [7:0] uio_out;
    wire [7:0] uio_oe;
`ifdef GL_TEST
    wire VPWR = 1'b1;
    wire VGND = 1'b0;
`endif
    tt_um_jeffadickson_tinytmr user_project (
`ifdef GL_TEST
        .VPWR(VPWR),
        .VGND(VGND),
`endif
        .clk(clk),
        .rst_n(rst_n),
        .ena(ena),
        .ui_in(ui_in),
        .uio_in(uio_in),
        .uo_out(uo_out),
        .uio_out(uio_out),
        .uio_oe(uio_oe)
    );
endmodule
`default_nettype wire
