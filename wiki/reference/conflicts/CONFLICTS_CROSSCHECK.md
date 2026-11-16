# Conflict cross-check: John Mitchell's list vs the ISCA conflict list

Prepared 2026-11-09. Raw inputs: `mitchell_conflicts.txt` and `isca_conflicts.txt` (this directory, pasted verbatim). Script: surname/given-name/fuzzy matching of all 212 Mitchell names against all 414 ISCA entries, plus a search for "Stanford" in ISCA affiliations. The matching is by name only, with no outside lookups.

## Result in one line

There is NO exact full-name match between the two lists (0 of 414 ISCA entries equal any of the 212 Mitchell names), and no ISCA entry lists Stanford. The only ISCA entries that already carry a conflict flag are the three below.

## 1. Already flagged by the ISCA list itself (include in the final list)

- George Michelogiannakis, Microsoft: "Possible conflict with authors #1–4".
- Ke (Cory) Wang, UNC Charlotte: "Possible conflict with author #4".
- Kevin Skadron, U. Virginia: "Possible conflict with author #4".

## 2. Close or unclear: need Anna's call (human check against real identities)

- **Tony Nowatzki (UCLA) vs "T Nowacki"** (Mitchell collaborator list): one-letter surname difference, same first initial. Most likely different people (Nowacki is a different surname), but this is the closest near-miss.
- **Neil Zhao (UT Austin & NVIDIA) vs Neil Gong / Neil Zhenqiang Gong**: same given name only. Probably different people.
- **Zhi Zhang (UWA) and Zheng Zhang (Rutgers) vs "Z Zhang" / Zhikun Zhang**: Mitchell lists "Z Zhang" as a bare initial plus Zhikun Zhang. Either ISCA person could be "Z Zhang" in principle.
- **Yu Huang (HUST) vs Yue Huang / Yixin Huang** (trustworthy-AI position paper): similar given name, same surname. Also Guyue Huang (NVIDIA) vs Yue Huang.
- **Yun Liang (Peking U) vs Yiyun Liang** (collaborator list): similar given name, same surname.
- **Sanchari Sen (IISc) vs Shayak Sen**: same surname, different given name.
- **Jongouk Choi (UCF) vs Jihye Choi**: same surname, different given name.
- **Hao Wang (NVIDIA) vs Haoran Wang**: very common name pattern; the position paper is a large multi-author list, so a coincidence is plausible.
- **Yiran Chen (Duke), Yun Chen (HKUST-GZ), Xuhao Chen (MSU), Lizhong Chen (OSU), Chixiao Chen (Fudan) vs Xun / Yong / Tianlong / Pin-Yu / Brad Chen**: same surname only.
- **Zhaoxuan Li (CAS), Xueqi Li (ICT), Chao Li (SJTU), Bingyao Li, Bingzhe Li, Wantong Li, Tingting Li vs the Li's** (Chunyuan, Xiang, Xiner, Yuan, Ninghui Li): same surname only.
- **Chang Liu, Changxi Liu, Fangxin Liu, Hongyuan Liu, Sihang Liu vs the Liu's** (Hao, Jian, Tianming, Yan, Yixin, Zhengliang Liu): same surname only.
- **Hongyuan Liu, Ying Wang, Xin Wang, Xinkai Wang and others vs the Wang's** in the lists: same surname only.
- **Fan Yao (UCF) vs Huaxiu Yao**; **Hai Jin (HUST) vs Heng Ji**; **Guanghui He (SJTU) vs Changhua He**; **Kai Bu (Zhejiang) vs Kai Shu / Kai-Wei Chang** (given-name overlap only).
- **John Kim (KAIST) vs John Mitchell / Jeongyeon Kim**; **Daniel Sanchez (MIT) vs Daniel Huang / Daniel Kang**: common given or family names only.

Full list of every ISCA entry sharing a surname with a Mitchell name (kept so nothing can be a false negative):

