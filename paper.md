# Counterexamples to EFX for Submodular and Subadditive Valuations

Simon Mackenzie, Mashbat Suzuki

## Abstract

The paper constructs:

- a **three-agent, eight-good** instance with **monotone subadditive valuations** such that **no allocation satisfies \(\alpha\)-EFX** for any
  \[
  \alpha > \frac{1}{\sqrt[6]{2}} \approx 0.89
  \]
- a closely related **three-agent, eight-good** instance with **submodular (weighted coverage)** valuations for which **no EFX allocation exists**

Key feature: **symmetry** — agents’ valuations are identical up to relabeling of goods. This makes the counterexamples compact and human-verifiable.

## 1 Introduction

- Envy-freeness is a central fairness notion.
- For indivisible goods, EF is impossible in general.
- EFX (“envy-free up to any item”) is one of the strongest relaxations.
- Main question: **Does EFX always exist?**
- The paper answers with **structured counterexamples** in well-studied valuation classes.

It also notes that earlier general monotone counterexamples existed but were SAT-based and hard to verify manually.

## Theorem 1.1

There exists a fair division instance with **three agents and eight goods**, where every agent has a **weighted coverage valuation**, such that **no allocation is EFX**.

In particular, EFX need not exist for **monotone submodular valuations**.

## Theorem 1.2

There exists a fair division instance with **three agents and eight goods**, in which every agent has a **monotone subadditive valuation**, such that **no allocation is \(\alpha\)-EFX for any**
\[
\alpha \in (2^{-1/6}, 1].
\]

Additional content:

- The results are **highly symmetric**
- Goods are grouped as:
  \[
  A, A, B, B, C, C, x, y
  \]
- Agents share the same valuation structure; they differ only by cyclic relabeling of \(A, B, C\)
- The construction uses the same \(n=3\), \(m=8\) scale as Akrami et al.’s general counterexample
- Related work is introduced, including positive results for some 3-agent and subadditive cases

## Related work and motivation

Earlier EFX/near-EF work by Gourvès et al., Caragiannis et al., Plaut and Roughgarden is discussed.

For three agents, positive theory beyond additive valuations is mentioned.

Under subadditive valuations, exact EFX remains less understood.

A **\(1/2\)-EFX** allocation is known to exist for subadditive valuations.

The paper’s result shows no universal guarantee can exceed
\[
2^{-1/6} \approx 0.891.
\]

It contrasts the paper’s construction with Akrami et al.’s SAT-generated instance:

- Akrami et al. had large tables of all bundle rankings
- This paper instead uses a **compact cyclic typed obstruction**

# 2 A Cyclic Ordinal Obstruction to EFX

Agents have weak preferences over bundles.

Preferences are represented by **monotone rank functions**.

An allocation is EFX if for every agent \(i\), every agent \(j\), and every good \(g \in X_j\),
\[
X_i \succeq_i X_j \setminus \{g\}.
\]

The equivalent rank formulation is given.

## EFX-feasibility and strong envy

An allocation \(X=(X_1,\dots,X_n)\) is **EFX-feasible for agent \(i\)** if
\[
X_i \succeq_i X_j \setminus \{g\}
\quad \text{for all } j \in N,\ g \in X_j.
\]

Agent \(i\) **strongly-envies** agent \(j\) if there exists \(g \in X_j\) such that
\[
X_i \prec_i X_j \setminus \{g\}.
\]

An allocation is EFX iff it is EFX-feasible for every agent.

## Theorem 2.1

There exists an instance with **three agents and eight items**, with a **monotone weak preference profile**, such that **no allocation satisfies EFX**.

## Instance description

- Agents \(N=\{0,1,2\}\)
- Goods \(M=\{0,\dots,7\}\)
- Preferences are generated from a base order \(\succeq_0\)
- Cyclic relabeling permutation:
  \[
  \sigma=(0\ 1\ 2)(3\ 4\ 5)
  \]
