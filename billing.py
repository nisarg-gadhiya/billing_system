import tkinter
from tkinter import ttk, messagebox
from datetime import datetime
import mysql.connector
import random
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
import numpy as np
from tkinter import simpledialog


def init_database():
    conn = mysql.connector.connect(
        host='localhost',
        user='root',
        password='9819170158@n*'
    )
    cursor = conn.cursor()
    
    cursor.execute('CREATE DATABASE IF NOT EXISTS billing_system')
    cursor.execute('USE billing_system')

    # Create orders table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            order_id VARCHAR(50) PRIMARY KEY,
            bill_number VARCHAR(50),
            order_date DATE,
            order_time TIME,
            total_amount FLOAT,
            payment_type VARCHAR(20)
        )
    ''')

    # Create order_items table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS order_items (
            item_id INT AUTO_INCREMENT PRIMARY KEY,
            order_id VARCHAR(50),
            item_name VARCHAR(50),
            quantity INT,
            price FLOAT,
            FOREIGN KEY (order_id) REFERENCES orders (order_id)
        )
    ''')

    # Create order_audit table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS order_audit (
            audit_id INT AUTO_INCREMENT PRIMARY KEY,
            order_id VARCHAR(50),
            bill_number VARCHAR(50),
            action VARCHAR(10),
            action_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Create total sales function
    cursor.execute('''
        CREATE FUNCTION IF NOT EXISTS get_total_sales(start_date DATE, end_date DATE)
        RETURNS FLOAT
        DETERMINISTIC
        BEGIN
            DECLARE total FLOAT;
            SELECT SUM(total_amount) INTO total FROM orders 
            WHERE order_date BETWEEN start_date AND end_date;
            RETURN IFNULL(total, 0);
        END;
    ''')

    # Create monthly sales procedure
    cursor.execute('''
        CREATE PROCEDURE IF NOT EXISTS monthly_sales_report(IN report_month VARCHAR(7))
        BEGIN
            SELECT 
                DATE_FORMAT(order_date, '%Y-%m-%d') AS order_date,
                COUNT(*) AS num_orders,
                SUM(total_amount) AS total_sales
            FROM orders 
            WHERE DATE_FORMAT(order_date, '%Y-%m') = report_month
            GROUP BY order_date
            ORDER BY order_date;
        END;
    ''')

    # Create order tracking trigger
    cursor.execute('''
        CREATE TRIGGER IF NOT EXISTS after_order_insert
        AFTER INSERT ON orders
        FOR EACH ROW
        BEGIN
            INSERT INTO order_audit (order_id, bill_number, action) 
            VALUES (NEW.order_id, NEW.bill_number, 'INSERT');
        END;
    ''')

    conn.commit()
    conn.close()



init_database()

ordered_items = {}
current_item_id = 1

prices = {
    "Pizza": 12.99, "Pasta": 10.99, "Lasagna": 14.99,
    "Nachos": 8.99, "Tacos": 9.99, "Burger": 11.99,
    "Buritto": 10.99, "Cheese Fries": 6.99, "Coke": 2.99,
    "Cold Coffee": 4.99, "Mojito": 5.99
}

window = tkinter.Tk()
window.title("Billing System")


def generate_order_id():
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    random_num = random.randint(1000, 9999)
    return f"ORD{timestamp}{random_num}"

def generate_bill_number():
    return f"BILL{random.randint(10000, 99999)}"

def get_current_date():
    return datetime.now().strftime("%Y-%m-%d")

def get_current_time():
    return datetime.now().strftime("%H:%M:%S")

def get_total_sales():
    try:
        conn = mysql.connector.connect(
            host='localhost',
            user='root',
            password='9819170158@n*',
            database='billing_system'
        )
        cursor = conn.cursor()

        start_date = simpledialog.askstring("Input", "Enter Start Date (YYYY-MM-DD):")
        end_date = simpledialog.askstring("Input", "Enter End Date (YYYY-MM-DD):")

        if not start_date or not end_date:
            messagebox.showerror("Error", "Please enter both start and end dates.")
            return

        cursor.execute("SELECT get_total_sales(%s, %s)", (start_date, end_date))
        total_sales = cursor.fetchone()[0]

        messagebox.showinfo("Total Sales", f"Total sales from {start_date} to {end_date}: ${total_sales:.2f}")

        conn.close()
    except mysql.connector.Error as e:
        messagebox.showerror("Database Error", f"An error occurred: {str(e)}")

