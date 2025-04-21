import streamlit as st
import pandas as pd
import numpy as np
import altair as alt
import re

def safe_division(numerator, denominator, default=0.0):
    """Safely perform division with error handling"""
    try:
        if denominator == 0:
            return default
        return (numerator / denominator)
    except:
        return default

def calculate_compliance_rate(in_range_count, total_count):
    """Calculate compliance rate with safety checks"""
    if total_count == 0:
        return 0.0
    return safe_division(in_range_count, total_count) * 100

def get_parameter_ranges(df):
    """Extract parameter-specific ranges from the data"""
    ranges = {}
    
    # Debug: Print dataframe info before extracting ranges
    print("DEBUG - get_parameter_ranges called")
    print(f"DEBUG - DataFrame shape: {df.shape}")
    print(f"DEBUG - Process_Parameters unique values: {df['Process_Parameters'].unique().tolist()}")
    
    # First, get ranges from Process_Parameters column
    for index, row in df.iterrows():
        param = row['Process_Parameters']
        if param not in ranges:  # Only add if not already present
            ranges[param] = {
                'min': float(row['Min']),
                'max': float(row['Max']),
                'avg': float(row['Average'])
            }
            # Debug: Print range added
            print(f"DEBUG - Added range for parameter '{param}': min={ranges[param]['min']}, max={ranges[param]['max']}, avg={ranges[param]['avg']}")
    
    # Add specific ranges for parameters based on domain knowledge
    # CALIPER specific range (example - adjust these values based on actual requirements)
    if 'CALIPER' not in ranges:
        ranges['CALIPER'] = {
            'min': 250.0,  # Example minimum value for CALIPER
            'max': 300.0,  # Example maximum value for CALIPER
            'avg': 275.0   # Example average value for CALIPER
        }
        print(f"DEBUG - Added default range for 'CALIPER': min=250.0, max=300.0, avg=275.0")
    
    # Add default ranges for other parameters if needed
    default_ranges = {
        'BULK': {'min': 250.0, 'max': 350.0, 'avg': 300.0},
        'MOISTURE': {'min': 200.0, 'max': 280.0, 'avg': 240.0},
        # Add more parameter ranges as needed
    }
    
    # Update ranges with defaults for missing parameters
    for param, range_values in default_ranges.items():
        if param not in ranges:
            ranges[param] = range_values
            print(f"DEBUG - Added default range for '{param}': min={range_values['min']}, max={range_values['max']}, avg={range_values['avg']}")
    
    # Debug: Print final ranges
    print(f"DEBUG - Total parameters with ranges: {len(ranges)}")
    
    return ranges

def get_parameter_status(param_value, min_val, max_val):
    """Get parameter status with proper type checking and range validation"""
    try:
        param_value = float(param_value)
        min_val = float(min_val)
        max_val = float(max_val)
        
        # Debug: Print parameter status check
        print(f"DEBUG - Checking parameter status: value={param_value}, min={min_val}, max={max_val}")
        
        # Ensure min_val is less than max_val
        if min_val > max_val:
            print(f"DEBUG - Warning: min_val ({min_val}) > max_val ({max_val}), swapping values")
            min_val, max_val = max_val, min_val
            
        if min_val <= param_value <= max_val:
            print(f"DEBUG - Parameter PASS: {param_value} in range [{min_val}, {max_val}]")
            return "PASS", 0.0
        
        # Calculate deviation from the nearest boundary
        if param_value < min_val:
            deviation = param_value - min_val
            print(f"DEBUG - Parameter FAIL_LOW: {param_value} < {min_val}, deviation={deviation}")
            return "FAIL_LOW", deviation
        else:
            deviation = param_value - max_val
            print(f"DEBUG - Parameter FAIL_HIGH: {param_value} > {max_val}, deviation={deviation}")
            return "FAIL_HIGH", deviation
            
    except (ValueError, TypeError) as e:
        print(f"DEBUG - Error in get_parameter_status: {e}")
        return "INVALID", 0.0

def display_parameter_card(label, value, min_val, max_val, process_param=False):
    """Display parameter card with enhanced range validation and failure indication"""
    try:
        status, deviation = get_parameter_status(value, min_val, max_val)
        
        if status == "PASS":
            status_class = "parameter-in-range"
            status_text = "✅ PASS"
            deviation_class = "deviation-ok"
        elif status == "FAIL_LOW":
            status_class = "parameter-out-of-range"
            status_text = "❌ FAIL (LOW)"
            deviation_class = "deviation-low"
        else:  # FAIL_HIGH
            status_class = "parameter-out-of-range"
            status_text = "❌ FAIL (HIGH)"
            deviation_class = "deviation-high"
        
        deviation_text = f"{deviation:+.2f}" if status != "PASS" else "✓"
        
        # Special styling for process parameters
        process_class = "process-parameter" if process_param else ""
        
        st.markdown(f"""
            <div class="parameter-card {status_class} {process_class}">
                <div style="display: flex; justify-content: space-between; align-items: start;">
                    <div>
                        <div class="parameter-header">
                            <strong>{label}</strong>
                            <span class="status-badge {status_class}">{status_text}</span>
                        </div>
                        <div class="range-indicator">
                            Acceptable Range: {min_val:.2f} - {max_val:.2f}
                        </div>
                    </div>
                    <div class="value-container">
                        <div class="current-value">Current: {value:.2f}</div>
                        <span class="deviation-value {deviation_class}">
                            Deviation: {deviation_text}
                        </span>
                    </div>
                </div>
            </div>
        """, unsafe_allow_html=True)
    except Exception as e:
        st.error(f"Error displaying parameter card: {str(e)}")