- Preferences for agents 1 and 2 are defined by applying \(\sigma\) and \(\sigma^2\)

Example 2.2 illustrates how bundle comparisons transfer under the relabeling.

## 2.1 Base rank function

The base weak order is defined via a rank function \(r_0\):

- \(r_0(\emptyset)=0\)
- items partitioned into types:
  \[
  A=\{0,3\},\quad B=\{1,4\},\quad C=\{2,5\},\quad x=6,\quad y=7
  \]
- singleton ranks: \(r_0(\{g\})=1\)
- pair ranks given by a table
- triples:
  - **exceptional** triples containing one item from \(A \cup \{x\}\), one from \(B\), one from \(C\)
  - exceptional triples get rank 7
  - all other triples get the max internal pair rank
- sets of size at least 4 inherit the max rank of any internal triple

## Cyclic relabeling

The other agents’ rank functions are defined by cyclic relabeling:
\[
r_1(S)=r_0(\sigma(S)),\quad r_2(S)=r_0(\sigma^2(S))
\]
with \(\sigma=(0\ 1\ 2)(3\ 4\ 5)\)

**Observation 2.3:** each \(r_i\) is monotone.

## Lemma 2.4 (Cyclic Symmetry)

If \(X=(X_0,X_1,X_2)\) is EFX, then
\[
X^\sigma=(\sigma(X_1),\sigma(X_2),\sigma(X_0))
\]
is also EFX.

This lets the proof restrict attention to size patterns:

- \(|X_0|\le 1\)
- \((2,2,4)\)
- \((2,3,3)\)

## Proposition 2.5

Every allocation with \(|X_0|\le 1\) fails EFX.

Reference tables are then introduced:

- pair ranks for \(r_0,r_1,r_2\)
- exceptional triples for all three agents

## Lemma 2.6 (First-pair restriction)

If \(|X_0|=2\) and \(|X_1|,|X_2|\ge 2\), and agent 0 is EFX-feasible, then \(X_0\) must be one of:
\[
Ax,\ Ay,\ BC,\ By,\ Cy
\]

## Proposition 2.7

No allocation of size pattern \((2,2,4)\) is EFX.

### Proof sketch
The proof considers each possibility for \(X_0\), rules out \(Ax\), and then performs case analysis for:
- \(X_0=Ay\)
- \(X_0=BC\)
- \(X_0=By\)
- \(X_0=Cy\)

In each subcase, agent 1 strongly envies agent 2.

## Proposition 2.8

No allocation of size pattern \((2,3,3)\) is EFX.

### Proof sketch
Cases are handled for:
- \(X_0=Ax\)
- \(X_0=BC\)
- \(X_0=Ay\)
- \(X_0=By\)
- \(X_0=Cy\)

Again, unavoidable strong envy arises for agent 1 or 2 in every case.

## Proof of Theorem 2.1

By cyclic symmetry and size-pattern reduction, all allocations are ruled out, so no allocation satisfies EFX.

# 3 Weak Preferences to Submodular and Subadditive Valuations

In this section, the ordinal obstruction is realized by explicit cardinal valuations.

## Lemma 3.1

Let \(\{\succeq_i\}_{i \in N}\) be a weak preference profile over bundles for which no allocation satisfies EFX. Suppose that, for each agent \(i\), the valuation function \(v_i : 2^M \to \mathbb{R}\) is consistent with the strict part of \(\succeq_i\), in the sense that
\[
S \succ_i T \Rightarrow v_i(S) > v_i(T)
\]
for all bundles \(S, T \subseteq M\). Then no allocation satisfies EFX under the cardinal valuation profile \((v_i)_{i \in N}\).

