# Review: Section 1, synthetic data generator

Follow this template exactly. Every number below must be backed by raw rows or raw
output printed in full in this file (CLAUDE.md rule 10). No paraphrased results.

## 1. Outcome

- Instruction file: `instructions/01_section_1.md`
- Outcome: stopped
- Last step reached: 1.6 (every step 1.0 to 1.6 is built and committed)
- Stop reason (if stopped): 2 stop conditions, both reported with 2 options in
  `decisions/OPEN.md`:
  1. **Step 1.6, calibration band (instruction 01 F, CLAUDE.md rule 4).**
     `arrears_90p_max` = 0.0316166537 against the band [0.001, 0.025];
     `tests/test_full_profile.py::test_calibration_bands` fails. Every other band passes.
     No parameter was changed. The reference values in instruction 01 C differ by more
     than 1% on several counts (part C asks for a sentence on this): see O-35 and the
     evidence under step 1.6. Short version: an independent scalar re-implementation of
     part E reproduces this panel exactly, so the code follows part E as written here.
     The excess arrears sit in IO loans, where the 12-month payment shock at a fixed rate
     expiry is about 2.5. No single alternative reading found reproduces the reference.
  2. **Step 1.4, a test that cannot pass as specified (CLAUDE.md rule 5).**
     `tests/test_synth_simulate.py::test_hardship_spell_lengths` (p_hardship = 1, "every
     hardship spell lasts 3 to 6 consecutive rows") fails with a run of 60 rows. Under
     E.5 a loan re-enters hardship in the month after each spell ends, so with
     p_hardship = 1 the spells join into one run. The test is committed as written,
     neither loosened nor skipped. See O-34.

  Following rule 1 and the instruction 01 F pattern, everything that doesn't depend on
  either question was finished: steps 1.5 and 1.6, the committed full data, the review and
  the status file.

## 2. Commits

Output of `git log --oneline` for this section's commits, oldest last, pasted verbatim.

```
1c6b3e5 step 1.6: full profile in data/raw, truth and calibration CSVs (arrears_90p_max band fails)
3810181 step 1.5: trustee files in formats A and B, raw parquet files and manifest
d5dbe0e step 1.4: month loop of instruction 01 part E (hardship spell test fails as specified)
01a6fd3 step 1.3: deal table and static loan draws in instruction 01 D.3 order
a30053b step 1.2: geography, monthly cash rate and suburb HPI
bca5202 step 1.1: config dataclass tree and config table loaders
a7ec489 step 1.0: config amendments, part B decisions in PLAN and conventions, full marker
```

The review file and the status file are committed after these, as
`section 1: review file and open decisions` and `section 1: status file`.

## 3. Steps

### Step 1.0: plan and config updates

- Files: `config.toml`, `pyproject.toml`, `PLAN.md`, `docs/CONVENTIONS_RESOLVED.md`,
  `CLAUDE.md`
- Signatures implemented: none
- Tests: the existing suite, 7 passed
- Outputs: none
- Evidence: the `config.toml` diff against session 0 (`git diff 527fa69 HEAD -- config.toml`):

```
diff --git a/config.toml b/config.toml
index fb737a7..7faad42 100644
--- a/config.toml
+++ b/config.toml
@@ -15,7 +15,8 @@ first_issue = "2019-01"
 issue_span_months = 60
 seasoning_min = 6
 seasoning_max = 36
-call_threshold = 0.10
+# stylised clean-up call at 25% of issue balance (instruction 01 C)
+call_threshold = 0.25          # was 0.10
 call_detect_share = 0.95
 
 [profiles.full]
@@ -73,7 +74,7 @@ base = 100.0
 p_hardship = 0.002
 hardship_min = 3
 hardship_max = 6
-a0 = -5.52
+a0 = -6.0                      # was -5.52
 a_shock = 3.0
 a_ltv = 4.0
 ltv_knot = 0.8
@@ -83,8 +84,9 @@ io_recent_months = 12
 p_cure = [0.55, 0.30, 0.15]
 p_roll = [0.25, 0.40, 0.55]
 roll_shock = 1.5
-p_cure_90 = 0.05
-default_after_90_months = 6
+shock_lookback_months = 12     # new key, after roll_shock
+p_cure_90 = 0.10               # was 0.05
+default_after_90_months = 9    # was 6
 smm_start = 0.004
 smm_flat = 0.015
 smm_ramp_months = 30
@@ -102,7 +104,7 @@ sale_haircut = 0.80
 [calibration]
 rows_min = 700000
 rows_max = 1600000
-arrears_90p_min = 0.002
+arrears_90p_min = 0.001        # was 0.002
 arrears_90p_max = 0.025
 arrears_peak_from = "2023-06"
 arrears_peak_to = "2025-06"
@@ -110,6 +112,7 @@ cpr12_min = 0.08
 cpr12_max = 0.35
 fixed_cliff_ratio_min = 2.0
 min_deals_called = 3
+min_b_deals_called = 3         # new key, after min_deals_called
 
 [resubmissions]
 deal_months = [["D004", "2023-06"], ["D017", "2024-02"], ["D033", "2025-11"]]
```

- Deviations from PLAN.md or the instruction file:
  - Instruction 01 H 1.0 says "Add rule 17 to `CLAUDE.md`". `CLAUDE.md` already had a
    rule 17 (kickoff 1.8, two audiences), so the new rule is numbered **18** and rule 17 is
    kept. This is recorded under `CLAUDE.md` "Amendments". Rule 8's mention of the
    `calibration` marker now names `full`. Claude Code's safety check did not refuse the
    edit, so `CLAUDE.md` and `PLAN.md` are both committed in step 1.0 (O-1).
  - `addopts` is `--disable-socket -m "not full"`. A command-line `-m full` overrides the
    `addopts` marker expression, which is how the `full` tests are run.

### Step 1.1: config and table loaders

- Files: `rmbsq/config.py`, `tests/test_config.py`
- Signatures implemented: `load_config(path: Path = Path("config.toml")) -> Config` (frozen
  dataclass tree, 1 dataclass per TOML section, arrays as tuples); `load_originators`,
  `load_geography`, `load_cash_steps`, `load_hpi_drift`, each `(path: Path) -> pd.DataFrame`
- Tests: `test_config_round_trip`, `test_originators_csv`, `test_geography_csv`,
  `test_cash_rate_csv`, `test_hpi_drift_csv`, result passed
- Outputs: none
- Evidence: the 4 loaded tables, with dtypes (pandas 3.1 shows text columns as `str`)

```

##### config/originators.csv via load_originators
   code                name trustee_format
0  HARB  Harbour Home Loans              A
1   KOO   Kookaburra Mutual              A
2   WAT      Wattle Lending              A
3   CST      Coastline Bank              B
4   RED      Redgum Finance              B
code              str
name              str
trustee_format    str

##### config/geography.csv via load_geography
         city state  weight            area  beta
0      Sydney   NSW    0.32       Blacktown   1.2
1      Sydney   NSW    0.32      Parramatta   1.1
2      Sydney   NSW    0.32         Penrith   1.3
3      Sydney   NSW    0.32      Sutherland   0.9
4   Melbourne   VIC    0.28           Casey   1.2
5   Melbourne   VIC    0.28         Wyndham   1.3
6   Melbourne   VIC    0.28      Whittlesea   1.1
7   Melbourne   VIC    0.28      Boroondara   0.8
8    Brisbane   QLD    0.20         Ipswich   1.2
9    Brisbane   QLD    0.20           Logan   1.3
10   Brisbane   QLD    0.20     Moreton Bay   1.0
11   Brisbane   QLD    0.20  Brisbane Inner   0.9
12      Perth    WA    0.12        Wanneroo   1.1
13      Perth    WA    0.12       Joondalup   0.9
14      Perth    WA    0.12      Rockingham   1.2
15      Perth    WA    0.12        Stirling   1.0
16   Adelaide    SA    0.08       Salisbury   1.1
17   Adelaide    SA    0.08     Onkaparinga   1.0
18   Adelaide    SA    0.08        Playford   1.3
19   Adelaide    SA    0.08   Charles Sturt   0.9
city          str
state         str
weight    float64
area          str
beta      float64

##### config/cash_rate.csv via load_cash_steps
     period    rate
0   2016-01  0.0200
1   2016-05  0.0175
2   2016-08  0.0150
3   2019-06  0.0125
4   2019-07  0.0100
5   2019-10  0.0075
6   2020-03  0.0025
7   2020-11  0.0010
8   2022-05  0.0035
9   2022-06  0.0085
10  2022-07  0.0135
11  2022-08  0.0185
12  2022-09  0.0235
13  2022-10  0.0260
14  2022-11  0.0285
15  2022-12  0.0310
16  2023-02  0.0335
17  2023-03  0.0360
18  2023-05  0.0385
19  2023-06  0.0410
20  2023-11  0.0435
21  2025-02  0.0410
22  2025-05  0.0385
23  2025-08  0.0360
period        str
rate      float64

##### config/hpi_drift.csv via load_hpi_drift
      from       to  Sydney  Melbourne  Brisbane  Perth  Adelaide
0  2016-01  2017-12     0.6        0.7       0.2   -0.2       0.3
1  2018-01  2019-06    -0.8       -0.8       0.0   -0.6       0.0
2  2019-07  2020-03     0.8        0.8       0.3    0.0       0.2
3  2020-04  2020-09    -0.2       -0.2      -0.2    0.0      -0.2
4  2020-10  2022-03     1.6        1.0       2.0    0.8       1.7
5  2022-04  2023-01    -1.4       -1.0      -1.2    0.2       0.0
6  2023-02  2024-12     0.5        0.0       1.0    1.5       1.0
7  2025-01  2026-09     0.4        0.3       0.6    0.7       0.6
from             str
to               str
Sydney       float64
Melbourne    float64
Brisbane     float64
Perth        float64
Adelaide     float64
```

- Deviations from PLAN.md or the instruction file: `Config` has 1 field that isn't a TOML
  key, `root` (the folder holding `config.toml`). The synth functions take only `cfg`
  (kickoff 7) and need it to find `config/*.csv`. `config_to_dict` drops it, and the round
  trip test compares every TOML key and value.

### Step 1.2: geography, cash rate, HPI

- Files: `rmbsq/synth/geography.py`, `rmbsq/synth/rates.py`, `rmbsq/synth/hpi.py`,
  `rmbsq/synth/months.py` (month helpers: a month is an int, months since 1970-01),
  `tests/conftest.py`, `tests/test_synth_market.py`
- Signatures implemented: `build_geography(cfg)`, `build_cash_rate(cfg)`,
  `build_hpi(cfg, geo, rng)`
- Tests: `test_sixty_suburbs_in_order`, `test_cash_rate_points`, `test_hpi_deterministic`,
  `test_hpi_zero_noise_blacktown_north`, `test_hpi_frame_rows`, result passed
- Outputs: none committed
- Evidence: geography, the cash rate path, HPI for the first suburb of each city, and the
  zero-noise check

```

##### build_geography (60 rows)
         city state            area  beta                  suburb
0      Sydney   NSW       Blacktown   1.2         Blacktown North
1      Sydney   NSW       Blacktown   1.2       Blacktown Central
2      Sydney   NSW       Blacktown   1.2         Blacktown South
3      Sydney   NSW      Parramatta   1.1        Parramatta North
4      Sydney   NSW      Parramatta   1.1      Parramatta Central
5      Sydney   NSW      Parramatta   1.1        Parramatta South
6      Sydney   NSW         Penrith   1.3           Penrith North
7      Sydney   NSW         Penrith   1.3         Penrith Central
8      Sydney   NSW         Penrith   1.3           Penrith South
9      Sydney   NSW      Sutherland   0.9        Sutherland North
10     Sydney   NSW      Sutherland   0.9      Sutherland Central
11     Sydney   NSW      Sutherland   0.9        Sutherland South
12  Melbourne   VIC           Casey   1.2             Casey North
13  Melbourne   VIC           Casey   1.2           Casey Central
14  Melbourne   VIC           Casey   1.2             Casey South
15  Melbourne   VIC         Wyndham   1.3           Wyndham North
16  Melbourne   VIC         Wyndham   1.3         Wyndham Central
17  Melbourne   VIC         Wyndham   1.3           Wyndham South
18  Melbourne   VIC      Whittlesea   1.1        Whittlesea North
19  Melbourne   VIC      Whittlesea   1.1      Whittlesea Central
20  Melbourne   VIC      Whittlesea   1.1        Whittlesea South
21  Melbourne   VIC      Boroondara   0.8        Boroondara North
22  Melbourne   VIC      Boroondara   0.8      Boroondara Central
23  Melbourne   VIC      Boroondara   0.8        Boroondara South
24   Brisbane   QLD         Ipswich   1.2           Ipswich North
25   Brisbane   QLD         Ipswich   1.2         Ipswich Central
26   Brisbane   QLD         Ipswich   1.2           Ipswich South
27   Brisbane   QLD           Logan   1.3             Logan North
28   Brisbane   QLD           Logan   1.3           Logan Central
29   Brisbane   QLD           Logan   1.3             Logan South
30   Brisbane   QLD     Moreton Bay   1.0       Moreton Bay North
31   Brisbane   QLD     Moreton Bay   1.0     Moreton Bay Central
32   Brisbane   QLD     Moreton Bay   1.0       Moreton Bay South
33   Brisbane   QLD  Brisbane Inner   0.9    Brisbane Inner North
34   Brisbane   QLD  Brisbane Inner   0.9  Brisbane Inner Central
35   Brisbane   QLD  Brisbane Inner   0.9    Brisbane Inner South
36      Perth    WA        Wanneroo   1.1          Wanneroo North
37      Perth    WA        Wanneroo   1.1        Wanneroo Central
38      Perth    WA        Wanneroo   1.1          Wanneroo South
39      Perth    WA       Joondalup   0.9         Joondalup North
40      Perth    WA       Joondalup   0.9       Joondalup Central
41      Perth    WA       Joondalup   0.9         Joondalup South
42      Perth    WA      Rockingham   1.2        Rockingham North
43      Perth    WA      Rockingham   1.2      Rockingham Central
44      Perth    WA      Rockingham   1.2        Rockingham South
45      Perth    WA        Stirling   1.0          Stirling North
46      Perth    WA        Stirling   1.0        Stirling Central
47      Perth    WA        Stirling   1.0          Stirling South
48   Adelaide    SA       Salisbury   1.1         Salisbury North
49   Adelaide    SA       Salisbury   1.1       Salisbury Central
50   Adelaide    SA       Salisbury   1.1         Salisbury South
51   Adelaide    SA     Onkaparinga   1.0       Onkaparinga North
52   Adelaide    SA     Onkaparinga   1.0     Onkaparinga Central
53   Adelaide    SA     Onkaparinga   1.0       Onkaparinga South
54   Adelaide    SA        Playford   1.3          Playford North
55   Adelaide    SA        Playford   1.3        Playford Central
56   Adelaide    SA        Playford   1.3          Playford South
57   Adelaide    SA   Charles Sturt   0.9     Charles Sturt North
58   Adelaide    SA   Charles Sturt   0.9   Charles Sturt Central
59   Adelaide    SA   Charles Sturt   0.9     Charles Sturt South

##### build_cash_rate (129 rows)
      period    rate
0    2016-01  0.0200
1    2016-02  0.0200
2    2016-03  0.0200
3    2016-04  0.0200
4    2016-05  0.0175
5    2016-06  0.0175
6    2016-07  0.0175
7    2016-08  0.0150
8    2016-09  0.0150
9    2016-10  0.0150
10   2016-11  0.0150
11   2016-12  0.0150
12   2017-01  0.0150
13   2017-02  0.0150
14   2017-03  0.0150
15   2017-04  0.0150
16   2017-05  0.0150
17   2017-06  0.0150
18   2017-07  0.0150
19   2017-08  0.0150
20   2017-09  0.0150
21   2017-10  0.0150
22   2017-11  0.0150
23   2017-12  0.0150
24   2018-01  0.0150
25   2018-02  0.0150
26   2018-03  0.0150
27   2018-04  0.0150
28   2018-05  0.0150
29   2018-06  0.0150
30   2018-07  0.0150
31   2018-08  0.0150
32   2018-09  0.0150
33   2018-10  0.0150
34   2018-11  0.0150
35   2018-12  0.0150
36   2019-01  0.0150
37   2019-02  0.0150
38   2019-03  0.0150
39   2019-04  0.0150
40   2019-05  0.0150
41   2019-06  0.0125
42   2019-07  0.0100
43   2019-08  0.0100
44   2019-09  0.0100
45   2019-10  0.0075
46   2019-11  0.0075
47   2019-12  0.0075
48   2020-01  0.0075
49   2020-02  0.0075
50   2020-03  0.0025
51   2020-04  0.0025
52   2020-05  0.0025
53   2020-06  0.0025
54   2020-07  0.0025
55   2020-08  0.0025
56   2020-09  0.0025
57   2020-10  0.0025
58   2020-11  0.0010
59   2020-12  0.0010
60   2021-01  0.0010
61   2021-02  0.0010
62   2021-03  0.0010
63   2021-04  0.0010
64   2021-05  0.0010
65   2021-06  0.0010
66   2021-07  0.0010
67   2021-08  0.0010
68   2021-09  0.0010
69   2021-10  0.0010
70   2021-11  0.0010
71   2021-12  0.0010
72   2022-01  0.0010
73   2022-02  0.0010
74   2022-03  0.0010
75   2022-04  0.0010
76   2022-05  0.0035
77   2022-06  0.0085
78   2022-07  0.0135
79   2022-08  0.0185
80   2022-09  0.0235
81   2022-10  0.0260
82   2022-11  0.0285
83   2022-12  0.0310
84   2023-01  0.0310
85   2023-02  0.0335
86   2023-03  0.0360
87   2023-04  0.0360
88   2023-05  0.0385
89   2023-06  0.0410
90   2023-07  0.0410
91   2023-08  0.0410
92   2023-09  0.0410
93   2023-10  0.0410
94   2023-11  0.0435
95   2023-12  0.0435
96   2024-01  0.0435
97   2024-02  0.0435
98   2024-03  0.0435
99   2024-04  0.0435
100  2024-05  0.0435
101  2024-06  0.0435
102  2024-07  0.0435
103  2024-08  0.0435
104  2024-09  0.0435
105  2024-10  0.0435
106  2024-11  0.0435
107  2024-12  0.0435
108  2025-01  0.0435
109  2025-02  0.0410
110  2025-03  0.0410
111  2025-04  0.0410
112  2025-05  0.0385
113  2025-06  0.0385
114  2025-07  0.0385
115  2025-08  0.0360
116  2025-09  0.0360
117  2025-10  0.0360
118  2025-11  0.0360
119  2025-12  0.0360
120  2026-01  0.0360
121  2026-02  0.0360
122  2026-03  0.0360
123  2026-04  0.0360
124  2026-05  0.0360
125  2026-06  0.0360
126  2026-07  0.0360
127  2026-08  0.0360
128  2026-09  0.0360

##### HPI, first suburb of each city
m                  2016-01    2022-03    2022-04    2023-01    2026-09
suburb                                                                
Blacktown North 100.000000 152.049587 149.716399 126.850992 162.750611
Casey North     100.000000 136.693587 134.387285 119.933960 130.373500
Ipswich North   100.000000 166.485597 164.321824 143.817796 221.263670
Wanneroo North  100.000000  99.721658  99.275273 102.327554 173.372890
Salisbury North 100.000000 150.982940 150.576086 151.702433 224.481047

##### zero-noise check, Blacktown North
measured log HPI(2023-01) - log HPI(2022-03) = -0.168000000000001
expected 1.2 x 10 x (-1.4) / 100          = -0.168000000000000
difference                                = -1.027e-15
```

- Deviations from PLAN.md or the instruction file: none. HPI uses the recursive product
  of D.1 month by month, not `exp(cumsum)`.

### Step 1.3: deals and static loan attributes

- Files: `rmbsq/synth/deals.py`, `rmbsq/synth/loans.py`, `tests/test_synth_loans.py`
- Signatures implemented: `build_deals(cfg, n_deals) -> pd.DataFrame`;
  `draw_loans(cfg, geo, cash, rng) -> pd.DataFrame`
- Tests: `test_loans_per_deal_unique_ids[small]`, `test_loans_per_deal_unique_ids[full]`,
  `test_ltv_range_and_lmi_flag`, `test_fixed_share_by_era`, `test_null_end_months`,
  `test_deal_names`, result passed
- Outputs: none committed
- Evidence: the 50 deal table, the first 5 loans of D001, the fixed share by era, orig_ltv
  range and the lmi crosstab (full profile)

```

##### build_deals(cfg, 50)
   deal_id    deal_name originator     originator_name trustee_format issue_month
0     D001  HARB 2019-1       HARB  Harbour Home Loans              A     2019-01
1     D002   KOO 2019-1        KOO   Kookaburra Mutual              A     2019-02
2     D003   WAT 2019-1        WAT      Wattle Lending              A     2019-03
3     D004   CST 2019-1        CST      Coastline Bank              B     2019-04
4     D005   RED 2019-1        RED      Redgum Finance              B     2019-05
5     D006  HARB 2019-2       HARB  Harbour Home Loans              A     2019-07
6     D007   KOO 2019-2        KOO   Kookaburra Mutual              A     2019-08
7     D008   WAT 2019-2        WAT      Wattle Lending              A     2019-09
8     D009   CST 2019-2        CST      Coastline Bank              B     2019-10
9     D010   RED 2019-2        RED      Redgum Finance              B     2019-11
10    D011  HARB 2020-1       HARB  Harbour Home Loans              A     2020-01
11    D012   KOO 2020-1        KOO   Kookaburra Mutual              A     2020-02
12    D013   WAT 2020-1        WAT      Wattle Lending              A     2020-03
13    D014   CST 2020-1        CST      Coastline Bank              B     2020-04
14    D015   RED 2020-1        RED      Redgum Finance              B     2020-05
15    D016  HARB 2020-2       HARB  Harbour Home Loans              A     2020-07
16    D017   KOO 2020-2        KOO   Kookaburra Mutual              A     2020-08
17    D018   WAT 2020-2        WAT      Wattle Lending              A     2020-09
18    D019   CST 2020-2        CST      Coastline Bank              B     2020-10
19    D020   RED 2020-2        RED      Redgum Finance              B     2020-11
20    D021  HARB 2021-1       HARB  Harbour Home Loans              A     2021-01
21    D022   KOO 2021-1        KOO   Kookaburra Mutual              A     2021-02
22    D023   WAT 2021-1        WAT      Wattle Lending              A     2021-03
23    D024   CST 2021-1        CST      Coastline Bank              B     2021-04
24    D025   RED 2021-1        RED      Redgum Finance              B     2021-05
25    D026  HARB 2021-2       HARB  Harbour Home Loans              A     2021-07
26    D027   KOO 2021-2        KOO   Kookaburra Mutual              A     2021-08
27    D028   WAT 2021-2        WAT      Wattle Lending              A     2021-09
28    D029   CST 2021-2        CST      Coastline Bank              B     2021-10
29    D030   RED 2021-2        RED      Redgum Finance              B     2021-11
30    D031  HARB 2022-1       HARB  Harbour Home Loans              A     2022-01
31    D032   KOO 2022-1        KOO   Kookaburra Mutual              A     2022-02
32    D033   WAT 2022-1        WAT      Wattle Lending              A     2022-03
33    D034   CST 2022-1        CST      Coastline Bank              B     2022-04
34    D035   RED 2022-1        RED      Redgum Finance              B     2022-05
35    D036  HARB 2022-2       HARB  Harbour Home Loans              A     2022-07
36    D037   KOO 2022-2        KOO   Kookaburra Mutual              A     2022-08
37    D038   WAT 2022-2        WAT      Wattle Lending              A     2022-09
38    D039   CST 2022-2        CST      Coastline Bank              B     2022-10
39    D040   RED 2022-2        RED      Redgum Finance              B     2022-11
40    D041  HARB 2023-1       HARB  Harbour Home Loans              A     2023-01
41    D042   KOO 2023-1        KOO   Kookaburra Mutual              A     2023-02
42    D043   WAT 2023-1        WAT      Wattle Lending              A     2023-03
43    D044   CST 2023-1        CST      Coastline Bank              B     2023-04
44    D045   RED 2023-1        RED      Redgum Finance              B     2023-05
45    D046  HARB 2023-2       HARB  Harbour Home Loans              A     2023-07
46    D047   KOO 2023-2        KOO   Kookaburra Mutual              A     2023-08
47    D048   WAT 2023-2        WAT      Wattle Lending              A     2023-09
48    D049   CST 2023-2        CST      Coastline Bank              B     2023-10
49    D050   RED 2023-2        RED      Redgum Finance              B     2023-11

##### first 5 loans of D001, every column
                                   0                      1                    2                    3                    4
loan_id                    D001-0001              D001-0002            D001-0003            D001-0004            D001-0005
deal_id                         D001                   D001                 D001                 D001                 D001
originator                      HARB                   HARB                 HARB                 HARB                 HARB
trustee_format                     A                      A                    A                    A                    A
issue_month      2019-01-01 00:00:00    2019-01-01 00:00:00  2019-01-01 00:00:00  2019-01-01 00:00:00  2019-01-01 00:00:00
seasoning                         14                     13                   19                   17                   15
orig_month       2017-11-01 00:00:00    2017-12-01 00:00:00  2017-06-01 00:00:00  2017-08-01 00:00:00  2017-10-01 00:00:00
city                        Brisbane               Adelaide             Brisbane             Adelaide               Sydney
state                            QLD                     SA                  QLD                   SA                  NSW
area                           Logan          Charles Sturt                Logan          Onkaparinga           Sutherland
suburb                   Logan South  Charles Sturt Central          Logan South    Onkaparinga North     Sutherland South
orig_balance                339391.0               822127.0             280029.0             332613.0             816272.0
orig_ltv                    0.473699               0.661167             0.704108             0.798867             0.695832
orig_valuation              716469.0              1243448.0             397707.0             416356.0            1173087.0
lmi_flag                       False                  False                False                False                False
occupancy                   investor                  owner                owner                owner                owner
io_flag                         True                  False                False                False                False
io_end_month     2022-11-01 00:00:00                    NaT                  NaT                  NaT                  NaT
rate_type                   variable               variable             variable                fixed                fixed
fixed_term                      <NA>                   <NA>                 <NA>                   36                   24
fixed_end_month                  NaT                    NaT                  NaT  2020-08-01 00:00:00  2019-10-01 00:00:00
margin                      0.036883               0.025516             0.029088             0.020758             0.021604
fixed_rate                       NaN                    NaN                  NaN             0.033569             0.035088

##### fixed share by origination era (full profile)
                  era      n  fixed     share  target  diff_pp
0      before 2020-01  13860   1998  0.144156    0.15   -0.584
1  2020-01 to 2022-03   9668   3922  0.405668    0.40    0.567
2       after 2022-03   1472    146  0.099185    0.10   -0.082

##### orig_ltv min and max
min 0.3918086714  max 0.9482356066

##### lmi_flag x (orig_ltv > 0.80)
orig_ltv>0.80  False  True 
lmi_flag                   
False          17119      0
True               0   7881
```

- Deviations from PLAN.md or the instruction file: none. `draw_loans` reads `n_deals` and
  `loans_per_deal` from `cfg.deals`. `run_profile` (in `rmbsq/synth/generate.py`) sets
  those from `[profiles.<name>]` with `dataclasses.replace`.

### Step 1.4: monthly simulation

- Files: `rmbsq/synth/simulate.py`, `rmbsq/synth/generate.py` (`profile_config`,
  `run_profile`), `tests/conftest.py` (session fixture `small`),
  `tests/test_synth_simulate.py`
- Signatures implemented: `simulate(cfg, loans, cash, hpi, rng) -> (panel, deals)`, with
  the panel columns of part E and the deals frame with `issue_balance`
- Tests: `test_pi_annuity_matches_npf_pmt`, `test_io_switch_at_io_end`,
  `test_fixed_to_variable_switch`, `test_hardship_rows_frozen`,
  `test_default_after_months_in_90`, `test_call_property_small`,
  `test_every_deal_full_at_issue`, `test_simulate_deterministic`, result passed;
  **`test_hardship_spell_lengths`, result failed** (stop reason 2, O-34)
- Outputs: none committed
- Evidence: the hand-built cases and the small-profile properties

```

##### annuity case: D001-0001, P&I variable, orig 2018-06, month 2024-03 (age 69)
       period  opening_balance  scheduled_principal  curtailment  closing_balance  interest_rate  dpd_bucket  hardship_flag  months_in_90 exit_reason
27 2024-01-01        416673.63               549.22       416.12        415708.29         0.0685           0          False             0         NaN
28 2024-02-01        415708.29               551.81       415.16        414741.32         0.0685           0          False             0         NaN
29 2024-03-01        414741.32               554.40       414.19        413772.73         0.0685           0          False             0         NaN
30 2024-04-01        413772.73               557.01       413.22        412802.50         0.0685           0          False             0         NaN
31 2024-05-01        412802.50               559.63       412.24        411830.63         0.0685           0          False             0         NaN
interest = opening x rate / 12          = 2367.481702
scheduled_principal + interest          = 2921.881702
npf.pmt(rate/12, 360-69+1, -opening)    = 2921.883561
difference                              = -0.001859

##### IO switch case: io_end_month 2023-06, rows 2023-03 to 2023-09
       period  opening_balance  scheduled_principal  curtailment  closing_balance  interest_rate  dpd_bucket  hardship_flag  months_in_90 exit_reason
17 2023-03-01        472756.31                 0.00       472.76        472283.55         0.0610           0          False             0         NaN
18 2023-04-01        472283.55                 0.00       472.28        471811.27         0.0610           0          False             0         NaN
19 2023-05-01        471811.27                 0.00       471.81        471339.46         0.0635           0          False             0         NaN
20 2023-06-01        471339.46               615.47       470.72        470253.27         0.0660           0          False             0         NaN
21 2023-07-01        470253.27               618.24       469.64        469165.39         0.0660           0          False             0         NaN
22 2023-08-01        469165.39               621.02       468.54        468075.83         0.0660           0          False             0         NaN
23 2023-09-01        468075.83               623.81       467.45        466984.57         0.0660           0          False             0         NaN

##### fixed to variable case: D050, fixed_rate 0.045, fixed_end_month 2025-06, margin 0.025
       period  opening_balance  scheduled_principal  curtailment  closing_balance  interest_rate  dpd_bucket  hardship_flag  months_in_90 exit_reason  cash_plus_margin
16 2025-03-01        462607.97               718.82       461.89        461427.26         0.0450           0          False             0         NaN            0.0660
17 2025-04-01        461427.26               720.80       460.71        460245.75         0.0450           0          False             0         NaN            0.0660
18 2025-05-01        460245.75               722.77       459.52        459063.46         0.0450           0          False             0         NaN            0.0635
19 2025-06-01        459063.46               532.94       458.53        458071.99         0.0635           0          False             0         NaN            0.0635
20 2025-07-01        458071.99               535.23       457.54        457079.22         0.0635           0          False             0         NaN            0.0635
21 2025-08-01        457079.22               560.74       456.52        456061.96         0.0610           0          False             0         NaN            0.0610
22 2025-09-01        456061.96               563.02       455.50        455043.44         0.0610           0          False             0         NaN            0.0610

##### hardship case (p_hardship = 1, 50 loans): first loan, first and last 4 rows
         period  opening_balance  scheduled_principal  curtailment  closing_balance  interest_rate  dpd_bucket  hardship_flag  months_in_90 exit_reason
0    2021-10-01         500000.0                  0.0          0.0         500000.0          0.026           0           True             0         NaN
50   2021-11-01         500000.0                  0.0          0.0         500000.0          0.026           0           True             0         NaN
100  2021-12-01         500000.0                  0.0          0.0         500000.0          0.026           0           True             0         NaN
150  2022-01-01         500000.0                  0.0          0.0         500000.0          0.026           0           True             0         NaN
2800 2026-06-01         500000.0                  0.0          0.0         500000.0          0.061           0           True             0         NaN
2850 2026-07-01         500000.0                  0.0          0.0         500000.0          0.061           0           True             0         NaN
2900 2026-08-01         500000.0                  0.0          0.0         500000.0          0.061           0           True             0         NaN
2950 2026-09-01         500000.0                  0.0          0.0         500000.0          0.061           0           True             0         NaN
rows: 3000  hardship rows: 3000
hardship run length per loan (all 50 loans): [60]

##### default case (a0 = 50, 200 loans in D050): loan D050-0001 rows
         period  opening_balance  scheduled_principal  curtailment  closing_balance  interest_rate  dpd_bucket  hardship_flag  months_in_90 exit_reason
0    2023-11-01        498104.72                 0.00         0.00        498104.72         0.0685           1          False             0         NaN
200  2023-12-01        498104.72               437.39       497.67        497169.66         0.0685           0          False             0         NaN
400  2024-01-01        497169.66                 0.00         0.00        497169.66         0.0685           1          False             0         NaN
600  2024-02-01        497169.66               442.34       496.73        496230.59         0.0685           0          False             0         NaN
798  2024-03-01        496230.59                 0.00         0.00        496230.59         0.0685           1          False             0         NaN
995  2024-04-01        496230.59               447.36       495.78        495287.45         0.0685           0          False             0         NaN
1191 2024-05-01        495287.45                 0.00         0.00        495287.45         0.0685           1          False             0         NaN
1387 2024-06-01        495287.45               452.44       494.84        494340.17         0.0685           0          False             0         NaN
1583 2024-07-01        494340.17                 0.00         0.00        494340.17         0.0685           1          False             0         NaN
1779 2024-08-01        494340.17               457.58       493.88        493388.71         0.0685           0          False             0         NaN
1975 2024-09-01        493388.71                 0.00         0.00        493388.71         0.0685           1          False             0         NaN
2171 2024-10-01        493388.71                 0.00         0.00        493388.71         0.0685           1          False             0         NaN
2367 2024-11-01        493388.71               465.87       492.92        492429.92         0.0685           0          False             0         NaN
2563 2024-12-01        492429.92                 0.00         0.00        492429.92         0.0685           1          False             0         NaN
2748 2025-01-01        492429.92               471.18       491.96        491466.78         0.0685           0          False             0         NaN
2931 2025-02-01        491466.78                 0.00         0.00        491466.78         0.0660           1          False             0         NaN
3108 2025-03-01        491466.78                 0.00         0.00        491466.78         0.0660           1          False             0         NaN
3281 2025-04-01        491466.78                 0.00         0.00        491466.78         0.0660           1          False             0         NaN
3451 2025-05-01        491466.78                 0.00         0.00        491466.78         0.0635           2          False             0         NaN
3616 2025-06-01        491466.78                 0.00         0.00        491466.78         0.0635           2          False             0         NaN
3778 2025-07-01        491466.78                 0.00         0.00        491466.78         0.0635           3          False             0         NaN
3937 2025-08-01        491466.78                 0.00         0.00        491466.78         0.0610           4          False             1         NaN
4090 2025-09-01        491466.78                 0.00         0.00        491466.78         0.0610           4          False             2         NaN
4242 2025-10-01        491466.78                 0.00         0.00        491466.78         0.0610           4          False             3         NaN
4393 2025-11-01        491466.78                 0.00         0.00        491466.78         0.0610           4          False             4         NaN
4539 2025-12-01        491466.78                 0.00         0.00        491466.78         0.0610           4          False             5         NaN
4681 2026-01-01        491466.78                 0.00         0.00        491466.78         0.0610           4          False             6         NaN
4821 2026-02-01        491466.78                 0.00         0.00        491466.78         0.0610           4          False             7         NaN
4956 2026-03-01        491466.78                 0.00         0.00        491466.78         0.0610           4          False             8         NaN
5081 2026-04-01        491466.78                 0.00         0.00        491466.78         0.0610           4          False             9         NaN
5202 2026-05-01        491466.78                 0.00         0.00             0.00         0.0610           4          False            10   defaulted
exit counts: {'defaulted': 77, 'prepaid': 10, 'repurchased': 3}

##### small profile: rows per deal in its issue month
  deal_id issue_month  in_window  rows_in_issue_month
0    D001     2019-01      False                    0
1    D002     2019-07      False                    0
2    D003     2020-01      False                    0
3    D004     2020-07      False                    0
4    D005     2021-01      False                    0
5    D006     2021-07      False                    0
6    D007     2022-01       True                   40
7    D008     2022-07       True                   40
8    D009     2023-01       True                   40
9    D010     2023-07       True                   40

##### small profile: called deals, first month summed closing <= 0.25 x issue_balance, and call month
  deal_id  issue_balance first_below  closing_sum_then call_month  called_rows  rows_in_call_month
0    D001    27708623.86     2025-01        6853111.14    2025-02           13                  13
1    D002    23718665.70     2025-03        5399442.22    2025-04           11                  11
2    D006    23563888.81     2026-05        5761547.15    2026-06           13                  13
small profile rows: 12563
```

Independent check of the month loop. A separate scalar implementation goes loan by loan
in plain Python, written straight from the part E text. It starts from the same rng state
after the static draws and is compared with `simulate` on the small profile. The script is
in the appendix.

```
rows 12563 12563
opening_balance        max abs diff 0.000e+00
scheduled_principal    max abs diff 0.000e+00
curtailment            max abs diff 0.000e+00
closing_balance        max abs diff 0.000e+00
interest_rate          max abs diff 0.000e+00
exit_balance           max abs diff 0.000e+00
loss                   max abs diff 0.000e+00
indexed_value          max abs diff 0.000e+00
indexed_ltv            max abs diff 0.000e+00
issue_balance 0.0
scalar reference matches
```

- Deviations from PLAN.md or the instruction file:
  - The hardship property is split into 2 tests. `test_hardship_rows_frozen` checks
    dpd_bucket 0, scheduled_principal 0 and an unchanged closing_balance on every hardship
    row. `test_hardship_spell_lengths` checks the 3 to 6 row spell length. Neither is
    loosened, and the second fails (O-34). Both use p_hardship = 1, plus p_repurchase = 0
    so that no hardship row is an exit row; an exit row would have closing_balance 0.
  - The annuity test accepts |scheduled_principal + interest − pmt| ≤ 0.005. That is "to
    the cent" for a scheduled_principal rounded to the cent (E.8), plus 1e-9 of float
    slack. The measured difference is 0.001859.
  - The P&I, IO and fixed tests use a "quiet" config: p_hardship 0, a0 −50, smm_start and
    smm_flat 0, p_repurchase 0. That makes the loan's path certain (O-26).
  - The default test uses a0 = 50 and nothing else. It checks the property on every
    realised path, and no call or repurchase interfered (exits: 77 defaulted, 10 prepaid,
    3 repurchased).
  - The default and fixed-to-variable frames use deal D050 (issue 2023-11 on the full
    deal count), so the loans are live at issue and their arrears history is in the
    window. A constructed loan that originates after its deal's issue month would see
    issue_balance = 0 (E.10), and the deal would then be called at once (E.11).

### Step 1.5: trustee files

- Files: `rmbsq/synth/trustee_formats.py`, `rmbsq/synth/generate.py` (`write_raw`,
  `write_manifest`, `generate`), `tests/conftest.py` (session fixture `small_raw`),
  `tests/test_trustee_formats.py`
- Signatures implemented: `write_trustee_files(cfg, panel, loans, out_dir, rng_aux) ->
  dict[str, str]` (relative POSIX path → sha256); `generate(cfg, profile, out_dir) -> None`
- Tests: `test_arrears_days_in_bucket_range`, `test_format_b_cents_int64`,
  `test_called_exit_codes`, `test_resubmissions_exactly_d004`, `test_column_lists`,
  `test_manifest_hashes`, result passed
- Outputs: the small profile's raw files in a pytest temp folder
- Evidence: the raw rows (part I items 5 to 7) are under step 1.6 below, from the
  committed full profile
- Deviations from PLAN.md or the instruction file:
  - G.3 for format B: seq 1 cents = `round(true_cents × inflate)` on the integer cents
    ("rounded to the integer cent in B"). Format A uses `round(dollars × inflate, 2)`.
  - Missing strings (exit_code, fixed_end_month, io_end_month) are parquet nulls.

### Step 1.6: full generation and calibration

- Files: `scripts/generate_data.py`, `rmbsq/synth/truth.py` (`pool_monthly`,
  `calibration`, `write_csv`), `tests/test_full_profile.py`
- Signatures implemented: `scripts/generate_data.py --profile {full,small} --out DIR`
- Tests (`-m full`): `test_full_regenerates_identically`, result passed;
  **`test_calibration_bands`, result failed** (stop reason 1, O-35)
- Outputs: `data/raw/` (50 trustee files, `deals.parquet`, `hpi.parquet`,
  `cash_rate.parquet`, `MANIFEST.json`); `outputs/pool_monthly_truth.csv` (60 rows + header);
  `outputs/calibration.csv` (9 rows + header)
- Evidence (instruction 01 part I, items 1 to 8):

```

##### 1. outputs/calibration.csv, with the instruction 01 part C reference values
                 stat         value       band_lo       band_hi   pass reference_part_C
0                rows        773971        700000       1600000   True           781909
1     arrears_90p_min  0.0015363690  0.0010000000  0.0250000000   True          0.00197
2     arrears_90p_max  0.0316166537  0.0010000000  0.0250000000  False          0.01757
3  arrears_peak_month       2023-08       2023-06       2025-06   True          2024-06
4           cpr12_min  0.1633538401  0.0800000000  0.3500000000   True           0.1625
5           cpr12_max  0.1854878584  0.0800000000  0.3500000000   True           0.1757
6   fixed_cliff_ratio  3.0196049946  2.0000000000                 True             2.52
7        deals_called            14             3                 True               16
8      b_deals_called             5             3                 True                6

##### 2. outputs/pool_monthly_truth.csv, selected rows
     period  arrears_30p_bal  arrears_90p_bal  hardship_share_bal          cpr          cdr  wa_indexed_ltv         balance_total
0   2021-10     0.0033765924     0.0015363690        0.0088587626 0.1907889445 0.0005101112    0.5598055580 6238779623.6499996185
12  2022-10     0.0125871564     0.0047161343        0.0085198810 0.1627070425 0.0021662226    0.5647931137 7678169812.4799995422
24  2023-10     0.0394367653     0.0299324837        0.0077939193 0.1716014713 0.0095060659    0.5749715361 8826728609.7700004578
32  2024-06     0.0248670443     0.0178466032        0.0095152316 0.1509215281 0.0217327060    0.5438529858 7799399222.6699991226
48  2025-10     0.0103771005     0.0078391119        0.0099149520 0.2076662310 0.0155876073    0.4908609627 5393904335.8499994278
59  2026-09     0.0049816370     0.0035302940        0.0084910177 0.1962578486 0.0020223732    0.4616355957 3811404242.1300005913

##### 3. called deals (full profile)
   deal_id originator trustee_format call_month
0     D001       HARB              A    2025-03
1     D002        KOO              A    2025-01
2     D003        WAT              A    2025-03
3     D004        CST              B    2025-12
4     D005        RED              B    2025-09
5     D006       HARB              A    2025-05
6     D007        KOO              A    2026-03
7     D008        WAT              A    2026-05
8     D009        CST              B    2025-12
9     D010        RED              B    2026-04
10    D011       HARB              A    2026-01
11    D012        KOO              A    2026-05
12    D013        WAT              A    2026-03
13    D014        CST              B    2026-07

##### 4a. exits by reason (full profile)
exit_reason
prepaid        11408
called          2078
defaulted        656
repurchased      386

##### 4b. rows by dpd_bucket and hardship_flag (full profile)
hardship_flag   False  True     All
dpd_bucket                         
0              743926  6554  750480
1                7916     0    7916
2                3245     0    3245
3                2151     0    2151
4               10179     0   10179
All            767417  6554  773971

##### 5. first 12 rows of data/raw/deals.parquet
   deal_id    deal_name originator     originator_name trustee_format issue_month  issue_balance
0     D001  HARB 2019-1       HARB  Harbour Home Loans              A     2019-01   295233241.52
1     D002   KOO 2019-1        KOO   Kookaburra Mutual              A     2019-02   282292913.23
2     D003   WAT 2019-1        WAT      Wattle Lending              A     2019-03   297659210.59
3     D004   CST 2019-1        CST      Coastline Bank              B     2019-04   281061725.34
4     D005   RED 2019-1        RED      Redgum Finance              B     2019-05   287074175.72
5     D006  HARB 2019-2       HARB  Harbour Home Loans              A     2019-07   298093224.03
6     D007   KOO 2019-2        KOO   Kookaburra Mutual              A     2019-08   287230096.19
7     D008   WAT 2019-2        WAT      Wattle Lending              A     2019-09   284421370.89
8     D009   CST 2019-2        CST      Coastline Bank              B     2019-10   284062373.94
9     D010   RED 2019-2        RED      Redgum Finance              B     2019-11   286137788.23
10    D011  HARB 2020-1       HARB  Harbour Home Loans              A     2020-01   283046558.26
11    D012   KOO 2020-1        KOO   Kookaburra Mutual              A     2020-02   287693870.29

##### 6a. format A rows (data/raw/trustee_a/D001.parquet): 1 called exit, 1 hardship row, 1 row at 90+
                                  9283                    288              775 
loan_id                      D001-0004               D001-0465        D001-0294
deal_id                           D001                    D001             D001
report_month                   2025-03                 2021-10          2021-12
submission_seq                       1                       1                1
opening_balance              259482.45               382135.54        751969.75
scheduled_principal                0.0                     0.0              0.0
curtailment                        0.0                     0.0              0.0
closing_balance                    0.0               382135.54        751969.75
interest_rate                 0.061758                 0.02776         0.029415
arrears_days                         0                       0              103
hardship_flag                        0                       1                0
exit_code                         CALL                     NaN              NaN
exit_balance                 259482.45                     0.0              0.0
loss_amount                        0.0                     0.0              0.0
orig_month                     2017-08                 2018-04          2016-02
orig_balance                  332613.0                397341.0         816251.0
orig_valuation                416356.0                477191.0        1048697.0
orig_ltv                      0.798867                0.832667         0.778348
rate_type                        fixed                variable         variable
fixed_end_month                2020-08                     NaN              NaN
io_flag                              0                       1                1
io_end_month                       NaN                 2023-04          2021-02
occupancy                        owner                investor            owner
lmi_flag                             0                       1                0
city                          Adelaide                Brisbane           Sydney
state                               SA                     QLD              NSW
area                       Onkaparinga          Brisbane Inner        Blacktown
suburb               Onkaparinga North  Brisbane Inner Central  Blacktown South

##### 6b. format B rows (data/raw/trustee_b/D004.parquet): 1 called exit, 1 hardship row, 1 row at 90+
                                    11868          83                1575 
LoanId                          D004-0001      D004-0127         D004-0022
DealId                               D004           D004              D004
ReportMonth                       2025-12        2021-10           2022-03
SubmissionSeq                           1              1                 1
OpeningBalanceCents              41685298      168155451          71947356
ScheduledPrincipalCents                 0              0                 0
CurtailmentCents                        0              0                 0
ClosingBalanceCents                     0      168155451          71947356
InterestRate                     0.058451       0.033439          0.032923
MissedPayments                          0              0                 4
Status                                  C              H                 A
ExitCode                                P            NaN               NaN
ExitBalanceCents                 41685298              0                 0
LossAmountCents                         0              0                 0
OrigMonth                         2017-04        2017-01           2016-08
OrigBalanceCents                 55586400      193479600          77293100
OrigValuationCents               75180200      234353400         107840700
OrigLtv                          0.739375       0.825589          0.716734
RateType                         variable       variable          variable
FixedEndMonth                         NaN            NaN               NaN
IoFlag                                  0              0                 1
IoEndMonth                            NaN            NaN           2021-08
Occupancy                           owner          owner             owner
LmiFlag                                 0              1                 0
City                                Perth         Sydney            Sydney
State                                  WA            NSW               NSW
Area                             Stirling        Penrith        Sutherland
Suburb                   Stirling Central  Penrith South  Sutherland North

##### 7. both submission_seq rows for the first 3 loans of D004 2023-06
         LoanId ReportMonth  SubmissionSeq  OpeningBalanceCents  ScheduledPrincipalCents  CurtailmentCents  ClosingBalanceCents  MissedPayments Status ExitCode
5681  D004-0001     2023-06              1             45131487                    67359             45515             45469255               0      C      NaN
5682  D004-0001     2023-06              2             45131487                    67359             45064             45019064               0      C      NaN
5683  D004-0002     2023-06              1             13077862                    17279             13192             13177997               0      C      NaN
5684  D004-0002     2023-06              2             13077862                    17279             13061             13047522               0      C      NaN
5685  D004-0004     2023-06              1             58988189                    73056             59504             59444780               0      C      NaN
5686  D004-0004     2023-06              2             58988189                    73056             58915             58856218               0      C      NaN
D004 2023-06 rows: 486  seq 1: 243  seq 2: 243
D004 2023-06: rows 486, seq 2 rows 243, seq 2 rows in other months 0
D017 2024-02: rows 518, seq 2 rows 259, seq 2 rows in other months 0
D033 2025-11: rows 490, seq 2 rows 245, seq 2 rows in other months 0

##### 8. manifest and size
MANIFEST entries: 53; files under data/raw incl. MANIFEST: 54
total size of data/raw: 28412804 bytes = 28.41 MB
{
  "cash_rate.parquet": "7c8b58dbf3b446b1cd677698e63fd2776c5be186d487a8dcefbab3f499cd73df",
  "deals.parquet": "6f186f68847ec94fec12c1e88ae1f5fda67fc7adf4460daf3f77f51dc961651d",
  "hpi.parquet": "e29b289033e5c242d45162fd4ed97b45d8438908d4f9ead6aeb3bc37e439cdf5"
}
```

Item 8, full generation runtime: `python scripts/generate_data.py --profile full --out
data/raw` printed `profile full: 773971 rows, raw files in 10.9 s, total 11.5 s` (wall
clock 12.75 s by `time`). The regeneration in section 5 below printed `raw files in 8.4 s,
total 8.8 s`.

Diagnostics for the arrears band (O-35). First: seed variation (the config seed and 4
others) and 90+ arrears by origination IO flag and rate type:

```
seed     rows  defaulted  arrears_90p_max  peak     fixed_cliff  deals_called
20261029 773971        656           0.0316  2023-08         3.02            14
1        768025        674           0.0348  2023-08         2.53            15
2        772439        651           0.0298  2023-09         2.52            16
3        771359        656           0.0288  2023-08         2.66            14
4        765557        650           0.0300  2023-09         2.93            17

arrears_90p_bal by origination IO flag / rate_type, every 3rd month (seed from config)
grp      IO/fixed  IO/variable  PI/fixed  PI/variable    pool
period                                                       
2021-10    0.0000       0.0011    0.0017       0.0017  0.0015
2022-01    0.0032       0.0034    0.0007       0.0018  0.0020
2022-04    0.0039       0.0059    0.0006       0.0020  0.0026
2022-07    0.0091       0.0053    0.0006       0.0018  0.0026
2022-10    0.0146       0.0092    0.0009       0.0035  0.0047
2023-01    0.0260       0.0264    0.0024       0.0063  0.0103
2023-04    0.0633       0.0454    0.0052       0.0099  0.0187
2023-07    0.1181       0.0759    0.0088       0.0122  0.0296
2023-10    0.1473       0.0698    0.0098       0.0110  0.0299
2024-01    0.1495       0.0510    0.0144       0.0090  0.0266
2024-04    0.1466       0.0192    0.0138       0.0091  0.0208
2024-07    0.1394       0.0082    0.0117       0.0062  0.0163
2024-10    0.1490       0.0057    0.0097       0.0026  0.0139
2025-01    0.1218       0.0074    0.0090       0.0026  0.0123
2025-04    0.1240       0.0047    0.0104       0.0033  0.0126
2025-07    0.1000       0.0056    0.0070       0.0024  0.0099
2025-10    0.0802       0.0024    0.0076       0.0018  0.0078
2026-01    0.0538       0.0041    0.0071       0.0012  0.0061
2026-04    0.0269       0.0030    0.0043       0.0026  0.0045
2026-07    0.0171       0.0023    0.0022       0.0024  0.0032

share of window balance by group: {'IO/fixed': 0.0608, 'IO/variable': 0.1761, 'PI/fixed': 0.1898, 'PI/variable': 0.5733}
```

Second: alternative readings of part E, tried by patching the payment function in a
scratch copy. Neither goes into the repo. V1 computes every payment as an annuity
(scheduled principal is still 0 while IO). V2 uses n = term − age.

```
as written                         rows  773971 a90max 0.03162 peak 2023-08 cpr12 0.1634-0.1855 cliff 3.02 called 14 P11408 C2078 D656 R386
V1 payment ignores IO              rows  777575 a90max 0.01290 peak 2023-10 cpr12 0.1633-0.1874 cliff 3.23 called 15 P11642 C2235 D312 R381
V2 n = term - age                  rows  771600 a90max 0.03162 peak 2023-08 cpr12 0.1634-0.1893 cliff 3.09 called 15 P11370 C2253 D671 R369
```

The comparison part C asks for (beyond about 1% on a count, or a different list of
called deals):
- **Rows:** 773,971 here, 781,909 in the reference (−1.0%).
- **Small profile:** 12,563 rows and 3 called deals here (D001, D002, D006), against
  12,570 and 3. That is close but not identical, which points to a rule difference
  rather than a whole different implementation.
- **Exits:** prepaid 11,408 (+1.7%), called 2,078 (−14%), defaulted 656 (+44%) and
  repurchased 386 (+4.6%), against 11,217, 2,429, 457 and 369.
- **Called deals:** 14 here (D001 to D014), against 16. The format B deals called are
  D004, D005, D009, D010 and D014 here, against D004, D005, D009, D010, D015 and D020.

**The rule I think differs is how IO loans enter the payment shock (E.4).** As written,
an IO loan's payment is B × r / 12 at both ends of the 12-month lookback, so the shock
moves 1 for 1 with the rate. A fixed IO loan reaching expiry goes from about 2% to about
7%, a shock near 2.5. 90+ arrears on IO/fixed loans then reach 15%, and on IO/variable
loans 7.6% in 2023-07. Those 2 groups are 24% of window balance, and they produce the
2023-08 peak. V1, which removes IO from the shock, brings arrears_90p_max to 0.0129 with
the peak at 2023-10. So the reference treats IO in some third way, which I could not
identify from the text. The scalar re-implementation above is the exact reading used
here, for comparison with the reference code.

- Deviations from PLAN.md or the instruction file:
  - The script writes the CSVs to `outputs/` under the repo root for any `--out`, as
    instruction 01 H 1.6 says.
  - In `calibration.csv`, the one-sided bands (`fixed_cliff_ratio`, `deals_called`,
    `b_deals_called`) have an empty `band_hi`. Integer statistics are written as integers
    and floats as `%.10f`.
  - `pool_monthly_truth.csv` writes `period` as YYYY-MM. Its columns are those of
    `pool_monthly.csv` (kickoff 7).

## 4. Full test suite

Command and its complete output (offline, `--disable-socket`), in the working copy at
`1c6b3e5`.

```
$ .venv/Scripts/python -m pytest -v -p no:cacheprovider
tests/test_config.py::test_config_round_trip PASSED                      [  2%]
tests/test_config.py::test_originators_csv PASSED                        [  5%]
tests/test_config.py::test_geography_csv PASSED                          [  7%]
tests/test_config.py::test_cash_rate_csv PASSED                          [ 10%]
tests/test_config.py::test_hpi_drift_csv PASSED                          [ 13%]
tests/test_placeholder.py::test_skeleton_imports[rmbsq] PASSED           [ 15%]
tests/test_placeholder.py::test_skeleton_imports[rmbsq.synth] PASSED     [ 18%]
tests/test_placeholder.py::test_skeleton_imports[rmbsq.canonical] PASSED [ 21%]
tests/test_placeholder.py::test_skeleton_imports[rmbsq.semantic] PASSED  [ 23%]
tests/test_placeholder.py::test_skeleton_imports[rmbsq.llm] PASSED       [ 26%]
tests/test_placeholder.py::test_skeleton_imports[rmbsq.eval] PASSED      [ 28%]
tests/test_placeholder.py::test_skeleton_imports[rmbsq.deliverable] PASSED [ 31%]
tests/test_synth_loans.py::test_loans_per_deal_unique_ids[small] PASSED  [ 34%]
tests/test_synth_loans.py::test_loans_per_deal_unique_ids[full] PASSED   [ 36%]
tests/test_synth_loans.py::test_ltv_range_and_lmi_flag PASSED            [ 39%]
tests/test_synth_loans.py::test_fixed_share_by_era PASSED                [ 42%]
tests/test_synth_loans.py::test_null_end_months PASSED                   [ 44%]
tests/test_synth_loans.py::test_deal_names PASSED                        [ 47%]
tests/test_synth_market.py::test_sixty_suburbs_in_order PASSED           [ 50%]
tests/test_synth_market.py::test_cash_rate_points PASSED                 [ 52%]
tests/test_synth_market.py::test_hpi_deterministic PASSED                [ 55%]
tests/test_synth_market.py::test_hpi_zero_noise_blacktown_north PASSED   [ 57%]
tests/test_synth_market.py::test_hpi_frame_rows PASSED                   [ 60%]
tests/test_synth_simulate.py::test_pi_annuity_matches_npf_pmt PASSED     [ 63%]
tests/test_synth_simulate.py::test_io_switch_at_io_end PASSED            [ 65%]
tests/test_synth_simulate.py::test_fixed_to_variable_switch PASSED       [ 68%]
tests/test_synth_simulate.py::test_hardship_rows_frozen PASSED           [ 71%]
tests/test_synth_simulate.py::test_hardship_spell_lengths FAILED         [ 73%]
tests/test_synth_simulate.py::test_default_after_months_in_90 PASSED     [ 76%]
tests/test_synth_simulate.py::test_call_property_small PASSED            [ 78%]
tests/test_synth_simulate.py::test_every_deal_full_at_issue PASSED       [ 81%]
tests/test_synth_simulate.py::test_simulate_deterministic PASSED         [ 84%]
tests/test_trustee_formats.py::test_arrears_days_in_bucket_range PASSED  [ 86%]
tests/test_trustee_formats.py::test_format_b_cents_int64 PASSED          [ 89%]
tests/test_trustee_formats.py::test_called_exit_codes PASSED             [ 92%]
tests/test_trustee_formats.py::test_resubmissions_exactly_d004 PASSED    [ 94%]
tests/test_trustee_formats.py::test_column_lists PASSED                  [ 97%]
tests/test_trustee_formats.py::test_manifest_hashes PASSED               [100%]
FAILED tests/test_synth_simulate.py::test_hardship_spell_lengths - AssertionE...
================= 1 failed, 37 passed, 2 deselected in 2.13s ==================

$ .venv/Scripts/python -m pytest -v -m full -p no:cacheprovider
tests/test_full_profile.py::test_calibration_bands FAILED                [ 50%]
tests/test_full_profile.py::test_full_regenerates_identically PASSED     [100%]
        failed = [r for r in rows if r["pass"] != "True"]
>       assert not failed, failed
FAILED tests/test_full_profile.py::test_calibration_bands - AssertionError: [...
================= 1 failed, 1 passed, 38 deselected in 15.35s =================
```

## 5. Determinism

The outputs regenerated twice and compared byte for byte (SHA-256 of each file, both runs).
Run 1 is the committed generation into `data/raw/`. Run 2 is
`python scripts/generate_data.py --profile full --out <scratch>/run2`, which rewrote
`outputs/*.csv` in place. Afterwards `git status` was clean.

```
run 1 (committed data/raw and outputs/):
ceac9c2f6edb42c67f319225f2858d0ed76941f22459173063aef7c70e1be73f *./MANIFEST.json
7c8b58dbf3b446b1cd677698e63fd2776c5be186d487a8dcefbab3f499cd73df *./cash_rate.parquet
6f186f68847ec94fec12c1e88ae1f5fda67fc7adf4460daf3f77f51dc961651d *./deals.parquet
e29b289033e5c242d45162fd4ed97b45d8438908d4f9ead6aeb3bc37e439cdf5 *./hpi.parquet
79270caa48ea8f6498128cd7cd11edbf4af61bfde2defbaadca4433b652b0d32 *./trustee_a/D001.parquet
0505917afa601c960ad0f286b9ab1d6729695c3f15ccdcf3ba4d989c5702d826 *./trustee_a/D002.parquet
34ea164253d9625fb55e52ac454c6232218da4faf3998fe2789bb74d97b69d3c *./trustee_a/D003.parquet
99fe834ab0a46ba0a4e8dd216879c51484aecb4e5be7d33e2bc00e835e5d97a4 *./trustee_a/D006.parquet
6b277185ace0e4ad152c934eb4c5ef373e561ba5e0817f9bd3ffba584b147732 *./trustee_a/D007.parquet
a92ff2cd8979c700fddcd31bc31609ade132e72f8ad7093f591ca3f59debfd65 *./trustee_a/D008.parquet
428378e26ea3097ebc52c413cfbb620dd5fb4a0cce640fe5e77ac6a14a9a84f3 *./trustee_a/D011.parquet
8dd904596a56e0925948c2cbedef7a6d53530297cd1c47223071c3e1b98e3b26 *./trustee_a/D012.parquet
e19eb8721c49e76d1123e1aed242c3d8065879ddcf96301a3b022de3de250abc *./trustee_a/D013.parquet
25714ecc5d89747130d2f2451c00248d4a931cbdbec19d450d9edfa271df89e1 *./trustee_a/D016.parquet
395ab45d82753561c1beba71caa121fb80ad5fd8a0b6590340bdaa58e5960970 *./trustee_a/D017.parquet
fa1f2d91fc5fa77824a8a9b07c23347ebb1dc54318a3e34c1ad27b2fb1f3ac0d *./trustee_a/D018.parquet
20f74aea1c715a32b60fa98869f732c72e2f6b9d7ca072e78a038cbc14944e1c *./trustee_a/D021.parquet
d312d0f03ba87edfa54d648e4321fbdb6b562d177d8bb77c3ade326812abee52 *./trustee_a/D022.parquet
ba24de349db7f271ebb10554ce653184b5e81fbde5f50c462ab5d8a3ec0d8f6b *./trustee_a/D023.parquet
bce4681632e622374b4f359389a9017f99b8dc6cfadd21cdfd371339a1504f66 *./trustee_a/D026.parquet
c2ae33ef42404f7a236c45ee744d11bc8c43c624721b2d81b897ca2b1e7b1d48 *./trustee_a/D027.parquet
19a5326e323a27882bdb1394b6eb223190763cebcafe3405792c5501f74f1a86 *./trustee_a/D028.parquet
2a2bf47ea8ee52062c7eff70e2e543b602a1f0d1686dc7c0476ff3cf4d578106 *./trustee_a/D031.parquet
2a76881583c97b07d26f3493e0ba932a207886397475241d6de82bc2a2583fc7 *./trustee_a/D032.parquet
83c714506ba2df64f6485a3fb7d62f5fd1a20f808d3a6c45f1b4d861b1cba8a7 *./trustee_a/D033.parquet
b7fee3c61055b0f58db113a482c3cf3748e117c204f7547e3e0c9e0599cdee2c *./trustee_a/D036.parquet
b1c382f5c9028b4d2bfb8e9eac16673103fcf89ea1f526c4a1376baebae0478a *./trustee_a/D037.parquet
f112d884e1b15050971feebdfdb674b372d7d322da6a7764be793339dd043ac4 *./trustee_a/D038.parquet
52470733de3bc96595092692af4a8c33e1e23eeba86e3d4714a242daaf52d2ea *./trustee_a/D041.parquet
d16c1a63a04fdc07a0dc1052a43fd04a52ab5f3096f69fd82d7bec3d716ab5d9 *./trustee_a/D042.parquet
f4a811a9651a8c9d279f5d988a8dd0182b4a63b59db991f9c7bd66fdd4724b09 *./trustee_a/D043.parquet
f74773455850f30230d5c23ae7bf5d147b4df1e5b96c9d28911ce2a96fc6a1fa *./trustee_a/D046.parquet
f727f06379cf87f2aeed3d2cb22f4ab8cbf48b433d807d03589e6f0b11d4b1e9 *./trustee_a/D047.parquet
3ca7f812cfe69330aac14e43b7c95e9c2dfbc498633408606f3d18e2a1bbb5f2 *./trustee_a/D048.parquet
0dbc79be0b4a064d068ba36aff3de9b3018882a3fdbea447feae940df98521c4 *./trustee_b/D004.parquet
9747f416bd933188dab01f71e7ad2929ff98ce210025cb7f21c6851fe596b1d5 *./trustee_b/D005.parquet
3e653236486a9cbb5e650fa89a87cb23e6b70c01120fb23c77c096d0c67e4144 *./trustee_b/D009.parquet
794cbb0919f0efcfc5c3fcbb09e53cfa9e07f2babeda0e4cc88dbfd1ba3fe236 *./trustee_b/D010.parquet
fae8cfcdedba78cd7036276908dfa24299fd2ce3d52d810492df5d039b2c766d *./trustee_b/D014.parquet
a4d7e1199d0b2c806967906301ea63add1dce8cf56c82c28dabf00105e1fe6ab *./trustee_b/D015.parquet
745d92bc2eb33f531a24851f118839f2948b9603b1a1f996d3cb26446a85f26c *./trustee_b/D019.parquet
97cbd0768c0443d81f61a07e73eff33bc7886c972471adcd925c53ed011b2397 *./trustee_b/D020.parquet
d7e8c89f1489a5ec26577e464d3cfb58e08beab4af5020f0564804837848f449 *./trustee_b/D024.parquet
767153a218d950beead936f666596c24a3d9ec1f6896c0e39d47bd59dde4da3a *./trustee_b/D025.parquet
22b55d398633cc7ebb68c82e8a41f3d97293b5d55d865f042fbae8d46ed48448 *./trustee_b/D029.parquet
aeece641b6788e641907ab74905742af87efb800cd5ff6be43074b7d9a9ff5d7 *./trustee_b/D030.parquet
228c9829bcbd94086f2e83c9df34c2017f3fb6d4f0925ebb09e9fac6acae6ef8 *./trustee_b/D034.parquet
41285e099ef18141f9eb15f55d2d55a6e3f209bd11fbf3b39419389b1d0a0c8b *./trustee_b/D035.parquet
e6c354c92d4e58610acb3c8cbe5a9c974df4a2218e896c333d750425146d616f *./trustee_b/D039.parquet
4bb9ea57158a4818001b2d0320cd054a7a04a07f475f2d6fb20df87572ba85e1 *./trustee_b/D040.parquet
0a3c5402b60cbfda8cb755e82069e0df4e4556bb0c535534371a9ae1d3660138 *./trustee_b/D044.parquet
296575ac56b99a014b81f502d716dccfce1e4e0677753729f03e0ce88bd61d4c *./trustee_b/D045.parquet
1a2a3d7277bc580f8f4b00a88cb2a8d7075b4f90a501968b6c9c2932a01ef43d *./trustee_b/D049.parquet
a309e393d84f22701f8837ad29ca6f238f7e8935667c00e203cc1ab6a99c018e *./trustee_b/D050.parquet
b8fa4b15ce4fc9ac790c39d9c50f5fdf9e3fedf0e5164834941b3bf28e4474aa *outputs/calibration.csv
d5ff6ce6f42f6228fe38dbd6627f2441fbcee9c9407fa2075f20e6483a6f5870 *outputs/pool_monthly_truth.csv

run 2 (regenerated):
ceac9c2f6edb42c67f319225f2858d0ed76941f22459173063aef7c70e1be73f *./MANIFEST.json
7c8b58dbf3b446b1cd677698e63fd2776c5be186d487a8dcefbab3f499cd73df *./cash_rate.parquet
6f186f68847ec94fec12c1e88ae1f5fda67fc7adf4460daf3f77f51dc961651d *./deals.parquet
e29b289033e5c242d45162fd4ed97b45d8438908d4f9ead6aeb3bc37e439cdf5 *./hpi.parquet
79270caa48ea8f6498128cd7cd11edbf4af61bfde2defbaadca4433b652b0d32 *./trustee_a/D001.parquet
0505917afa601c960ad0f286b9ab1d6729695c3f15ccdcf3ba4d989c5702d826 *./trustee_a/D002.parquet
34ea164253d9625fb55e52ac454c6232218da4faf3998fe2789bb74d97b69d3c *./trustee_a/D003.parquet
99fe834ab0a46ba0a4e8dd216879c51484aecb4e5be7d33e2bc00e835e5d97a4 *./trustee_a/D006.parquet
6b277185ace0e4ad152c934eb4c5ef373e561ba5e0817f9bd3ffba584b147732 *./trustee_a/D007.parquet
a92ff2cd8979c700fddcd31bc31609ade132e72f8ad7093f591ca3f59debfd65 *./trustee_a/D008.parquet
428378e26ea3097ebc52c413cfbb620dd5fb4a0cce640fe5e77ac6a14a9a84f3 *./trustee_a/D011.parquet
8dd904596a56e0925948c2cbedef7a6d53530297cd1c47223071c3e1b98e3b26 *./trustee_a/D012.parquet
e19eb8721c49e76d1123e1aed242c3d8065879ddcf96301a3b022de3de250abc *./trustee_a/D013.parquet
25714ecc5d89747130d2f2451c00248d4a931cbdbec19d450d9edfa271df89e1 *./trustee_a/D016.parquet
395ab45d82753561c1beba71caa121fb80ad5fd8a0b6590340bdaa58e5960970 *./trustee_a/D017.parquet
fa1f2d91fc5fa77824a8a9b07c23347ebb1dc54318a3e34c1ad27b2fb1f3ac0d *./trustee_a/D018.parquet
20f74aea1c715a32b60fa98869f732c72e2f6b9d7ca072e78a038cbc14944e1c *./trustee_a/D021.parquet
d312d0f03ba87edfa54d648e4321fbdb6b562d177d8bb77c3ade326812abee52 *./trustee_a/D022.parquet
ba24de349db7f271ebb10554ce653184b5e81fbde5f50c462ab5d8a3ec0d8f6b *./trustee_a/D023.parquet
bce4681632e622374b4f359389a9017f99b8dc6cfadd21cdfd371339a1504f66 *./trustee_a/D026.parquet
c2ae33ef42404f7a236c45ee744d11bc8c43c624721b2d81b897ca2b1e7b1d48 *./trustee_a/D027.parquet
19a5326e323a27882bdb1394b6eb223190763cebcafe3405792c5501f74f1a86 *./trustee_a/D028.parquet
2a2bf47ea8ee52062c7eff70e2e543b602a1f0d1686dc7c0476ff3cf4d578106 *./trustee_a/D031.parquet
2a76881583c97b07d26f3493e0ba932a207886397475241d6de82bc2a2583fc7 *./trustee_a/D032.parquet
83c714506ba2df64f6485a3fb7d62f5fd1a20f808d3a6c45f1b4d861b1cba8a7 *./trustee_a/D033.parquet
b7fee3c61055b0f58db113a482c3cf3748e117c204f7547e3e0c9e0599cdee2c *./trustee_a/D036.parquet
b1c382f5c9028b4d2bfb8e9eac16673103fcf89ea1f526c4a1376baebae0478a *./trustee_a/D037.parquet
f112d884e1b15050971feebdfdb674b372d7d322da6a7764be793339dd043ac4 *./trustee_a/D038.parquet
52470733de3bc96595092692af4a8c33e1e23eeba86e3d4714a242daaf52d2ea *./trustee_a/D041.parquet
d16c1a63a04fdc07a0dc1052a43fd04a52ab5f3096f69fd82d7bec3d716ab5d9 *./trustee_a/D042.parquet
f4a811a9651a8c9d279f5d988a8dd0182b4a63b59db991f9c7bd66fdd4724b09 *./trustee_a/D043.parquet
f74773455850f30230d5c23ae7bf5d147b4df1e5b96c9d28911ce2a96fc6a1fa *./trustee_a/D046.parquet
f727f06379cf87f2aeed3d2cb22f4ab8cbf48b433d807d03589e6f0b11d4b1e9 *./trustee_a/D047.parquet
3ca7f812cfe69330aac14e43b7c95e9c2dfbc498633408606f3d18e2a1bbb5f2 *./trustee_a/D048.parquet
0dbc79be0b4a064d068ba36aff3de9b3018882a3fdbea447feae940df98521c4 *./trustee_b/D004.parquet
9747f416bd933188dab01f71e7ad2929ff98ce210025cb7f21c6851fe596b1d5 *./trustee_b/D005.parquet
3e653236486a9cbb5e650fa89a87cb23e6b70c01120fb23c77c096d0c67e4144 *./trustee_b/D009.parquet
794cbb0919f0efcfc5c3fcbb09e53cfa9e07f2babeda0e4cc88dbfd1ba3fe236 *./trustee_b/D010.parquet
fae8cfcdedba78cd7036276908dfa24299fd2ce3d52d810492df5d039b2c766d *./trustee_b/D014.parquet
a4d7e1199d0b2c806967906301ea63add1dce8cf56c82c28dabf00105e1fe6ab *./trustee_b/D015.parquet
745d92bc2eb33f531a24851f118839f2948b9603b1a1f996d3cb26446a85f26c *./trustee_b/D019.parquet
97cbd0768c0443d81f61a07e73eff33bc7886c972471adcd925c53ed011b2397 *./trustee_b/D020.parquet
d7e8c89f1489a5ec26577e464d3cfb58e08beab4af5020f0564804837848f449 *./trustee_b/D024.parquet
767153a218d950beead936f666596c24a3d9ec1f6896c0e39d47bd59dde4da3a *./trustee_b/D025.parquet
22b55d398633cc7ebb68c82e8a41f3d97293b5d55d865f042fbae8d46ed48448 *./trustee_b/D029.parquet
aeece641b6788e641907ab74905742af87efb800cd5ff6be43074b7d9a9ff5d7 *./trustee_b/D030.parquet
228c9829bcbd94086f2e83c9df34c2017f3fb6d4f0925ebb09e9fac6acae6ef8 *./trustee_b/D034.parquet
41285e099ef18141f9eb15f55d2d55a6e3f209bd11fbf3b39419389b1d0a0c8b *./trustee_b/D035.parquet
e6c354c92d4e58610acb3c8cbe5a9c974df4a2218e896c333d750425146d616f *./trustee_b/D039.parquet
4bb9ea57158a4818001b2d0320cd054a7a04a07f475f2d6fb20df87572ba85e1 *./trustee_b/D040.parquet
0a3c5402b60cbfda8cb755e82069e0df4e4556bb0c535534371a9ae1d3660138 *./trustee_b/D044.parquet
296575ac56b99a014b81f502d716dccfce1e4e0677753729f03e0ce88bd61d4c *./trustee_b/D045.parquet
1a2a3d7277bc580f8f4b00a88cb2a8d7075b4f90a501968b6c9c2932a01ef43d *./trustee_b/D049.parquet
a309e393d84f22701f8837ad29ca6f238f7e8935667c00e203cc1ab6a99c018e *./trustee_b/D050.parquet
b8fa4b15ce4fc9ac790c39d9c50f5fdf9e3fedf0e5164834941b3bf28e4474aa *outputs/calibration.csv
d5ff6ce6f42f6228fe38dbd6627f2441fbcee9c9407fa2075f20e6483a6f5870 *outputs/pool_monthly_truth.csv
```

`diff run1.sha run2.sha` printed nothing: all 56 files (54 under `data/raw/` and 2 CSVs)
are identical. `test_full_regenerates_identically` checks the same thing for `data/raw/`
on every `-m full` run, and `test_simulate_deterministic` does it for the small panel.

## 6. Fresh-clone check

Clone into a short temp path, `uv venv --python 3.12`, `uv pip sync requirements-lock.txt`,
run the suite. Paste the commands and the complete output. (The `+ <package>` install lines
of `uv pip sync` are left out; the lock installs 44 packages.)

```
$ git clone "<repo>" %LOCALAPPDATA%\Temp\rq1 && cd rq1
$ git log --oneline -1
1c6b3e5 step 1.6: full profile in data/raw, truth and calibration CSVs (arrears_90p_max band fails)
$ uv venv --python 3.12 .venv
Using CPython 3.12.13
Creating virtual environment at: .venv
Activate with: .venv\Scripts\activate
$ uv pip sync --python .venv requirements-lock.txt
Resolved 44 packages in 90ms
warning: Failed to hardlink files; falling back to full copy. This may lead to degraded performance.
         If the cache and target directories are on different filesystems, hardlinking may not be supported.
         If this is intentional, set `export UV_LINK_MODE=copy` or use `--link-mode=copy` to suppress this warning.
Installed 44 packages in 4.06s
$ .venv/Scripts/python -m pytest -q
...........................F..........                                   [100%]
================================== FAILURES ===================================
_________________________ test_hardship_spell_lengths _________________________

cfg = Config(project=Project(seed=20261029, seed_aux=20261030), calendar=Calendar(sim_start='2016-01', window_start='2021-10... design_max_pages=4, summary_max_pages=1, font='Helvetica'), root=WindowsPath('C:/Users/astha/AppData/Local/Temp/rq1'))
hardship_panel =         loan_id deal_id     period  ...  loss  indexed_value  indexed_ltv
0     D001-0001    D001 2021-10-01  ...   0....79e+06     0.427541
2999  D001-0050    D001 2026-09-01  ...   0.0   1.169479e+06     0.427541

[3000 rows x 16 columns]

    def test_hardship_spell_lengths(cfg, hardship_panel):
        """Every hardship spell lasts hardship_min to hardship_max consecutive rows."""
        p = hardship_panel.sort_values(["loan_id", "period"])
        for _, g in p.groupby("loan_id"):
            flags = g["hardship_flag"].to_numpy()
            runs, n = [], 0
            for f in flags:
                if f:
                    n += 1
                elif n:
                    runs.append(n)
                    n = 0
            if n:
                runs.append(n)
>           assert all(cfg.behaviour.hardship_min <= r <= cfg.behaviour.hardship_max for r in runs), runs
E           AssertionError: [60]
E           assert False
E            +  where False = all(<generator object test_hardship_spell_lengths.<locals>.<genexpr> at 0x000002A52E783BC0>)

tests\test_synth_simulate.py:130: AssertionError
=========================== short test summary info ===========================
FAILED tests/test_synth_simulate.py::test_hardship_spell_lengths - AssertionE...
1 failed, 37 passed, 2 deselected in 2.44s
$ .venv/Scripts/python -m pytest -q -m full
F.                                                                       [100%]
================================== FAILURES ===================================
___________________________ test_calibration_bands ____________________________

    def test_calibration_bands():
        with open(ROOT / "outputs" / "calibration.csv", encoding="utf-8", newline="") as f:
            rows = list(csv.DictReader(f))
        assert len(rows) == 9
        failed = [r for r in rows if r["pass"] != "True"]
>       assert not failed, failed
E       AssertionError: [{'stat': 'arrears_90p_max', 'value': '0.0316166537', 'band_lo': '0.0010000000', 'band_hi': '0.0250000000', ...}]
E       assert not [{'stat': 'arrears_90p_max', 'value': '0.0316166537', 'band_lo': '0.0010000000', 'band_hi': '0.0250000000', ...}]

tests\test_full_profile.py:26: AssertionError
=========================== short test summary info ===========================
FAILED tests/test_full_profile.py::test_calibration_bands - AssertionError: [...
1 failed, 1 passed, 38 deselected in 9.28s
```

`git ls-files --eol` in the clone: 65 text files `i/lf w/lf`, 2 empty files
(`decisions/OPEN.md` before this session's edit, and `deliverable/.gitkeep`), and the
parquet files stored as binary.

## 7. Open questions for the reviewer

Same list as `decisions/OPEN.md` and the status file.

1. **O-34, step 1.4: the hardship spell test cannot pass as specified.** With
   p_hardship = 1, E.5 puts a loan back into hardship the month after each spell ends,
   so spells join into one 60-row run, and the panel has no column marking spell starts.
   - (a) The true panel gains a boolean `hardship_entry` column (true in the month of
     entry at E.5; not written to the trustee files). The test splits runs at entry rows
     and checks each spell is 3 to 6 rows.
   - (b) The test uses the configured p_hardship (0.002) and checks interior runs (not
     touching the first row, the last row or an exit row). Measured: 16 of 16 interior
     runs are 3 to 6 rows on the small profile. On the full profile, 6 of 1,330 are 9 to
     12 rows, because spells chained.
2. **O-35, step 1.6: arrears_90p_max = 0.0316166537 fails the band [0.001, 0.025].**
   - (a) Chat Claude compares its reference implementation with part E as written, using
     the scalar script in the appendix. Instruction 01b then restates the rule where the
     two differ, most likely how IO payments enter the payment shock.
   - (b) Part E stands, and instruction 01b sets a new config value: the band ceiling, or
     an IO-related behaviour parameter. Section 1 is then regenerated.

Measured hardship runs on the realised paths at p_hardship = 0.002 (for O-34 (b)):

```
small hardship runs by length and position:
where   ends at last row  interior  starts at first row
length                                                 
3                      1         4                    1
4                      1         5                    1
5                      0         4                    1
6                      0         3                    0
full hardship runs by length and position:
where   ends at last row  ends on exit row  interior  starts at first row
length                                                                   
1                     19                 4         0                   22
2                      9                 2         0                   26
3                      9                 4       353                   26
4                     13                 1       325                   22
5                      7                 2       318                   14
6                      7                 1       328                    6
9                      0                 0         4                    0
10                     0                 0         1                    0
12                     0                 0         1                    0
```

## Appendix: the scalar re-implementation of part E

The scratch script behind the "scalar reference matches" output in step 1.4. It is not
part of the package or the suite.

```python
"""Independent scalar re-implementation of instruction 01 part E, loan by loan with plain
Python math, written straight from the instruction text. Compared with
rmbsq.synth.simulate on the small profile."""

import dataclasses
import math

import numpy as np
import pandas as pd

from rmbsq.config import load_config
from rmbsq.synth.geography import build_geography
from rmbsq.synth.hpi import build_hpi
from rmbsq.synth.loans import draw_loans
from rmbsq.synth.rates import build_cash_rate
from rmbsq.synth.simulate import simulate


def ym(ts):
    return ts.year * 12 + ts.month - 1


cfg = load_config()
p = cfg.profiles["small"]
cfg = dataclasses.replace(cfg, deals=dataclasses.replace(cfg.deals, n_deals=p.n_deals, loans_per_deal=p.loans_per_deal))
geo = build_geography(cfg)
cash = build_cash_rate(cfg)

rng = np.random.Generator(np.random.PCG64(cfg.project.seed))
hpi = build_hpi(cfg, geo, rng)
loans = draw_loans(cfg, geo, cash, rng)
state_after_static = rng.bit_generator.state
panel, deals = simulate(cfg, loans, cash, hpi, rng)

# --- scalar version, same rng state after the static draws
rng2 = np.random.Generator(np.random.PCG64(cfg.project.seed))
rng2.bit_generator.state = state_after_static
B = cfg.behaviour
cashd = {ym(r.period): r.rate for r in cash.itertuples()}
H = {(r.suburb, ym(r.period)): r.hpi for r in hpi.itertuples()}
LS = []
for r in loans.itertuples():
    LS.append(dict(
        id=r.loan_id, deal=r.deal_id, issue=ym(r.issue_month), orig=ym(r.orig_month),
        io=bool(r.io_flag), io_end=ym(r.io_end_month) if r.io_flag else None,
        fixed=r.rate_type == "fixed", fe=ym(r.fixed_end_month) if r.rate_type == "fixed" else None,
        fr=r.fixed_rate, margin=r.margin, inv=r.occupancy == "investor", ob=r.orig_balance,
        ov=r.orig_valuation, sub=r.suburb,
        close=r.orig_balance, bucket=0, m90=0, hr=0, dflag=False, gone=False, hist={},
    ))
deal_issue = {d: ym(i) for d, i in zip(deals.deal_id, deals.issue_month)}
call = {d: False for d in deal_issue}
ib = {}


def rate(L, t):
    if L["fixed"] and t < L["fe"]:
        return L["fr"]
    return cashd[t] + L["margin"]


def pay(L, b, r, a, t):
    if L["io"] and t < L["io_end"]:
        return b * r / 12
    i = r / 12
    n = cfg.loans.term - a + 1
    return b * i / (1 - (1 + i) ** (-n))


for L in LS:
    L["porig"] = pay(L, L["ob"], rate(L, L["orig"]), 1, L["orig"])
    L["hist"][L["orig"]] = L["porig"]

rows = []
t0, t1, ws = ym(pd.Timestamp("2016-02-01")), ym(pd.Timestamp("2026-09-01")), ym(pd.Timestamp("2021-10-01"))
for t in range(t0, t1 + 1):
    live = [L for L in LS if L["orig"] < t and not L["gone"]]
    for L in live:
        if L["issue"] == t:
            L["bucket"], L["m90"], L["hr"], L["dflag"] = 0, 0, 0, False
    n = len(live)
    uh, ut, up, ur = rng2.random(n), rng2.random(n), rng2.random(n), rng2.random(n)
    dsum, dopen = {}, {}
    for j, L in enumerate(live):
        op = L["close"]
        age = t - L["orig"]
        r = rate(L, t)
        pm = pay(L, op, r, age, t)
        L["hist"][t] = pm
        m = t - B.shock_lookback_months
        ref = L["porig"] if m <= L["orig"] else L["hist"][m]
        shock = max(pm / ref - 1, 0)
        iv = L["ov"] * H[(L["sub"], t)] / H[(L["sub"], L["orig"])]
        lo = op / iv
        io_now = L["io"] and t < L["io_end"]
        sched = 0.0 if io_now else min(pm - op * r / 12, op)
        b = L["bucket"]
        if b == 0 and L["hr"] == 0 and uh[j] < B.p_hardship:
            L["hr"] = B.hardship_min + math.floor((B.hardship_max - B.hardship_min + 1) * uh[j] / B.p_hardship)
        inh = L["hr"] > 0
        nb = b
        if not inh:
            if b == 0:
                iorec = L["io"] and 0 <= t - L["io_end"] < B.io_recent_months
                x = B.a0 + B.a_shock * shock + B.a_ltv * max(lo - B.ltv_knot, 0) + B.a_investor * L["inv"] + B.a_io_recent * iorec
                if ut[j] < 1 / (1 + math.exp(-x)):
                    nb = 1
            elif b in (1, 2, 3):
                pc, pr = B.p_cure[b - 1], B.p_roll[b - 1]
                pre = min(pr * math.exp(B.roll_shock * shock), 0.95 - pc)
                if ut[j] < pc:
                    nb = 0
                elif ut[j] < pc + pre:
                    nb = b + 1
            else:
                if ut[j] < B.p_cure_90:
                    nb = 0
        L["m90"] = L["m90"] + 1 if nb == 4 else 0
        reason = None
        if t >= L["issue"]:
            base = B.smm_start + (B.smm_flat - B.smm_start) * min(age, B.smm_ramp_months) / B.smm_ramp_months
            if L["fixed"] and 0 <= t - L["fe"] < B.fixed_cliff_months:
                inc = B.fixed_cliff_mult
            else:
                inc = 1 + B.refi_slope * max(0, r - (cashd[t] + B.refi_spread))
            damp = B.damp_mult if lo > B.damp_ltv else 1
            smm = min(base * inc * damp, B.smm_cap)
            if call[L["deal"]]:
                reason = "called"
            elif L["dflag"]:
                reason = "defaulted"
            elif ur[j] < B.p_repurchase:
                reason = "repurchased"
            elif (not inh) and nb == 0 and up[j] < smm:
                reason = "prepaid"
        ex = reason is not None
        payer = (not ex) and (not inh) and nb == 0
        sp = float(np.round(sched, 2)) if payer else 0.0
        cu = float(np.round(B.curtailment * (op - sp), 2)) if payer else 0.0
        cl = 0.0 if ex else float(np.round(op - sp - cu, 2))
        loss = float(np.round(max(0, op - B.sale_haircut * iv), 2)) if reason == "defaulted" else 0.0
        L["dflag"] = (not ex) and L["m90"] >= B.default_after_90_months
        if inh:
            L["hr"] -= 1
        L["bucket"], L["close"] = nb, cl
        if ex:
            L["gone"] = True
        dsum[L["deal"]] = dsum.get(L["deal"], 0.0) + cl
        if L["issue"] == t:
            dopen[L["deal"]] = dopen.get(L["deal"], 0.0) + op
        if t >= ws and t >= L["issue"]:
            rows.append((L["id"], t, op, sp, cu, cl, r, 0 if inh else nb, inh, L["m90"], reason,
                         op if ex else 0.0, loss, iv, (op if ex else cl) / iv))
    for d, s in dopen.items():
        ib[d] = s
    for d in deal_issue:
        if t >= deal_issue[d] and d in ib and dsum.get(d, 0.0) <= cfg.deals.call_threshold * ib[d]:
            call[d] = True

ref = pd.DataFrame(rows, columns=["loan_id", "t", "opening_balance", "scheduled_principal", "curtailment",
                                  "closing_balance", "interest_rate", "dpd_bucket", "hardship_flag",
                                  "months_in_90", "exit_reason", "exit_balance", "loss", "indexed_value", "indexed_ltv"])
mine = panel.assign(t=[ym(x) for x in panel["period"]])
a = mine.sort_values(["t", "loan_id"]).reset_index(drop=True)
b = ref.sort_values(["t", "loan_id"]).reset_index(drop=True)
print("rows", len(a), len(b))
assert len(a) == len(b)
assert (a["loan_id"] == b["loan_id"]).all() and (a["t"] == b["t"]).all()
for c in ["dpd_bucket", "months_in_90", "hardship_flag"]:
    assert (a[c].to_numpy() == b[c].to_numpy()).all(), c
assert (a["exit_reason"].fillna("").to_numpy() == b["exit_reason"].fillna("").to_numpy()).all()
for c in ["opening_balance", "scheduled_principal", "curtailment", "closing_balance", "interest_rate",
          "exit_balance", "loss", "indexed_value", "indexed_ltv"]:
    d = np.abs(a[c].to_numpy() - b[c].to_numpy()).max()
    print(f"{c:22s} max abs diff {d:.3e}")
print("issue_balance", np.abs(deals.set_index("deal_id")["issue_balance"] - pd.Series(ib)).max())
print("scalar reference matches")
```
