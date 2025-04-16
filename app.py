import streamlit as st
import pandas as pd
import numpy as np

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
    </style>
""", unsafe_allow_html=True)

# Title with icon and subtitle
st.markdown("""
    <div style='text-align: center; padding: 2rem 0;'>
        <h1 style='font-size: 2.5rem; margin-bottom: 0.5rem;'>🔍 Quality Inspection Dashboard</h1>
        <p style='font-size: 1.1rem; opacity: 0.8;'>Monitor and analyze quality parameters in real-time</p>
    </div>
""", unsafe_allow_html=True)

# Define parameter groups with icons
parameter_groups = {
    '📋 Basic Information': ['M_C', 'Jumbo_ID', 'Track', 'KIT', 'Quality', 'SUBSTANCE'],
    '📏 Physical Properties': ['CALIPER', 'BULK', 'GSM_2SIGMA_ABB', 'CALIPER_CD_2SIGMA_ABB'],
    '🔍 Surface Properties': [
        'COBB_TS', 'COBB_WS', 'COBB_FL_3MIN', 'COBB_WS_3MIN',
        'GLOSS_AT_75_TS', 'ROUGHNESS_PPS_TS'
    ],
    '👁️ Optical Properties': [
        'BRIGHTNESS_ISO_TS', 'BRIGHTNESS_ISO_BS',
        'WHITENESS_TS',
        'L_VALUE_TS', 'a_VALUE_TS', 'b_VALUE_TS',
        'L_VALUE_BS', 'a_VALUE_BS', 'b_VALUE_BS',
        'DELTA_E_TS'
    ],
    '⚡ Mechanical Properties': [
        'STIFFNESS_L_W_MD', 'STIFFNESS_L_W_CD', 'STIFFNESS_L_W_GM',
        'STIFFNESS_RATIO', 'PLYBOND'
    ],
    '🧪 Chemical Properties': [
        'MOISTURE', 'MOISTURE_2SIGMA_ABB',
        'ASH_TOP_LAYER', 'ASH_BOTTOM_LAYER'
    ],
    '📊 Performance Indicators': [
        'IGT_PICK_TOP_MED_VIS', 'IGT_PICK_BOT_MED_VIS',
        'TL_GSM', 'BL_GSM', 'GSM_2SIGMA_CD_ABB'
    ]
}

# Load data with loading indicator
@st.cache_data(show_spinner=True)
def load_data():
    return pd.read_csv("Dummy_PM7_Data_1000_Rows.csv")

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
                st.markdown("### 🎯 Process Parameters Analysis")
                
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
                    
                    # Display process parameter card with special styling
                    display_parameter_card(
                        f"Process Parameter: {param_name}",
                        current_value,
                        param_min,
                        param_max,
                        process_param=True
                    )
                    
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
                    
                    # Display parameter analysis sections
                    st.markdown("### 📑 Parameter Analysis")
                    
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

# Footer with additional information
st.markdown("---")
st.markdown("""
    <div style='text-align: center; padding: 1rem;'>
        <p style='opacity: 0.7;'>Quality Inspection Dashboard | Real-time monitoring and analysis</p>
    </div>
""", unsafe_allow_html=True) 