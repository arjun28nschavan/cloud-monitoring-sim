import argparse
import pandas as pd

def detect_anomalies(df, column, window, threshold):
    df = df.copy()
    # Use shift(1) so the spike is NOT included in its own baseline
    df['rolling_mean'] = df[column].shift(1).rolling(window=window, min_periods=1).mean()
    df['rolling_std'] = df[column].shift(1).rolling(window=window, min_periods=1).std().fillna(0)
    safe_std = df['rolling_std'].replace(0, 1e-9)
    df['z_score'] = (df[column] - df['rolling_mean']) / safe_std
    df['is_anomaly'] = df['z_score'].abs() > threshold
    return df

parser = argparse.ArgumentParser()
parser.add_argument('csv_path')
parser.add_argument('--column', default='value')
parser.add_argument('--window', type=int, default=3)
parser.add_argument('--threshold', type=float, default=2.0)
args = parser.parse_args()

df = pd.read_csv(args.csv_path)
result = detect_anomalies(df, args.column, args.window, args.threshold)
anomalies = result[result['is_anomaly']]
print(f'Analyzed {len(result)} points, found {len(anomalies)} anomalies.')
if not anomalies.empty:
    print(anomalies[['timestamp', args.column, 'z_score']].to_string(index=False))
else:
    print('No anomalies found at this threshold.')
out = args.csv_path.replace('.csv', '_annotated.csv')
result.to_csv(out, index=False)
print(f'Output written to {out}')