### Proof
Consider any allocation \(X = (X_1, \ldots, X_n)\). Since \(X\) is not EFX with respect to the weak preference profile, there exist agents \(i, j \in N\) and a good \(g \in X_j\) such that
\[
X_j \setminus \{g\} \succ_i X_i.
\]
By consistency of \(v_i\) with the strict preference order, this implies
\[
v_i(X_j \setminus \{g\}) > v_i(X_i).
\]
Thus, agent \(i\) envies agent \(j\) even after the removal of \(g\), so \(X\) is not EFX under the cardinal valuations.

## 3.1 Subadditive valuations: an approximation barrier

Let \(\lambda = 2^{-1/6}\). Define valuation functions from the rank functions \(r_0, r_1, r_2\) constructed in Section 2. For each agent \(i\), define
\[
v_i(S) =
\begin{cases}
0, & \text{if } S = \emptyset, \\
\lambda^{7-r_i(S)}, & \text{if } S \neq \emptyset.
\end{cases}
\]

## Proposition 3.2

The profile \((v_0, v_1, v_2)\) is normalised, monotone, and subadditive.

### Proof
Normalisation is immediate. Monotonicity follows from Observation 2.3, since \(\lambda < 1\). It remains to prove subadditivity. Fix an agent \(i\) and let \(S, T \subseteq M\). If either set is empty, the claim is immediate. Otherwise, both sets are non-empty, and hence
\[
v_i(S) \ge \lambda^6 = \frac{1}{2}, \quad v_i(T) \ge \lambda^6 = \frac{1}{2}.
\]
Since the value of every set is at most \(1\), we obtain
\[
v_i(S) + v_i(T) \ge 1 \ge v_i(S \cup T).
\]
Thus \(v_i\) is subadditive.

## Lemma 3.3 (One rank gap gives the \(\alpha\)-gap)

Let \(\alpha > \lambda\). If \(S, T \neq \emptyset\) and
\[
r_i(T) > r_i(S),
\]
then
\[
v_i(S) < \alpha v_i(T).
\]

### Proof
Since the ranks are integer-valued, \(r_i(T) > r_i(S)\) implies \(r_i(T) \ge r_i(S) + 1\). Equivalently,
\[
7 - r_i(S) \ge 7 - r_i(T) + 1.
\]
By the definition of the valuation function, and using \(0 < \lambda < 1\), we therefore have
\[
v_i(S) = \lambda^{7-r_i(S)} \le \lambda^{7-r_i(T)+1} = \lambda \lambda^{7-r_i(T)} = \lambda v_i(T).
\]
Since \(\alpha > \lambda\), it follows that
\[
v_i(S) \le \lambda v_i(T) < \alpha v_i(T)
\]
as desired.

## Theorem 3.4

For every \(\alpha \in (2^{-1/6}, 1]\), the subadditive valuation profile \((v_0, v_1, v_2)\) admits no \(\alpha\)-EFX allocation.

### Proof
Suppose, for a contradiction, that \(X\) is an \(\alpha\)-EFX allocation. Since the underlying ordinal profile has no EFX allocation by Theorem 2.1, there exist agents \(i, j\) and a good \(g \in X_j\) such that
\[
r_i(X_j \setminus \{g\}) > r_i(X_i).
\]
If \(X_i = \emptyset\), then \(v_i(X_i)=0\), while \(X_j \setminus \{g\}\) is non-empty and hence has a positive value, so the \(\alpha\)-EFX inequality is violated. Otherwise, both \(X_i\) and \(X_j \setminus \{g\}\) are non-empty. By Lemma 3.3, we obtain
\[
v_i(X_i) < \alpha v_i(X_j \setminus \{g\}),
\]
which again contradicts \(\alpha\)-EFX. Therefore no \(\alpha\)-EFX allocation exists for the valuation profile.

Together with Proposition 3.2, this proves Theorem 1.2.

## 3.2 Submodular valuations via weighted coverage

### Instance description

The weighted-coverage valuation below is chosen to realise the strict comparisons of the rank order from Section 2. It depends only on which of the five types \(A, B, C, x, y\) are represented in a bundle. Thus, after the formula is given, strict consistency can be checked over the 32 possible type supports rather than over all \(2^8\) bundles.

