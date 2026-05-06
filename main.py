from read_files import load
import matplotlib.pyplot as plt
import pandas as pd

import logging
logging.basicConfig(level=logging.INFO)   #so we can see the logs in the terminal

# --- SETTINGS ---
FILE_PATH = "data/OFT07935.txt"   #
DATA_TYPE = "OFT"               # Options: "SRV", "SRV_FSA", "OFT"

def main():
    print(f"Loading file: {FILE_PATH}")

    try:
        # Expected types:
        # df -> pd.DataFrame (main measurement data)
        # step_df -> pd.DataFrame | None (step metadata, may be missing)
        # header -> dict | None (header metadata, may be missing)
        df: pd.DataFrame
        step_df: pd.DataFrame | None
        header: dict | None
        df, step_df, header = load.load_data(FILE_PATH, DATA_TYPE)

        print("✅ Data loaded successfully!")

        # Plot CoF vs Zeit
        plt.plot(df['Zeit [s]'], df['CoF'])
        plt.xlabel('Zeit [s]')
        plt.ylabel('Coefficient of Friction (CoF)')
        plt.title('CoF vs Zeit')
        plt.show()

    except FileNotFoundError:
        print("❌ File not found!")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()