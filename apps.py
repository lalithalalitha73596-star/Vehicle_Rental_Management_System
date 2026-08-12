import streamlit as st
import oracledb
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import date


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="Vehicle Rental Management",
    page_icon="🚗",
    layout="wide",
    initial_sidebar_state="expanded"
)


# ============================================================
# ORACLE DATABASE CONFIGURATION
# ============================================================

ORACLE_USER = "Vehicle_App"
ORACLE_PASSWORD = "Oracle@789"

# Change this if your Oracle service name is different
ORACLE_DSN = "localhost:1521/XEPDB1"


# ============================================================
# CUSTOM CSS
# ============================================================

st.markdown(
    """
    <style>

    /* Main background */
    .stApp {
        background-color: #f5f7fb;
    }

    /* Remove excessive top spacing */
    .block-container {
        padding-top: 1.5rem;
        padding-bottom: 2rem;
        max-width: 1500px;
    }

    /* Sidebar */
    section[data-testid="stSidebar"] {
        background-color: #111827;
    }

    section[data-testid="stSidebar"] * {
        color: white;
    }

    /* Header */
    .dashboard-title {
        font-size: 34px;
        font-weight: 750;
        color: #111827;
        margin-bottom: 0px;
    }

    .dashboard-subtitle {
        color: #6b7280;
        font-size: 15px;
        margin-bottom: 25px;
    }

    /* KPI cards */
    div[data-testid="stMetric"] {
        background-color: white;
        border: 1px solid #e5e7eb;
        border-radius: 14px;
        padding: 18px 20px;
        box-shadow: 0px 2px 8px rgba(0, 0, 0, 0.04);
        min-height: 120px;
    }

    div[data-testid="stMetricLabel"] {
        color: #6b7280;
        font-size: 14px;
    }

    div[data-testid="stMetricValue"] {
        color: #111827;
        font-size: 27px;
        font-weight: 700;
    }

    /* Section titles */
    .section-title {
        font-size: 20px;
        font-weight: 700;
        color: #111827;
        margin-top: 18px;
        margin-bottom: 12px;
    }

    /* Info boxes */
    .info-card {
        background: white;
        border: 1px solid #e5e7eb;
        border-radius: 14px;
        padding: 18px;
        margin-bottom: 15px;
    }

    /* Status */
    .status-success {
        color: #16a34a;
        font-weight: 600;
    }

    /* Tables */
    div[data-testid="stDataFrame"] {
        border-radius: 10px;
    }

    /* Buttons */
    .stButton > button {
        border-radius: 8px;
        font-weight: 600;
    }

    </style>
    """,
    unsafe_allow_html=True
)


# ============================================================
# ORACLE CONNECTION
# ============================================================

@st.cache_resource
def get_connection():
    return oracledb.connect(
        user="Vehicle_App",
        password="Oracle@789",
        dsn="localhost:1521/XEPDB1"
    )


# ============================================================
# DATABASE TEST
# ============================================================

def test_database():

    try:
        conn = get_connection()

        cursor = conn.cursor()
        cursor.execute("SELECT SYSDATE FROM DUAL")

        result = cursor.fetchone()

        cursor.close()

        return True, result[0]

    except Exception as e:

        return False, str(e)


# ============================================================
# GENERIC QUERY FUNCTION
# ============================================================

@st.cache_data(ttl=60)
def run_query(query):

    conn = get_connection()

    df = pd.read_sql(query, conn)

    return df


# ============================================================
# KPI DATA
# ============================================================

