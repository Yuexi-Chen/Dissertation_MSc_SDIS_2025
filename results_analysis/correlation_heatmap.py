import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

data = pd.read_csv('table_output/correlation_heatmap.csv')

matrix_data = data.set_index('Metric').T

plt.figure(figsize=(10, 8), dpi=300)

heatmap = sns.heatmap(matrix_data, 
                      cmap='RdGy_r',  
                      center=0,        
                      vmin=-1,         
                      vmax=1,          
                      annot=True,      
                      fmt='.2f',       
                      square=True,     
                      cbar_kws={
                          'label': 'Correlation Coefficient',
                          'shrink': 0.3,    
                          'aspect': 20,     
                          'orientation': 'vertical'
                      })

plt.title('Correlation Heatmap of Performance Metrics', pad=20)
plt.tight_layout()

plt.savefig('figure/correlation_heatmap.png', 
            bbox_inches='tight',       
            dpi=300)                   

plt.close()