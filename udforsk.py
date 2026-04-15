import pandas as pd

# Indlæs CSV-filen
df = pd.read_csv('movies_metadata.csv', low_memory=False)

# Se de første 5 rækker
print(df.head())

# Se alle kolonnenavne
print(df.columns.tolist())

# Hvor mange film er der?
print(f'Antal film: {len(df)}')