- **Cao**: ISCA Shijie Cao, Ting Cao, Weidong Cao
- **Chen**: ISCA Chixiao Chen, Haibo Chen, Lizhong Chen, WENZHI CHEN, Xuhao Chen, Yiran Chen, Yun Chen
- **Choi**: ISCA Jongouk Choi
- **Gao**: ISCA Mingyu Gao
- **Gu**: ISCA Qi Guo, Yufeng Gu
- **Gupta**: ISCA Rajiv Gupta, Siddharth Gupta
- **He**: ISCA Guanghui He
- **Huang**: ISCA Da Zhang, Guyue Huang, Jiayi Huang, Lixin Zhang, Qijing Huang, Sitao Huang, Tsung-Wei Huang, Yu Huang
- **Ji**: ISCA Hai Jin
- **Jiang**: ISCA Zhiding Liang
- **Kang**: ISCA Mingu Kang
- **Kim**: ISCA Daehyun Kim, EJ Kim, Gwangsun Kim, Jangwoo Kim, John Kim, Joonsung Kim, Jungrae Kim, Nam Sung Kim, Seah Kim, Yeseong Kim, Young Geun Kim, Youngsok Kim
- **Li**: ISCA Bingyao Li, Bingzhe Li, Calvin Lin, Chang Liu, Changxi Liu, Chao Li, Meng Li, Tingting Li, Wantong Li, Xu Liu, Xueqi Li, Zhaoxuan Li
- **Liang**: ISCA Shengwen Liang, Yun Liang, Zhiding Liang
- **Liu**: ISCA Chang Liu, Changxi Liu, Fangfei Liu, Fangxin Liu, Hang Lu, Hongyuan Liu, Lei Liu, Liu Liu, Shiwei Liu, Sihang Liu, Tingting Li, Weifeng Liu, Xu Liu, Zhaoxuan Li
- **Nowacki**: ISCA Tony Nowatzki
- **Pei**: ISCA Shuyi Pei
- **Roy**: ISCA Saion K. Roy
- **Sen**: ISCA Sanchari Sen
- **Song**: ISCA Linghao Song, William Song, Zhuoran Song
- **Sun**: ISCA Guangyu Sun, Hyojin Sung, Jinghan Sun
- **Tang**: ISCA Wei Tang
- **Wang**: ISCA Chengning Wang, Chunhao Wang, Dongsheng Wang, Hao Wang, Jooyoung Hwang, Ke (Cory) Wang, Xin Wang, Xinkai Wang, Ying Wang, Yongqin Wang, Zeke Wang, Zhengrong Wang
- **Wu**: ISCA Anbang Wu, Di Wu, Nan Wu
- **Xiao**: ISCA Yuan Xiao
- **Xie**: ISCA Yuan Xie
- **Xiong**: ISCA Wenjie Xiong
- **Xu**: ISCA Ceyu Xu, Jiang Xu, Qiumin Xu, Xiaolin Xu
- **Yang**: ISCA Kaiyuan Yang, Ming-Chang Yang, Zhaohui Yang
- **Yao**: ISCA Fan Yao, Peng Yao, Pengcheng Yao
- **Ye**: ISCA Chencheng Ye
- **Yoo**: ISCA Hoi-Jun Yoo
- **Zhang**: ISCA Chen Zhang, Da Zhang, Guowei Zhang, Hao Zheng, Jeff Zhang, Jie Zhang <carlzhang4@zju.edu.cn>, Jie Zhang <jiez@pku.edu.cn>, Lixin Zhang, Qijing Huang, Sai Qian Zhang, Wei Zhang, Yu Huang, Zheng Zhang, Zhi Zhang
- **Zhao**: ISCA Hui Zhao, Jiacheng Zhao, Jiechen Zhao, Laiping Zhao, Neil Zhao, Yang Zhao, Yiwei Zhao, Ziming Zhao
- **Zhou**: ISCA Huiyang Zhou, Minxuan Zhou, Ruoyu Zhou, Yangjie Zhou

