import pandas as pd
from ydata_profiling import ProfileReport

# Load your dataset
df = pd.read_csv("usdc_zar_cryptocompare_90d.csv")

# Generate the profiling report
profile = ProfileReport(df, title="USDC-ZAR CryptoCompare 90d Report", explorative=True)

# Save report as HTML
profile.to_file("usdc_zar_report.html")
print("✅ Profiling report saved at reports/usdc_zar_profiling.html")
