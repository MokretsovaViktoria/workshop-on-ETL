import mysql.connector
from mysql.connector import Error
import pandas as pd
import random
from datetime import datetime, timedelta
import os
import logging
from dotenv import load_dotenv
import matplotlib.pyplot as plt

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename='logistics_etl.log'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'user': os.getenv('DB_USER', 'root'),
    'password': os.getenv('DB_PASSWORD', ''),
    'database': os.getenv('DB_NAME', 'logistics_db')
}

def test_mysql_connection():
    """Test MySQL server connection"""
    try:
        conn = mysql.connector.connect(
            host=DB_CONFIG['host'],
            user=DB_CONFIG['user'],
            password=DB_CONFIG['password']
        )
        if conn.is_connected():
            logger.info("Successfully connected to MySQL server")
            conn.close()
            return True
    except Error as e:
        logger.error(f"MySQL Connection Error: {e}")
        print(f"\nError connecting to MySQL: {e}")
        print("Troubleshooting steps:")
        print("1. Make sure MySQL server is running: sudo systemctl status mysql")
        print("2. Verify your credentials in .env file")
        print("3. Try connecting manually: mysql -u root -p")
        return False

def ensure_database_exists():
    """Ensure database and tables exist"""
    try:
        conn = mysql.connector.connect(
            host=DB_CONFIG['host'],
            user=DB_CONFIG['user'],
            password=DB_CONFIG['password']
        )
        cursor = conn.cursor()
        
        # Create database if not exists
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DB_CONFIG['database']}")
        cursor.execute(f"USE {DB_CONFIG['database']}")
        
        # Check if tables exist
        cursor.execute("SHOW TABLES LIKE 'shipments'")
        if not cursor.fetchone():
            create_test_data(conn)
        else:
            logger.info("Database and tables already exist")
            
        conn.close()
        return True
        
    except Error as e:
        logger.error(f"Database creation error: {e}")
        print(f"Error creating database: {e}")
        return False

def create_test_data(conn):
    """Generate test data in MySQL database"""
    try:
        cursor = conn.cursor()
        
        # Create tables
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS shipments (
            shipment_id VARCHAR(20) PRIMARY KEY,
            vehicle_id VARCHAR(20),
            route_id VARCHAR(20),
            distance_km DECIMAL(10,2),
            shipment_date DATE,
            fuel_type VARCHAR(20),
            driver_id VARCHAR(20),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )""")
        
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS fuel_costs (
            fuel_type VARCHAR(20) PRIMARY KEY,
            price_per_liter DECIMAL(10,2),
            effective_date DATE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )""")
        
        # Generate sample shipments
        vehicles = [f'TRUCK-{i:02d}' for i in range(1, 6)]
        drivers = [f'DRIVER-{i:03d}' for i in range(1, 11)]
        fuel_types = ['diesel', 'gasoline', 'LNG']
        routes = [f'ROUTE-{i:03d}' for i in range(1, 21)]
        
        for i in range(1, 101):
            cursor.execute(
                "INSERT INTO shipments (shipment_id, vehicle_id, route_id, distance_km, shipment_date, fuel_type, driver_id) "
                "VALUES (%s, %s, %s, %s, %s, %s, %s)",
                (
                    f"SH{1000+i}",
                    random.choice(vehicles),
                    random.choice(routes),
                    round(random.uniform(50, 500), 1),
                    (datetime.now() - timedelta(days=random.randint(1, 30))).strftime('%Y-%m-%d'),
                    random.choice(fuel_types),
                    random.choice(drivers)
                )
            )
        
        # Generate fuel costs
        for fuel in fuel_types:
            cursor.execute(
                "INSERT INTO fuel_costs (fuel_type, price_per_liter, effective_date) "
                "VALUES (%s, %s, %s)",
                (
                    fuel,
                    round({'diesel': 1.80, 'gasoline': 2.10, 'LNG': 1.20}[fuel] * random.uniform(0.9, 1.1), 2),
                    (datetime.now() - timedelta(days=10)).strftime('%Y-%m-%d')
                )
            )
        
        conn.commit()
        logger.info("Test data generated successfully")
        
        # Generate route data CSV
        shipments = pd.read_sql("SELECT shipment_id, distance_km FROM shipments", conn)
        route_data = [{
            'shipment_id': row['shipment_id'],
            'fuel_consumed': round(row['distance_km'] * random.uniform(0.3, 0.5), 1),
            'actual_duration': round(random.uniform(2, 8), 1),
            'notes': random.choice(['On time', 'Delayed', 'Early arrival'])
        } for _, row in shipments.iterrows()]
        
        pd.DataFrame(route_data).to_csv('route_data.csv', index=False)
        logger.info("Route data CSV generated")
        
    except Error as e:
        logger.error(f"Error generating test data: {e}")
        raise

def extract_data():
    """Extract data from MySQL and CSV"""
    logger.info("Extracting data from sources")
    
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        
        # Extract shipments data
        shipments = pd.read_sql("SELECT * FROM shipments", conn)
        
        # Extract fuel costs
        fuel_costs = pd.read_sql("SELECT * FROM fuel_costs", conn)
        
        # Extract route data from CSV
        try:
            route_data = pd.read_csv('route_data.csv')
        except FileNotFoundError:
            logger.warning("Route data CSV not found, generating estimates")
            route_data = pd.DataFrame({
                'shipment_id': shipments['shipment_id'],
                'fuel_consumed': shipments['distance_km'] * random.uniform(0.3, 0.5)
            })
        
        return shipments, fuel_costs, route_data
        
    except Error as e:
        logger.error(f"Data extraction failed: {e}")
        raise
    finally:
        if conn.is_connected():
            conn.close()

