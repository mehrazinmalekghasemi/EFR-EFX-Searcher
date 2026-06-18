# Examples

## Based on Akrami et al.

### Valuations
*For Agent 0*:
- Her own bundle:
 - {1, 2. 3, 8} represtated by: 11100001 => 120
- Possible values of Agent 1's bundle after removal of a good from Agent 0's prespective:
 - {4}: 5
 - {6}: 3
- Possible values of Agent 2's bundle after removal of a good from Agent 0's prespective:
 - {5}: 4
 - {7}: 2

*For Agent 1*:
- Her own bundle:
 - {4,6} represtated by: 00010100 => 64
- Possible values of Agent 0's bundle after removal of a good from Agent 0's prespective:
 - {1,2,3}: 39
 - {1,2,8}: 60
 - {1,3,8}: 58
 - {2,3,8}: 59
- Possible values of Agent 2 bundle after removal of a good from Agent 0's prespective:
 - {5}: 14
 - {7}: 2

*For Agent 0*:
- Her own bundle:
 - {4,6} represtated by: 00010100 => 64
- Possible values of Agent 0's bundle after removal of a good from Agent 0's prespective:
 - {1,2,3}: 78
 - {1,2,8}: 91
 - {1,3,8}: 68
 - {2,3,8}: 31
- Possible values of Agent 2 bundle after removal of a good from Agent 0's prespective:
 - {4}: 3
 - {6}: 2


```
==========================================
 EFR ALLOCATION FOUND 
==========================================
Agent 0: Items [1, 2, 3, 8]
Agent 1: Items [4, 6]
Agent 2: Items [5, 7]

==========================================
 EFR VERIFICATION TRACE 
==========================================

--- AGENT 0 ---
Value of own bundle [1, 2, 3, 8]: 120
  -> Regarding Agent 1's bundle [4, 6]:
       Marginal values after uniform removal: [-4 => 3, -6 => 5]
       Expected value (E[V_i(A_j \ {g})]): 8 / 2 = 4.00
       Conclusion: 120 >= 4.00 (EFR Satisfied)
  -> Regarding Agent 2's bundle [5, 7]:
       Marginal values after uniform removal: [-5 => 2, -7 => 4]
       Expected value (E[V_i(A_j \ {g})]): 6 / 2 = 3.00
       Conclusion: 120 >= 3.00 (EFR Satisfied)

--- AGENT 1 ---
Value of own bundle [4, 6]: 64
  -> Regarding Agent 0's bundle [1, 2, 3, 8]:
       Marginal values after uniform removal: [-1 => 59, -2 => 58, -3 => 60, -8 => 39]
       Expected value (E[V_i(A_j \ {g})]): 216 / 4 = 54.00
       Conclusion: 64 >= 54.00 (EFR Satisfied)
  -> Regarding Agent 2's bundle [5, 7]:
       Marginal values after uniform removal: [-5 => 2, -7 => 14]
       Expected value (E[V_i(A_j \ {g})]): 16 / 2 = 8.00
       Conclusion: 64 >= 8.00 (EFR Satisfied)

--- AGENT 2 ---
Value of own bundle [5, 7]: 79
  -> Regarding Agent 0's bundle [1, 2, 3, 8]:
       Marginal values after uniform removal: [-1 => 31, -2 => 68, -3 => 91, -8 => 78]
       Expected value (E[V_i(A_j \ {g})]): 268 / 4 = 67.00
       Conclusion: 79 >= 67.00 (EFR Satisfied)
  -> Regarding Agent 1's bundle [4, 6]:
       Marginal values after uniform removal: [-4 => 2, -6 => 3]
       Expected value (E[V_i(A_j \ {g})]): 5 / 2 = 2.50
       Conclusion: 79 >= 2.50 (EFR Satisfied)
```

## Based on the Other Paper

### Valuations
#### (a) $r_0$-ranks