# Set page configuration with theme-independent settings
st.set_page_config(
    page_title="Quality Inspection Dashboard",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Add theme-independent custom CSS
st.markdown("""
    <style>
    /* Container styling */
    .stApp {
        max-width: 100%;
        padding: 1rem 2rem;
    }
    
    /* Card styling */
    div[data-testid="stMetric"] {
        background-color: var(--background-color);
        border: 1px solid var(--secondary-background-color);
        padding: 1rem;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    
    div[data-testid="stMetric"]:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
    }
    
    /* Metric label styling */
    div[data-testid="stMetricLabel"] {
        font-size: 0.875rem !important;
        font-weight: 500 !important;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
    }
    
    /* Metric value styling */
    div[data-testid="stMetricValue"] {
        font-size: 1.5rem !important;
        font-weight: 600 !important;
    }
    
    /* Tab styling */
    button[data-baseweb="tab"] {
        font-size: 1rem !important;
        font-weight: 500 !important;
        padding: 0.75rem 1rem !important;
    }
    
    /* Header styling */
    h1, h2, h3 {
        font-weight: 600 !important;
        margin-bottom: 1.5rem !important;
    }
    
    /* Dataframe styling */
    .stDataFrame {
        border: 1px solid var(--secondary-background-color);
        border-radius: 8px;
        padding: 1rem;
        margin: 1rem 0;
        width: 100% !important;
        max-width: 100% !important;
        overflow: auto !important;
    }
    
    /* Fix for Parameter Range table flickering */
    div[data-testid="stDataFrame"] {
        width: 100% !important;
        min-width: 100% !important;
    }
    
    div[data-testid="stDataFrame"] > div {
        width: 100% !important;
        min-width: 100% !important;
    }
    
    div[data-testid="stDataFrame"] table {
        width: 100% !important;
        min-width: 100% !important;
    }
    
    /* Search box styling */
    div[data-baseweb="input"] {
        border-radius: 8px !important;
    }
    
    /* Alert/Info box styling */
    div[data-testid="stAlert"] {
        border-radius: 8px;
        padding: 1rem;
        margin: 1rem 0;
        border: none;
    }
    
    /* Grade status styling */
    .grade-status {
        padding: 1rem;
        border-radius: 12px;
        text-align: center;
        margin: 1rem 0;
        font-weight: bold;
        font-size: 1.5rem;
        transition: all 0.3s ease;
    }
    
    .grade-ok {
        background: linear-gradient(135deg, rgba(0, 200, 0, 0.1) 0%, rgba(0, 200, 0, 0.2) 100%);
        border: 2px solid rgba(0, 200, 0, 0.3);
        color: #00c853;
    }
    
    .grade-not-ok {
        background: linear-gradient(135deg, rgba(255, 0, 0, 0.1) 0%, rgba(255, 0, 0, 0.2) 100%);
        border: 2px solid rgba(255, 0, 0, 0.3);
        color: #ff1744;
    }
    
    /* Enhanced metric styling for grade */
    .grade-metric {
        transform: scale(1.1);
        margin: 1rem 0;
    }
    
    /* Pulsing animation for grade status */
    @keyframes pulse {
        0% { transform: scale(1); }
        50% { transform: scale(1.02); }
        100% { transform: scale(1); }
    }
    
    .grade-pulse {
        animation: pulse 2s infinite;
    }
    
    /* Parameter range indicator */
    .parameter-card {
        padding: 1.5rem;
        border-radius: 10px;
        margin: 0.8rem 0;
        border: 1px solid var(--secondary-background-color);
        transition: all 0.3s ease;
    }
    
    .process-parameter {
        transform: scale(1.02);
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
        border-width: 2px;
    }
    
    .parameter-header {
        display: flex;
        align-items: center;
        gap: 1rem;
        margin-bottom: 0.5rem;
    }
    
    .status-badge {
        padding: 0.3rem 0.6rem;
        border-radius: 4px;
        font-size: 0.9rem;
        font-weight: 500;
    }
    
    .value-container {
        text-align: right;
    }
    
    .current-value {
        font-size: 1.1rem;
        font-weight: 500;
        margin-bottom: 0.3rem;
    }
    
    .parameter-in-range {
        background: linear-gradient(135deg, rgba(0, 200, 0, 0.05) 0%, rgba(0, 200, 0, 0.1) 100%);
        border-left: 4px solid #00c853;
    }
    
    .parameter-in-range .status-badge {
        background: rgba(0, 200, 0, 0.1);
        color: #00c853;
    }
    
    .parameter-out-of-range {
        background: linear-gradient(135deg, rgba(255, 0, 0, 0.05) 0%, rgba(255, 0, 0, 0.1) 100%);
        border-left: 4px solid #ff1744;
    }
    
    .parameter-out-of-range .status-badge {
        background: rgba(255, 0, 0, 0.1);
        color: #ff1744;
    }
    
    .failure-summary {
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
        background: rgba(255, 0, 0, 0.05);
        border: 1px solid rgba(255, 0, 0, 0.2);
    }
    
    .failure-summary h4 {
        color: #ff1744;
        margin: 0 0 0.5rem 0;
    }
    
    .failure-item {
        margin: 0.3rem 0;
        padding: 0.5rem;
        background: rgba(255, 255, 255, 0.05);
        border-radius: 4px;
    }
    
    .chart-container {
        width: 100%;
        max-width: 450px;
        margin: 0 auto;
        padding: 10px;
    }
    
    /* Parameter range table - prevent flickering */
    .parameter-range-table {
        width: 100% !important;
        margin: 1rem 0;
        border-radius: 8px;
        overflow: hidden;
    }
    
    .parameter-range-table div[data-testid="stDataFrame"] {
        width: 100% !important;
        min-width: 100% !important;
    }
    
    .parameter-range-table div[data-testid="stDataFrame"] table {
        table-layout: fixed !important;
        width: 100% !important;
    }
    
    .parameter-range-table div[data-testid="stDataFrame"] td,
    .parameter-range-table div[data-testid="stDataFrame"] th {
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
    }
    </style>
""", unsafe_allow_html=True)

# Title with icon and subtitle
st.markdown("""
    <div style='text-align: center; padding: 2rem 0;'>
        <h1 style='font-size: 2.5rem; margin-bottom: 0.5rem;'>🔍 Quality Inspection Dashboard</h1>
        <p style='font-size: 1.1rem; opacity: 0.8;'>Monitor and analyze quality parameters in real-time</p>
    </div>
""", unsafe_allow_html=True)

# Load data with loading indicator
@st.cache_data(show_spinner=True)
def load_data():
    df = pd.read_csv("Dummy_PM7_Data_1000_Rows.csv")
    # Debug: Print dataset columns for troubleshooting
    print("DEBUG - Dataset Columns:", df.columns.tolist())
    print("DEBUG - Dataset Column Types:")
    for col in df.columns:
        print(f"  {col}: {df[col].dtype}")
    return df

# Define parameter groups with icons - moved outside tabs
parameter_groups = {
    '📋 Basic Information': ['M_C', 'Jumbo_ID', 'Track', 'KIT', 'Quality', 
                           'GSM_2SIGMA_ABB', 'CALIPER_CD_2SIGMA_ABB', 'MOISTURE_2SIGMA_ABB',
                           'TL_GSM', 'BL_GSM', 'GSM_2SIGMA_CD_ABB'],
    '📏 Physical Properties': ['SUBSTANCE', 'CALIPER', 'BULK'],
    '🔍 Surface Properties': [
        'COBB_TS', 'COBB_WS', 'COBB_FL_3MIN', 'COBB_WS_3MIN',
        'GLOSS_AT_75_TS', 'ROUGHNESS_PPS_TS'
    ],
    '👁️ Optical Properties': [
        'BRIGHTNESS_ISO_TS', 'BRIGHTNESS_ISO_BS',
        'WHITENESS_TS',
        'L_VALUE_TS', 'a_VALUE_TS', 'b_VALUE_TS',
        'L_VALUE_BS', 'a_VALUE_BS', 'b_VALUE_BS',
        'DELTA_E_TS', 'IGT_PICK_TOP_MED_VIS', 'IGT_PICK_BOT_MED_VIS'
    ],
    '⚡ Mechanical Properties': [
        'STIFFNESS_L_W_MD', 'STIFFNESS_L_W_CD', 'STIFFNESS_L_W_GM',
        'STIFFNESS_RATIO', 'PLYBOND'
    ],
    '🧪 Chemical Properties': [
        'MOISTURE', 'ASH_TOP_LAYER', 'ASH_BOTTOM_LAYER'
    ]
}

# Create navigation tabs
nav_tabs = st.tabs(["📊 Overall Analysis", "🔎 Track ID Search", "📊 Parameter Comparison"])

# Overall Analysis Tab
with nav_tabs[0]:
    st.markdown("### 📈 Overall Data Analysis")
    
    # Load data if not already loaded
    try:
        with st.spinner('Analyzing data...'):
            df = load_data()
            
            # 1. Count unique Track IDs with OK and NOT OK Quality
            # Get unique Track IDs and their associated Quality status
            track_quality = df[['Track', 'Quality']].drop_duplicates()
            
            # Count Track IDs by Quality status
            ok_count = sum(track_quality['Quality'].str.strip().str.upper() == 'OK')
            not_ok_count = len(track_quality) - ok_count
            
            # Display counts in metrics
            st.markdown("#### 📊 Quality Status Distribution")
            cols = st.columns(3)
            
            with cols[0]:
                st.metric(
                    "Total Unique Track IDs",
                    len(track_quality),
                    help="Total number of unique Track IDs in the dataset"
                )
            
            with cols[1]:
                st.metric(
                    "OK Quality Track IDs",
                    ok_count,
                    delta=f"{ok_count/len(track_quality):.1%}",
                    delta_color="normal",
                    help="Number of unique Track IDs with OK quality status"
                )
            
            with cols[2]:
                st.metric(
                    "NOT OK Quality Track IDs",
                    not_ok_count,
                    delta=f"{not_ok_count/len(track_quality):.1%}",
                    delta_color="inverse",
                    help="Number of unique Track IDs with NOT OK quality status"
                )
            
            # Improved visualizations with uniform styling and reduced width
            st.markdown("---")
            
            # Define consistent chart dimensions
            chart_width = 400
            chart_height = 300
            
            # Add CSS to ensure consistent container sizes
            st.markdown("""
                <style>
                .chart-container {
                    width: 100%;
                    max-width: 450px;
                    margin: 0 auto;
                    padding: 10px;
                }
                </style>
            """, unsafe_allow_html=True)
            
            fig_col1, fig_col2 = st.columns(2)
            
            with fig_col1:
                # Pie chart with consistent styling
                st.markdown("<div class='chart-container'>", unsafe_allow_html=True)
                st.markdown("#### Quality Distribution (Pie Chart)")
                
                # Create data for charts
                status_data = pd.DataFrame({
                    'Status': ['OK', 'NOT OK'],
                    'Count': [ok_count, not_ok_count]
                })
                
                pie = alt.Chart(status_data).mark_arc().encode(
                    theta=alt.Theta(field="Count", type="quantitative"),
                    color=alt.Color(
                        'Status:N',
                        scale=alt.Scale(
                            domain=['OK', 'NOT OK'],
                            range=['#00c853', '#ff1744']
                        ),
                        legend=alt.Legend(
                            title="Quality Status",
                            orient="bottom"
                        )
                    ),
                    tooltip=['Status', 'Count']
                ).properties(
                    width=chart_width,
                    height=chart_height
                )
                
                # Apply configuration after combining
                pie_configured = pie.configure_view(
                    strokeWidth=0
                )
                
                st.altair_chart(pie_configured, use_container_width=False)
                st.markdown("</div>", unsafe_allow_html=True)
            
            # 2. Analyze parameter failures for NOT OK Track IDs
            st.markdown("### ❌ Parameter Failure Analysis")
            
            # Get all NOT OK rows
            not_ok_rows = df[df['Quality'].str.strip().str.upper() != 'OK']
            
            # Debug: Print NOT OK rows info
            print(f"DEBUG - NOT OK Rows Count: {len(not_ok_rows)}")
            if len(not_ok_rows) > 0:
                print(f"DEBUG - NOT OK Quality Values: {not_ok_rows['Quality'].unique().tolist()}")
            
            if len(not_ok_rows) > 0:
                # Get unique Track IDs with NOT OK status
                not_ok_track_ids = not_ok_rows['Track'].unique()
                
                # Get all numeric columns from the dataframe for analysis
                # Exclude non-parameter columns
                exclude_columns = ['M_C', 'Jumbo_ID', 'Track', 'KIT', 'Quality', 'Process_Parameters', 'Min', 'Max', 'Average']
                numeric_columns = df.select_dtypes(include=['number']).columns.tolist()
                parameter_columns = [col for col in numeric_columns if col not in exclude_columns]
                
                # Debug: Print parameter columns for troubleshooting
                print("DEBUG - Numeric Columns:", numeric_columns)
                print("DEBUG - Parameter Columns:", parameter_columns)
                
                # Extract ranges from Process_Parameters column
                param_ranges = {}
                for param in parameter_columns:
                    # Check if this parameter appears in Process_Parameters
                    param_rows = df[df['Process_Parameters'] == param]
                    if not param_rows.empty:
                        # Use the range from the data
                        param_ranges[param] = {
                            'min': float(param_rows['Min'].iloc[0]),
                            'max': float(param_rows['Max'].iloc[0]),
                            'avg': float(param_rows['Average'].iloc[0])
                        }
                    else:
                        # Calculate ranges from the actual data
                        try:
                            values = df[param].dropna()
                            if len(values) > 0:
                                min_val = float(values.min())
                                max_val = float(values.max())
                                avg_val = float(values.mean())
                                
                                # Widen the range slightly to avoid false positives
                                range_width = max_val - min_val
                                min_val = max(0, min_val - (range_width * 0.1))
                                max_val = max_val + (range_width * 0.1)
                                
                                param_ranges[param] = {
                                    'min': min_val,
                                    'max': max_val,
                                    'avg': avg_val
                                }
                        except Exception as e:
                            pass
                
                # Dictionary to store parameter failure counts
                param_failures = {}
                
                # Analyze each NOT OK Track ID
                for track_id in not_ok_track_ids:
                    # Get data for this Track ID
                    track_data = df[df['Track'] == track_id]
                    
                    # Check each parameter for this Track ID
                    for param in parameter_columns:
                        if param in param_ranges:
                            try:
                                # Get the value for this parameter
                                value = track_data[param].iloc[0]
                                
                                # Skip NaN values
                                if pd.isna(value):
                                    continue
                                    
                                # Convert to float
                                value = float(value)
                                
                                # Get the range
                                min_val = param_ranges[param]['min']
                                max_val = param_ranges[param]['max']
                                
                                # Check if value is out of range
                                if not (min_val <= value <= max_val):
                                    # Count the failure
                                    if param in param_failures:
                                        param_failures[param] += 1
                                    else:
                                        param_failures[param] = 1
                            except Exception as e:
                                pass
                
                # Display parameter failure counts with improved visualization
                if param_failures:
                    # Convert to DataFrame for display
                    failure_data = pd.DataFrame({
                        'Parameter': list(param_failures.keys()),
                        'Failure Count': list(param_failures.values())
                    })
                    
                    # Calculate percentage of NOT OK Track IDs
                    failure_data['Failure Percentage'] = (failure_data['Failure Count'] / len(not_ok_track_ids) * 100).round(1)
                    
                    # Sort by failure count (descending)
                    failure_data = failure_data.sort_values('Failure Count', ascending=False)
                    
                    # Display as improved bar chart with consistent styling
                    with fig_col2:
                        st.markdown("<div class='chart-container'>", unsafe_allow_html=True)
                        st.markdown("#### Parameter Failure Counts")
                        
                        # Limit to top 10 parameters for cleaner display
                        top_failures = failure_data.head(10).copy()
                        
                        # Create Altair horizontal bar chart with consistent styling
                        bars = alt.Chart(top_failures).mark_bar().encode(
                            y=alt.Y('Parameter:N', sort='-x', title=None),
                            x=alt.X('Failure Count:Q', title='Number of Failures'),
                            color=alt.value('#ff5252'),
                            tooltip=['Parameter', 'Failure Count', 'Failure Percentage']
                        ).properties(
                            width=chart_width,
                            height=min(chart_height, len(top_failures) * 25 + 50)
                        )
                        
                        # Add text labels
                        text = bars.mark_text(
                            align='left',
                            baseline='middle',
                            dx=3,
                            color='white'
                        ).encode(
                            text=alt.Text('Failure Count:Q')
                        )
                        
                        # Combine charts first, then apply configuration
                        combined_chart = (bars + text).configure_view(
                            strokeWidth=0
                        ).configure_axis(
                            grid=False
                        )
                        
                        st.altair_chart(combined_chart, use_container_width=False)
                        st.markdown("</div>", unsafe_allow_html=True)
                    
                    # Format the percentage column for display
                    failure_data['Failure Percentage'] = failure_data['Failure Percentage'].apply(lambda x: f"{x}%")
                    
                    # Create a container with scrollable height for all parameters
                    with st.container():
                        # Create multiple columns for parameter cards
                        num_cols = 3
                        for i in range(0, len(failure_data), num_cols):
                            cols = st.columns(num_cols)
                            
                            # Get the slice of parameters for this row
                            row_params = failure_data.iloc[i:min(i+num_cols, len(failure_data))]
                            
                            # For each parameter in this row
                            for j, (_, row) in enumerate(row_params.iterrows()):
                                with cols[j]:
                                    param_name = row['Parameter']
                                    failure_count = row['Failure Count']
                                    failure_pct = row['Failure Percentage']
                                    
                                    # Determine color intensity based on failure count (higher = more intense red)
                                    color_intensity = min(0.1 + (float(failure_count) / not_ok_count) * 0.15, 0.25)
                                    border_intensity = min(0.3 + (float(failure_count) / not_ok_count) * 0.3, 0.6)
                                    
                                    st.markdown(f"""
                                        <div style="padding: 1rem; 
                                            background: linear-gradient(135deg, rgba(255, 0, 0, {color_intensity}) 0%, rgba(255, 0, 0, {color_intensity+0.05}) 100%); 
                                            border-left: 4px solid rgba(255, 0, 0, {border_intensity}); 
                                            border-radius: 5px; 
                                            margin: 0.5rem 0;
                                            height: 100%;">
                                            <h4 style="margin: 0 0 0.5rem 0;">{param_name}</h4>
                                            <p style="margin: 0 0 0.3rem 0;"><strong>Failed in:</strong> {failure_count} Track IDs</p>
                                            <p style="margin: 0;"><strong>Percentage:</strong> {failure_pct} of NOT OK Track IDs</p>
                                        </div>
                                    """, unsafe_allow_html=True)
                    
                    # Calculate ranges but don't display the table
                    range_data = []
                    for param in failure_data['Parameter']:
                        if param in param_ranges:
                            range_data.append({
                                'Parameter': param,
                                'Min Value': f"{param_ranges[param]['min']:.2f}",
                                'Max Value': f"{param_ranges[param]['max']:.2f}",
                                'Target Value': f"{param_ranges[param]['avg']:.2f}",
                                'Failure Count': failure_data[failure_data['Parameter'] == param]['Failure Count'].iloc[0],
                                'Failure %': failure_data[failure_data['Parameter'] == param]['Failure Percentage'].iloc[0]
                            })
                else:
                    st.info("No parameter failures detected in NOT OK Track IDs. This might indicate data inconsistency.")
            else:
                st.info("No NOT OK Track IDs found in the dataset.")
                
    except Exception as e:
        st.error(f"Error analyzing data: {str(e)}")
        st.info("Please check your data format and try again.")

# Track ID Search Tab - Contains all existing functionality
with nav_tabs[1]:
    # Main application logic
    try:
        with st.spinner('Loading data...'):
            df = load_data()
    
        # Search section with improved UI
        st.markdown("### 🔎 Search Records")
        search_col1, search_col2 = st.columns([2, 1])
    
        with search_col1:
            search_value = st.text_input(
                "Enter Track ID or Jumbo ID",
                placeholder="Enter numerical Track ID or alphanumeric Jumbo ID...",
                help="Track ID is numerical (e.g., 12345600) while Jumbo ID is alphanumerical (e.g., ABCD123456)"
            )
    
        # Process and display data
        if search_value:
            # Determine input type and filter data
            is_track_id = search_value.isdigit()
            with search_col2:
                st.info(f"📍 Detected: {'Track ID' if is_track_id else 'Jumbo ID'}")
            
            # Debug: Print search criteria
            print(f"DEBUG - Search Type: {'Track ID' if is_track_id else 'Jumbo ID'}")
            print(f"DEBUG - Search Value: {search_value}")
            
            # Filter data with proper type handling
            try:
                if is_track_id:
                    track_id = int(search_value)
                    # Debug: Show track ID value types
                    print(f"DEBUG - Track ID (int): {track_id}")
                    print(f"DEBUG - Track column type: {df['Track'].dtype}")
                    print(f"DEBUG - Sample Track values: {df['Track'].head(3).tolist()}")
                    
                    filtered_df = df[df['Track'].astype(str).str.strip() == str(track_id)]
                else:
                    # Debug: Show jumbo ID search
                    print(f"DEBUG - Jumbo ID: {search_value}")
                    print(f"DEBUG - Jumbo_ID column type: {df['Jumbo_ID'].dtype}")
                    print(f"DEBUG - Sample Jumbo_ID values: {df['Jumbo_ID'].head(3).tolist()}")
                    
                    filtered_df = df[df['Jumbo_ID'].astype(str).str.strip() == search_value.strip()]
                
                # Debug: Show filtered results
                print(f"DEBUG - Filtered records found: {len(filtered_df)}")
                
                if not filtered_df.empty:
                    # Grade Status Banner - Fixed to handle exact string matching
                    quality_status = filtered_df['Quality'].iloc[0].strip()  # Remove any whitespace
                    is_ok = quality_status.upper() == "OK"  # Case-insensitive comparison
                    
                    st.markdown(f"""
                        <div class='grade-status grade-{"ok" if is_ok else "not-ok"} grade-pulse'>
                            Grade Status: {quality_status}
                            {"✅" if is_ok else "❌"}
                        </div>
                    """, unsafe_allow_html=True)
    
                    # Key metrics with corrected grade status
                    st.markdown("### 📊 Key Metrics")
                    metric_cols = st.columns(5)
                    
                    with metric_cols[0]:
                        delta_color = "normal" if is_ok else "inverse"
                        status_delta = "PASS" if is_ok else "FAIL"
                        st.markdown('<div class="grade-metric">', unsafe_allow_html=True)
                        st.metric(
                            "Quality",
                            quality_status,
                            delta=status_delta,
                            delta_color=delta_color,
                            help="Overall quality status of the product"
                        )
                        st.markdown('</div>', unsafe_allow_html=True)
                        
                    with metric_cols[1]:
                        # Get the grade from the GRADE column
                        grade_value = "N/A"
                        grade_found = False
                        
                        # Get Quality value to avoid confusion
                        quality_value = filtered_df['Quality'].iloc[0]
                        if pd.notna(quality_value):
                            quality_value = str(quality_value).strip().upper()
                        else:
                            quality_value = ""
                            
                        print(f"DEBUG - Quality value is: {quality_value}")
                        
                        # Debug - print all column names to check for GRADE column
                        print(f"DEBUG - All columns in filtered_df: {filtered_df.columns.tolist()}")
                        
                        # Debug - print the entire first 2 rows to inspect all column values
                        for idx, row in filtered_df.head(2).iterrows():
                            print(f"DEBUG - Row {idx} data:")
                            for col, val in row.items():
                                print(f"  {col}: {val}")
                        
                        # Check for the GRADE column directly 
                        if 'GRADE' in filtered_df.columns:
                            print(f"DEBUG - Found exact GRADE column")
                            # Add debug to show the actual values in the GRADE column
                            print(f"DEBUG - GRADE column values (first 5): {filtered_df['GRADE'].head(5).tolist()}")
                            print(f"DEBUG - GRADE column dtype: {filtered_df['GRADE'].dtype}")
                            grade_val = filtered_df['GRADE'].iloc[0]
                            if pd.notna(grade_val) and str(grade_val).strip():
                                grade_value = str(grade_val).strip().upper()
                                grade_found = True
                                print(f"DEBUG - Using value from GRADE column: {grade_value}")
                            else:
                                print(f"DEBUG - GRADE column exists but value is empty or NaN")
                        
                        # Check if there's a case-insensitive match for 'grade'
                        grade_cols = [col for col in filtered_df.columns if col.upper() == 'GRADE']
                        
                        # Also check for common typos and variations
                        typo_variations = ['GRAD', 'GRADES', 'GREADE', 'GARDE']
                        for variation in typo_variations:
                            typo_cols = [col for col in filtered_df.columns if variation in col.upper()]
                            if typo_cols:
                                grade_cols.extend(typo_cols)
                                print(f"DEBUG - Found possible typo variation: {typo_cols}")
                        
                        # Check for fuzzy matches
                        for col in filtered_df.columns:
                            if 'GRA' in col.upper() and 'DE' in col.upper():
                                if col not in grade_cols:
                                    grade_cols.append(col)
                                    print(f"DEBUG - Found fuzzy match: {col}")
                        
                        # Debug - print all potential grade columns found
                        print(f"DEBUG - All identified potential grade columns: {grade_cols}")
                        
                        if grade_cols and not grade_found:
                            print(f"DEBUG - Found case variation of GRADE: {grade_cols[0]}")
                            # Add debug to show values in this column
                            print(f"DEBUG - Column '{grade_cols[0]}' values (first 5): {filtered_df[grade_cols[0]].head(5).tolist()}")
                            print(f"DEBUG - Column '{grade_cols[0]}' dtype: {filtered_df[grade_cols[0]].dtype}")
                            grade_val = filtered_df[grade_cols[0]].iloc[0]
                            if pd.notna(grade_val) and str(grade_val).strip():
                                grade_value = str(grade_val).strip().upper()
                                grade_found = True
                                print(f"DEBUG - Using value from {grade_cols[0]} column: {grade_value}")
                        
                        # Define pattern for FILOPACK 255 format
                        grade_pattern = re.compile(r'([A-Za-z]+\s*PACK\s*\d+)', re.IGNORECASE)
                        
                        # If grade not found, use pattern matching as fallback
                        if not grade_found:
                            print(f"DEBUG - Grade not found in standard columns, searching with pattern: {grade_pattern.pattern}")
                            # Search for the pattern in all columns
                            for col in filtered_df.columns:
                                try:
                                    val = str(filtered_df[col].iloc[0])
                                    # Skip if this is exactly the Quality column
                                    if col == 'Quality':
                                        continue
                                    
                                    # Debug - show columns with FILO or PACK in them
                                    if "FILO" in val.upper() or "PACK" in val.upper():
                                        print(f"DEBUG - Column {col} contains FILO/PACK: {val}")
                                        
                                    match = grade_pattern.search(val)
                                    if match:
                                        potential_grade = match.group(1).strip().upper()
                                        # Make sure this isn't the Quality value
                                        if potential_grade != quality_value:
                                            grade_value = potential_grade
                                            grade_found = True
                                            print(f"DEBUG - Found FILOPACK pattern in {col}: {grade_value}")
                                            break
                                except Exception as e:
                                    print(f"DEBUG - Error processing column {col}: {str(e)}")
                        
                        # If not found yet, try comma-separated values
                        if not grade_found:
                            for col in filtered_df.columns:
                                try:
                                    val = str(filtered_df[col].iloc[0])
                                    if "," in val:
                                        parts = val.split(",")
                                        for part in parts:
                                            match = grade_pattern.search(part)
                                            if match:
                                                potential_grade = match.group(1).strip().upper()
                                                # Make sure this isn't the Quality value
                                                if potential_grade != quality_value:
                                                    grade_value = potential_grade
                                                    grade_found = True
                                                    print(f"DEBUG - Found FILOPACK pattern in {col} part: {grade_value}")
                                                    break
                                        if grade_found:
                                            break
                                except Exception as e:
                                    print(f"DEBUG - Error processing comma-separated values in {col}: {str(e)}")
                        
                        # As absolute fallback, search for FILOPACK anywhere
                        if not grade_found:
                            for col in filtered_df.columns:
                                try:
                                    val = str(filtered_df[col].iloc[0])
                                    if "FILOPACK" in val.upper().replace(" ", "") or "FILO PACK" in val.upper():
                                        # Try to extract just the FILOPACK part
                                        words = val.upper().split()
                                        for i, word in enumerate(words):
                                            if "FILO" in word or "PACK" in word:
                                                # Try to get the word plus the next one if it exists
                                                if i+1 < len(words) and words[i+1].isdigit():
                                                    grade_value = f"{word} {words[i+1]}"
                                                    grade_found = True
                                                    print(f"DEBUG - Found FILO/PACK word pattern: {grade_value}")
                                                    break
                                        
                                        # If still not found, just use the whole value
                                        if not grade_found:
                                            grade_value = val.strip().upper()
                                            grade_found = True
                                            print(f"DEBUG - Using full value containing FILOPACK: {grade_value}")
                                        break
                                except Exception as e:
                                    print(f"DEBUG - Error processing FILOPACK search in {col}: {str(e)}")
                        
                        # Make sure we aren't using Quality value as Grade
                        if grade_value == quality_value or "NOT OK" in grade_value or "OK" == grade_value:
                            print(f"DEBUG - Rejected grade value '{grade_value}' because it matches quality info")
                            print(f"DEBUG - Quality value: '{quality_value}'")
                            print(f"DEBUG - Rejection reason: {'grade=quality' if grade_value == quality_value else 'contains NOT OK' if 'NOT OK' in grade_value else 'is just OK'}")
                            grade_value = "N/A"
                        
                        st.metric(
                            "GRADE",
                            grade_value,
                            help="Product grade classification (e.g., FILOPACK 255)"
                        )
                        
                    with metric_cols[2]:
                        success_rate = 100.0 if is_ok else 0.0
                        st.metric(
                            "Success Rate",
                            f"{success_rate:.1f}%",
                            delta=f"{success_rate:.1f}%" if success_rate > 80 else f"{success_rate:.1f}%",
                            delta_color="normal" if success_rate > 80 else "inverse",
                            help="Percentage of successful quality checks"
                        )
                        
                    with metric_cols[3]:
                        st.metric(
                            "KIT Number",
                            filtered_df['KIT'].iloc[0],
                            help="Product identification number"
                        )
                        
                    with metric_cols[4]:
                        st.metric(
                            "Total Records",
                            len(filtered_df),
                            help="Number of records found"
                        )
    
                    # Add a separator
                    st.markdown("<hr style='margin: 2rem 0; opacity: 0.3;'>", unsafe_allow_html=True)
    
                    # Parameters display in tabs
                    st.markdown("### 📑 Detailed Parameters")
                    
                    # Debug: Print parameter groups and their columns
                    for group_name, parameters in parameter_groups.items():
                        available_params = [p for p in parameters if p in filtered_df.columns]
                        missing_params = [p for p in parameters if p not in filtered_df.columns]
                        print(f"DEBUG - Parameter Group '{group_name}':")
                        print(f"  Available parameters: {available_params}")
                        if missing_params:
                            print(f"  Missing parameters: {missing_params}")
                    
                    tabs = st.tabs(list(parameter_groups.keys()))
                    
                    for tab, (group_name, parameters) in zip(tabs, parameter_groups.items()):
                        with tab:
                            cols = st.columns(3)
                            for idx, param in enumerate(parameters):
                                if param in filtered_df.columns:
                                    col_idx = idx % 3
                                    with cols[col_idx]:
                                        value = filtered_df[param].iloc[0]
                                        st.metric(
                                            label=param,
                                            value=f"{value:.2f}" if isinstance(value, (float, int)) else value,
                                            help=f"Parameter: {param}"
                                        )
    
                    # Process Parameters Analysis
                    
                    try:
                        # Get all parameter ranges
                        parameter_ranges = get_parameter_ranges(df)
                        
                        # Debug: Print parameter ranges
                        print("DEBUG - Parameter Ranges from get_parameter_ranges:")
                        for param, range_data in parameter_ranges.items():
                            print(f"  {param}: min={range_data['min']}, max={range_data['max']}, avg={range_data['avg']}")
                        
                        # Get current process parameter
                        process_params = filtered_df[['Process_Parameters', 'Min', 'Max', 'Average']].iloc[0]
                        current_process = str(process_params['Process_Parameters'])
                        
                        # Debug: Print current process parameter details
                        print(f"DEBUG - Current Process Parameter: {current_process}")
                        print(f"DEBUG - Min: {process_params['Min']}, Max: {process_params['Max']}, Avg: {process_params['Average']}")
                        
                        # Display process parameter status with enhanced visibility
                        param_name = current_process
                        param_min = float(process_params['Min'])
                        param_max = float(process_params['Max'])
                        current_value = float(filtered_df[param_name].iloc[0])
                        
                        st.markdown("### 🎯 Process Parameter Analysis")
                        
                        # Check if all process parameter values are 0
                        all_zeros = True
                        for param in filtered_df.columns:
                            if param in parameter_groups['📏 Physical Properties'] or \
                               param in parameter_groups['🔍 Surface Properties'] or \
                               param in parameter_groups['👁️ Optical Properties'] or \
                               param in parameter_groups['⚡ Mechanical Properties'] or \
                               param in parameter_groups['🧪 Chemical Properties']:
                                try:
                                    value = float(filtered_df[param].iloc[0])
                                    if value != 0:
                                        all_zeros = False
                                        break
                                except (ValueError, TypeError):
                                    continue
                        
                        if not is_ok and all_zeros:
                            st.warning("⚠️ No data available for this grade in Process Parameter Analysis")
                        else:
                            # Display current process parameter card with special styling
                            display_parameter_card(
                                f"Process Parameter: {param_name}",
                                current_value,
                                param_min,
                                param_max,
                                process_param=True
                            )
                            
                            # If Quality is NOT OK, show all failed parameters
                            if not is_ok:
                                # First collect all the parameters that are failing
                                failed_params = []
                                param_ranges = {}
                                
                                # Find ranges for all parameters from Process_Parameters
                                for _, row in df.iterrows():
                                    process_param = row['Process_Parameters']
                                    if process_param not in param_ranges:
                                        param_ranges[process_param] = {
                                            'min': float(row['Min']),
                                            'max': float(row['Max']),
                                            'avg': float(row['Average'])
                                        }
                                
                                # Check all parameters to see which ones are failing
                                for param in filtered_df.columns:
                                    if param in param_ranges:
                                        try:
                                            value = float(filtered_df[param].iloc[0])
                                            min_val = param_ranges[param]['min']
                                            max_val = param_ranges[param]['max']
                                            
                                            status, deviation = get_parameter_status(value, min_val, max_val)
                                            
                                            if status != "PASS":
                                                failed_params.append({
                                                    'name': param,
                                                    'value': value,
                                                    'min': min_val,
                                                    'max': max_val,
                                                    'deviation': deviation,
                                                    'status': status
                                                })
                                        except (ValueError, TypeError):
                                            # Skip if parameter can't be converted to float
                                            continue
                                
                                # Display all failed parameters
                                if failed_params:
                                    st.markdown("#### ❌ Failed Parameters")
                                    st.markdown("The following parameters are outside their acceptable ranges:")
                                    
                                    for param in failed_params:
                                        display_parameter_card(
                                            f"Failed Parameter: {param['name']}",
                                            param['value'],
                                            param['min'],
                                            param['max'],
                                            process_param=True
                                        )
                        
                        # Add Gradewise Quality Range section
                        st.markdown("### 📊 Gradewise Quality Range")
                        st.markdown(f"Quality Grade: **{quality_status}**")
                        
                        # Get the Jumbo ID from the filtered data
                        jumbo_id = filtered_df['Jumbo_ID'].iloc[0]
                        
                        # Find all rows with this Jumbo ID
                        same_jumbo_rows = df[df['Jumbo_ID'] == jumbo_id]
                        
                        # Get all process parameters associated with this Jumbo ID
                        associated_params = same_jumbo_rows['Process_Parameters'].unique()
                        
                        if not is_ok and all_zeros:
                            st.warning("⚠️ No data available for this grade in Gradewise Quality Range")
                        elif len(associated_params) > 0:
                            st.markdown("The following process parameters are associated with this grade:")
                            
                            # Create a table to display parameter ranges
                            range_data = []
                            
                            # Get process parameters with their ranges
                            for param in associated_params:
                                param_rows = df[df['Process_Parameters'] == param]
                                if not param_rows.empty:
                                    min_val = float(param_rows['Min'].iloc[0])
                                    max_val = float(param_rows['Max'].iloc[0])
                                    avg_val = float(param_rows['Average'].iloc[0])
                                    
                                    # Get current value for this parameter if it exists in filtered_df
                                    current_val = "N/A"
                                    param_status = "OK"  # Default status
                                    try:
                                        if param in filtered_df.columns:
                                            value = filtered_df[param].iloc[0]
                                            if pd.notna(value):
                                                current_val = f"{float(value):.2f}"
                                                # Check if parameter is out of range
                                                if float(value) < min_val or float(value) > max_val:
                                                    param_status = "FAIL"
                                    except:
                                        pass
                                    
                                    range_data.append({
                                        "Parameter": param,
                                        "Min Value": f"{float(min_val):.2f}",
                                        "Max Value": f"{float(max_val):.2f}",
                                        "Target Value": f"{float(avg_val):.2f}",
                                        "Current Value": current_val,
                                        "Status": param_status
                                    })
                            
                            # Display as a nice table with highlighting
                            if range_data:
                                range_df = pd.DataFrame(range_data)
                                
                                # Apply conditional formatting to highlight "FAIL" status cells
                                styled_df = range_df.copy()
                                # Only keep Status column for highlighting logic, not for display
                                has_status = 'Status' in styled_df.columns
                                
                                # Wrap in a container with fixed width to prevent flickering
                                st.markdown('<div class="parameter-range-table" style="width:100%;">', unsafe_allow_html=True)
                                st.dataframe(
                                    styled_df if not has_status else styled_df.drop(columns=['Status']),
                                    use_container_width=True,
                                    hide_index=True,
                                    height=min(35 * (len(range_data) + 1), 450),  # Fixed height based on number of rows
                                    column_config={
                                        "Parameter": st.column_config.TextColumn("Process Parameter"),
                                        "Min Value": st.column_config.TextColumn("Min Value"),
                                        "Max Value": st.column_config.TextColumn("Max Value"),
                                        "Target Value": st.column_config.TextColumn("Target Value"),
                                        "Current Value": st.column_config.TextColumn("Current Value")
                                    }
                                )
                                st.markdown('</div>', unsafe_allow_html=True)
                        else:
                            st.info("No specific process parameters associated with this Track ID/Jumbo ID.")
                        
                        # Initialize tracking
                        failures = []
                        valid_params = []
                        out_of_range_params = []
                        in_range_params = []
                        
                        # Analyze parameters
                        for group_name, parameters in parameter_groups.items():
                            for param in parameters:
                                if param in filtered_df.columns:
                                    try:
                                        value = filtered_df[param].iloc[0]
                                        if pd.notna(value) and isinstance(value, (int, float)):
                                            # Find the range for this parameter
                                            param_range = next(
                                                (ranges for param_name, ranges in parameter_ranges.items() 
                                                 if param == param_name),
                                                None
                                            )
                                            
                                            if param_range:
                                                valid_params.append(param)
                                                status, deviation = get_parameter_status(
                                                    value,
                                                    param_range['min'],
                                                    param_range['max']
                                                )
                                                param_data = {
                                                    'name': param,
                                                    'value': float(value),
                                                    'min': param_range['min'],
                                                    'max': param_range['max'],
                                                    'deviation': deviation,
                                                    'status': status,
                                                    'group': group_name
                                                }
                                                if status == "PASS":
                                                    in_range_params.append(param_data)
                                                else:
                                                    out_of_range_params.append(param_data)
                                                    failures.append(param_data)
                                    except (ValueError, TypeError):
                                        continue
                        
                        # Display Failure Summary if any parameters failed
                        if failures:
                            st.markdown("""
                                <div class="failure-summary">
                                    <h4>⚠️ Quality Check Failed</h4>
                                    <p>The following parameters are outside their specific acceptable ranges:</p>
                            """, unsafe_allow_html=True)
                            
                            for failure in sorted(failures, key=lambda x: abs(x['deviation']), reverse=True):
                                status_text = "HIGH" if failure['deviation'] > 0 else "LOW"
                                st.markdown(f"""
                                    <div class="failure-item">
                                        <strong>{failure['name']}</strong> ({failure['group']})<br>
                                        Value: {failure['value']:.2f} | Range: {failure['min']:.2f} - {failure['max']:.2f} | 
                                        Deviation: {failure['deviation']:+.2f} | Status: {status_text}
                                    </div>
                                """, unsafe_allow_html=True)
                            
                            st.markdown("</div>", unsafe_allow_html=True)
                        
                        # Display out of range parameters
                        if out_of_range_params:
                            st.markdown("#### Parameters Outside Range")
                            sorted_out_of_range = sorted(out_of_range_params, 
                                                       key=lambda x: abs(x['deviation']), 
                                                       reverse=True)
                            
                            for param in sorted_out_of_range:
                                display_parameter_card(
                                    f"{param['name']} ({param['group']})",
                                    param['value'],
                                    param['min'],
                                    param['max']
                                )
                        
                        # Display in range parameters
                        if in_range_params:
                            st.markdown("#### Parameters Within Range")
                            cols = st.columns(2)
                            for idx, param in enumerate(in_range_params):
                                with cols[idx % 2]:
                                    display_parameter_card(
                                        param['name'],
                                        param['value'],
                                        param['min'],
                                        param['max']
                                    )
                        
                        # Display summary metrics
                        total_valid_params = len(valid_params)
                        if total_valid_params > 0:
                            st.markdown("### 📈 Quality Analysis Summary")
                            summary_cols = st.columns(3)
                            
                            with summary_cols[0]:
                                st.metric(
                                    "Parameters in Range",
                                    len(in_range_params),
                                    delta=f"{len(in_range_params)}/{total_valid_params}",
                                    delta_color="normal"
                                )
                            
                            with summary_cols[1]:
                                st.metric(
                                    "Parameters Out of Range",
                                    len(out_of_range_params),
                                    delta=f"{len(out_of_range_params)}/{total_valid_params}",
                                    delta_color="inverse"
                                )
                            
                            with summary_cols[2]:
                                quality_status = "FAIL" if failures else "PASS"
                                st.metric(
                                    "Overall Status",
                                    quality_status,
                                    delta="All parameters in range" if quality_status == "PASS" else f"{len(failures)} parameters failed",
                                    delta_color="normal" if quality_status == "PASS" else "inverse"
                                )
                        
                    except Exception as e:
                        st.error(f"Error in parameter analysis: {str(e)}")
                        st.info("Please check the data format and try again.")
    
                else:
                    st.error("❌ No records found for the given input.")
    
            except Exception as e:
                st.error(f"Error processing data: {str(e)}")
                st.info("Please check the input format and try again.")
    
        else:
            st.info("Please enter a Track ID or Jumbo ID to search.")
    
    except Exception as e:
        st.error(f"An error occurred: {str(e)}")
        st.info("Please check your data and try again.")

# End of Track ID Search tab

# Parameter Comparison Tab
with nav_tabs[2]:
    st.markdown("### 📊 Process Parameter Comparison")
    st.markdown("Compare process parameter values across tracks, with min/max range visualization")
    
    try:
        with st.spinner('Loading data...'):
            df = load_data()
            
            # Extract unique values for filters
            process_parameters = sorted(df['Process_Parameters'].unique().tolist())
            
            # Determine grade and machine columns
            # Using GRADE for grade and M_C for machine
            grade_column = 'GRADE'
            machine_column = 'M_C'
            
            # Extract unique grades with special handling
            grades = []
            # First try to get grades from the GRADE column if it exists
            if grade_column in df.columns:
                grades = df[grade_column].dropna().unique().tolist()
                
            # If no grades found, try to extract from other columns
            if not grades:
                print("DEBUG - No grades found in GRADE column, looking in other columns")
                grade_values = set()
                
                # Look for common grade patterns in string columns
                for col in df.columns:
                    try:
                        # Check first few values
                        for val in df[col].head(100).values:
                            if pd.notna(val) and isinstance(val, str):
                                # Look for words followed by numbers - common in grade designations
                                # For example "PACK 255", "GRADE A", etc.
                                val_str = str(val).strip()
                                # Check for patterns like "WORD NUMBER" or text containing "PACK"
                                if ("PACK" in val_str.upper() or "GRADE" in val_str.upper() or 
                                    re.search(r'\b[A-Za-z]+\s+\d+\b', val_str)):
                                    grade_values.add(val_str.upper())  # Convert to uppercase
                    except:
                        pass
                
                # Also check for comma-separated values in string columns
                for col in df.columns:
                    try:
                        # Check first few values
                        for val in df[col].head(100).values:
                            if pd.notna(val) and isinstance(val, str) and "," in val:
                                parts = val.split(",")
                                if len(parts) >= 7:  # Based on the screenshot format
                                    # Last part is often the grade
                                    potential_grade = parts[-1].strip()
                                    # Grade often contains words like "PACK" or follows pattern of words and numbers
                                    if (len(potential_grade.split()) >= 2 or "PACK" in potential_grade.upper() or
                                        re.search(r'\b[A-Za-z]+\s+\d+\b', potential_grade)):
                                        grade_values.add(potential_grade.upper())  # Convert to uppercase
                    except:
                        pass
                
                grades = sorted(list(grade_values))
                print(f"DEBUG - Found {len(grades)} potential grade values")
                print(f"DEBUG - Raw grade values before sorting/processing: {list(grade_values)}")
            
            # Sort grades and ensure they're strings
            grades = sorted([str(g).strip().upper() for g in grades if pd.notna(g)])  # Convert to uppercase
            print(f"DEBUG - Final grades list: {grades}")
            
            machines = sorted(df[machine_column].dropna().unique().tolist())
            
            # Create filter widgets
            col1, col2, col3 = st.columns(3)
            
            with col1:
                selected_parameter = st.selectbox(
                    "Select Process Parameter",
                    options=process_parameters,
                    help="Choose the process parameter to analyze"
                )
            
            with col2:
                selected_grade = st.selectbox(
                    "Select Grade",
                    options=["All"] + grades,
                    help="Filter by product grade"
                )
            
            with col3:
                selected_machine = st.selectbox(
                    "Select Machine",
                    options=["All"] + machines,
                    help="Filter by machine"
                )
            
            # Optional track ID input for comparison
            track_id_input = st.text_input(
                "Enter Track ID for Comparison (Optional)",
                placeholder="Enter a Track ID to highlight in the comparison",
                help="If provided, this Track ID's value will be highlighted in the visualization"
            )
            
            # Filter data based on selections
            filtered_data = df.copy()
            
            # Filter by parameter
            filtered_data = filtered_data[filtered_data['Process_Parameters'] == selected_parameter]
            
            # Filter by grade if not "All"
            if selected_grade != "All":
                # Try to match in GRADE column first
                if grade_column in filtered_data.columns:
                    grade_mask = filtered_data[grade_column].astype(str).str.strip().str.upper() == selected_grade.upper()
                    filtered_data = filtered_data[grade_mask]
                    
                    # If no matches, try looking in other columns
                    if filtered_data.empty:
                        print(f"DEBUG - No tracks found with {grade_column}='{selected_grade}', looking in other columns")
                        filtered_rows = []
                        
                        # Check all columns for the grade value
                        for _, row in filtered_data.iterrows():
                            found = False
                            for col in row.index:
                                val = row[col]
                                if pd.notna(val) and isinstance(val, str):
                                    # Direct match - case insensitive
                                    if selected_grade.upper() in val.upper():
                                        filtered_rows.append(row)
                                        found = True
                                        break
                                    # Split and check if comma-separated
                                    if "," in val:
                                        parts = val.split(",")
                                        # Check if the last part looks like the selected grade
                                        if len(parts) >= 7 and (selected_grade.upper() in parts[-1].upper() or 
                                                             any(selected_grade.upper() in part.upper() for part in parts)):
                                            filtered_rows.append(row)
                                            found = True
                                            break
                            if found:
                                break
                        
                        if filtered_rows:
                            filtered_data = pd.DataFrame(filtered_rows)
                
                else:
                    # If GRADE column doesn't exist, search in string columns
                    filtered_rows = []
                    
                    # Check all columns for the grade value
                    for _, row in filtered_data.iterrows():
                        found = False
                        for col in row.index:
                            val = row[col]
                            if pd.notna(val) and isinstance(val, str):
                                # Direct match - case insensitive
                                if selected_grade.upper() in val.upper():
                                    filtered_rows.append(row)
                                    found = True
                                    break
                                # Split and check if comma-separated
                                if "," in val:
                                    parts = val.split(",")
                                    # Check if the last part looks like the selected grade - case insensitive
                                    if len(parts) >= 7 and (selected_grade.upper() in parts[-1].upper() or 
                                                         any(selected_grade.upper() in part.upper() for part in parts)):
                                        filtered_rows.append(row)
                                        found = True
                                        break
                        if found:
                            break
                    
                    if filtered_rows:
                        filtered_data = pd.DataFrame(filtered_rows)
            
            # Filter by machine if not "All"
            if selected_machine != "All":
                filtered_data = filtered_data[filtered_data[machine_column] == selected_machine]
            
            # Get the min and max values for the selected parameter
            if not filtered_data.empty:
                param_min = float(filtered_data['Min'].iloc[0])
                param_max = float(filtered_data['Max'].iloc[0])
                param_avg = float(filtered_data['Average'].iloc[0])
                
                # Get all tracks with this parameter
                all_tracks_data = df[df['Process_Parameters'] == selected_parameter]
                
                # Filter tracks by grade if not "All"
                if selected_grade != "All":
                    # Try to match in GRADE column first
                    if grade_column in all_tracks_data.columns:
                        grade_mask = all_tracks_data[grade_column].astype(str).str.strip().str.upper() == selected_grade.upper()
                        filtered_tracks = all_tracks_data[grade_mask]
                        
                        # If no matches, try looking in other columns
                        if filtered_tracks.empty:
                            print(f"DEBUG - No tracks found with {grade_column}='{selected_grade}', looking in other columns")
                            filtered_rows = []
                            
                            # Check all columns for the grade value
                            for _, row in all_tracks_data.iterrows():
                                found = False
                                for col in row.index:
                                    val = row[col]
                                    if pd.notna(val) and isinstance(val, str):
                                        # Direct match - case insensitive
                                        if selected_grade.upper() in val.upper():
                                            filtered_rows.append(row)
                                            found = True
                                            break
                                        # Split and check if comma-separated
                                        if "," in val:
                                            parts = val.split(",")
                                            # Check if the last part looks like the selected grade - case insensitive
                                            if len(parts) >= 7 and (selected_grade.upper() in parts[-1].upper() or 
                                                                 any(selected_grade.upper() in part.upper() for part in parts)):
                                                filtered_rows.append(row)
                                                found = True
                                                break
                                if found:
                                    break
                            
                            if filtered_rows:
                                filtered_tracks = pd.DataFrame(filtered_rows)
                            else:
                                # If still no matches, keep the original filter
                                filtered_tracks = all_tracks_data
                        
                        all_tracks_data = filtered_tracks
                    else:
                        # If GRADE column doesn't exist, search in string columns
                        filtered_rows = []
                        
                        # Check all columns for the grade value
                        for _, row in all_tracks_data.iterrows():
                            found = False
                            for col in row.index:
                                val = row[col]
                                if pd.notna(val) and isinstance(val, str):
                                    # Direct match - case insensitive
                                    if selected_grade.upper() in val.upper():
                                        filtered_rows.append(row)
                                        found = True
                                        break
                                    # Split and check if comma-separated
                                    if "," in val:
                                        parts = val.split(",")
                                        # Check if the last part looks like the selected grade - case insensitive
                                        if len(parts) >= 7 and (selected_grade.upper() in parts[-1].upper() or 
                                                             any(selected_grade.upper() in part.upper() for part in parts)):
                                            filtered_rows.append(row)
                                            found = True
                                            break
                            if found:
                                break
                        
                        if filtered_rows:
                            all_tracks_data = pd.DataFrame(filtered_rows)
                
                # Filter tracks by machine if not "All"
                if selected_machine != "All":
                    all_tracks_data = all_tracks_data[all_tracks_data[machine_column] == selected_machine]
                
                # Get all unique Track IDs for the filtered criteria
                track_ids = all_tracks_data['Track'].unique()
                
                # Create a dataframe with parameter values for these tracks
                track_values = []
                for track in track_ids:
                    try:
                        track_data = df[df['Track'] == track]
                        if selected_parameter in track_data.columns:
                            value = track_data[selected_parameter].iloc[0]
                            if pd.notna(value):
                                try:
                                    # Ensure value is converted to float
                                    float_value = float(value)
                                    # Ensure min/max are floats
                                    min_val = float(param_min)
                                    max_val = float(param_max)
                                    status = "Within Range" if min_val <= float_value <= max_val else "Outside Range"
                                    track_values.append({
                                        'Track': track,
                                        'Value': float_value,
                                        'Status': status
                                    })
                                except (ValueError, TypeError):
                                    # Skip values that can't be converted to float
                                    print(f"DEBUG - Skipping value '{value}' for Track {track} that can't be converted to float")
                                    continue
                    except Exception as e:
                        print(f"DEBUG - Error processing Track {track}: {str(e)}")
                        continue
                
                if track_values:
                    # Convert to dataframe for plotting
                    track_values_df = pd.DataFrame(track_values)
                    
                    # Check if selected track ID exists
                    selected_track_value = None
                    if track_id_input and track_id_input.isdigit():
                        try:
                            track_id = int(track_id_input)
                            track_row = track_values_df[track_values_df['Track'] == track_id]
                            if not track_row.empty:
                                selected_track_value = float(track_row['Value'].iloc[0])
                                st.markdown(f"#### Selected Track ID: {track_id}")
                                
                                # Calculate deviation from min/max/avg
                                if selected_track_value < param_min:
                                    deviation = selected_track_value - param_min
                                    status = "BELOW Range"
                                elif selected_track_value > param_max:
                                    deviation = selected_track_value - param_max
                                    status = "ABOVE Range"
                                else:
                                    deviation = 0
                                    status = "Within Range"
                                
                                # Display selected track's information
                                st.markdown(f"""
                                    <div style="
                                        padding: 1rem;
                                        border-radius: 10px;
                                        margin: 1rem 0;
                                        background: {"rgba(0, 200, 0, 0.1)" if status == "Within Range" else "rgba(255, 0, 0, 0.1)"};
                                        border-left: 4px solid {"#00c853" if status == "Within Range" else "#ff1744"};
                                    ">
                                        <div style="display: flex; justify-content: space-between;">
                                            <div>
                                                <h4 style="margin: 0;">Track ID: {track_id}</h4>
                                                <p>Parameter: <strong>{selected_parameter}</strong></p>
                                                <p>Value: <strong>{selected_track_value:.2f}</strong></p>
                                            </div>
                                            <div style="text-align: right;">
                                                <p>Min: <strong>{param_min:.2f}</strong></p>
                                                <p>Max: <strong>{param_max:.2f}</strong></p>
                                                <p>Status: <strong>{status}</strong></p>
                                                <p>Deviation: <strong>{deviation:+.2f}</strong></p>
                                            </div>
                                        </div>
                                    </div>
                                """, unsafe_allow_html=True)
                            else:
                                st.warning(f"Track ID {track_id_input} not found in the filtered data")
                        except Exception as e:
                            st.warning(f"Error processing Track ID: {str(e)}")
                    
                    # Create visualization using Altair
                    import altair as alt
                    
                    # Title for the chart
                    st.markdown(f"#### Distribution of {selected_parameter} Values")
                    st.markdown(f"Min: {param_min:.2f} | Max: {param_max:.2f} | Target: {param_avg:.2f}")
                    
                    try:
                        # Ensure all values in the dataframe are the correct types
                        track_values_df['Value'] = track_values_df['Value'].astype(float)
                        track_values_df['Track'] = track_values_df['Track'].astype(str)
                        
                        # Create a box plot using Altair
                        base = alt.Chart(track_values_df).encode(
                            x=alt.X('Value:Q', title=f'{selected_parameter} Value'),
                            color=alt.Color('Status:N', 
                                           scale=alt.Scale(
                                               domain=['Within Range', 'Outside Range'],
                                               range=['#00c853', '#ff1744']
                                           ))
                        )
                        
                        # Box plot
                        box_plot = base.mark_boxplot(size=50).encode(
                            y=alt.Y('Status:N', axis=None)
                        )
                        
                        # Points for all values
                        points = base.mark_circle(opacity=0.5).encode(
                            y=alt.Y('jitter:Q', title=None),
                            tooltip=['Track:N', 'Value:Q', 'Status:N']
                        ).transform_calculate(
                            # Generate jitter values for the y-axis
                            jitter='random() * 0.5'
                        )
                        
                        # Min and max reference lines
                        min_rule = alt.Chart(pd.DataFrame({'Value': [float(param_min)]})).mark_rule(
                            color='blue', strokeDash=[5, 5]
                        ).encode(x='Value:Q')
                        
                        max_rule = alt.Chart(pd.DataFrame({'Value': [float(param_max)]})).mark_rule(
                            color='blue', strokeDash=[5, 5]
                        ).encode(x='Value:Q')
                        
                        avg_rule = alt.Chart(pd.DataFrame({'Value': [float(param_avg)]})).mark_rule(
                            color='green'
                        ).encode(x='Value:Q')
                        
                        # Highlight selected track ID if provided
                        highlight = None
                        if selected_track_value is not None:
                            highlight = alt.Chart(pd.DataFrame({'Value': [float(selected_track_value)]})).mark_rule(
                                color='orange', size=3
                            ).encode(x='Value:Q')
                        
                        # Combine all elements
                        combined_chart = alt.layer(
                            box_plot, points, min_rule, max_rule, avg_rule,
                            *([] if highlight is None else [highlight])
                        ).properties(
                            width=700,
                            height=300
                        ).configure_axis(
                            labelFontSize=12,
                            titleFontSize=14
                        )
                        
                        # Display the chart
                        st.altair_chart(combined_chart, use_container_width=True)
                        
                        # Additional statistics
                        st.markdown("#### Distribution Statistics")
                        
                        stats_cols = st.columns(5)
                        with stats_cols[0]:
                            st.metric("Count", len(track_values_df))
                            
                        with stats_cols[1]:
                            st.metric("Average", f"{track_values_df['Value'].mean():.2f}")
                            
                        with stats_cols[2]:
                            st.metric("Median", f"{track_values_df['Value'].median():.2f}")
                            
                        with stats_cols[3]:
                            within_range = sum(track_values_df['Status'] == 'Within Range')
                            st.metric(
                                "Within Range", 
                                f"{within_range} ({within_range/len(track_values_df):.1%})"
                            )
                            
                        with stats_cols[4]:
                            outside_range = sum(track_values_df['Status'] == 'Outside Range')
                            st.metric(
                                "Outside Range", 
                                f"{outside_range} ({outside_range/len(track_values_df):.1%})"
                            )
                            
                        # Show data table (collapsible)
                        with st.expander("View Data Table"):
                            st.dataframe(
                                track_values_df.sort_values('Value'),
                                use_container_width=True,
                                hide_index=True,
                                column_config={
                                    "Track": st.column_config.NumberColumn("Track ID"),
                                    "Value": st.column_config.NumberColumn(f"{selected_parameter} Value", format="%.2f"),
                                    "Status": st.column_config.TextColumn("Status")
                                }
                            )
                    except Exception as e:
                        st.error(f"Error creating visualization: {str(e)}")
                        st.info("Please check that all selected parameter values can be properly converted to numbers.")
                        print(f"DEBUG - Visualization error details: {str(e)}")
                        
                        # Display the raw data for debugging
                        st.markdown("### Data Preview (Debug)")
                        st.write("This table shows the raw data being used for visualization:")
                        st.dataframe(
                            track_values_df,
                            use_container_width=True,
                            hide_index=False
                        )
                else:
                    st.warning(f"No data found for the selected parameter, grade, and machine combination")
            else:
                st.warning("No data available for the selected filters")
                
    except Exception as e:
        st.error(f"Error creating visualization: {str(e)}")
        st.info("Please check your data and try again.")

# Footer with additional information
st.markdown("---")
st.markdown("""
    <div style='text-align: center; padding: 1rem;'>
        <p style='opacity: 0.7;'>Quality Inspection Dashboard | Real-time monitoring and analysis</p>
    </div>
""", unsafe_allow_html=True) 