For a set \(R \subseteq M\), define the coverage indicator
\[
\chi_R(S) = \mathbf{1}\{S \cap R \neq \emptyset\}.
\]

We define the base valuation \(u_0 : 2^M \to \mathbb{R}_{\ge 0}\) by
\[
u_0(S) =
\chi_B(S) + \chi_C(S)
+ 3\chi_{A \cup \{x\}}(S) + 3\chi_{B \cup \{y\}}(S) + 3\chi_{C \cup \{y\}}(S)
+ 8\chi_{A \cup B}(S) + 8\chi_{A \cup C}(S)
+ 9\chi_{B \cup \{x,y\}}(S) + 9\chi_{C \cup \{x,y\}}(S)
+ 2\chi_{A \cup B \cup \{y\}}(S) + 2\chi_{A \cup C \cup \{y\}}(S).
\]

The other two valuations are cyclic relabellings:
\[
u_1(S) = u_0(\sigma(S)), \quad u_2(S) = u_0(\sigma^2(S)).
\]

## Proposition 3.5

The profile \((u_0, u_1, u_2)\) consists of weighted coverage valuations. In particular, the valuations are normalised, monotone, and submodular.

### Proof
The function \(u_0\) is a non-negative linear combination of coverage indicators. Equivalently, for each displayed set \(R\), one may introduce a coverage atom whose weight is the coefficient of \(\chi_R\). Thus \(u_0\) is a weighted coverage valuation, and hence is normalised, monotone, and submodular. The valuations \(u_1\) and \(u_2\) are obtained from \(u_0\) by relabelling the goods, and therefore inherit the same properties.

# Proof of consistency

We now show that the weighted coverage function \(u_0\) is consistent with the weak monotone order from Section 2.

For a bundle \(S\), write \(\operatorname{supp}(S) \subseteq \{A, B, C, x, y\}\) for the set of types represented in \(S\). For example,
\[
\operatorname{supp}(AABB) = AB, \quad \operatorname{supp}(AACx) = ACx.
\]

In the next table, words such as AB, ACx, and BCxy denote type supports, not type multisets.

## Lemma 3.6 (Support collapse)

For every bundle \(S \subseteq M\), both \(r_0(S)\) and \(u_0(S)\) depend only on \(\operatorname{supp}(S)\).

### Proof
This is immediate for \(u_0\), since each term in its definition is a coverage indicator depending only on which types are represented in \(S\).

For \(r_0\), repeating a type does not create a higher rank: all singletons and same-type pairs have rank 1. A non-exceptional triple inherits the largest rank of an internal pair, while an exceptional triple exists exactly when the support contains ABC or BCx. For sets of size at least four, \(r_0\) is the maximum rank of an internal triple. Thus \(r_0(S)\) is determined entirely by \(\operatorname{supp}(S)\).

The only remaining point is that the coverage values strictly refine the rank order. Since both \(r_0\) and \(u_0\) depend only on type support, it is enough to check the 32 possible supports listed in Table 5. Thus the table is the finite certificate for strict consistency, not merely an illustration of the valuation.

## Table 5: Exhaustive support table for \(r_0\) and \(u_0\)

Words denote type supports. Thus the row AB, for example, includes AB, AAB, ABB, AABB.

- \(r_0(S) = 0\): \(\emptyset\)
- \(r_0(S) = 1\): \(21, 23, 28, 31, 35, x, A, B, C, y, xy, Bx, Cx\)
- \(r_0(S) = 2\): \(36, AB, AC\)
- \(r_0(S) = 3\): \(37, 40, By, Cy, Bxy, Cxy\)
- \(r_0(S) = 4\): \(41, 45, Ax, ABx, ACx\)
- \(r_0(S) = 5\): \(46, BC, BCy\)
- \(r_0(S) = 6\): \(47, 48, Ay, Axy, ABy, ACy, ABxy, ACxy\)
- \(r_0(S) = 7\): \(49, ABC, ABCx, ABCy, ABCxy, BCx, BCxy\)

