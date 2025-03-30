import yfinance as yf
import json
import sys
import pandas as pd

# Ensure a symbol is provided
if len(sys.argv) < 2:
    sys.stdout.write(json.dumps({"error": "No symbol provided"}) + "\n")
    sys.stdout.flush()
    sys.exit(1)

symbol = sys.argv[1]

try:
    ticker = yf.Ticker(symbol)
    expiration_dates = ticker.options  # Get available expiration dates

    if not expiration_dates:
        sys.stdout.write(json.dumps({"error": f"No options data available for {symbol}"}) + "\n")
        sys.stdout.flush()
        sys.exit(1)

    exp_date = expiration_dates[0]  # First available expiration date
    options_chain = ticker.option_chain(exp_date)

    # ✅ Convert Pandas DataFrame to JSON-safe format
    def convert_dataframe(df):
        """Convert Pandas DataFrame to JSON serializable format."""
        df = df.copy()
        for col in df.columns:
            if pd.api.types.is_datetime64_any_dtype(df[col]):  # Convert Timestamp columns
                df[col] = df[col].astype(str)
        return df.to_dict(orient="records")

    result = {
        "symbol": symbol,
        "expiration_date": str(exp_date),  # Convert expiration date to string
        "calls": convert_dataframe(options_chain.calls),
        "puts": convert_dataframe(options_chain.puts),
    }

    # ✅ Ensure JSON is fully printed in one go
    json_output = json.dumps(result, separators=(",", ":"))  # Minify JSON
    sys.stdout.write(json_output + "\n")  # Print entire JSON on one line
    sys.stdout.flush()  # Force output to be fully written

except Exception as e:
    sys.stdout.write(json.dumps({"error": f"Failed to fetch options data: {str(e)}"}) + "\n")
    sys.stdout.flush()
    sys.exit(1)