def get_monthly_sales():
    try:
        conn = mysql.connector.connect(
            host='localhost',
            user='root',
            password='9819170158@n*',
            database='billing_system'
        )
        cursor = conn.cursor()

        month = simpledialog.askstring("Input", "Enter Month (YYYY-MM):")
        if not month:
            messagebox.showerror("Error", "Please enter a valid month.")
            return

        cursor.execute("CALL monthly_sales_report(%s)", (month,))
        results = cursor.fetchall()

        if not results:
            messagebox.showinfo("Monthly Sales", f"No sales data found for {month}.")
            return

        report_text = f"Sales Report for {month}:\n\n"
        for row in results:
            report_text += f"Date: {row[0]}, Orders: {row[1]}, Sales: ${row[2]:.2f}\n"

        messagebox.showinfo("Monthly Sales Report", report_text)

        conn.close()
    except mysql.connector.Error as e:
        messagebox.showerror("Database Error", f"An error occurred: {str(e)}")


def show_sales_graph(filters=None):
    try:
        graph_window = tkinter.Toplevel(window)
        graph_window.title("Sales Analysis Dashboard")
        graph_window.geometry("1400x1000")

        # Database connection and initial setup remains the same
        conn = mysql.connector.connect(
            host='localhost',
            user='root',
            password='9819170158@n*',
            database='billing_system'
        )
        
        # Get monthly sales data
        cursor = conn.cursor()
        cursor.execute('''
            SELECT 
                DATE_FORMAT(order_date, '%Y-%m') as month,
                COUNT(*) as num_orders,
                SUM(total_amount) as total_sales,
                AVG(total_amount) as avg_order_value,
                payment_type,
                COUNT(DISTINCT order_id) as unique_orders
            FROM orders 
            WHERE order_date >= '2025-01-01'
            GROUP BY DATE_FORMAT(order_date, '%Y-%m'), payment_type
            ORDER BY month
        ''')
        monthly_data = cursor.fetchall()

        # Rest of the data fetching remains the same...
        cursor.execute('''
            SELECT 
                item_name,
                SUM(quantity) as total_quantity,
                SUM(quantity * price) as total_revenue
            FROM order_items oi
            JOIN orders o ON oi.order_id = o.order_id
            WHERE o.order_date >= '2025-01-01'
            GROUP BY item_name
            ORDER BY total_revenue DESC
            LIMIT 5
        ''')
        top_items_data = cursor.fetchall()

        cursor.execute('''
            SELECT 
                payment_type,
                COUNT(*) as count,
                SUM(total_amount) as total_amount
            FROM orders
            WHERE order_date >= '2025-01-01'
            GROUP BY payment_type
        ''')
        payment_data = cursor.fetchall()

        conn.close()

        if not monthly_data:
            messagebox.showinfo("No Data", "No sales data available to display!")
            graph_window.destroy()
            return

        # Prepare data
        months = sorted(list(set([row[0] for row in monthly_data])))
        payment_types = sorted(list(set([row[4] for row in monthly_data])))
        
        # Convert month strings to datetime for plotting
        import datetime
        month_dates = [datetime.datetime.strptime(month, '%Y-%m') for month in months]
        
        import matplotlib.pyplot as plt
        import matplotlib.dates as mdates
        from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
        import numpy as np

        # Create figure with subplots
        fig = plt.figure(figsize=(15, 12))
        
        # Create GridSpec with more space between plots
        gs = fig.add_gridspec(3, 2, height_ratios=[1, 1, 1], 
                            hspace=0.6,
                            wspace=0.3)

        # 1. Monthly Sales Trend (Grouped Bar Chart)
        ax1 = fig.add_subplot(gs[0, :])
        
        # Set the width of each bar and positions of the bars
        width = 0.8 / len(payment_types)
        x = np.arange(len(months))
        
        # Create bars for each payment type
        for i, payment_type in enumerate(payment_types):
            sales_data = [next((row[2] for row in monthly_data if row[0] == month and row[4] == payment_type), 0) 
                         for month in months]
            positions = x + (i - len(payment_types)/2 + 0.5) * width
            bars = ax1.bar(positions, sales_data, width, label=payment_type)
            
            # Add value labels on top of each bar
            for pos, sale in zip(positions, sales_data):
                if sale > 0:  # Only show label if there's a sale
                    ax1.text(pos, sale, f'${sale:,.0f}', 
                            ha='center', va='bottom', 
                            rotation=45, fontsize=8)
        
        ax1.set_title('Monthly Sales by Payment Method', pad=20, fontsize=12, fontweight='bold')
        ax1.set_xlabel('Month', labelpad=10)
        ax1.set_ylabel('Sales Amount ($)', labelpad=10)
        
        # Set the tick positions and labels
        ax1.set_xticks(x)
        ax1.set_xticklabels([month for month in months], rotation=45, ha='right')
        
        ax1.grid(True, linestyle='--', alpha=0.7, axis='y')
        ax1.legend(title='Payment Type', bbox_to_anchor=(1.05, 1), loc='upper left')
        ax1.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x:,.0f}'))

        # Rest of the visualization code (Top Items, Payment Distribution, and Average Order Value) remains the same...
        # 2. Top Selling Items (Horizontal Bar Chart)
        ax2 = fig.add_subplot(gs[1, 0])
        items = [row[0] for row in top_items_data]
        revenues = [row[2] for row in top_items_data]
        y_pos = np.arange(len(items))
        
        bars = ax2.barh(y_pos, revenues, align='center')
        ax2.set_yticks(y_pos)
        ax2.set_yticklabels(items)
        ax2.invert_yaxis()
        ax2.set_title('Top 5 Items by Revenue', pad=20, fontsize=12, fontweight='bold')
        ax2.set_xlabel('Revenue ($)', labelpad=10)
        
        for i, bar in enumerate(bars):
            width = bar.get_width()
            ax2.text(width, bar.get_y() + bar.get_height()/2,
                    f'${width:,.2f}',
                    ha='left', va='center', fontweight='bold')

        # 3. Payment Method Distribution (Pie Chart)
        ax3 = fig.add_subplot(gs[1, 1])
        payment_amounts = [row[2] for row in payment_data]
        payment_labels = [f'{row[0]}\n(${row[2]:,.2f})' for row in payment_data]
        
        ax3.pie(payment_amounts, labels=payment_labels, autopct='%1.1f%%',
                startangle=90, explode=[0.05] * len(payment_amounts))
        ax3.set_title('Payment Method Distribution', pad=20, fontsize=12, fontweight='bold')

        # 4. Average Order Value Trend
        ax4 = fig.add_subplot(gs[2, :])
        avg_orders = []
        for month in months:
            monthly_total = sum(row[2] for row in monthly_data if row[0] == month)
            monthly_count = sum(row[1] for row in monthly_data if row[0] == month)
            avg_orders.append(monthly_total / monthly_count if monthly_count > 0 else 0)

        ax4.plot(x, avg_orders, marker='o', linestyle='-', linewidth=2, markersize=8)
        ax4.set_title('Monthly Average Order Value Trend', pad=20, fontsize=12, fontweight='bold')
        ax4.set_xlabel('Month', labelpad=10)
        ax4.set_ylabel('Average Order Value ($)', labelpad=10)
        
        # Set the tick positions and labels
        ax4.set_xticks(x)
        ax4.set_xticklabels([month for month in months], rotation=45, ha='right')
        
        ax4.grid(True, linestyle='--', alpha=0.7)
        ax4.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x:,.2f}'))

        # Add value labels
        for i, value in enumerate(avg_orders):
            ax4.text(i, value, f'${value:,.2f}',
                    ha='center', va='bottom', rotation=45, fontsize=8)

        # Create frame for canvas and toolbar
        frame = ttk.Frame(graph_window)
        frame.pack(fill='both', expand=True)

        # Create canvas and toolbar
        canvas = FigureCanvasTkAgg(fig, master=frame)
        toolbar = NavigationToolbar2Tk(canvas, frame)
        toolbar.pack(side='bottom', fill='x')
        
        # Adjust layout before packing canvas
        plt.tight_layout()
        
        # Pack canvas
        canvas.draw()
        canvas.get_tk_widget().pack(side='top', fill='both', expand=True, padx=20, pady=20)

    except mysql.connector.Error as e:
        messagebox.showerror("Database Error", f"An error occurred while fetching data: {str(e)}")
    except Exception as e:
        messagebox.showerror("Error", f"An error occurred: {str(e)}")
        
