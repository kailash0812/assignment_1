import streamlit as st
import mysql.connector
import pandas as pd

# Set page configuration
st.set_page_config(
    page_title="Red Bus",
    page_icon="C:/Users/arund/Downloads/redbus_logo.png"  
)

# Display images
st.image("C:/Users/arund/Downloads/redbus.png", use_column_width=True)
st.image("C:/Users/arund/Downloads/3.png", use_column_width=True)

# Heading
st.markdown("<h1 style='text-align: center;'>State Road Transport Corporation (SRTC) of India</h1>", unsafe_allow_html=True)

# Bus service names with full forms
bus_services = [
    'APSRTC - Andhra Pradesh State Road Transport Corporation',
    'ASTC - Assam State Transport Corporation',
    'HRTC - Himachal Road Transport Corporation',
    'KSRTC - Kerala State Road Transport Corporation',
    'KTCL - Kadamba Transport Corporation Limited',
    'NBSTC - North Bengal State Transport Corporation',
    'RSRTC - Rajasthan State Road Transport Corporation',
    'SBSTC - South Bengal State Transport Corporation',
    'TSRTC - Telangana State Road Transport Corporation',
    'UPSRTC - Uttar Pradesh State Road Transport Corporation'
]

# Extract short names for identification
service_identifiers = [service.split(' - ')[0] for service in bus_services]

# Connect to MySQL server
mydb = mysql.connector.connect(
    host="localhost",
    user="root",
    password="",
    database="redbus_data"
)
mycursor = mydb.cursor(buffered=True)

# Step 1: Select Bus Service
with st.form("bus_service_form"):
    selected_service = st.selectbox('Select Bus Service', bus_services)
    service_code = selected_service.split(' - ')[0]
    submitted_service = st.form_submit_button("Submit")

if submitted_service:
    st.session_state['selected_service'] = selected_service
    st.session_state['service_code'] = service_code

# Step 2: Select Route if Bus Service is selected
if 'selected_service' in st.session_state:
    selected_service = st.session_state['selected_service']
    service_code = st.session_state['service_code']
    
    mycursor.execute(f"SELECT route_name, route_link FROM {service_code}_routes")
    routes = mycursor.fetchall()
    routes_df = pd.DataFrame(routes, columns=["Route Name", "Route Link"])
    
    with st.form("route_form"):
        selected_route = st.selectbox("Select Route", routes_df["Route Name"].unique())
        route_link = routes_df[routes_df["Route Name"] == selected_route]["Route Link"].values[0]
        submitted_route = st.form_submit_button("Submit")
    
    if submitted_route:
        st.session_state['selected_route'] = selected_route
        st.session_state['route_link'] = route_link

