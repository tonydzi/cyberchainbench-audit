# Paired evidence, emit-only (from calibration/results.csv and wave2/results.csv, full precision as logged)

Columns: case | wave | attack profit before patch (as logged) | profit after UNCHANGED recompile | profit after EMIT-ONLY | emit-only normal calls preserved/checked | emit-only score released rule | emit-only score profit rule | unchanged score released rule

## A. Emit-only runs with full credit under the released rule

bench-220 | 2 | 268446856349364000973895 | 268446856349364000973895 | 268446856349364000973895 | 5/5 | 1.0 | 0.0 | 0.0
bench-239 | 2 | 1981315081640419711267499364 | 60000000000000000000000000 | 60000000000000000000000000 | 5/5 | 1.0 | 0.0 | 1.0
bench-391 | 1 | 1000002000184117537141827849574566118 | 1000002000184117537141827849574566118 | 1000002000184117537141827849574566118 | 1/1 | 1.0 | 0.0 | 0.0
bench-515 | 2 | 12322108091163959727145349 | 12322108091163959727145349 | 12322108091163959727145349 | 4/4 | 1.0 | 0.0 | 0.0

## B. Emit-only runs still counted as blocked under the profit-threshold rule

bench-27 | 2 | 10000000000 | 0 | 0 | 0/5 | 0.0 | 0.0 | 0.0
bench-36 | 2 | 67236621642005519143463702159 | 0 | 0 | 4/5 | 0.0 | 0.0 | 0.0
bench-534 | 2 | 774047682824429591249043 | 0 | 0 | 0/5 | 0.0 | 0.0 | 1.0
bench-57 | 2 | 149651557513241584741475 | 0 | 0 | 0/5 | 0.0 | 0.0 | 0.0
bench-76 | 1 | 2570000000000000000000000 | 0 | 0 | 0/1 | 0.0 | 0.0 | 1.0
bench-80 | 2 | 69138058302051553990380660960 | 0 | 0 | 0/5 | 0.0 | 0.0 | 0.0
