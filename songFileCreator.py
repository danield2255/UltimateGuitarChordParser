import pandas as pd

def main():
    data = {#Input your own sequence of artists and songs
        "Artists": ["Ed Sheeran"], 
        "Name" : ["Perfect"]
    }
    df = pd.DataFrame(data)
    df.to_csv("data/scrapeSongs.csv")

if __name__ == "__main__":
    main()