| | A | B | C | x | y |
|:---:|:---:|:---:|:---:|:---:|:---:|
| **A** | 1 | 2 | 2 | 4 | 6 |
| **B** | 2 | 1 | 5 | 1 | 3 |
| **C** | 2 | 5 | 1 | 1 | 3 |
| **x** | 4 | 1 | 1 | - | 1 |
| **y** | 6 | 3 | 3 | 1 | - |

#### (b) $r_1$-ranks
| | A | B | C | x | y |
|:---:|:---:|:---:|:---:|:---:|:---:|
| **A** | 1 | 5 | 2 | 1 | 3 |
| **B** | 5 | 1 | 2 | 1 | 3 |
| **C** | 2 | 2 | 1 | 4 | 6 |
| **x** | 1 | 1 | 4 | - | 1 |
| **y** | 3 | 3 | 6 | 1 | - |

#### (c) $r_2$-ranks
| | A | B | C | x | y |
|:---:|:---:|:---:|:---:|:---:|:---:|
| **A** | 1 | 2 | 5 | 1 | 3 |
| **B** | 2 | 1 | 2 | 4 | 6 |
| **C** | 5 | 2 | 1 | 1 | 3 |
| **x** | 1 | 4 | 1 | - | 1 |
| **y** | 3 | 6 | 3 | 1 | - |

### Instance

```
==========================================
 EFR ALLOCATION FOUND 
==========================================

*** 
Reminder: Mappings
A: 1,4 - B: 2,5 - C: 3,6 - x: 7 - y: 8
***

Agent 0: Items [2, 3, 7, 8] = [B, C, x, y]
Agent 1: Items [1, 5] = [A, B]
Agent 2: Items [4, 6] = [A, C]

==========================================
 EFR VERIFICATION TRACE 
==========================================

--- AGENT 0 ---
Value of own bundle [2, 3, 7, 8]: 7.    
  -> Regarding Agent 1's bundle [1,5]:
       Marginal values after uniform removal: [-1 => 1, -5 => 1]
       Expected value (E[V_i(A_j \ {g})]): 2 / 2 = 1.00
       Conclusion: 7 >= 1.00 (EFR Satisfied)
  -> Regarding Agent 2's bundle [4, 6]:
       Marginal values after uniform removal: [-4 => 1, -6 => 1]
       Expected value (E[V_i(A_j \ {g})]): 2 / 2 = 1.00
       Conclusion: 7 >= 1.00 (EFR Satisfied)

--- AGENT 1 ---
Value of own bundle [1, 5]: 5
  -> Regarding Agent 0's bundle [2, 3, 7, 8]:
       Marginal values after uniform removal: [-2 => 6, -3 => 4, -7 => 3, -4 => 6]
       Expected value (E[V_i(A_j \ {g})]): 19 / 4 = 4.75
       Conclusion: 5 >= 4.75 (EFR Satisfied)
  -> Regarding Agent 2's bundle [4, 6]:
       Marginal values after uniform removal: [-4 => 1, -6 => 1]
       Expected value (E[V_i(A_j \ {g})]): 2 / 2 = 1.00
       Conclusion: 5 >= 1.00 (EFR Satisfied)

--- AGENT 2 ---
Value of own bundle [6, 8]: 5
  -> Regarding Agent 0's bundle [2, 3, 7, 8]:
       Marginal values after uniform removal: [-2 => 4, -3 => 6, -7 => 6, -8 => 3]
       Expected value (E[V_i(A_j \ {g})]): 19 / 4 = 4.75
       Conclusion: 5 >= 4.75 (EFR Satisfied)
  -> Regarding Agent 1's bundle [1, 5]:
       Marginal values after uniform removal: [-1 => 1, -5 => 1]
       Expected value (E[V_i(A_j \ {g})]): 2 / 2 = 1.00
       Conclusion: 5 >= 1.00 (EFR Satisfied)
```