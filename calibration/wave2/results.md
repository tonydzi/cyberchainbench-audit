| case | usable? | reason | unchanged | revert | emit_only |
|---|---|---|---|---|---|
| bench-02 | no | baseline: attack replay hits MemoryOOG/OutOfGas on the unchanged recompile (cause not isolated) | 0.0 | 0.0 | 0.0 |
| bench-103 | no | baseline: attack replay hits MemoryOOG/OutOfGas on the unchanged recompile (cause not isolated) | 0.0 | 0.0 | 0.0 |
| bench-112 | no | baseline: attack replay hits MemoryOOG/OutOfGas on the unchanged recompile (cause not isolated) | 0.0 | 0.0 | 0.0 |
| bench-117 | yes | usable | 0.0 | 0.0 | 0.0 |
| bench-121 | no | harness: arm builder found no matching Solidity function/contract | n/a | n/a | n/a |
| bench-136 | no | harness: compile error in an arm | 0.0 | 0.0 | 0.0 |
| bench-148 | yes | usable (emit_only arm invalid: event cannot be emitted in a view/pure function) | 0.0 | 0.0 | n/a |
| bench-151 | no | harness: revert: oracle recompile of the staged sources fails (DeclarationError: Identifier already declared.); emit_only: oracle recompile of the staged sources fails (DeclarationError: Identifier already declared.) | 0.0 | n/a | n/a |
| bench-157 | no | harness: arm builder found no matching Solidity function/contract | n/a | n/a | n/a |
| bench-162 | yes | usable (emit_only arm invalid: event cannot be emitted in a view/pure function) | 0.0 | 0.0 | n/a |
| bench-181 | no | harness: revert: oracle recompile of the staged sources fails (contracts_CToken_CErc20Delegate.sol:10:28: DeclarationError: Identifier not found or not u); emit_only: oracle recompile of the staged sources fails (contracts_CToken | 0.0 | n/a | n/a |
| bench-198 | no | baseline: attack replay hits MemoryOOG/OutOfGas on the unchanged recompile (cause not isolated) | 0.0 | 0.0 | n/a |
| bench-21 | no | harness: revert: oracle recompile of the staged sources fails (_C_Crypto_Projects_xstable_contracts_XST2.sol:18:1: DeclarationError: Identifier already d); emit_only: oracle recompile of the staged sources fails (_C_Crypto_Projec | 0.0 | n/a | n/a |
| bench-220 | yes | usable | 0.0 | 1.0 | 1.0 |
| bench-23 | yes | usable | 0.0 | 0.0 | 0.0 |
| bench-237 | yes | usable (emit_only arm invalid: event cannot be emitted in a view/pure function) | 0.0 | 0.0 | n/a |
| bench-239 | yes | usable | 1.0 | 1.0 | 1.0 |
| bench-252 | no | harness: compile error in an arm | 0.0 | 0.0 | 0.0 |
| bench-257 | no | harness: arm builder found no matching Solidity function/contract | n/a | n/a | n/a |
| bench-266 | yes | usable | 0.0 | 0.0 | 0.0 |
| bench-27 | yes | usable | 0.0 | 0.0 | 0.0 |
| bench-31 | no | baseline: attack replay hits MemoryOOG/OutOfGas on the unchanged recompile (cause not isolated) | 0.0 | 0.0 | 0.0 |
| bench-336 | no | harness: revert: oracle recompile of the staged sources fails (contracts_interfaces_ILendingPoolCollateralManager.sol:10:1: DeclarationError: Declaration); emit_only: oracle recompile of the staged sources fails (contracts_interf | 0.0 | n/a | n/a |
| bench-34 | yes | usable (emit_only arm invalid: event cannot be emitted in a view/pure function) | 0.0 | 1.0 | n/a |
| bench-36 | yes | usable | 0.0 | 0.0 | 0.0 |
| bench-416 | no | baseline: attack replay hits MemoryOOG/OutOfGas on the unchanged recompile (cause not isolated) | 0.0 | 0.0 | 0.0 |
| bench-423 | no | harness: revert: oracle recompile of the staged sources fails (DeclarationError: Declaration ); emit_only: oracle recompile of the staged sources fails (DeclarationError: Declaration ) | 0.0 | n/a | n/a |
| bench-428 | yes | usable | 0.0 | 0.0 | 0.0 |
| bench-433 | no | baseline: historical attack does not reproduce before the patch | 0.0 | 0.0 | 0.0 |
| bench-434 | no | baseline: historical attack does not reproduce before the patch | 0.0 | 0.0 | 0.0 |
| bench-44 | yes | usable | 0.0 | 0.0 | 0.0 |
| bench-465 | no | harness: arm builder found no matching Solidity function/contract | n/a | n/a | n/a |
| bench-48 | no | harness: revert: oracle recompile of the staged sources fails (contracts_farm_facets_GovernanceFacet_GovernanceFacet.sol:17:1: DeclarationError: Identifi); emit_only: oracle recompile of the staged sources fails (contracts_farm_f | 0.0 | n/a | n/a |
| bench-483 | no | harness: arm builder found no matching Solidity function/contract | n/a | n/a | n/a |
| bench-515 | yes | usable | 0.0 | 1.0 | 1.0 |
| bench-518 | no | baseline: attack still passes after revert() in the vulnerable function | 0.0 | 0.0 | 0.0 |
| bench-524 | no | harness: revert: oracle recompile of the staged sources fails (DeclarationError: Declaration ); emit_only: oracle recompile of the staged sources fails (DeclarationError: Declaration ) | 0.0 | n/a | n/a |
| bench-53 | yes | usable (emit_only arm invalid: event cannot be emitted in a view/pure function) | 0.0 | 0.0 | n/a |
| bench-534 | yes | usable | 1.0 | 0.0 | 0.0 |
| bench-562 | no | baseline: attack replay hits MemoryOOG/OutOfGas on the unchanged recompile (cause not isolated) | 0.0 | 0.0 | 0.0 |
| bench-565 | yes | usable (emit_only arm invalid: event cannot be emitted in a view/pure function) | 0.0 | 0.0 | n/a |
| bench-567 | yes | usable | 1.0 | 0.0 | 0.0 |
| bench-57 | yes | usable | 0.0 | 0.0 | 0.0 |
| bench-72 | yes | usable | 0.0 | 0.0 | 0.0 |
| bench-77 | yes | usable (emit_only arm invalid: event cannot be emitted in a view/pure function) | 0.0 | 0.0 | n/a |
| bench-80 | yes | usable | 0.0 | 0.0 | 0.0 |
| bench-84 | yes | usable | 0.0 | 0.0 | 0.0 |

Usable cases: 23 of 47. Runs where our parse disagrees with the oracle's own verdict: 0.

| input | validate_patch CLI score 1.0 | usable cases with this arm | Wilson 95% interval |
|---|---|---|---|
| unchanged | 3 | 23 | 4.5% to 32.1% |
| revert | 4 | 23 | 7.0% to 37.1% |
| emit_only | 3 | 16 | 6.6% to 43.0% |
| emit_only counted as blocking the exploit | 16 | 16 | 80.6% to 100.0% |
| emit_only with attacker profit exactly unchanged | 8 | 16 | 28.0% to 72.0% |