@st.cache_data(ttl=60)
def get_kpis():

    queries = {

        "customers": """
            SELECT COUNT(*) AS VALUE
            FROM CUSTOMERS
        """,

        "vehicles": """
            SELECT COUNT(*) AS VALUE
            FROM VEHICLES
        """,

        "available_vehicles": """
            SELECT COUNT(*) AS VALUE
            FROM VEHICLES
            WHERE UPPER(VEHICLE_STATUS) = 'AVAILABLE'
        """,

        "rentals": """
            SELECT COUNT(*) AS VALUE
            FROM RENTALS
        """,

        "active_rentals": """
            SELECT COUNT(*) AS VALUE
            FROM RENTALS
            WHERE UPPER(RENTAL_STATUS) = 'ACTIVE'
        """,

        "revenue": """
            SELECT NVL(SUM(PAYMENT_AMOUNT), 0) AS VALUE
            FROM PAYMENTS
            WHERE UPPER(PAYMENT_STATUS)
            IN ('PAID', 'COMPLETED', 'SUCCESS')
        """,

        "pending_payments": """
            SELECT NVL(SUM(PAYMENT_AMOUNT), 0) AS VALUE
            FROM PAYMENTS
            WHERE UPPER(PAYMENT_STATUS)
            IN ('PENDING', 'DUE')
        """,

        "rejected": """
            SELECT COUNT(*) AS VALUE
            FROM RENTAL_REJECTS
        """
    }

    result = {}

    for name, query in queries.items():

        df = run_query(query)

        result[name] = df.iloc[0]["VALUE"]

    return result


# ============================================================
# REVENUE TREND
# ============================================================

@st.cache_data(ttl=60)
def get_revenue_trend():

    query = """
        SELECT
            TRUNC(PAYMENT_DATE, 'MM') AS MONTH,
            NVL(SUM(PAYMENT_AMOUNT), 0) AS REVENUE
        FROM PAYMENTS
        WHERE UPPER(PAYMENT_STATUS)
        IN ('PAID', 'COMPLETED', 'SUCCESS')
        GROUP BY TRUNC(PAYMENT_DATE, 'MM')
        ORDER BY MONTH
    """

    df = run_query(query)

    if not df.empty:
        df["MONTH"] = pd.to_datetime(df["MONTH"])

    return df


# ============================================================
# RENTAL TREND
# ============================================================

@st.cache_data(ttl=60)
def get_rental_trend():

    query = """
        SELECT
            TRUNC(BOOKING_DATE, 'MM') AS MONTH,
            COUNT(*) AS RENTALS
        FROM RENTALS
        GROUP BY TRUNC(BOOKING_DATE, 'MM')
        ORDER BY MONTH
    """

    df = run_query(query)

    if not df.empty:
        df["MONTH"] = pd.to_datetime(df["MONTH"])

    return df


# ============================================================
# VEHICLE STATUS
# ============================================================

@st.cache_data(ttl=60)
def get_vehicle_status():

    query = """
        SELECT
            VEHICLE_STATUS,
            COUNT(*) AS VEHICLE_COUNT
        FROM VEHICLES
        GROUP BY VEHICLE_STATUS
        ORDER BY VEHICLE_COUNT DESC
    """

    return run_query(query)


# ============================================================
# RENTAL STATUS
# ============================================================

@st.cache_data(ttl=60)
def get_rental_status():

    query = """
        SELECT
            RENTAL_STATUS,
            COUNT(*) AS RENTAL_COUNT
        FROM RENTALS
        GROUP BY RENTAL_STATUS
        ORDER BY RENTAL_COUNT DESC
    """

    return run_query(query)


# ============================================================
# VEHICLE TYPE
# ============================================================

@st.cache_data(ttl=60)
def get_vehicle_types():

    query = """
        SELECT
            VEHICLE_TYPE,
            COUNT(*) AS VEHICLE_COUNT
        FROM VEHICLES
        GROUP BY VEHICLE_TYPE
        ORDER BY VEHICLE_COUNT DESC
    """

    return run_query(query)


# ============================================================
# TOP VEHICLES
# ============================================================

@st.cache_data(ttl=60)
def get_top_vehicles():

    query = """
        SELECT
            V.VEHICLE_BRAND,
            V.VEHICLE_MODEL,
            COUNT(R.RENTAL_ID) AS TOTAL_RENTALS,
            NVL(SUM(R.RENTAL_CHARGE), 0) AS TOTAL_REVENUE
        FROM VEHICLES V
        LEFT JOIN RENTALS R
            ON V.VEHICLE_ID = R.VEHICLE_ID
        GROUP BY
            V.VEHICLE_BRAND,
            V.VEHICLE_MODEL
        ORDER BY TOTAL_REVENUE DESC
        FETCH FIRST 10 ROWS ONLY
    """

    return run_query(query)


# ============================================================
# BRANCH PERFORMANCE
# ============================================================

