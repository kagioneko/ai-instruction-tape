# AIT Token Cost Benchmark v3 - Full Edition
# Compares token cost across: Natural Lang (JA/EN), EAP Unicode, EAP ASCII, AIT
#
# Usage:
#   pip install tiktoken pandas matplotlib numpy
#   python ait_benchmark_v3.py

import tiktoken
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

enc = tiktoken.get_encoding('cl100k_base')


def count_tokens(text):
    return len(enc.encode(text))


# ===== Task Definitions =====
tasks = [
    # --- Core Agent Tasks ---
    {
        'name': 'XSS Scan',
        'category': 'Agent Task',
        'natural_ja': '過去ログ4番のXSSを超ガチで見て',
        'natural_en': 'Please thoroughly inspect context 4 for XSS vulnerabilities at the highest priority.',
        'eap_unicode': '◤SEC::XSS ➔ 📦[#ctx4] ⚡9',
        'eap_ascii':   '>SEC:XSS #ctx4 !9',
        'ait':         's4x9',
    },
    {
        'name': 'Data Summary',
        'category': 'Agent Task',
        'natural_ja': 'コンテキスト2のデータを要約してください。優先度は中程度でお願いします。',
        'natural_en': 'Please summarize the data in context 2. Priority is medium.',
        'eap_unicode': '◤DAT::SUM ➔ 📦[#ctx2] ⚡5',
        'eap_ascii':   '>DAT:SUM #ctx2 !5',
        'ait':         'd2m5',
    },
    {
        'name': 'Refactor',
        'category': 'Agent Task',
        'natural_ja': 'コンテキスト7のコードをリファクタリングして修正してください。緊急度高めで。',
        'natural_en': 'Please refactor and fix the code in context 7 with high urgency.',
        'eap_unicode': '◤REF::FIX ➔ 📦[#ctx7] ⚡8',
        'eap_ascii':   '>REF:FIX #ctx7 !8',
        'ait':         'r7f8',
    },
    {
        'name': 'Sec Audit',
        'category': 'Agent Task',
        'natural_ja': 'コンテキスト1全体のセキュリティ監査を実施してください。最優先でお願いします。',
        'natural_en': 'Please conduct a full security audit of context 1. This is the highest priority.',
        'eap_unicode': '◤SEC::AUD ➔ 📦[#ctx1] ⚡9',
        'eap_ascii':   '>SEC:AUD #ctx1 !9',
        'ait':         's1a9',
    },
    {
        'name': 'NeuroState',
        'category': 'Agent Task',
        'natural_ja': 'コンテキスト3のNeuroStateパラメータを更新してバリデーションしてください。',
        'natural_en': 'Please update and validate the NeuroState parameters in context 3.',
        'eap_unicode': '◤NEU::UPD ➔ 📦[#ctx3] ⚡6',
        'eap_ascii':   '>NEU:UPD #ctx3 !6',
        'ait':         'n3u6',
    },

    # --- Casual ---
    {
        'name': 'Good Morning',
        'category': 'Casual',
        'natural_ja': 'おはよう',
        'natural_en': 'Good morning',
        'eap_unicode': '▰SYS::HLO ➔ 📦[#usr] ⚡1',
        'eap_ascii':   '=SYS:HLO #usr !1',
        'ait':         'yuh1',
    },
    {
        'name': 'How are you',
        'category': 'Casual',
        'natural_ja': '最近調子どう？なんか変わったことあった？',
        'natural_en': 'How are you doing lately? Anything new going on?',
        'eap_unicode': '▰SYS::CHK ➔ 📦[#usr] ⚡2',
        'eap_ascii':   '=SYS:CHK #usr !2',
        'ait':         'yuc2',
    },
    {
        'name': 'Thank you',
        'category': 'Casual',
        'natural_ja': 'ありがとう、助かったよ！またよろしくね。',
        'natural_en': 'Thank you, that was really helpful! Talk to you again soon.',
        'eap_unicode': '▰SYS::ACK ➔ 📦[#usr] ⚡1',
        'eap_ascii':   '=SYS:ACK #usr !1',
        'ait':         'yua1',
    },

    # --- Complex Multi-step ---
    {
        'name': 'Multi-step (short)',
        'category': 'Complex',
        'natural_ja': 'ログ5番を見て、XSSとSQLiを両方チェックして、問題あれば修正案も出して。優先度最高で。',
        'natural_en': 'Review log 5, check for both XSS and SQLi, and if issues are found, suggest fixes. Highest priority.',
        'eap_unicode': '◤SEC::XSS ➔ 📦[#ctx5] ⚡9 ◤SEC::SQL ➔ 📦[#ctx5] ⚡9 ◤REF::FIX ➔ 📦[#ctx5] ⚡9',
        'eap_ascii':   '>SEC:XSS #ctx5 !9 >SEC:SQL #ctx5 !9 >REF:FIX #ctx5 !9',
        'ait':         's5x9 s5q9 r5f9',
    },
    {
        'name': 'Multi-step (long)',
        'category': 'Complex',
        'natural_ja': 'コンテキスト6のコードについて、まずセキュリティ上の問題点を全部洗い出してください。次にパフォーマンスの問題も確認して、最後にリファクタリング案を優先度順に整理してまとめてください。緊急度は高めでお願いします。',
        'natural_en': 'For the code in context 6, first identify all security issues, then check for performance problems, and finally organize refactoring suggestions by priority. Urgency is high.',
        'eap_unicode': '◤SEC::AUD ➔ 📦[#ctx6] ⚡8 ◤DAT::VAL ➔ 📦[#ctx6] ⚡7 ◤REF::FIX ➔ 📦[#ctx6] ⚡8',
        'eap_ascii':   '>SEC:AUD #ctx6 !8 >DAT:VAL #ctx6 !7 >REF:FIX #ctx6 !8',
        'ait':         's6a8 d6v7 r6f8',
    },

    # --- Context Reference ---
    {
        'name': 'Vague reference',
        'category': 'Context Ref',
        'natural_ja': 'さっき言ってたやつ、もう一回やって',
        'natural_en': 'Please do that thing you mentioned earlier again.',
        'eap_unicode': '◤SYS::RPT ➔ 📦[#prev] ⚡5',
        'eap_ascii':   '>SYS:RPT #prev !5',
        'ait':         'yp r5',
    },
    {
        'name': 'Explicit ref',
        'category': 'Context Ref',
        'natural_ja': '3つ前のログで検出されたXSSの件、修正してください。',
        'natural_en': 'Please fix the XSS issue that was detected in the log from 3 steps ago.',
        'eap_unicode': '◤SEC::FIX ➔ 📦[#ctx-3] ⚡7',
        'eap_ascii':   '>SEC:FIX #ctx-3 !7',
        'ait':         'sNf7',
    },

    # --- Conditional / Error Handling ---
    {
        'name': 'Error handling',
        'category': 'Conditional',
        'natural_ja': 'コンテキスト8を処理して、もしエラーが出たらログに記録してもう一回試みてください。それでもダメなら私に報告して。',
        'natural_en': 'Process context 8. If an error occurs, log it and retry once. If it still fails, report back to me.',
        'eap_unicode': '◤DAT::RUN ➔ 📦[#ctx8] ⚡6 ⁝ on_err=retry,report',
        'eap_ascii':   '>DAT:RUN #ctx8 !6 | on_err=retry,report',
        'ait':         'd8r6|e=rr',
    },
    {
        'name': 'Conditional branch',
        'category': 'Conditional',
        'natural_ja': 'ログ9番を確認して、脆弱性があればすぐ修正、なければ次のタスクに進んでいいよ。',
        'natural_en': 'Check log 9. If vulnerable, fix immediately. If clean, proceed to the next task.',
        'eap_unicode': '◤SEC::CHK ➔ 📦[#ctx9] ⚡7 ⁝ if_vul=fix,else=next',
        'eap_ascii':   '>SEC:CHK #ctx9 !7 | if_vul=fix,else=next',
        'ait':         's9c7|v=fn',
    },
]

