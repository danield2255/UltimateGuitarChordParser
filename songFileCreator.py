import pandas as pd

def main():
    data = {#Input your own sequence of artists and songs
        "Artists": ["Ed Sheeran", "Foo Fighters"], 
        "Name" : ["Perfect", "Everlong"]
    }
    df = pd.DataFrame(data)
    df.to_csv("data/scrapeSongs.csv")

if __name__ == "__main__":
    main()

    