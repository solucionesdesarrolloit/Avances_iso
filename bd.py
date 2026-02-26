import psycopg2

config = {
    'host': 'localhost',
    'port': 5432,
    'dbname': 'avances_iso',
    'user': 'postgres',
    'password': '1234'
}

try:
    conexion = psycopg2.connect(**config)
    print("✅ Conexión exitosa")
    conexion.close()
except Exception as e:
    print(f"❌ Error: {e}")