formats = ['natural_ja', 'natural_en', 'eap_unicode', 'eap_ascii', 'ait']
labels = {
    'natural_ja':  'Natural Lang (JA)',
    'natural_en':  'Natural Lang (EN)',
    'eap_unicode': 'EAP Unicode',
    'eap_ascii':   'EAP ASCII',
    'ait':         'AIT',
}
colors = ['#e74c3c', '#e67e22', '#3498db', '#2ecc71', '#9b59b6']
categories = ['Agent Task', 'Casual', 'Complex', 'Context Ref', 'Conditional']

# ===== Measure =====
print('=== Token counts per task ===')
results = []
for task in tasks:
    row = {'Task': task['name'], 'Category': task['category']}
    for fmt in formats:
        row[labels[fmt]] = count_tokens(task[fmt])
    results.append(row)
    print(
        f"  [{task['category']:12s}] {task['name']:20s} | "
        f"JA={row[labels['natural_ja']]:3d}  EN={row[labels['natural_en']]:3d}  "
        f"EAP-U={row[labels['eap_unicode']]:3d}  EAP-A={row[labels['eap_ascii']]:3d}  "
        f"AIT={row[labels['ait']]:3d}"
    )

df = pd.DataFrame(results).set_index('Task')
token_cols = [labels[f] for f in formats]
df_tokens = df[token_cols]

# ===== Category averages =====
print('\n=== Average tokens by category ===')
df['Category'] = [t['category'] for t in tasks]
for cat in categories:
    sub = df[df['Category'] == cat][token_cols]
    if len(sub) == 0:
        continue
    print(f'\n  [{cat}]')
    for fmt in formats:
        print(f'    {labels[fmt]:18s}: avg {sub[labels[fmt]].mean():.1f}')

# ===== Loop cost projection =====
totals = {fmt: df_tokens[labels[fmt]].sum() for fmt in formats}
loop_counts = [1, 10, 50, 100, 500, 1000]

