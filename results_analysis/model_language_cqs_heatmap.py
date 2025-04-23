import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap

file_path = 'table_output/model_language_cqs.csv'
df = pd.read_csv(file_path)

df.set_index('model', inplace=True)

heatmap_data = df[['Go', 'JavaScript', 'Python']]


colors = ["white", "red", "black"]

cmap_name = 'white_red_black'
custom_cmap = LinearSegmentedColormap.from_list(cmap_name, colors)

vmin = heatmap_data.min().min() - 5
vmax = heatmap_data.max().max()


plt.figure(figsize=(8, 4))
sns.heatmap(
    heatmap_data,
    annot=True,      
    fmt=".2f",  
    cmap=custom_cmap, 
    linewidths=.5, 
    linecolor='grey', 
    cbar_kws={'label': 'Code Quality Score (CQS)'}, 
    vmin=vmin,     
    vmax=vmax   
)

plt.title('Model Performance across Languages (CQS)') 
plt.ylabel('Model') 
plt.xlabel('Programming Language') 
plt.xticks(rotation=0) 
plt.yticks(rotation=0) 
plt.tight_layout() 


output_path = 'figure/model_language_cqs_heatmap.png'
plt.savefig(output_path, dpi=300)

print(f"Heatmap saved to {output_path}")