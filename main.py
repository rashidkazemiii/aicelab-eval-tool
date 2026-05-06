from read_files import load
import matplotlib.pyplot as plt

import logging
logging.basicConfig(level=logging.INFO)   #so we can see the logs in the terminal

# --- SETTINGS ---
FILE_PATH = "data/OFT07935.txt"   #
DATA_TYPE = "OFT"               # Options: "SRV", "SRV_FSA", "OFT"

def main():
    print(f"Loading file: {FILE_PATH}")

    try:
        df, step_df, header = load.load_data(FILE_PATH, DATA_TYPE)

        print("✅ Data loaded successfully!")

        # Inspect the data
        print("\n--- df (first rows) ---")
        print(df.head())

        # Plot CoF vs Time
        plt.plot(df['time'], df['CoF'])
        plt.xlabel('Time')
        plt.ylabel('Coefficient of Friction (CoF)')
        plt.title('CoF vs Time')
        plt.show()

    except FileNotFoundError:
        print("❌ File not found!")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()