def show_database_viewer():
    try:
        db_window = tkinter.Toplevel(window)
        db_window.title("Database Viewer")
        db_window.geometry("1200x600")

        # Create notebook for tabs
        notebook = ttk.Notebook(db_window)
        notebook.pack(fill='both', expand=True, padx=10, pady=10)

        # Create frames for each table
        orders_frame = ttk.Frame(notebook)
        items_frame = ttk.Frame(notebook)
        joined_frame = ttk.Frame(notebook)
        
        notebook.add(orders_frame, text='Orders')
        notebook.add(items_frame, text='Order Items')
        notebook.add(joined_frame, text='Joined View')

        # Create Treeview for Orders
        orders_tree = ttk.Treeview(orders_frame)
        orders_tree['columns'] = ('order_id', 'bill_number', 'order_date', 'order_time', 'total_amount', 'payment_type')

        # Format columns for Orders
        orders_tree.column('#0', width=0, stretch=tkinter.NO)
        orders_tree.column('order_id', width=150, anchor=tkinter.CENTER)
        orders_tree.column('bill_number', width=100, anchor=tkinter.CENTER)
        orders_tree.column('order_date', width=100, anchor=tkinter.CENTER)
        orders_tree.column('order_time', width=100, anchor=tkinter.CENTER)
        orders_tree.column('total_amount', width=100, anchor=tkinter.CENTER)
        orders_tree.column('payment_type', width=100, anchor=tkinter.CENTER)

        # Create headings for the Orders Treeview
        orders_tree.heading('order_id', text='Order ID')
        orders_tree.heading('bill_number', text='Bill Number')
        orders_tree.heading('order_date', text='Order Date')
        orders_tree.heading('order_time', text='Order Time')
        orders_tree.heading('total_amount', text='Total Amount')
        orders_tree.heading('payment_type', text='Payment Type')

        # Add scrollbar for Orders Treeview
        orders_scroll = ttk.Scrollbar(orders_frame, orient="vertical", command=orders_tree.yview)
        orders_tree.configure(yscrollcommand=orders_scroll.set)
        
        # Pack the Orders Treeview and Scrollbar
        orders_tree.pack(side="left", fill="both", expand=True)
        orders_scroll.pack(side="right", fill="y")

        # Create Treeview for Order Items
        items_tree = ttk.Treeview(items_frame)
        items_tree['columns'] = ('item_id', 'item_name', 'quantity', 'price')

        # Format columns for Order Items
        items_tree.column('#0', width=0, stretch=tkinter.NO)
        items_tree.column('item_id', width=150, anchor=tkinter.CENTER)
        items_tree.column('item_name', width=200, anchor=tkinter.CENTER)
        items_tree.column('quantity', width=100, anchor=tkinter.CENTER)
        items_tree.column('price', width=100, anchor=tkinter.CENTER)

        # Create headings for the Order Items Treeview
        items_tree.heading('item_id', text='Item ID')
        items_tree.heading('item_name', text='Item Name')
        items_tree.heading('quantity', text='Quantity')
        items_tree.heading('price', text='Price')

        # Add scrollbar for Order Items Treeview
        items_scroll = ttk.Scrollbar(items_frame, orient="vertical", command=items_tree.yview)
        items_tree.configure(yscrollcommand=items_scroll.set)
        
        # Pack the Order Items Treeview and Scrollbar
        items_tree.pack(side="left", fill="both", expand=True)
        items_scroll.pack(side="right", fill="y")

        # Create Treeview for the Joined View
        joined_tree = ttk.Treeview(joined_frame)
        joined_tree['columns'] = ('order_id', 'bill_number', 'order_date', 'order_time', 'total_amount', 'payment_type', 'item_id', 'item_name', 'quantity', 'price')

        # Format columns for the Joined View
        joined_tree.column('#0', width=0, stretch=tkinter.NO)
        joined_tree.column('order_id', width=150, anchor=tkinter.CENTER)
        joined_tree.column('bill_number', width=100, anchor=tkinter.CENTER)
        joined_tree.column('order_date', width=100, anchor=tkinter.CENTER)
        joined_tree.column('order_time', width=100, anchor=tkinter.CENTER)
        joined_tree.column('total_amount', width=100, anchor=tkinter.CENTER)
        joined_tree.column('payment_type', width=100, anchor=tkinter.CENTER)
        joined_tree.column('item_id', width=150, anchor=tkinter.CENTER)
        joined_tree.column('item_name', width=150, anchor=tkinter.CENTER)
        joined_tree.column('quantity', width=100, anchor=tkinter.CENTER)
        joined_tree.column('price', width=100, anchor=tkinter.CENTER)

        # Create headings for the Joined View Treeview
        joined_tree.heading('order_id', text='Order ID')
        joined_tree.heading('bill_number', text='Bill Number')
        joined_tree.heading('order_date', text='Order Date')
        joined_tree.heading('order_time', text='Order Time')
        joined_tree.heading('total_amount', text='Total Amount')
        joined_tree.heading('payment_type', text='Payment Type')
        joined_tree.heading('item_id', text='Item ID')
        joined_tree.heading('item_name', text='Item Name')
        joined_tree.heading('quantity', text='Quantity')
        joined_tree.heading('price', text='Price')

        # Add scrollbar for the Joined View Treeview
        joined_scroll = ttk.Scrollbar(joined_frame, orient="vertical", command=joined_tree.yview)
        joined_tree.configure(yscrollcommand=joined_scroll.set)
        
        # Pack the Joined Treeview and Scrollbar
        joined_tree.pack(side="left", fill="both", expand=True)
        joined_scroll.pack(side="right", fill="y")

        def refresh_data():
            # Clear existing items in the Treeviews
            for item in orders_tree.get_children():
                orders_tree.delete(item)
            for item in items_tree.get_children():
                items_tree.delete(item)
            for item in joined_tree.get_children():
                joined_tree.delete(item)

            # Connect to the database
            conn = mysql.connector.connect(
                host='localhost',
                user='root',
                password='9819170158@n*',
                database='billing_system'
            )
            cursor = conn.cursor()

            # Fetch data for Orders
            cursor.execute("SELECT order_id, bill_number, order_date, order_time, total_amount, payment_type FROM orders")
            for row in cursor.fetchall():
                orders_tree.insert('', 'end', values=row)

            # Fetch data for Order Items
            cursor.execute("SELECT item_id, item_name, quantity, price FROM order_items")
            for row in cursor.fetchall():
                items_tree.insert('', 'end', values=row)

            # Fetch data for the Joined View (Orders + Order Items)
            cursor.execute('''
                SELECT o.order_id, o.bill_number, o.order_date, o.order_time, o.total_amount, o.payment_type,
                       oi.item_id, oi.item_name, oi.quantity, oi.price
                FROM orders o
                LEFT JOIN order_items oi ON o.order_id = oi.order_id
                ORDER BY o.order_date DESC, o.order_time DESC
            ''')
            for row in cursor.fetchall():
                joined_tree.insert('', 'end', values=row)

            conn.close()

        # Add refresh button
        refresh_btn = ttk.Button(db_window, text="Refresh Data", command=refresh_data)
        refresh_btn.pack(pady=10)

        # Load initial data
        refresh_data()

    except mysql.connector.Error as e:
        messagebox.showerror("Database Error", f"An error occurred while fetching data: {str(e)}")
    except Exception as e:
        messagebox.showerror("Error", f"An error occurred: {str(e)}")

