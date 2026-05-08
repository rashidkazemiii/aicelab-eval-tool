from read_files import load
from physics import utility_functions
import matplotlib.pyplot as plt

df, step_df, header = load.load_data("data/OFT07935.txt", "OFT")
df_offset = utility_functions.offset(df.copy(), step_df)
df_filtered = utility_functions.filter(df_offset.copy(), step_df, 25)

# Use the correct column names
plt.plot(df_filtered['Zeit [s]'], df_filtered['CoF'])
plt.show()