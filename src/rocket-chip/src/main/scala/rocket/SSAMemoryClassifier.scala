// See LICENSE.Berkeley for license details.
package freechips.rocketchip.rocket

import chisel3._
import chisel3.util._

/** Rule 1: exclusive per-context retired integer memory instruction classification.
  * Two trusted epochs; history replacement is FIFO, never a claim of randomness.
  */
class SSAMemoryClassifier extends Module {
  val io = IO(new Bundle {
    val session = Input(UInt(64.W))
    val base = Input(UInt(64.W))
    val command = Input(UInt(2.W))
    val index = Input(UInt(6.W))
    val data = Output(Vec(8, UInt(64.W)))
    val observe = Input(Bool())
    val pc = Input(UInt(64.W))
    val address = Input(UInt(64.W))
    val store = Input(Bool())
    val size = Input(UInt(2.W))
    val contextExit = Input(Bool())
    val call = Input(Bool())
    val depth = Input(UInt(64.W))
    val rid = Input(UInt(18.W))
  })
  val epochs = RegInit(VecInit(Seq.fill(2)(0.U(64.W))))
  val bases = Reg(Vec(2, UInt(64.W)))
  val depths = RegInit(VecInit(Seq.fill(2)(0.U(9.W))))
  val spills = RegInit(VecInit(Seq.fill(2)(0.U(32.W))))
  val invalid = RegInit(VecInit(Seq.fill(2)(false.B)))
  val overflows = RegInit(VecInit(Seq.fill(2)(false.B)))
  val dropped = RegInit(VecInit(Seq.fill(2)(0.U(64.W))))
  val unframed = RegInit(VecInit(Seq.fill(2)(0.U(64.W))))
  val inputs = RegInit(VecInit(Seq.fill(2)(0.U(64.W))))
  val evictions = RegInit(VecInit(Seq.fill(2)(0.U(64.W))))
  val heads = RegInit(VecInit(Seq.fill(2)(0.U(4.W))))
  val stack = Mem(512, UInt(18.W))
  val counts = Mem(128, Vec(5, UInt(64.W)))
  val valid = RegInit(VecInit(Seq.fill(32)(false.B)))
  val pcs = Reg(Vec(32, UInt(64.W)))
  val rids = Reg(Vec(32, UInt(18.W)))
  val ops = Reg(Vec(32, Bool()))
  val sizes = Reg(Vec(32, UInt(2.W)))
  val last = Reg(Vec(32, UInt(64.W)))
  val deltas = Reg(Vec(32, UInt(64.W)))
  val mature = Reg(Vec(32, Bool()))
  val busy = RegInit(false.B)
  val clearingBank = Reg(UInt(1.W))
  val clearIndex = Reg(UInt(6.W))
  val found = io.session.orR && (epochs(0) === io.session || epochs(1) === io.session)
  val bank = Mux(epochs(0) === io.session, 0.U(1.W), 1.U(1.W))
  val active = found && !busy && io.base.orR && bases(bank) === io.base
  val top = stack(Cat(bank, (depths(bank)-1.U)(7,0)))
  val supported = !invalid(bank) && !spills(bank).orR && depths(bank).orR && top.orR && top < 64.U
  val rowAddr = Cat(bank, io.index)
  val row = counts(rowAddr)
  for (i <- 0 until 8) io.data(i) := 0.U
  when(found && !busy) {
    for (i <- 0 until 5) io.data(i) := row(i)
    io.data(5) := inputs(bank)
    io.data(6) := evictions(bank)
    io.data(7) := dropped(bank)
    when(io.index === 0.U) {
      // status: present,busy,invalid,history discontinuity,overflow,spill
      io.data(0) := 1.U | (invalid(bank).asUInt << 2) | (evictions(bank).orR.asUInt << 3) |
        (overflows(bank).asUInt << 4) | (spills(bank).orR.asUInt << 5)
      io.data(1) := depths(bank)
      io.data(2) := spills(bank)
      io.data(3) := unframed(bank)
      io.data(4) := Mux(depths(bank).orR, top, 0.U)
    }
  }
  when(busy) { io.data(0) := 2.U }