def show_audit_logs():
    try:
        audit_window = tkinter.Toplevel(window)
        audit_window.title("Audit Log Viewer")
        audit_window.geometry("800x400")

        # Create Treeview
        audit_tree = ttk.Treeview(audit_window)
        audit_tree['columns'] = ('audit_id', 'order_id', 'bill_number', 'action', 'action_time')

        # Define columns
        audit_tree.column('#0', width=0, stretch=tkinter.NO)
        audit_tree.column('audit_id', width=50, anchor=tkinter.CENTER)
        audit_tree.column('order_id', width=150, anchor=tkinter.CENTER)
        audit_tree.column('bill_number', width=100, anchor=tkinter.CENTER)
        audit_tree.column('action', width=100, anchor=tkinter.CENTER)
        audit_tree.column('action_time', width=150, anchor=tkinter.CENTER)

        # Create headings
        audit_tree.heading('audit_id', text='Audit ID')
        audit_tree.heading('order_id', text='Order ID')
        audit_tree.heading('bill_number', text='Bill Number')
        audit_tree.heading('action', text='Action')
        audit_tree.heading('action_time', text='Timestamp')

        # Scrollbar
        audit_scroll = ttk.Scrollbar(audit_window, orient="vertical", command=audit_tree.yview)
        audit_tree.configure(yscrollcommand=audit_scroll.set)

        audit_tree.pack(side="left", fill="both", expand=True, padx=10, pady=10)
        audit_scroll.pack(side="right", fill="y")

        # Fetch data from audit table
        conn = mysql.connector.connect(
            host='localhost',
            user='root',
            password='9819170158@n*',
            database='billing_system'
        )
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM order_audit ORDER BY action_time DESC")
        records = cursor.fetchall()

        # Insert data into Treeview
        for row in records:
            audit_tree.insert('', 'end', values=row)

        conn.close()

    except mysql.connector.Error as e:
        messagebox.showerror("Database Error", f"An error occurred: {str(e)}")


