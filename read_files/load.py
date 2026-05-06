from read_files import SRV, SRV_FSA, OFT
import pandas as pd


def load_data(filename, data_origin):  #function to load data from different file formats based on the data origin 
    df = None    
    print(type(df))                        
    step_df = None
    header = None
    if data_origin == "SRV":            #so dataorigin is string type
        df, step_df = SRV.readRawFile(filename)
    elif data_origin == "SRV_FSA":
        df, step_df = SRV_FSA.readRawFile(filename)
    elif data_origin == "OFT":
        df, step_df, header = OFT.readRawFile(filename)
    else:
        raise Exception(
            f"File format {data_origin} is not implemented. Filename provided is {filename}"    #The f before the string stands for "formatted string literal" (also called f-string), which is a feature introduced in Python 3.6.
        )                                                                                       #The f tells Python to evaluate expressions inside curly braces {} and insert their values into the string.
    if step_df is None:
        if df is not None and not df.empty:
            step_df = pd.DataFrame(
                {
                    'Step': [0],
                    'Startzeit [s]': [0],
                    'Endtime [s]': [df["time"].max()],
                    'inactive': [False],
                }
            )
        else:
            print("Warning: df is empty, cannot generate step_df.")
    df['stroke'] = df['stroke'].astype(float)
    return df, step_df, header
