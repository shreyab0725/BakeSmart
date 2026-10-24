import sqlite3
from datetime import date, datetime

import pandas as pd
import plotly.express as px
import streamlit as st

DB = "bakery.db"

st.set_page_config(
    page_title="BakeSmart | Smart Bakery",
    page_icon="🧁",
    layout="wide",
)

# -------------------- DESIGN --------------------
st.markdown("""
<style>
.stApp {
    background: linear-gradient(135deg, #fff8f1 0%, #fff0f5 55%, #fffaf0 100%);
}
[data-testid="stSidebar"] {
    background: #552b3a;
}
[data-testid="stSidebar"] * {
    color: #fff8f1 !important;
}
.hero {
    padding: 28px;
    border-radius: 22px;
    background: linear-gradient(120deg, #6f3448, #b65d76);
    color: white;
    margin-bottom: 20px;
}
.hero h1 { color: white; margin-bottom: 4px; }
.hero p { color: #fff1f5; font-size: 17px; }
div[data-testid="stMetric"] {
    background: white;
    border: 1px solid #f0d5dc;
    padding: 16px;
    border-radius: 16px;
}
.product-card {
    background: white;
    padding: 18px;
    border: 1px solid #f1d8df;
    border-radius: 16px;
    margin-bottom: 10px;
}
</style>
""", unsafe_allow_html=True)


# -------------------- DATABASE --------------------
def connect_db():
    return sqlite3.connect(DB, check_same_thread=False)


