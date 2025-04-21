# Quality Inspection Dashboard

A Streamlit-based dashboard for monitoring and analyzing quality parameters in real-time.

## Features

- Track ID and Jumbo ID search functionality
- Grade detection with multiple fallback strategies
- Parameter comparison across different tracks
- Visualization of quality parameters with min/max range
- Detailed parameter analysis with failure detection

## Data

The dashboard uses the `Dummy_PM7_Data_1000_Rows.csv` file for demonstration purposes.

## Setup

1. Install the required packages:
   ```
   pip install streamlit pandas numpy altair
   ```

2. Run the dashboard:
   ```
   streamlit run app.py
   ```

## Debug Information

The app includes detailed debug print statements to track grade detection and parameter analysis.