  // A reset is trusted, bank-indexed and requires a nonzero epoch and pool.
  when(io.command === 1.U && !busy && io.session.orR && io.base.orR && io.index < 2.U) {
    val b = io.index(0)
    epochs(b) := io.session; bases(b) := io.base
    depths(b) := 0.U; spills(b) := 0.U; invalid(b) := false.B
    overflows(b) := false.B; dropped(b) := 0.U; unframed(b) := 0.U
    inputs(b) := 0.U; evictions(b) := 0.U; heads(b) := 0.U
    for(i <- 0 until 32) { when(b === (i/16).U) { valid(i) := false.B } }
    busy := true.B; clearingBank := b; clearIndex := 0.U
  }.elsewhen(busy) {
    counts(Cat(clearingBank, clearIndex)) := VecInit(Seq.fill(5)(0.U(64.W)))
    clearIndex := clearIndex + 1.U
    when(clearIndex === 63.U) { busy := false.B }
  }.otherwise {
    // Mirror committed private-ROM frame transitions; no extra ROM instructions.
    when(active && io.contextExit) {
      when(io.call) {
        when(io.depth === depths(bank)+1.U && depths(bank) < 256.U && !spills(bank).orR) {
          stack(Cat(bank, depths(bank)(7,0))) := io.rid
          depths(bank) := depths(bank)+1.U
        }.elsewhen(io.depth === depths(bank)) {
          spills(bank) := spills(bank)+1.U
        }.otherwise { invalid(bank) := true.B }
      }.otherwise {
        when(spills(bank).orR && io.depth === depths(bank)) { spills(bank) := spills(bank)-1.U }
          .elsewhen(depths(bank).orR && io.depth === depths(bank)-1.U) { depths(bank) := depths(bank)-1.U }
          .elsewhen(io.depth =/= 0.U || depths(bank) =/= 0.U) { invalid(bank) := true.B }
      }
    }
    when(active && io.observe) {
      inputs(bank) := inputs(bank)+1.U
      when(inputs(bank).andR) { overflows(bank) := true.B }
      when(!depths(bank).orR) { unframed(bank) := unframed(bank)+1.U }
        .elsewhen(!supported) { dropped(bank) := dropped(bank)+1.U }
        .otherwise {
          val hits = Wire(Vec(16, Bool()))
          for(i <- 0 until 16) {
            val j = Cat(bank, i.U(4.W))
            hits(i) := valid(j) && pcs(j) === io.pc && rids(j) === top && ops(j) === io.store && sizes(j) === io.size
          }
          val hit = hits.asUInt.orR
          val slot = Cat(bank, Mux(hit, PriorityEncoder(hits), heads(bank)))
          val delta = io.address-last(slot)
          val signedDelta = delta.asSInt
          val aligned = (delta & ((1.U(64.W) << io.size)-1.U)) === 0.U
          val stream = signedDelta >= (-4096).S && signedDelta <= 4096.S && delta.orR && aligned
          val category = Mux(!hit || !mature(slot), 0.U(2.W),
            Mux(delta === deltas(slot) && !delta.orR, 1.U,
              Mux(delta === deltas(slot) && stream, 2.U, 3.U)))
          val addr = Cat(bank, top(5,0))
          val old = counts(addr)
          val next = Wire(Vec(5, UInt(64.W)))
          next := old
          next(0) := old(0)+1.U
          for(i <- 1 until 5) {
            when(category === (i-1).U) { next(i) := old(i)+1.U }
          }
          counts(addr) := next
          when(old(0).andR) { overflows(bank) := true.B }
          when(!hit) {
            when(valid(slot)) { evictions(bank) := evictions(bank)+1.U }
            heads(bank) := heads(bank)+1.U
            pcs(slot) := io.pc; rids(slot) := top; ops(slot) := io.store; sizes(slot) := io.size
            valid(slot) := true.B; mature(slot) := false.B
          }.otherwise { mature(slot) := true.B }
          last(slot) := io.address; deltas(slot) := delta
          printf("SSA_MEM_OBS session=%d rid=%d pc=%x va=%x store=%d size=%d category=%d slot=%d eviction=%d\n",
            io.session, top, io.pc, io.address, io.store, io.size, category, slot, !hit && valid(slot))
        }
    }
  }
}