def setup_database():
    with connect_db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                category TEXT NOT NULL,
                price REAL NOT NULL,
                stock INTEGER NOT NULL DEFAULT 0,
                emoji TEXT NOT NULL DEFAULT '🧁'
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS sales (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sale_date TEXT NOT NULL,
                product_name TEXT NOT NULL,
                quantity INTEGER NOT NULL,
                unit_price REAL NOT NULL,
                total REAL NOT NULL
            )
        """)
        count = conn.execute("SELECT COUNT(*) FROM products").fetchone()[0]
        if count == 0:
            starter_products = [
                ("Chocolate Cake", "Cake", 650, 12, "🎂"),
                ("Black Forest Cake", "Cake", 700, 8, "🍰"),
                ("Chocolate Pastry", "Pastry", 90, 30, "🧁"),
                ("Butter Cookies", "Cookies", 150, 25, "🍪"),
                ("Fresh Bread", "Bread", 50, 20, "🍞"),
                ("Blueberry Muffin", "Muffin", 80, 18, "🧁"),
            ]
            conn.executemany(
                "INSERT INTO products(name, category, price, stock, emoji) VALUES (?, ?, ?, ?, ?)",
                starter_products,
            )


setup_database()


def read_products():
    with connect_db() as conn:
        return pd.read_sql_query("SELECT * FROM products ORDER BY name", conn)


def read_sales():
    with connect_db() as conn:
        return pd.read_sql_query(
            "SELECT * FROM sales ORDER BY sale_date DESC, id DESC", conn
        )


# -------------------- SIDEBAR --------------------
st.sidebar.markdown("# 🧁 BakeSmart")
st.sidebar.caption("SMART BAKERY MANAGEMENT")
page = st.sidebar.radio(
    "Navigate",
    ["🏠 Home", "🍰 Products", "🧾 Sales Entry", "📊 Analytics Dashboard", "ℹ️ About"],
)
st.sidebar.markdown("---")
st.sidebar.info("Bakery management & sales analytics")


products = read_products()
sales = read_sales()

# -------------------- HOME --------------------
if page == "🏠 Home":
    st.markdown("""
    <div class="hero">
      <h1>🧁 Welcome to BakeSmart</h1>
      <p>Your smart space to manage bakery products, record sales and understand your business.</p>
    </div>
    """, unsafe_allow_html=True)

    total_revenue = float(sales["total"].sum()) if not sales.empty else 0
    total_orders = int(len(sales))
    units_sold = int(sales["quantity"].sum()) if not sales.empty else 0
    product_count = int(len(products))

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("💰 Total Revenue", f"₹{total_revenue:,.2f}")
    c2.metric("🧾 Sales Records", f"{total_orders:,}")
    c3.metric("🛍️ Units Sold", f"{units_sold:,}")
    c4.metric("🍰 Products", f"{product_count:,}")

    st.subheader("✨ Explore your bakery")
    a, b = st.columns(2)
    with a:
        st.markdown('<div class="product-card"><h3>🍰 Manage Products</h3><p>View products, prices and stock. Add new bakery items whenever needed.</p></div>', unsafe_allow_html=True)
        st.markdown('<div class="product-card"><h3>📊 Understand Sales</h3><p>Use charts and summary metrics to understand your bakery sales.</p></div>', unsafe_allow_html=True)
    with b:
        st.markdown('<div class="product-card"><h3>🧾 Record a Sale</h3><p>Choose a product, enter quantity and save the sale to your database.</p></div>', unsafe_allow_html=True)
        st.markdown('<div class="product-card"><h3>💡 Make Better Decisions</h3><p>Find popular products and compare revenue by product.</p></div>', unsafe_allow_html=True)

    st.caption("Note: Starter products are sample/demo data. Replace them with your real bakery information when available.")

# -------------------- PRODUCTS --------------------
elif page == "🍰 Products":
    st.markdown('<div class="hero"><h1>🍰 Bakery Products</h1><p>Manage your menu, prices and stock.</p></div>', unsafe_allow_html=True)

    with st.expander("➕ Add a new product", expanded=False):
        with st.form("add_product_form", clear_on_submit=True):
            p1, p2 = st.columns(2)
            name = p1.text_input("Product name")
            category = p2.selectbox("Category", ["Cake", "Pastry", "Cookies", "Bread", "Muffin", "Other"])
            p3, p4, p5 = st.columns(3)
            price = p3.number_input("Price (₹)", min_value=0.0, value=100.0, step=10.0)
            stock = p4.number_input("Stock quantity", min_value=0, value=10, step=1)
            emoji = p5.selectbox("Icon", ["🎂", "🍰", "🧁", "🍪", "🍞", "🥐", "🍩"])
            submitted = st.form_submit_button("Save product", use_container_width=True)
            if submitted:
                if not name.strip():
                    st.error("Please enter a product name.")
                else:
                    try:
                        with connect_db() as conn:
                            conn.execute(
                                "INSERT INTO products(name, category, price, stock, emoji) VALUES (?, ?, ?, ?, ?)",
                                (name.strip(), category, price, int(stock), emoji),
                            )
                        st.success(f"{name.strip()} added successfully!")
                        st.rerun()
                    except sqlite3.IntegrityError:
                        st.error("This product already exists. Choose another name.")

    products = read_products()
    if products.empty:
        st.info("No products yet. Add your first product above.")
    else:
        search = st.text_input("🔎 Search products", placeholder="Type a product name...")
        shown = products[products["name"].str.contains(search, case=False, na=False)] if search else products
        cols = st.columns(3)
        for i, row in shown.reset_index(drop=True).iterrows():
            with cols[i % 3]:
                st.markdown(
                    f"""<div class="product-card">
                    <div style="font-size:36px">{row['emoji']}</div>
                    <h3>{row['name']}</h3>
                    <p>Category: {row['category']}</p>
                    <h3>₹{row['price']:,.2f}</h3>
                    <p>Stock: {int(row['stock'])}</p>
                    </div>""",
                    unsafe_allow_html=True,
                )

        st.subheader("✏️ Update price or stock")
        product_names = products["name"].tolist()
        chosen = st.selectbox("Select product to update", product_names, key="update_product")
        selected = products[products["name"] == chosen].iloc[0]
        with st.form("update_product_form"):
            new_price = st.number_input("New price (₹)", min_value=0.0, value=float(selected["price"]), step=10.0)
            new_stock = st.number_input("New stock", min_value=0, value=int(selected["stock"]), step=1)
            update = st.form_submit_button("Update product", use_container_width=True)
            if update:
                with connect_db() as conn:
                    conn.execute("UPDATE products SET price = ?, stock = ? WHERE name = ?", (new_price, int(new_stock), chosen))
                st.success("Product updated.")
                st.rerun()

# -------------------- SALES ENTRY --------------------
elif page == "🧾 Sales Entry":
    st.markdown('<div class="hero"><h1>🧾 Record a Sale</h1><p>Save each order and track your bakery sales.</p></div>', unsafe_allow_html=True)
    products = read_products()

    if products.empty:
        st.warning("Add at least one product in the Products page before recording a sale.")
    else:
        with st.form("sale_form", clear_on_submit=True):
            product_names = products["name"].tolist()
            chosen = st.selectbox("Choose product", product_names)
            selected = products[products["name"] == chosen].iloc[0]
            st.write(f"**Price per unit:** ₹{float(selected['price']):,.2f}  |  **Available stock:** {int(selected['stock'])}")
            quantity = st.number_input("Quantity sold", min_value=1, max_value=max(1, int(selected["stock"])) if int(selected["stock"]) > 0 else 1, value=1, step=1)
            sale_date = st.date_input("Sale date", value=date.today())
            total = float(selected["price"]) * int(quantity)
            st.metric("Order total", f"₹{total:,.2f}")
            save_sale = st.form_submit_button("💾 Save sale", use_container_width=True)

            if save_sale:
                if int(selected["stock"]) < int(quantity):
                    st.error("Not enough stock. Update stock on the Products page.")
                else:
                    with connect_db() as conn:
                        conn.execute(
                            "INSERT INTO sales(sale_date, product_name, quantity, unit_price, total) VALUES (?, ?, ?, ?, ?)",
                            (sale_date.isoformat(), chosen, int(quantity), float(selected["price"]), total),
                        )
                        conn.execute(
                            "UPDATE products SET stock = stock - ? WHERE name = ?",
                            (int(quantity), chosen),
                        )
                    st.success(f"Sale saved! Total: ₹{total:,.2f}")
                    st.rerun()

    st.subheader("Recent sales")
    sales = read_sales()
    if sales.empty:
        st.info("No sales recorded yet. Add a sale using the form above.")
    else:
        display_sales = sales.rename(columns={
            "id": "Sale ID", "sale_date": "Date", "product_name": "Product",
            "quantity": "Quantity", "unit_price": "Unit Price (₹)", "total": "Total (₹)"
        })
        st.dataframe(display_sales, use_container_width=True, hide_index=True)

# -------------------- ANALYTICS --------------------
elif page == "📊 Analytics Dashboard":
    st.markdown('<div class="hero"><h1>📊 Bakery Analytics Dashboard</h1><p>Explore revenue, products and sales trends.</p></div>', unsafe_allow_html=True)
    sales = read_sales()

    if sales.empty:
        st.info("Your dashboard will display charts after you record some sales in Sales Entry. You can add demo sales below for a college presentation.")
        if st.button("➕ Add sample demo sales"):
            demo_rows = [
                (date.today().isoformat(), "Chocolate Cake", 2, 650.0, 1300.0),
                (date.today().isoformat(), "Chocolate Pastry", 5, 90.0, 450.0),
                (date.today().isoformat(), "Butter Cookies", 3, 150.0, 450.0),
                (date.today().isoformat(), "Fresh Bread", 4, 50.0, 200.0),
                (date.today().isoformat(), "Black Forest Cake", 1, 700.0, 700.0),
            ]
            with connect_db() as conn:
                conn.executemany(
                    "INSERT INTO sales(sale_date, product_name, quantity, unit_price, total) VALUES (?, ?, ?, ?, ?)",
                    demo_rows,
                )
                for _, product_name, qty, _, _ in demo_rows:
                    conn.execute("UPDATE products SET stock = MAX(0, stock - ?) WHERE name = ?", (qty, product_name))
            st.success("Sample/demo sales added. These are not real business records.")
            st.rerun()
    else:
        total_revenue = float(sales["total"].sum())
        total_orders = len(sales)
        total_units = int(sales["quantity"].sum())
        average_sale = total_revenue / total_orders if total_orders else 0

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("💰 Revenue", f"₹{total_revenue:,.2f}")
        c2.metric("🧾 Sales Records", f"{total_orders:,}")
        c3.metric("🛍️ Units Sold", f"{total_units:,}")
        c4.metric("📈 Average Sale", f"₹{average_sale:,.2f}")

        by_product = sales.groupby("product_name", as_index=False).agg(
            Revenue=("total", "sum"), Quantity=("quantity", "sum")
        ).sort_values("Revenue", ascending=False)

        left, right = st.columns(2)
        with left:
            fig_bar = px.bar(by_product, x="product_name", y="Revenue", title="Revenue by Product", color="Revenue", labels={"product_name": "Product", "Revenue": "Revenue (₹)"})
            fig_bar.update_layout(xaxis_title="", yaxis_title="Revenue (₹)", plot_bgcolor="white", paper_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig_bar, use_container_width=True)
        with right:
            fig_pie = px.pie(by_product, names="product_name", values="Quantity", title="Units Sold by Product", hole=0.45)
            st.plotly_chart(fig_pie, use_container_width=True)

        daily = sales.groupby("sale_date", as_index=False)["total"].sum().sort_values("sale_date")
        fig_line = px.line(daily, x="sale_date", y="total", markers=True, title="Sales Trend", labels={"sale_date": "Date", "total": "Revenue (₹)"})
        fig_line.update_layout(plot_bgcolor="white", paper_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig_line, use_container_width=True)

        best = by_product.iloc[0]
        st.success(f"Top revenue product in the recorded data: {best['product_name']} (₹{best['Revenue']:,.2f}).")
        st.caption("Use real sales records for genuine business insights. Any sample/demo records are illustrative only.")

        st.subheader("📥 Download sales data")
        csv = sales.to_csv(index=False).encode("utf-8")
        st.download_button("Download CSV", data=csv, file_name="bakesmart_sales.csv", mime="text/csv")

# -------------------- ABOUT --------------------
elif page == "ℹ️ About":
    st.markdown('<div class="hero"><h1>ℹ️ About BakeSmart</h1><p>A sample bakery management and sales analytics project built with Python.</p></div>', unsafe_allow_html=True)
    st.write("""
    **BakeSmart** is a demonstration web app that helps a bakery:
    - View and manage products and stock.
    - Record sales and calculate order totals.
    - Store records in a local SQLite database.
    - Explore sales performance using interactive charts.
    - Download sales data as a CSV file.

    **Technology stack:** Python, Streamlit, SQLite, Pandas and Plotly.

    **Academic project note:** Starter products and optional demo sales are sample data. They should not be described as real company or internship results.
    """)
    st.warning("The SQLite database is stored in the app's working folder. For a deployed public website, persistent storage needs to be planned separately.")