def show_filtered_data():
    def show_stats(filter_tree):
        amounts = [float(filter_tree.item(item, 'values')[4]) for item in filter_tree.get_children()]
    
        if amounts:
            total_sum = sum(amounts)
            avg_value = total_sum / len(amounts)
            min_value = min(amounts)
            max_value = max(amounts)
        
            messagebox.showinfo("Statistics", f"Sum: ${total_sum:.2f}\nAvg: ${avg_value:.2f}\nMin: ${min_value:.2f}\nMax: ${max_value:.2f}")
        else:
            messagebox.showinfo("Statistics", "No data available")

    def apply_filter():
        try:
            # Get filter inputs
            date_start = filter_date_start_entry.get()
            date_end = filter_date_end_entry.get()
            amount_min = filter_amount_min_entry.get()
            amount_max = filter_amount_max_entry.get()
            payment_type = filter_payment_type_entry.get()

            # Connect to the database
            conn = mysql.connector.connect(
                host='localhost',
                user='root',
                password='9819170158@n*',
                database='billing_system'
            )
            cursor = conn.cursor()

            # Construct SQL query with filters
            query = "SELECT order_id, bill_number, order_date, order_time, total_amount, payment_type FROM orders WHERE 1=1"
            params = []

            if date_start and date_end:
                query += " AND order_date BETWEEN %s AND %s"
                params.extend([date_start, date_end])
            if amount_min and amount_max:
                query += " AND total_amount BETWEEN %s AND %s"
                params.extend([float(amount_min), float(amount_max)])
            if payment_type != "All":
                query += " AND (payment_type = %s OR payment_type = 'Cash')"
                params.append(payment_type)

            cursor.execute(query, params)
            results = cursor.fetchall()

            # Clear existing data
            for item in filter_tree.get_children():
                filter_tree.delete(item)

            # Display results in Treeview
            for row in results:
                filter_tree.insert('', 'end', values=row)

            conn.close()

        except mysql.connector.Error as e:
            messagebox.showerror("Database Error", f"An error occurred: {str(e)}")
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {str(e)}")
    
    filter_window = tkinter.Toplevel(window)
    filter_window.title("Filter Data")
    filter_window.geometry("800x600")

    # Filter inputs
    filter_frame = ttk.Frame(filter_window)
    filter_frame.pack(pady=10, padx=10, fill='x')

    ttk.Label(filter_frame, text="Start Date (YYYY-MM-DD):").grid(row=0, column=0, padx=5, pady=5)
    filter_date_start_entry = ttk.Entry(filter_frame, width=20)
    filter_date_start_entry.grid(row=0, column=1, padx=5, pady=5)

    ttk.Label(filter_frame, text="End Date (YYYY-MM-DD):").grid(row=0, column=2, padx=5, pady=5)
    filter_date_end_entry = ttk.Entry(filter_frame, width=20)
    filter_date_end_entry.grid(row=0, column=3, padx=5, pady=5)

    ttk.Label(filter_frame, text="Min Amount:").grid(row=1, column=0, padx=5, pady=5)
    filter_amount_min_entry = ttk.Entry(filter_frame, width=20)
    filter_amount_min_entry.grid(row=1, column=1, padx=5, pady=5)

    ttk.Label(filter_frame, text="Max Amount:").grid(row=1, column=2, padx=5, pady=5)
    filter_amount_max_entry = ttk.Entry(filter_frame, width=20)
    filter_amount_max_entry.grid(row=1, column=3, padx=5, pady=5)

    ttk.Label(filter_frame, text="Payment Type:").grid(row=2, column=0, padx=5, pady=5)
    filter_payment_type_entry = ttk.Combobox(filter_frame, values=["All", "UPI", "Cash", "Card"], width=18)
    filter_payment_type_entry.set("All")
    filter_payment_type_entry.grid(row=2, column=1, padx=5, pady=5)

    # Apply filter button
    apply_filter_button = ttk.Button(filter_frame, text="Apply Filter", command=apply_filter)
    apply_filter_button.grid(row=2, column=2, padx=5, pady=5)


    # Stats button
    show_stats_button = ttk.Button(filter_frame, text="Show Stats", command=lambda: show_stats(filter_tree))
    show_stats_button.grid(row=2, column=3, padx=5, pady=5)

    # Treeview to display filtered data
    filter_tree = ttk.Treeview(filter_window)
    filter_tree['columns'] = ('order_id', 'bill_number', 'order_date', 'order_time', 'total_amount', 'payment_type')

    # Format columns
    filter_tree.column('#0', width=0, stretch=tkinter.NO)
    filter_tree.column('order_id', width=100, anchor=tkinter.CENTER)
    filter_tree.column('bill_number', width=100, anchor=tkinter.CENTER)
    filter_tree.column('order_date', width=100, anchor=tkinter.CENTER)
    filter_tree.column('order_time', width=100, anchor=tkinter.CENTER)
    filter_tree.column('total_amount', width=100, anchor=tkinter.CENTER)
    filter_tree.column('payment_type', width=100, anchor=tkinter.CENTER)

    # Create headings
    filter_tree.heading('order_id', text='Order ID')
    filter_tree.heading('bill_number', text='Bill Number')
    filter_tree.heading('order_date', text='Order Date')
    filter_tree.heading('order_time', text='Order Time')
    filter_tree.heading('total_amount', text='Total Amount')
    filter_tree.heading('payment_type', text='Payment Type')

    # Pack Treeview and scrollbar
    filter_scroll = ttk.Scrollbar(filter_window, orient="vertical", command=filter_tree.yview)
    filter_tree.configure(yscrollcommand=filter_scroll.set)

    filter_tree.pack(side="left", fill="both", expand=True, padx=10, pady=10)
    filter_scroll.pack(side="right", fill="y")