## Lemma 3.7 (Strict consistency of the weighted-coverage realization)

For all bundles \(S, T \subseteq M\),
\[
r_0(S) > r_0(T) \Rightarrow u_0(S) > u_0(T).
\]

### Proof
By Lemma 3.6, it suffices to check type supports. There are exactly \(2^5 = 32\) type supports, since each of \(A, B, C, x, y\) is either present or absent. The supports in Table 5 are exhaustive: the table lists the empty support and
\[
8 + 2 + 4 + 3 + 2 + 6 + 6 = 31
\]
non-empty supports.

The value ranges in successive rank rows are strictly separated:
\[
0 < 21 \le 35 < 36 < 37 \le 40 < 41 \le 45 < 46 < 47 \le 48 < 49.
\]
Equivalently, the minimum value in each positive-rank row is larger than the maximum value in the preceding row. Therefore \(r_0(S) > r_0(T)\) implies \(u_0(S) > u_0(T)\). The statement for agents 1 and 2 follows from
\[
r_i(S) = r_0(\sigma^i(S)), \quad u_i(S) = u_0(\sigma^i(S)).
\]

## Theorem 3.8

The weighted-coverage valuation profile \((u_0, u_1, u_2)\) admits no EFX allocation.

### Proof
By Proposition 3.5, the profile consists of weighted coverage valuations, and by Lemma 3.7, it preserves every strict comparison of the ordinal profile constructed in Section 2. Since this ordinal profile admits no EFX allocation by Theorem 2.1, Lemma 3.1 implies that the weighted coverage profile also admits no EFX allocation.

As an independent check, we also ran the EFX-verification code of Akrami et al. [2026] on the valuation profiles constructed above. For each of the three profiles, namely the ordinal profile, the subadditive profile, and the weighted coverage profile, the code found no EFX allocation. These computations are not used in the proof and serve only as an additional verification of the explicit examples.

## 4 Discussion and Open Directions

Beyond the counterexamples themselves, the construction gives a useful way to organize the search for structured failures of EFX. The first step is ordinal: we specify only how agents rank bundles, and the non-existence proof uses only those rankings. The typed structure of the goods and the cyclic symmetry between the agents keep the proof small enough to check by hand: the case analysis is over bundle types such as Ay, BBCC, and CCx | AAB, rather than over arbitrary valuation tables.

The cardinal constructions then answer a separate question: which valuation classes can express the same ordinal pattern? For the subadditive result, the ranks are converted into separated numerical levels. For the submodular result, the weighted-coverage formula is chosen so that its values strictly preserve the relevant rank order. Thus the subadditive and weighted-coverage examples share the same underlying preference pattern, even though the cardinal valuations used to realize it are quite different.

This suggests a general strategy for finding counterexamples in restricted valuation classes. One can first look for monotone ordinal profiles with no EFX allocation and enough structure to be understandable. One can then ask whether those profiles, or small modifications of them, can be realized by valuations from a target class. The present paper shows that this approach can reach both monotone subadditive valuations and weighted coverage valuations.

The relabeling symmetry is also worth studying in its own right. In our examples, all agents share a single valuation template: they differ only in the permutation of the goods through which they evaluate bundles. This makes the profile far more restricted than an arbitrary heterogeneous one, yet still expressive enough to produce instances which admit no EFX allocations for both subadditive and weighted-coverage valuations. It would be interesting to understand which positive EFX results survive under this identical-up-to-relabeling assumption, and how useful this symmetry class is as a testing ground for fair division conjectures.

For subadditive valuations, the present construction leaves a large gap. A \(1/2\)-EFX allocation is known to exist, while our instance rules out \(\alpha\)-EFX for every \(\alpha \in (2^{-1/6}, 1]\). Improving the upper bound may require more goods or agents, but it may also require a different obstruction, or a realization in which the bad comparisons depend on more detailed cardinal information rather than only on ordinal rank gaps.