@st.cache_data(ttl=60)
def get_branch_performance():

    query = """
        SELECT
            V.BRANCH_NAME,
            COUNT(R.RENTAL_ID) AS TOTAL_RENTALS,
            NVL(SUM(R.RENTAL_CHARGE), 0) AS TOTAL_REVENUE
        FROM VEHICLES V
        LEFT JOIN RENTALS R
            ON V.VEHICLE_ID = R.VEHICLE_ID
        GROUP BY V.BRANCH_NAME
        ORDER BY TOTAL_REVENUE DESC
    """

    return run_query(query)


# ============================================================
# PAYMENT METHODS
# ============================================================

@st.cache_data(ttl=60)
def get_payment_methods():

    query = """
        SELECT
            PAYMENT_METHOD,
            COUNT(*) AS TRANSACTIONS,
            NVL(SUM(PAYMENT_AMOUNT), 0) AS TOTAL_AMOUNT
        FROM PAYMENTS
        GROUP BY PAYMENT_METHOD
        ORDER BY TOTAL_AMOUNT DESC
    """

    return run_query(query)


# ============================================================
# RECENT RENTALS
# ============================================================

@st.cache_data(ttl=60)
def get_recent_rentals():

    query = """
        SELECT
            R.RENTAL_ID,
            C.CUSTOMER_NAME,
            V.VEHICLE_BRAND,
            V.VEHICLE_MODEL,
            V.REGISTRATION_NO,
            R.RENTAL_START_DATE,
            R.RENTAL_END_DATE,
            R.BOOKING_DATE,
            R.RENTAL_DAYS,
            R.RENTAL_CHARGE,
            R.RENTAL_STATUS,
            R.VEHICLE_AVAILABLE
        FROM RENTALS R

        LEFT JOIN CUSTOMERS C
            ON R.CUSTOMER_ID = C.CUSTOMER_ID

        LEFT JOIN VEHICLES V
            ON R.VEHICLE_ID = V.VEHICLE_ID

        ORDER BY R.BOOKING_DATE DESC

        FETCH FIRST 15 ROWS ONLY
    """

    return run_query(query)


# ============================================================
# ALL RENTALS
# ============================================================

@st.cache_data(ttl=60)
def get_all_rentals():

    query = """
        SELECT
            R.RENTAL_ID,
            C.CUSTOMER_NAME,
            V.VEHICLE_BRAND,
            V.VEHICLE_MODEL,
            V.REGISTRATION_NO,
            R.RENTAL_START_DATE,
            R.RENTAL_END_DATE,
            R.BOOKING_DATE,
            R.RENTAL_DAYS,
            R.RENTAL_CHARGE,
            R.RENTAL_STATUS,
            R.VEHICLE_AVAILABLE
        FROM RENTALS R

        LEFT JOIN CUSTOMERS C
            ON R.CUSTOMER_ID = C.CUSTOMER_ID

        LEFT JOIN VEHICLES V
            ON R.VEHICLE_ID = V.VEHICLE_ID

        ORDER BY R.BOOKING_DATE DESC
    """

    return run_query(query)


# ============================================================
# ALL VEHICLES
# ============================================================

@st.cache_data(ttl=60)
def get_all_vehicles():

    query = """
        SELECT
            VEHICLE_ID,
            REGISTRATION_NO,
            VEHICLE_TYPE,
            VEHICLE_BRAND,
            VEHICLE_MODEL,
            BRANCH_NAME,
            DAILY_RENTAL_RATE,
            VEHICLE_STATUS
        FROM VEHICLES
        ORDER BY VEHICLE_ID
    """

    return run_query(query)


# ============================================================
# ALL CUSTOMERS
# ============================================================

@st.cache_data(ttl=60)
def get_all_customers():

    query = """
        SELECT
            CUSTOMER_ID,
            CUSTOMER_NAME,
            CUSTOMER_PHONE,
            CUSTOMER_EMAIL,
            DRIVING_LICENSE_NO
        FROM CUSTOMERS
        ORDER BY CUSTOMER_NAME
    """

    return run_query(query)


# ============================================================
# ALL PAYMENTS
# ============================================================

