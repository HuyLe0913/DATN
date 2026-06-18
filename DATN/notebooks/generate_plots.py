import os
import matplotlib.pyplot as plt
import seaborn as sns

# Set style
sns.set_theme(style="whitegrid")
plt.rcParams.update({'font.size': 11, 'font.family': 'sans-serif'})

# Output directory in Overleaf project figures folder
output_dir = r"d:\Hoctap\20252\DATN\chatbot-bctc\Overleaf_Project\figures"
os.makedirs(output_dir, exist_ok=True)

# 1. Sector Distribution
sectors = ['Banking', 'Manufacturing & Others', 'Real Estate', 'Securities', 'Insurance']
counts = [13, 11, 4, 1, 1]

plt.figure(figsize=(8, 4.5))
colors = sns.color_palette("ch:s=-.2,r=.6", len(sectors))
bars = plt.barh(sectors, counts, color=colors, edgecolor='grey', height=0.6)

# Add values on bars
for bar in bars:
    width = bar.get_width()
    plt.text(width + 0.3, bar.get_y() + bar.get_height()/2, f'{int(width)}', 
             va='center', ha='left', fontweight='bold', color='#333333')

plt.title("Distribution of Companies across Sectors (VN30)", pad=15, fontweight='bold')
plt.xlabel("Number of Companies")
plt.xlim(0, 15)
plt.gca().invert_yaxis()  # top-down
plt.tight_layout()
plt.savefig(os.path.join(output_dir, "dataset_sector_distribution.png"), dpi=300)
plt.close()

# 2. Temporal Distribution (Subplots side by side: Year & Quarter)
years = ['2024', '2025']
year_counts = [107, 108]

quarters = ['Q1', 'Q2', 'Q3', 'Q4']
quarter_counts = [55, 55, 47, 57]

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 4.5))

# Year bar chart
colors_y = sns.color_palette("Blues_r", 2)
bars_y = ax1.bar(years, year_counts, color=colors_y, edgecolor='grey', width=0.4)
for bar in bars_y:
    height = bar.get_height()
    ax1.text(bar.get_x() + bar.get_width()/2, height + 2, f'{int(height)}', 
             va='bottom', ha='center', fontweight='bold')
ax1.set_title("Distribution of Reports by Year", fontweight='bold', pad=10)
ax1.set_ylabel("Number of Reports")
ax1.set_ylim(0, 130)

# Quarter bar chart
colors_q = sns.color_palette("crest", 4)
bars_q = ax2.bar(quarters, quarter_counts, color=colors_q, edgecolor='grey', width=0.5)
for bar in bars_q:
    height = bar.get_height()
    ax2.text(bar.get_x() + bar.get_width()/2, height + 1.5, f'{int(height)}', 
             va='bottom', ha='center', fontweight='bold')
ax2.set_title("Distribution of Reports by Quarter", fontweight='bold', pad=10)
ax2.set_ylabel("Number of Reports")
ax2.set_ylim(0, 70)

plt.suptitle("Dataset Temporal Characteristics (Total: 238 Reports)", fontweight='bold', fontsize=14, y=0.98)
plt.tight_layout()
plt.savefig(os.path.join(output_dir, "dataset_temporal_distribution.png"), dpi=300)
plt.close()

print("Plots successfully generated and saved to:", output_dir)
