import pandas as pd


class CSVReader:

    def __init__(self, path):
        self.df = pd.read_csv(path)

    def get_leads(self):
        return self.df.to_dict(orient="records")