@st.cache_data(ttl=60)
def get_all_payments():

    query = """
        SELECT
            PAYMENT_ID,
            RENTAL_ID,
            PAYMENT_DATE,
            PAYMENT_METHOD,
            PAYMENT_AMOUNT,
            PAYMENT_STATUS
        FROM PAYMENTS
        ORDER BY PAYMENT_DATE DESC
    """

    return run_query(query)


# ============================================================
# REJECTED RENTALS
# ============================================================

@st.cache_data(ttl=60)
def get_rejected_rentals():

    query = """
        SELECT
            RENTAL_ID,
            RENTAL_CUSTOMER_ID,
            RENTAL_VEHICLE_ID,
            RENTAL_START_DATE,
            RENTAL_END_DATE,
            RENTAL_BOOKING_DATE,
            RENTAL_STATUS,
            REJECT_REASON,
            REJECT_DATE
        FROM RENTAL_REJECTS
        ORDER BY REJECT_DATE DESC
    """

    return run_query(query)


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.markdown("## 🚗 VEHICLE RENTAL")

    st.caption("Management System")

    st.markdown("---")

    page = st.radio(
        "MAIN MENU",
        [
            "🏠 Dashboard",
            "📋 Rentals",
            "🚗 Vehicles",
            "👥 Customers",
            "💳 Payments",
            "⚠️ Exceptions"
        ]
    )

    st.markdown("---")

    st.markdown("### Database")

    connected, db_info = test_database()

    if connected:

        st.success("Oracle Connected")

        st.caption(
            f"Database time: {db_info}"
        )

    else:

        st.error("Oracle Connection Failed")

    st.markdown("---")

    if st.button(
        "🔄 Refresh Dashboard",
        use_container_width=True
    ):

        st.cache_data.clear()

        st.rerun()


# ============================================================
# HEADER
# ============================================================

st.markdown(
    '<div class="dashboard-title">'
    '🚗 Vehicle Rental Management'
    '</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="dashboard-subtitle">'
    'Operational, Fleet & Financial Overview'
    '</div>',
    unsafe_allow_html=True
)


# ============================================================
# DASHBOARD PAGE
# ============================================================