print('\n=== AIT reduction vs Natural Lang (JA) - all tasks ===')
for n in loop_counts:
    ja  = totals['natural_ja'] * n
    ait = totals['ait'] * n
    r   = (1 - ait / ja) * 100
    print(f'  loop={n:5d}: JA={ja:7d}  AIT={ait:5d}  reduction={r:.1f}%')

# ===== Plots =====
fig = plt.figure(figsize=(18, 12))
fig.suptitle('AIT Token Cost Benchmark v3 — Full Edition (cl100k_base)', fontsize=15, fontweight='bold')

# Plot 1: per-task token counts
ax1 = fig.add_subplot(2, 2, 1)
x = np.arange(len(tasks))
width = 0.15
for i, (fmt, color) in enumerate(zip(formats, colors)):
    vals = [count_tokens(t[fmt]) for t in tasks]
    ax1.bar(x + (i - 2) * width, vals, width, label=labels[fmt], color=color, alpha=0.85)
ax1.set_title('Tokens per Task (All)')
ax1.set_ylabel('Tokens')
ax1.set_xticks(x)
ax1.set_xticklabels([t['name'] for t in tasks], rotation=30, ha='right', fontsize=7)
ax1.legend(fontsize=7)
ax1.grid(axis='y', alpha=0.3)

# Plot 2: category averages
ax2 = fig.add_subplot(2, 2, 2)
cat_avgs = {fmt: [] for fmt in formats}
for cat in categories:
    sub = df[df['Category'] == cat][token_cols]
    for fmt in formats:
        cat_avgs[fmt].append(sub[labels[fmt]].mean() if len(sub) > 0 else 0)
x2 = np.arange(len(categories))
for i, (fmt, color) in enumerate(zip(formats, colors)):
    ax2.bar(x2 + (i - 2) * width, cat_avgs[fmt], width, label=labels[fmt], color=color, alpha=0.85)
ax2.set_title('Average Tokens by Category')
ax2.set_ylabel('Avg Tokens')
ax2.set_xticks(x2)
ax2.set_xticklabels(categories, rotation=15, ha='right', fontsize=8)
ax2.legend(fontsize=7)
ax2.grid(axis='y', alpha=0.3)

# Plot 3: cumulative loop cost
ax3 = fig.add_subplot(2, 2, 3)
for fmt, color in zip(formats, colors):
    vals = [totals[fmt] * n for n in loop_counts]
    ax3.plot(loop_counts, vals, marker='o', label=labels[fmt], color=color, linewidth=2)
ax3.set_title('Cumulative Token Cost by Loop Count')
ax3.set_xlabel('Loop Count')
ax3.set_ylabel('Total Tokens')
ax3.legend(fontsize=7)
ax3.grid(alpha=0.3)
ax3.set_xscale('log')

# Plot 4: AIT reduction % by category
ax4 = fig.add_subplot(2, 2, 4)
reductions_vs_ja = []
reductions_vs_en = []
for cat in categories:
    sub = df[df['Category'] == cat][token_cols]
    if len(sub) == 0:
        reductions_vs_ja.append(0)
        reductions_vs_en.append(0)
        continue
    ja_avg  = sub[labels['natural_ja']].mean()
    en_avg  = sub[labels['natural_en']].mean()
    ait_avg = sub[labels['ait']].mean()
    reductions_vs_ja.append((1 - ait_avg / ja_avg) * 100 if ja_avg > 0 else 0)
    reductions_vs_en.append((1 - ait_avg / en_avg) * 100 if en_avg > 0 else 0)
x4 = np.arange(len(categories))
ax4.bar(x4 - 0.2, reductions_vs_ja, 0.4, label='vs JA', color='#e74c3c', alpha=0.85)
ax4.bar(x4 + 0.2, reductions_vs_en, 0.4, label='vs EN', color='#e67e22', alpha=0.85)
ax4.set_title('AIT Token Reduction Rate by Category (%)')
ax4.set_ylabel('Reduction (%)')
ax4.set_xticks(x4)
ax4.set_xticklabels(categories, rotation=15, ha='right', fontsize=8)
ax4.legend(fontsize=8)
ax4.grid(axis='y', alpha=0.3)
ax4.axhline(y=0, color='black', linewidth=0.5)

plt.tight_layout()
plt.savefig('ait_benchmark_v3.png', dpi=150, bbox_inches='tight')
print('\nSaved: ait_benchmark_v3.png')

# ===== Summary =====
ait_avg = df_tokens[labels['ait']].mean()
ja_avg  = df_tokens[labels['natural_ja']].mean()
en_avg  = df_tokens[labels['natural_en']].mean()
print('\n=== Overall Summary ===')
for fmt in formats:
    print(f'  {labels[fmt]:18s}: avg {df_tokens[labels[fmt]].mean():.1f} tokens/task')
print(f'\nAIT reduction (all tasks): vs JA {(1 - ait_avg / ja_avg) * 100:.1f}%  vs EN {(1 - ait_avg / en_avg) * 100:.1f}%')
print(f'loop x1000: JA {totals["natural_ja"] * 1000:,} -> AIT {totals["ait"] * 1000:,} tokens')
print(f'saved: {(totals["natural_ja"] - totals["ait"]) * 1000:,} tokens')