def update_ordered_items_display():
    display_text = ""
    sorted_items = sorted(ordered_items.items(), key=lambda x: x[1]['id'])
    for item, details in sorted_items:
        display_text += f"#{details['id']}: {item} x{details['qty']}\n"
    label_items_ordered_label.config(text=display_text)

def handle_item_click(event):
    global current_item_id
    selection = label_menu_listbox.curselection()
    if selection:
        item = label_menu_listbox.get(selection[0])
        if item in ordered_items:
            ordered_items[item]['qty'] += 1
        else:
            ordered_items[item] = {'qty': 1, 'id': current_item_id}
            current_item_id += 1
        update_ordered_items_display()

def delete_items():
    global current_item_id
    ordered_items.clear()
    current_item_id = 1
    update_ordered_items_display()
    label_bill_entry.delete(0, tkinter.END)

def save_order_to_database():
    if not ordered_items:
        messagebox.showerror("Error", "Please add items to the order first!")
        return
    
    if label_ptype_entry.get() == "Select mode":
        messagebox.showerror("Error", "Please select a payment mode!")
        return
    
    try:
        conn = mysql.connector.connect(
            host='localhost',
            user='root',
            password='9819170158@n*', 
            database='billing_system'
        )
        cursor = conn.cursor()
        
        order_id = generate_order_id()
        bill_number = label_bill_num_entry.get() or generate_bill_number()
        
        total = sum(prices[item] * details['qty'] for item, details in ordered_items.items())
        
        cursor.execute('''
            INSERT INTO orders (order_id, bill_number, order_date, order_time, 
                              total_amount, payment_type)
            VALUES (%s, %s, %s, %s, %s, %s)
        ''', (order_id, bill_number, get_current_date(), get_current_time(), 
              total, label_ptype_entry.get()))
        
        for item, details in ordered_items.items():
            cursor.execute('''
                INSERT INTO order_items (order_id, item_name, quantity, price)
                VALUES (%s, %s, %s, %s)
            ''', (order_id, item, details['qty'], prices[item]))
        
        conn.commit()
        conn.close()
        
        messagebox.showinfo("Success", f"Order saved successfully!\nOrder ID: {order_id}")
        
        delete_items()
        label_bill_num_entry.delete(0, tkinter.END)
        label_bill_num_entry.insert(0, generate_bill_number())
        label_ptype_entry.set("Select mode")
        
    except mysql.connector.Error as e:
        messagebox.showerror("Database Error", f"An error occurred: {str(e)}")