The weighted-coverage valuations are a strict subclass of submodular valuations. A natural next question is whether the failure persists in other well structured submodular classes. A gross-substitutes counterexample would already be significant, and an OXS counterexample would be stronger still. These classes are highly structured and economically important, but they are not contained in the MMS-feasible class. The known three-agent EFX existence result for two arbitrary monotone valuations and one MMS-feasible valuation therefore does not rule them out.

Another direction is to look for genuinely four-agent obstructions, where the failure uses a four-way interaction rather than extending a three-agent counterexample by adding agents or goods. Such examples might reveal new structural phenomena or lead to stronger approximation barriers.

## Acknowledgements

The paper is supported by the NSF–CSIRO project on **“Fair Sequential Collective Decision-Making”** and the ARC Laureate Project **FL200100204** on **“Trustworthy AI”**.

## References

- Hannaneh Akrami, Noga Alon, Bhaskar Ray Chaudhury, Jugal Garg, Kurt Mehlhorn, and Ruta Mehta. *EFX allocations: Simplifications and improvements*, 2022. URL: https://arxiv.org/abs/2205.07638.
- Hannaneh Akrami, Alexander Mayorov, Kurt Mehlhorn, Shreyas Srinivas, and Christoph Weidenbach. *A counterexample to EFX: n ≥ 3 agents, m ≥ n + 5 items, monotone valuations via SAT-solving*, 2026.
- Moshe Babaioff, Tomer Ezra, and Uriel Feige. *Fair and truthful mechanisms for dichotomous valuations*. In *Proceedings of the Thirty-Fifth AAAI Conference on Artificial Intelligence*, pages 5119–5126, 2021. doi: 10.1609/aaai.v35i6.16647.
- Siddharth Barman and Mashbat Suzuki. *Compatibility of fairness and nash welfare under subadditive valuations*. In *Proceedings of the 2026 Annual ACM-SIAM Symposium on Discrete Algorithms (SODA)*, pages 1724–1746. SIAM, 2026.
- Xiaolin Bu, Jiaxin Song, and Ziqi Yu. *EFX allocations exist for binary valuations*, 2023.
- I. Caragiannis, D. Kurokawa, H. Moulin, A. Procaccia, N. Shah, and J. Wang. *The unreasonable fairness of maximum Nash welfare*. In *Proceedings of the 2016 ACM Conference on Economics and Computation (EC)*, pages 305–322, 2016.
- Ioannis Caragiannis, David Kurokawa, Hervé Moulin, Ariel D. Procaccia, Nisarg Shah, and Junxing Wang. *The unreasonable fairness of maximum Nash welfare*. *ACM Transactions on Economics and Computation*, 7(3):12:1–12:32, 2019. doi: 10.1145/3355902.
- Bhaskar Ray Chaudhury, Jugal Garg, and Ruta Mehta. *Fair and efficient allocations under subadditive valuations*. In *Proceedings of the Thirty-Fifth AAAI Conference on Artificial Intelligence*, pages 5269–5276, 2021. doi: 10.1609/aaai.v35i6.16665.
- Laurent Gourvès, Jérôme Monnot, and Lydia Tlilane. *Near fairness in matroids*. In *Proceedings of the 21st European Conference on Artificial Intelligence*, pages 393–398, 2014. doi: 10.3233/978-1-61499-419-0-393.
- Benjamin Plaut and Tim Roughgarden. *Almost envy-freeness with general valuations*. *SIAM Journal on Discrete Mathematics*, 34(2):1039–1068, 2020. doi: 10.1137/19M124397X.
- Ariel D Procaccia. *Technical perspective: An answer to fair division’s most enigmatic question*. *Communications of the ACM*, 63(4):118–118, 2020.
- H. Steinhaus. *The problem of fair division*. *Econometrica*, 16(1):101–104, 1948.