def transform_data(shipments, fuel_costs, route_data):
    """Clean and transform data"""
    logger.info("Transforming data")
    
    try:
        # Data validation
        if shipments.empty:
            raise ValueError("No shipment data available")
        
        # Data cleaning
        shipments['shipment_date'] = pd.to_datetime(shipments['shipment_date'])
        shipments['distance_km'] = shipments['distance_km'].fillna(0)
        
        fuel_costs = fuel_costs.dropna(subset=['price_per_liter'])
        fuel_costs['price_per_liter'] = fuel_costs['price_per_liter'].astype(float)
        
        route_data['fuel_consumed'] = pd.to_numeric(route_data['fuel_consumed'], errors='coerce')
        route_data = route_data.dropna(subset=['fuel_consumed'])
        
        # Merge data
        merged = pd.merge(shipments, route_data, on='shipment_id')
        merged = pd.merge(merged, fuel_costs, on='fuel_type')
        
        # Calculate metrics
        merged['fuel_cost'] = merged['fuel_consumed'] * merged['price_per_liter']
        merged['cost_per_km'] = merged['fuel_cost'] / merged['distance_km']
        merged['efficiency'] = merged['distance_km'] / merged['fuel_consumed']
        
        logger.info(f"Data transformation complete. {len(merged)} records processed")
        return merged
        
    except Exception as e:
        logger.error(f"Data transformation failed: {e}")
        raise

def load_data(merged_df):
    """Save results to files"""
    logger.info("Loading results")
    
    try:
        os.makedirs('results', exist_ok=True)
        
        # Save merged data
        merged_df.to_csv('results/merged_logistics.csv', index=False)
        
        # Save analysis reports
        with pd.ExcelWriter('results/logistics_analysis.xlsx') as writer:
            # All data
            merged_df.to_excel(writer, sheet_name='All Data', index=False)
            
            # Route analysis
            route_stats = merged_df.groupby('route_id').agg({
                'fuel_cost': 'sum',
                'distance_km': 'mean',
                'efficiency': 'mean'
            }).sort_values('fuel_cost', ascending=False)
            route_stats.to_excel(writer, sheet_name='Route Analysis')
            
            # Driver performance
            driver_stats = merged_df.groupby('driver_id').agg({
                'fuel_cost': 'mean',
                'efficiency': 'mean'
            }).sort_values('efficiency', ascending=False)
            driver_stats.to_excel(writer, sheet_name='Driver Performance')
            
            # Weekly trends
            merged_df['week'] = merged_df['shipment_date'].dt.isocalendar().week
            weekly_stats = merged_df.groupby('week')['fuel_cost'].sum()
            weekly_stats.to_excel(writer, sheet_name='Weekly Trends')
        
        # Create visualizations
        plt.figure(figsize=(10, 6))
        merged_df.groupby('fuel_type')['efficiency'].mean().plot(kind='bar')
        plt.title('Fuel Efficiency by Type')
        plt.ylabel('km per liter')
        plt.savefig('results/fuel_efficiency.png')
        plt.close()
        
        logger.info("Results saved successfully")
        
    except Exception as e:
        logger.error(f"Failed to save results: {e}")
        raise

def generate_report():
    """Generate final analysis report"""
    logger.info("Generating final report")
    
    try:
        merged = pd.read_csv('results/merged_logistics.csv')
        
        # Calculate statistics
        stats = {
            'total_shipments': len(merged),
            'total_fuel_cost': merged['fuel_cost'].sum(),
            'avg_efficiency': merged['efficiency'].mean(),
            'most_expensive_route': merged.groupby('route_id')['fuel_cost'].sum().idxmax(),
            'most_efficient_driver': merged.groupby('driver_id')['efficiency'].mean().idxmax(),
            'data_quality': {
                'missing_values': merged.isnull().sum().to_dict(),
                'duplicates': merged.duplicated().sum()
            }
        }
        
        # Generate report text
        report = f"""
        Logistics Data Integration Report
        ================================
        
        1. Summary Statistics:
        - Total shipments processed: {stats['total_shipments']}
        - Total fuel costs: ${stats['total_fuel_cost']:,.2f}
        - Average efficiency: {stats['avg_efficiency']:.2f} km/l
        
        2. Optimization Opportunities:
        - Most expensive route: {stats['most_expensive_route']}
        - Most efficient driver: {stats['most_efficient_driver']}
        
        3. Data Quality:
        - Missing values: {stats['data_quality']['missing_values']}
        - Duplicate records: {stats['data_quality']['duplicates']}
        """
        
        # Save report
        with open('results/final_report.txt', 'w') as f:
            f.write(report)
        
        logger.info("Report generated successfully")
        return stats
        
    except Exception as e:
        logger.error(f"Report generation failed: {e}")
        raise

def main():
    """Main ETL workflow"""
    try:
        logger.info("Starting logistics data integration")
        
        # Verify MySQL connection
        if not test_mysql_connection():
            print("Cannot connect to MySQL server. Check the logs for details.")
            return
        
        # Ensure database exists
        if not ensure_database_exists():
            print("Failed to initialize database")
            return
        
        # ETL Process
        print("Extracting data...")
        shipments, fuel_costs, route_data = extract_data()
        
        print("Transforming data...")
        merged_data = transform_data(shipments, fuel_costs, route_data)
        
        print("Saving results...")
        load_data(merged_data)
        
        print("Generating report...")
        stats = generate_report()
        
        print("\nETL process completed successfully!")
        print(f"Processed {stats['total_shipments']} shipments")
        print(f"Total fuel costs: ${stats['total_fuel_cost']:,.2f}")
        print(f"Results saved in 'results' directory")
        
    except Exception as e:
        logger.error(f"Process failed: {e}")
        print(f"Error: {e}")

if __name__ == "__main__":
    main()