if page == "🏠 Dashboard":

    try:

        kpi = get_kpis()

        # ====================================================
        # KPI ROW 1
        # ====================================================

        col1, col2, col3, col4 = st.columns(4)

        col1.metric(
            "👥 Total Customers",
            f"{int(kpi['customers']):,}"
        )

        col2.metric(
            "🚗 Total Vehicles",
            f"{int(kpi['vehicles']):,}"
        )

        col3.metric(
            "🟢 Available Vehicles",
            f"{int(kpi['available_vehicles']):,}"
        )

        col4.metric(
            "📋 Total Rentals",
            f"{int(kpi['rentals']):,}"
        )

        st.write("")

        # ====================================================
        # KPI ROW 2
        # ====================================================

        col1, col2, col3, col4 = st.columns(4)

        col1.metric(
            "🔵 Active Rentals",
            f"{int(kpi['active_rentals']):,}"
        )

        col2.metric(
            "💰 Total Revenue",
            f"₹{float(kpi['revenue']):,.2f}"
        )

        col3.metric(
            "⏳ Pending Payments",
            f"₹{float(kpi['pending_payments']):,.2f}"
        )

        col4.metric(
            "⚠️ Rejected Rentals",
            f"{int(kpi['rejected']):,}"
        )

        st.markdown("")

        # ====================================================
        # REVENUE TREND
        # ====================================================

        left, right = st.columns([2, 1])

        with left:

            st.markdown(
                '<div class="section-title">'
                '📈 Revenue Trend'
                '</div>',
                unsafe_allow_html=True
            )

            revenue_df = get_revenue_trend()

            if not revenue_df.empty:

                fig = px.line(
                    revenue_df,
                    x="MONTH",
                    y="REVENUE",
                    markers=True,
                    labels={
                        "MONTH": "Month",
                        "REVENUE": "Revenue"
                    }
                )

                fig.update_layout(
                    height=380,
                    margin=dict(
                        l=10,
                        r=10,
                        t=20,
                        b=10
                    ),
                    hovermode="x unified",
                    yaxis_tickprefix="₹"
                )

                st.plotly_chart(
                    fig,
                    use_container_width=True
                )

            else:

                st.info(
                    "No revenue data available."
                )

        # ====================================================
        # FLEET STATUS
        # ====================================================

        with right:

            st.markdown(
                '<div class="section-title">'
                '🚗 Fleet Status'
                '</div>',
                unsafe_allow_html=True
            )

            vehicle_df = get_vehicle_status()

            if not vehicle_df.empty:

                fig = px.pie(
                    vehicle_df,
                    names="VEHICLE_STATUS",
                    values="VEHICLE_COUNT",
                    hole=0.58
                )

                fig.update_layout(
                    height=380,
                    margin=dict(
                        l=10,
                        r=10,
                        t=20,
                        b=10
                    )
                )

                st.plotly_chart(
                    fig,
                    use_container_width=True
                )

            else:

                st.info(
                    "No vehicle status data."
                )

        # ====================================================
        # RENTAL TREND
        # ====================================================

        left, right = st.columns([2, 1])

        with left:

            st.markdown(
                '<div class="section-title">'
                '📊 Rental Trend'
                '</div>',
                unsafe_allow_html=True
            )

            rental_df = get_rental_trend()

            if not rental_df.empty:

                fig = px.bar(
                    rental_df,
                    x="MONTH",
                    y="RENTALS",
                    labels={
                        "MONTH": "Month",
                        "RENTALS": "Number of Rentals"
                    }
                )

                fig.update_layout(
                    height=380,
                    margin=dict(
                        l=10,
                        r=10,
                        t=20,
                        b=10
                    )
                )

                st.plotly_chart(
                    fig,
                    use_container_width=True
                )

            else:

                st.info(
                    "No rental data available."
                )

        # ====================================================
        # RENTAL STATUS
        # ====================================================

        with right:

            st.markdown(
                '<div class="section-title">'
                '📋 Rental Status'
                '</div>',
                unsafe_allow_html=True
            )

            rental_status_df = get_rental_status()

            if not rental_status_df.empty:

                fig = px.pie(
                    rental_status_df,
                    names="RENTAL_STATUS",
                    values="RENTAL_COUNT",
                    hole=0.58
                )

                fig.update_layout(
                    height=380,
                    margin=dict(
                        l=10,
                        r=10,
                        t=20,
                        b=10
                    )
                )

                st.plotly_chart(
                    fig,
                    use_container_width=True
                )

            else:

                st.info(
                    "No rental status data."
                )

        # ====================================================
        # TOP VEHICLES
        # ====================================================

        st.markdown(
            '<div class="section-title">'
            '🏆 Top Performing Vehicles'
            '</div>',
            unsafe_allow_html=True
        )

        top_df = get_top_vehicles()

        if not top_df.empty:

            top_df["VEHICLE"] = (
                top_df["VEHICLE_BRAND"].fillna("")
                + " "
                + top_df["VEHICLE_MODEL"].fillna("")
            )

            chart_df = top_df[
                [
                    "VEHICLE",
                    "TOTAL_REVENUE"
                ]
            ].copy()

            fig = px.bar(
                chart_df,
                x="TOTAL_REVENUE",
                y="VEHICLE",
                orientation="h",
                labels={
                    "TOTAL_REVENUE": "Revenue",
                    "VEHICLE": "Vehicle"
                }
            )

            fig.update_layout(
                height=420,
                margin=dict(
                    l=10,
                    r=10,
                    t=20,
                    b=10
                ),
                xaxis_tickprefix="₹"
            )

            st.plotly_chart(
                fig,
                use_container_width=True
            )

        # ====================================================
        # BRANCH PERFORMANCE
        # ====================================================

        left, right = st.columns(2)

        with left:

            st.markdown(
                '<div class="section-title">'
                '🏢 Branch Performance'
                '</div>',
                unsafe_allow_html=True
            )

            branch_df = get_branch_performance()

            if not branch_df.empty:

                fig = px.bar(
                    branch_df,
                    x="BRANCH_NAME",
                    y="TOTAL_REVENUE",
                    labels={
                        "BRANCH_NAME": "Branch",
                        "TOTAL_REVENUE": "Revenue"
                    }
                )

                fig.update_layout(
                    height=350,
                    margin=dict(
                        l=10,
                        r=10,
                        t=20,
                        b=10
                    ),
                    yaxis_tickprefix="₹"
                )

                st.plotly_chart(
                    fig,
                    use_container_width=True
                )

        # ====================================================
        # PAYMENT METHODS
        # ====================================================

        with right:

            st.markdown(
                '<div class="section-title">'
                '💳 Payment Methods'
                '</div>',
                unsafe_allow_html=True
            )

            payment_method_df = get_payment_methods()

            if not payment_method_df.empty:

                fig = px.pie(
                    payment_method_df,
                    names="PAYMENT_METHOD",
                    values="TOTAL_AMOUNT",
                    hole=0.55
                )

                fig.update_layout(
                    height=350,
                    margin=dict(
                        l=10,
                        r=10,
                        t=20,
                        b=10
                    )
                )

                st.plotly_chart(
                    fig,
                    use_container_width=True
                )

        # ====================================================
        # RECENT RENTALS
        # ====================================================

        st.markdown(
            '<div class="section-title">'
            '📋 Recent Rentals'
            '</div>',
            unsafe_allow_html=True
        )

        recent_df = get_recent_rentals()

        if not recent_df.empty:

            recent_df["VEHICLE"] = (
                recent_df["VEHICLE_BRAND"].fillna("")
                + " "
                + recent_df["VEHICLE_MODEL"].fillna("")
            )

            display_df = recent_df[
                [
                    "RENTAL_ID",
                    "CUSTOMER_NAME",
                    "VEHICLE",
                    "REGISTRATION_NO",
                    "RENTAL_START_DATE",
                    "RENTAL_END_DATE",
                    "RENTAL_DAYS",
                    "RENTAL_CHARGE",
                    "RENTAL_STATUS"
                ]
            ].copy()

            display_df.columns = [
                "Rental ID",
                "Customer",
                "Vehicle",
                "Registration",
                "Start Date",
                "End Date",
                "Days",
                "Charge",
                "Status"
            ]

            display_df["Charge"] = display_df[
                "Charge"
            ].apply(
                lambda x: f"₹{float(x):,.2f}"
            )

            st.dataframe(
                display_df,
                use_container_width=True,
                hide_index=True
            )

        else:

            st.info("No rental records found.")

    except Exception as e:

        st.error(
            "Unable to load dashboard."
        )

        st.exception(e)