def calculate_total():
    total = sum(prices[item] * details['qty'] for item, details in ordered_items.items())
    label_bill_entry.delete(0, tkinter.END)
    label_bill_entry.insert(0, f"${total:.2f}")



frame1 = ttk.Frame(window, padding=20)
frame1.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

# Date Label and Entry
label_date = ttk.Label(frame1, text="Date:", padding=(10, 10))
label_date_entry = ttk.Entry(frame1, width=25)
label_date.grid(row=0, column=0, sticky="w", pady=5)
label_date_entry.grid(row=0, column=1, padx=10, pady=5, sticky="w")

# Time Label and Entry
label_time = ttk.Label(frame1, text="Time:", padding=(10, 10))
label_time_entry = ttk.Entry(frame1, width=25)
label_time.grid(row=1, column=0, sticky="w", pady=5)
label_time_entry.grid(row=1, column=1, padx=10, pady=5, sticky="w")

# Bill Number Label and Entry
label_bill_num = ttk.Label(frame1, text="Bill Number:", padding=(10, 10))
label_bill_num_entry = ttk.Entry(frame1, width=25)
label_bill_num.grid(row=2, column=0, sticky="w", pady=5)
label_bill_num_entry.grid(row=2, column=1, padx=10, pady=5, sticky="w")
label_bill_num_entry.insert(0, generate_bill_number())

