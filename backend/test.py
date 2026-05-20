from parsers import loader
from physics import cof
import matplotlib.pyplot as plt

df, step_df, header = loader.load_data("data/OFT07935.txt", "OFT")
df_offset = cof.cof_offset(df.copy(), step_df)
df_filtered = df_offset.copy()
df_filtered["cof_filtered"] = cof.cof_filter(df_filtered["cof"], 25)

plt.plot(df_filtered["time"], df_filtered["cof_filtered"])
plt.show()