## 3. Recommended final list (leaning toward false positives)

Strong: George Michelogiannakis, Ke (Cory) Wang, Kevin Skadron (ISCA-flagged).

Check-before-dropping (my recommendation is to keep these in the conflict list unless Anna can confirm they are different people): Tony Nowatzki, Zhi Zhang, Zheng Zhang, Yu Huang, Yun Liang, Neil Zhao.

Everything else in section 2 is surname-only or given-name-only overlap and is very likely coincidence; keep them off unless Anna wants the extra-cautious version.

## Caveats

- Name matching only. Authors may also be conflicted through shared institution, advisor, or recent co-authorship, none of which this check can see.
- Mitchell's list is partly initials ("C Piech", "DL Dill"): initial-only entries can match ISCA people I could not detect. I matched initial + surname, and found only the Z Zhang cases above.
- Transliteration variants (e.g. Chinese given names split differently) can hide a match; the fuzzy tiers above are meant to catch those but are not exhaustive.

## Addendum 2026-11-09: Caroline Trippel's list vs ISCA

Raw input: `caroline_conflicts.txt`. 71 named people plus two institution-wide entries ("Stanford (All)", "NVIDIA (All)"). Same name/affiliation matching as above.

**Exact or near-exact person matches:**
- **Kevin Skadron (University of Virginia)**: exact match with ISCA "Kevin Skadron, U. Virginia" (also carries the ISCA "possible conflict with author #4" flag).
- **Ke Wang (Visa Research)** vs ISCA **Ke (Cory) Wang (UNC Charlotte)**: same name, different affiliation, and ISCA already flags this entry. Treat as a conflict (could be the same person with a changed affiliation or a different person with the same name).

**Institution-wide: NVIDIA (All)** hits 15 ISCA entries (NVIDIA affiliation): Alon Amid, Dr. Hari Sadasivan (Nvidia and UW Seattle), Guilherme Cox, Guyue Huang, Hao Wang, Mohamed Tarek Ibn Ziad, Neil Zhao (UT Austin & NVIDIA), Nic McDonald, Preyesh Dalmia, Qijing Huang, Rachit Rajat, Rishabh Jain, Siddharth Gupta, Sungmin Yun, Zi Yan.

**Institution-wide: Stanford (All)**: no ISCA entry lists Stanford. (Also checked ISCA entries whose affiliation text mentions Stanford in any form: none.)

**Surname-only or loose overlaps (very likely coincidence):** Peijing Li and Yanjing Li vs the ISCA Li's; Shuhan Liu vs the ISCA Liu's (an automated "strong" hit on "Liu Liu" at Rensselaer is a token-set artifact, not a real match); Xinxin Wang vs the ISCA Wang's; Nathan Zhang vs the ISCA Zhang's; Bihan Zhao vs the ISCA Zhao's; Chuyue Sun vs Guangyu Sun and Jinghan Sun; Huanmi Tan vs Cheng Tan. No other name on Caroline's list matched any ISCA entry, including Martonosi, Mitra, Hahn, Timothy Trippel, Bhattacharjee, Fletcher, Fadiheh, Nemati, Chlipala, Olukotun, Kozyrakis and the rest.

**Names on both Caroline's and Mitchell's lists:** Hamed Nemati, Nicholas Mosier, Clark Barrett, John Mitchell. None of these appear in the ISCA list.

**Combined recommended conflict list for the ISCA paper (union of both checks):** George Michelogiannakis, Ke (Cory) Wang, Kevin Skadron (all three ISCA-flagged; Skadron and Wang also match Caroline's list), plus the 15 NVIDIA-affiliated ISCA entries above, plus the Mitchell close-matches kept earlier (Tony Nowatzki, Zhi Zhang, Zheng Zhang, Yu Huang, Yun Liang, Neil Zhao; Neil Zhao is also NVIDIA-affiliated).
