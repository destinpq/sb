import streamlit as st
import pandas as pd
import numpy as np
import altair as alt

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
    
    # First, get ranges from Process_Parameters column
    for index, row in df.iterrows():
        param = row['Process_Parameters']
        if param not in ranges:  # Only add if not already present
            ranges[param] = {
                'min': float(row['Min']),
                'max': float(row['Max']),
                'avg': float(row['Average'])
            }
    
    # Add specific ranges for parameters based on domain knowledge
    # CALIPER specific range (example - adjust these values based on actual requirements)
    if 'CALIPER' not in ranges:
        ranges['CALIPER'] = {
            'min': 250.0,  # Example minimum value for CALIPER
            'max': 300.0,  # Example maximum value for CALIPER
            'avg': 275.0   # Example average value for CALIPER
        }
    
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
    
    return ranges

def get_parameter_status(param_value, min_val, max_val):
    """Get parameter status with proper type checking and range validation"""
    try:
        param_value = float(param_value)
        min_val = float(min_val)
        max_val = float(max_val)
        
        # Ensure min_val is less than max_val
        if min_val > max_val:
            min_val, max_val = max_val, min_val
            
        if min_val <= param_value <= max_val:
            return "PASS", 0.0
        
        # Calculate deviation from the nearest boundary
        if param_value < min_val:
            deviation = param_value - min_val
            return "FAIL_LOW", deviation
        else:
            deviation = param_value - max_val
            return "FAIL_HIGH", deviation
            
    except (ValueError, TypeError) as e:
        print(f"Error in get_parameter_status: {e}")
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
    return pd.read_csv("Dummy_PM7_Data_1000_Rows.csv")

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
nav_tabs = st.tabs(["📊 Overall Analysis", "🔎 Track ID Search"])

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
                st.markdown("<div class='chart-container'>", unsafe_allow_html=True)
                st.markdown("#### Quality Status Distribution")
                
                # Create Altair bar chart with custom colors and consistent styling
                status_data = pd.DataFrame({
                    'Status': ['OK', 'NOT OK'],
                    'Count': [ok_count, not_ok_count]
                })
                
                bars = alt.Chart(status_data).mark_bar().encode(
                    x=alt.X('Status:N', axis=alt.Axis(labelAngle=0), title='Quality Status'),
                    y=alt.Y('Count:Q', title='Number of Track IDs'),
                    color=alt.Color('Status:N', scale=alt.Scale(
                        domain=['OK', 'NOT OK'],
                        range=['#00c853', '#ff1744']
                    )),
                    tooltip=['Status', 'Count']
                ).properties(
                    width=chart_width,
                    height=chart_height
                )
                
                # Apply configuration after rendering
                bars_configured = bars.configure_view(
                    strokeWidth=0
                ).configure_axis(
                    grid=False
                )
                
                st.altair_chart(bars_configured, use_container_width=False)
                st.markdown("</div>", unsafe_allow_html=True)
                
                # Pie chart with consistent styling
                st.markdown("<div class='chart-container'>", unsafe_allow_html=True)
                st.markdown("#### Quality Distribution (Pie Chart)")
                
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
            
            if len(not_ok_rows) > 0:
                # Debug: Show the columns in the dataset
                st.write("Debug - Dataset Columns:", df.columns.tolist())
                
                # Get unique Track IDs with NOT OK status
                not_ok_track_ids = not_ok_rows['Track'].unique()
                st.write(f"Debug - Found {len(not_ok_track_ids)} unique NOT OK Track IDs")
                
                # Get all numeric columns from the dataframe for analysis
                # Exclude non-parameter columns
                exclude_columns = ['M_C', 'Jumbo_ID', 'Track', 'KIT', 'Quality', 'Process_Parameters', 'Min', 'Max', 'Average']
                numeric_columns = df.select_dtypes(include=['number']).columns.tolist()
                parameter_columns = [col for col in numeric_columns if col not in exclude_columns]
                
                st.write(f"Debug - Found {len(parameter_columns)} potential parameter columns")
                
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
                            st.write(f"Debug - Error calculating range for {param}: {str(e)}")
                
                st.write(f"Debug - Calculated ranges for {len(param_ranges)} parameters")
                
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
                                st.write(f"Debug - Error checking {param} for Track ID {track_id}: {str(e)}")
                
                st.write(f"Debug - Found {len(param_failures)} parameters with failures")
                
                # Remove debug statements from final version
                # st.write("Debug - Parameter Failures:", param_failures)
                
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
                    
                    # Display full table with failure counts
                    st.markdown("#### Detailed Parameter Failure Analysis")
                    
                    # Format the percentage column for display
                    failure_data['Failure Percentage'] = failure_data['Failure Percentage'].apply(lambda x: f"{x}%")
                    
                    st.dataframe(
                        failure_data,
                        use_container_width=True,
                        hide_index=True,
                        column_config={
                            "Parameter": st.column_config.TextColumn("Process Parameter"),
                            "Failure Count": st.column_config.NumberColumn(
                                "Failure Count",
                                help="Number of NOT OK Track IDs where this parameter failed"
                            ),
                            "Failure Percentage": st.column_config.TextColumn(
                                "% of NOT OK Track IDs",
                                help="Percentage of NOT OK Track IDs where this parameter failed"
                            )
                        }
                    )
                    
                    # Replace the "Most Problematic Parameters" section with "All Parameters Analysis"
                    st.markdown("#### 🔍 All Parameters Analysis")
                    
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
                    
                    # Show parameter ranges for all failing parameters
                    st.markdown("#### Parameter Ranges for Failing Parameters")
                    
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
                    
                    if range_data:
                        range_df = pd.DataFrame(range_data)
                        
                        # Wrap in a container with fixed width to prevent flickering
                        st.markdown('<div class="parameter-range-table" style="width:100%;">', unsafe_allow_html=True)
                        st.dataframe(
                            range_df,
                            use_container_width=True,
                            hide_index=True,
                            height=min(35 * (len(range_data) + 1), 450),  # Fixed height based on number of rows
                            column_config={
                                'Parameter': st.column_config.TextColumn("Parameter Name"),
                                'Min Value': st.column_config.TextColumn("Min Value"),
                                'Max Value': st.column_config.TextColumn("Max Value"),
                                'Target Value': st.column_config.TextColumn("Target Value"),
                                'Failure Count': st.column_config.NumberColumn("Failure Count"),
                                'Failure %': st.column_config.TextColumn("Failure Percentage")
                            }
                        )
                        st.markdown('</div>', unsafe_allow_html=True)
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
            
            # Filter data with proper type handling
            try:
                if is_track_id:
                    track_id = int(search_value)
                    filtered_df = df[df['Track'].astype(str).str.strip() == str(track_id)]
                else:
                    filtered_df = df[df['Jumbo_ID'].astype(str).str.strip() == search_value.strip()]
                
                if not filtered_df.empty:
                    # Grade Status Banner - Fixed to handle exact string matching
                    quality_status = filtered_df['Quality'].iloc[0].strip()  # Remove any whitespace
                    is_ok = quality_status.upper() == "OK"  # Case-insensitive comparison
                    
                    # Debug logging
                    st.write("Debug - Quality Status:", quality_status)
                    st.write("Debug - Is OK:", is_ok)
                    
                    st.markdown(f"""
                        <div class='grade-status grade-{"ok" if is_ok else "not-ok"} grade-pulse'>
                            Grade Status: {quality_status}
                            {"✅" if is_ok else "❌"}
                        </div>
                    """, unsafe_allow_html=True)
    
                    # Key metrics with corrected grade status
                    st.markdown("### 📊 Key Metrics")
                    metric_cols = st.columns(4)
                    
                    with metric_cols[0]:
                        delta_color = "normal" if is_ok else "inverse"
                        status_delta = "PASS" if is_ok else "FAIL"
                        st.markdown('<div class="grade-metric">', unsafe_allow_html=True)
                        st.metric(
                            "Quality Grade",
                            quality_status,
                            delta=status_delta,
                            delta_color=delta_color,
                            help="Overall quality grade of the product"
                        )
                        st.markdown('</div>', unsafe_allow_html=True)
                        
                    with metric_cols[1]:
                        success_rate = 100.0 if is_ok else 0.0
                        st.metric(
                            "Success Rate",
                            f"{success_rate:.1f}%",
                            delta=f"{success_rate:.1f}%" if success_rate > 80 else f"{success_rate:.1f}%",
                            delta_color="normal" if success_rate > 80 else "inverse",
                            help="Percentage of successful quality checks"
                        )
                        
                    with metric_cols[2]:
                        st.metric(
                            "KIT Number",
                            filtered_df['KIT'].iloc[0],
                            help="Product identification number"
                        )
                        
                    with metric_cols[3]:
                        st.metric(
                            "Total Records",
                            len(filtered_df),
                            help="Number of records found"
                        )
    
                    # Add a separator
                    st.markdown("<hr style='margin: 2rem 0; opacity: 0.3;'>", unsafe_allow_html=True)
    
                    # Parameters display in tabs
                    st.markdown("### 📑 Detailed Parameters")
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
                        
                        # Get current process parameter
                        process_params = filtered_df[['Process_Parameters', 'Min', 'Max', 'Average']].iloc[0]
                        current_process = str(process_params['Process_Parameters'])
                        
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

# Footer with additional information
st.markdown("---")
st.markdown("""
    <div style='text-align: center; padding: 1rem;'>
        <p style='opacity: 0.7;'>Quality Inspection Dashboard | Real-time monitoring and analysis</p>
    </div>
""", unsafe_allow_html=True) 