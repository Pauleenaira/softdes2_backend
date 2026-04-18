import pandas as pd

def load_data():
    df = pd.read_csv("data/monthly_Sales.csv")

    # CLEAN DATA (based on your PDF)
    df = df.dropna()

    return df