# ============================================================
# RENTALS PAGE
# ============================================================

elif page == "📋 Rentals":

    st.subheader("📋 Rental Management")

    try:

        df = get_all_rentals()

        # Search
        search = st.text_input(
            "🔍 Search rentals",
            placeholder="Search by rental ID, customer, vehicle..."
        )

        if search:

            mask = df.astype(str).apply(
                lambda row: row.str.contains(
                    search,
                    case=False,
                    na=False
                ).any(),
                axis=1
            )

            df = df[mask]

        # Status filter
        statuses = sorted(
            df["RENTAL_STATUS"]
            .dropna()
            .unique()
            .tolist()
        )

        if statuses:

            selected_status = st.multiselect(
                "Filter by Rental Status",
                statuses,
                default=statuses
            )

            df = df[
                df["RENTAL_STATUS"].isin(
                    selected_status
                )
            ]

        st.metric(
            "Displayed Rentals",
            len(df)
        )

        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True
        )

        csv = df.to_csv(index=False).encode("utf-8")

        st.download_button(
            "📥 Download Rentals CSV",
            csv,
            "rentals.csv",
            "text/csv"
        )

    except Exception as e:

        st.error(e)


# ============================================================
# VEHICLES PAGE
# ============================================================

elif page == "🚗 Vehicles":

    st.subheader("🚗 Fleet Management")

    try:

        df = get_all_vehicles()

        col1, col2 = st.columns(2)

        with col1:

            statuses = sorted(
                df["VEHICLE_STATUS"]
                .dropna()
                .unique()
                .tolist()
            )

            selected = st.multiselect(
                "Vehicle Status",
                statuses,
                default=statuses
            )

        with col2:

            types = sorted(
                df["VEHICLE_TYPE"]
                .dropna()
                .unique()
                .tolist()
            )

            selected_types = st.multiselect(
                "Vehicle Type",
                types,
                default=types
            )

        filtered = df[
            df["VEHICLE_STATUS"].isin(selected)
            &
            df["VEHICLE_TYPE"].isin(selected_types)
        ]

        st.metric(
            "Vehicles Displayed",
            len(filtered)
        )

        st.dataframe(
            filtered,
            use_container_width=True,
            hide_index=True
        )

        csv = filtered.to_csv(
            index=False
        ).encode("utf-8")

        st.download_button(
            "📥 Download Vehicle CSV",
            csv,
            "vehicles.csv",
            "text/csv"
        )

    except Exception as e:

        st.error(e)