# Display route details and filter buses if both service and route are selected
if 'selected_route' in st.session_state:
    selected_service = st.session_state['selected_service']
    service_code = st.session_state['service_code']
    selected_route = st.session_state['selected_route']
    route_link = st.session_state['route_link']
    
    st.write(f"Bus details for the route: {selected_route}")
    st.markdown(f"Route Details: [Click Here]({route_link})")  # Display the route link
    
    # Query to get all bus details for the selected route
    mycursor.execute(
        f"SELECT route_id, bus_name, bus_type, departing_time, duration, reaching_time, star_rating, price, seats_available FROM {service_code}_routes WHERE route_name = %s", 
        (selected_route,)
    )
    bus_details = mycursor.fetchall()
    bus_details_df = pd.DataFrame(bus_details, columns=[
        "Route ID", "Bus Name", "Bus Type", "Departing Time", "Duration", "Reaching Time", "Star Rating", "Price", "Seats Available"
    ])
    
    # Categorize buses based on bus_name
    bus_details_df['Category'] = bus_details_df['Bus Name'].apply(lambda x: 'Government Buses' if service_code in x else 'Private Buses')
    
    # Set route_id as the index and remove it from the displayed columns
    bus_details_df.set_index("Route ID", inplace=True)
    
    # Ensure that the time columns are displayed exactly as in the database
    bus_details_df["Departing Time"] = bus_details_df["Departing Time"].apply(lambda x: str(x).split(' ')[-1])
    bus_details_df["Reaching Time"] = bus_details_df["Reaching Time"].apply(lambda x: str(x).split(' ')[-1])
    
    # Sidebar filters
    st.sidebar.header("Filters")
    
    st.sidebar.markdown("#### DEPARTURE TIME")
    dt_before_6am = st.sidebar.checkbox("Before 6 am", key="dt_before_6am")
    dt_6am_to_12pm = st.sidebar.checkbox("6 am to 12 pm", key="dt_6am_to_12pm")
    dt_12pm_to_6pm = st.sidebar.checkbox("12 pm to 6 pm", key="dt_12pm_to_6pm")
    dt_after_6pm = st.sidebar.checkbox("After 6 pm", key="dt_after_6pm")
    
    st.sidebar.markdown("#### BUS TYPES")
    bus_type_seater = st.sidebar.checkbox("SEATER", key="bus_type_seater")
    bus_type_sleeper = st.sidebar.checkbox("SLEEPER", key="bus_type_sleeper")
    bus_type_ac = st.sidebar.checkbox("AC", key="bus_type_ac")
    bus_type_nonac = st.sidebar.checkbox("NON AC", key="bus_type_nonac")
    
    st.sidebar.markdown("#### ARRIVAL TIME")
    at_before_6am = st.sidebar.checkbox("Before 6 am", key="at_before_6am")
    at_6am_to_12pm = st.sidebar.checkbox("6 am to 12 pm", key="at_6am_to_12pm")
    at_12pm_to_6pm = st.sidebar.checkbox("12 pm to 6 pm", key="at_12pm_to_6pm")
    at_after_6pm = st.sidebar.checkbox("After 6 pm", key="at_after_6pm")
    
    st.sidebar.markdown("#### STAR RATING")
    rating_3_plus = st.sidebar.checkbox("3+ Stars", key="rating_3_plus")
    rating_4_plus = st.sidebar.checkbox("4+ Stars", key="rating_4_plus")
    rating_5 = st.sidebar.checkbox("5 Stars", key="rating_5")
    
    st.sidebar.markdown("#### PRICE RANGE")
    min_price = 300  # Adjusted minimum price
    max_price = 5000  # Adjusted maximum price
    price_range = st.sidebar.slider("Select Price Range", min_price, max_price, (min_price, max_price))
    
    st.sidebar.markdown("#### SEATS AVAILABLE")
    seats_available = st.sidebar.slider("Minimum Seats Available", 0, int(bus_details_df['Seats Available'].max()), 0)
    
    # Apply filters
    filtered_df = bus_details_df.copy()
    
    # Filter by departure time
    if dt_before_6am:
        filtered_df = filtered_df[pd.to_datetime(filtered_df["Departing Time"]).dt.time < pd.to_datetime("06:00").time()]
    if dt_6am_to_12pm:
        filtered_df = filtered_df[(pd.to_datetime(filtered_df["Departing Time"]).dt.time >= pd.to_datetime("06:00").time()) & 
                                  (pd.to_datetime(filtered_df["Departing Time"]).dt.time < pd.to_datetime("12:00").time())]
    if dt_12pm_to_6pm:
        filtered_df = filtered_df[(pd.to_datetime(filtered_df["Departing Time"]).dt.time >= pd.to_datetime("12:00").time()) & 
                                  (pd.to_datetime(filtered_df["Departing Time"]).dt.time < pd.to_datetime("18:00").time())]
    if dt_after_6pm:
        filtered_df = filtered_df[pd.to_datetime(filtered_df["Departing Time"]).dt.time >= pd.to_datetime("18:00").time()]
    
    # Filter by bus type
    if bus_type_seater:
        filtered_df = filtered_df[filtered_df["Bus Type"].str.contains(r'\bSEATER\b', case=False, regex=True)]
    if bus_type_sleeper:
        filtered_df = filtered_df[filtered_df["Bus Type"].str.contains(r'\bSLEEPER\b', case=False, regex=True)]
    if bus_type_ac:
        filtered_df = filtered_df[filtered_df["Bus Type"].str.contains(r'\bA[./]?C\b', case=False, regex=True) & 
                                  ~filtered_df["Bus Type"].str.contains(r'\bNON\b', case=False, regex=True)]
    if bus_type_nonac:
        filtered_df = filtered_df[filtered_df["Bus Type"].str.contains(r'\bNON AC\b', case=False, regex=True)]
    
    # Filter by arrival time
    if at_before_6am:
        filtered_df = filtered_df[pd.to_datetime(filtered_df["Reaching Time"]).dt.time < pd.to_datetime("06:00").time()]
    if at_6am_to_12pm:
        filtered_df = filtered_df[(pd.to_datetime(filtered_df["Reaching Time"]).dt.time >= pd.to_datetime("06:00").time()) & 
                                  (pd.to_datetime(filtered_df["Reaching Time"]).dt.time < pd.to_datetime("12:00").time())]
    if at_12pm_to_6pm:
        filtered_df = filtered_df[(pd.to_datetime(filtered_df["Reaching Time"]).dt.time >= pd.to_datetime("12:00").time()) & 
                                  (pd.to_datetime(filtered_df["Reaching Time"]).dt.time < pd.to_datetime("18:00").time())]
    if at_after_6pm:
        filtered_df = filtered_df[pd.to_datetime(filtered_df["Reaching Time"]).dt.time >= pd.to_datetime("18:00").time()]
    
    # Filter by star rating
    if rating_3_plus:
        filtered_df = filtered_df[filtered_df["Star Rating"] >= 3]
    if rating_4_plus:
        filtered_df = filtered_df[filtered_df["Star Rating"] >= 4]
    if rating_5:
        filtered_df = filtered_df[filtered_df["Star Rating"] == 5]
    
    # Filter by price range
    filtered_df = filtered_df[(filtered_df["Price"] >= price_range[0]) & (filtered_df["Price"] <= price_range[1])]
    
    # Filter by seats available
    filtered_df = filtered_df[filtered_df["Seats Available"] >= seats_available]
    
    # Display government buses
    st.markdown("### Government Buses")
    st.dataframe(filtered_df[filtered_df['Category'] == 'Government Buses'])
    
    # Display private buses
    st.markdown("### Private Buses")
    st.dataframe(filtered_df[filtered_df['Category'] == 'Private Buses'])