# Menu Label and Listbox
label_menu = ttk.Label(frame1, text="Menu:", padding=(10, 10))
listvar = tkinter.StringVar(value=list(prices.keys()))
label_menu_listbox = tkinter.Listbox(frame1, listvariable=listvar, height=5, 
                                width=25, selectmode='single', bg="#f0f0f0", bd=1)
label_menu_listbox.bind('<<ListboxSelect>>', handle_item_click)
label_menu.grid(row=3, column=0, sticky="w", pady=5)
label_menu_listbox.grid(row=3, column=1, padx=10, pady=5, sticky="w")

# Items Ordered Label and Display
label_items_order = ttk.Label(frame1, text="Items Ordered:", padding=(10, 10))
label_items_ordered_label = ttk.Label(frame1, width=30, relief="sunken", anchor="nw", justify="left", background="#e6e6e6")
label_items_order.grid(row=4, column=0, sticky="nw", pady=5)
label_items_ordered_label.grid(row=4, column=1, padx=10, pady=5, sticky="w")

# Button Section
frame3 = ttk.Frame(frame1, padding=10)
frame3.grid(row=5, column=1, sticky="ew", pady=10)

button_delete = ttk.Button(frame3, text="Delete", command=delete_items)
button_order = ttk.Button(frame3, text="Order", 
                          command=lambda: [calculate_total(), save_order_to_database()])
button_graph = ttk.Button(frame3, text="Show Sales Graph", 
                          command=lambda: show_sales_graph(None))
button_delete.grid(row=0, column=0, padx=10, pady=5)
button_order.grid(row=0, column=1, padx=10, pady=5)
button_graph.grid(row=0, column=2, padx=10, pady=5)

button_db_viewer = ttk.Button(frame3, text="View Database", command=show_database_viewer)
button_db_viewer.grid(row=1, column=0, padx=10, pady=5)

# Total Bill Section
label_bill = ttk.Label(frame1, text="Total Bill:", padding=(10, 10))
label_bill_entry = ttk.Entry(frame1, width=25)
label_bill.grid(row=6, column=0, sticky="w", pady=5)
label_bill_entry.grid(row=6, column=1, padx=10, pady=5, sticky="w")

# Payment Type Section
label_ptype = ttk.Label(frame1, text="Payment:", padding=(10, 10))
label_ptype_entry = ttk.Combobox(frame1, values=["UPI", "Cash", "Card"], width=22, state="readonly")
label_ptype_entry.set("Select mode")
label_ptype.grid(row=7, column=0, sticky="w", pady=5)
label_ptype_entry.grid(row=7, column=1, padx=10, pady=5, sticky="w")

# Filter Button
button_filter = ttk.Button(frame3, text="Filter Data", command=show_filtered_data)
button_filter.grid(row=1, column=1, padx=10, pady=5)

button_total_sales = ttk.Button(frame3, text="Total Sales", command=get_total_sales)
button_monthly_sales = ttk.Button(frame3, text="Monthly Sales", command=get_monthly_sales)

button_total_sales.grid(row=1, column=2, padx=10, pady=5)
button_monthly_sales.grid(row=2, column=0, padx=10, pady=5)

button_audit_logs = ttk.Button(frame3, text="View Audit Logs", command=show_audit_logs)
button_audit_logs.grid(row=2, column=2, padx=10, pady=5)



# Pre-fill Date and Time Entries
label_date_entry.insert(0, get_current_date())  
label_time_entry.insert(0, get_current_time())


window.mainloop()