# ============================================================
# CUSTOMERS PAGE
# ============================================================

elif page == "👥 Customers":

    st.subheader("👥 Customer Management")

    try:

        df = get_all_customers()

        search = st.text_input(
            "🔍 Search customer",
            placeholder="Name, ID, phone or email..."
        )

        if search:

            mask = df.astype(str).apply(
                lambda row: row.str.contains(
                    search,
                    case=False,
                    na=False
                ).any(),
                axis=1
            )

            df = df[mask]

        st.metric(
            "Customers",
            len(df)
        )

        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True
        )

        csv = df.to_csv(
            index=False
        ).encode("utf-8")

        st.download_button(
            "📥 Download Customer CSV",
            csv,
            "customers.csv",
            "text/csv"
        )

    except Exception as e:

        st.error(e)


# ============================================================
# PAYMENTS PAGE
# ============================================================

elif page == "💳 Payments":

    st.subheader("💳 Payment Management")

    try:

        df = get_all_payments()

        # Payment status
        statuses = sorted(
            df["PAYMENT_STATUS"]
            .dropna()
            .unique()
            .tolist()
        )

        if statuses:

            selected = st.multiselect(
                "Payment Status",
                statuses,
                default=statuses
            )

            df = df[
                df["PAYMENT_STATUS"].isin(selected)
            ]

        col1, col2, col3 = st.columns(3)

        total_transactions = len(df)

        total_amount = df[
            "PAYMENT_AMOUNT"
        ].sum()

        average_amount = (
            df["PAYMENT_AMOUNT"].mean()
            if not df.empty
            else 0
        )

        col1.metric(
            "Transactions",
            f"{total_transactions:,}"
        )

        col2.metric(
            "Total Amount",
            f"₹{total_amount:,.2f}"
        )

        col3.metric(
            "Average Payment",
            f"₹{average_amount:,.2f}"
        )

        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True
        )

        csv = df.to_csv(
            index=False
        ).encode("utf-8")

        st.download_button(
            "📥 Download Payments CSV",
            csv,
            "payments.csv",
            "text/csv"
        )

    except Exception as e:

        st.error(e)


# ============================================================
# EXCEPTIONS PAGE
# ============================================================

elif page == "⚠️ Exceptions":

    st.subheader(
        "⚠️ Rental Validation & Exceptions"
    )

    try:

        df = get_rejected_rentals()

        if df.empty:

            st.success(
                "✅ No rejected rental records found."
            )

        else:

            st.warning(
                f"⚠️ {len(df)} rejected rental records found."
            )

            # Rejection reason chart
            reason_df = (
                df.groupby("REJECT_REASON")
                .size()
                .reset_index(
                    name="COUNT"
                )
                .sort_values(
                    "COUNT",
                    ascending=False
                )
            )

            if not reason_df.empty:

                fig = px.bar(
                    reason_df,
                    x="COUNT",
                    y="REJECT_REASON",
                    orientation="h",
                    labels={
                        "COUNT": "Rejected Records",
                        "REJECT_REASON": "Reason"
                    }
                )

                fig.update_layout(
                    height=350
                )

                st.plotly_chart(
                    fig,
                    use_container_width=True
                )

            st.dataframe(
                df,
                use_container_width=True,
                hide_index=True
            )

            csv = df.to_csv(
                index=False
            ).encode("utf-8")

            st.download_button(
                "📥 Download Exceptions CSV",
                csv,
                "rental_rejects.csv",
                "text/csv"
            )

    except Exception as e:

        st.error(e)


# ============================================================
# FOOTER
# ============================================================

st.markdown("---")

st.caption(
    "🚗 Vehicle Rental Management System | "
    "Python + Streamlit + Oracle"
)