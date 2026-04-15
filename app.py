from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import mysql.connector
from datetime import datetime
import logging
import os
import re

# Load .env file for local development (ignored on Railway)
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create Flask app
app = Flask(__name__)
CORS(app)

# ============================================
# RAILWAY / PRODUCTION CONFIGURATION
# ============================================

PORT = int(os.environ.get('PORT', 8080))

# Print all env vars for debugging (masks password)
print("=" * 50)
print("🔍 Environment Variables Detected:")
print(f"   MYSQL_URL:    {'SET ✅' if os.environ.get('MYSQL_URL') else 'NOT SET ❌'}")
print(f"   DATABASE_URL: {'SET ✅' if os.environ.get('DATABASE_URL') else 'NOT SET ❌'}")
print(f"   DB_HOST:      {os.environ.get('DB_HOST', 'NOT SET')}")
print(f"   DB_PORT:      {os.environ.get('DB_PORT', 'NOT SET')}")
print(f"   DB_USER:      {os.environ.get('DB_USER', 'NOT SET')}")
print(f"   DB_NAME:      {os.environ.get('DB_NAME', 'NOT SET')}")
print(f"   DB_PASSWORD:  {'SET ✅' if os.environ.get('DB_PASSWORD') or os.environ.get('Password') else 'NOT SET ❌'}")
print("=" * 50)

# Priority 1: MYSQL_URL or DATABASE_URL (full connection string)
DATABASE_URL = os.environ.get('MYSQL_URL') or os.environ.get('DATABASE_URL') or ''

if DATABASE_URL:
    match = re.match(r'mysql://([^:]+):([^@]+)@([^:]+):(\d+)/(.+)', DATABASE_URL)
    if match:
        DB_CONFIG = {
            'host': match.group(3),
            'port': int(match.group(4)),
            'user': match.group(1),
            'password': match.group(2),
            'database': match.group(5)
        }
        print(f"✅ Using MYSQL_URL → {match.group(3)}:{match.group(4)}/{match.group(5)}")
    else:
        print(f"❌ MYSQL_URL found but could not be parsed: {DATABASE_URL[:30]}...")
        DATABASE_URL = ''  # Force fallback

# Priority 2: Individual DB_* environment variables
if not DATABASE_URL:
    db_host = os.environ.get('DB_HOST')
    db_port = os.environ.get('DB_PORT')
    db_user = os.environ.get('DB_USER')
    db_name = os.environ.get('DB_NAME')
    # Support both 'DB_PASSWORD' and 'Password' variable names
    db_password = os.environ.get('DB_PASSWORD') or os.environ.get('Password') or ''

    if db_host and db_user and db_name:
        DB_CONFIG = {
            'host': db_host,
            'port': int(db_port) if db_port else 3306,
            'user': db_user,
            'password': db_password,
            'database': db_name
        }
        print(f"✅ Using individual DB vars → {db_host}/{db_name}")

    else:
        # Priority 3: Local development fallback
        DB_CONFIG = {
            'host': 'localhost',
            'port': 3306,
            'user': 'root',
            'password': '',
            'database': 'queue_management_system'
        }
        print("⚠️  No DB config found in environment — using LOCAL database config")

# ============================================
# SERVE HTML PAGES
# ============================================

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/<path:filename>')
def serve_static(filename):
    return send_from_directory('.', filename)

# ============================================
# DATABASE FUNCTIONS
# ============================================

def get_db_connection():
    """Create a FRESH database connection each time"""
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        return conn
    except Exception as e:
        print(f"❌ Database connection error: {e}")
        raise e

def execute_query(query, params=None, fetch_one=False, fetch_all=False, commit=False):
    """Execute SQL query with fresh connection"""
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute(query, params or ())

        if fetch_one:
            result = cursor.fetchone()
        elif fetch_all:
            result = cursor.fetchall()
        else:
            result = None

        if commit:
            conn.commit()
            result = cursor.lastrowid

        return result
    except Exception as e:
        if conn and commit:
            conn.rollback()
        print(f"❌ Query error: {e}")
        raise e
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

# ============================================
# HEALTH CHECK
# ============================================

@app.route('/api/health', methods=['GET'])
def health_check():
    """Check if API and database are running"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        cursor.close()
        conn.close()
        db_status = "connected"
    except Exception as e:
        print(f"Health check DB error: {e}")
        db_status = f"disconnected: {str(e)}"

    return jsonify({
        'status': 'ok',
        'database': db_status,
        'db_host': DB_CONFIG.get('host'),
        'db_name': DB_CONFIG.get('database'),
        'timestamp': datetime.now().isoformat()
    })

# ============================================
# TOKEN GENERATION
# ============================================

@app.route('/api/tokens', methods=['POST'])
def generate_token():
    data = request.get_json()

    service_category = data.get('service_category')
    customer_name = data.get('customer_name')
    customer_phone = data.get('customer_phone')
    source = data.get('source', 'form')

    if not service_category:
        return jsonify({'success': False, 'message': 'Service category is required'}), 400

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute("""
            SELECT category_name, estimated_service_time, prefix, next_number
            FROM service_categories 
            WHERE category_code = %s AND is_active = 1
        """, (service_category,))

        service = cursor.fetchone()

        if not service:
            return jsonify({'success': False, 'message': 'Invalid service category'}), 400

        next_num = service['next_number']
        token_number = f"{service['prefix']}{str(next_num).zfill(3)}"

        cursor.execute("""
            UPDATE service_categories 
            SET next_number = next_number + 1
            WHERE category_code = %s
        """, (service_category,))

        cursor.execute("""
            SELECT COUNT(*) as ahead_count
            FROM queue_tokens
            WHERE service_category = %s
            AND status IN ('waiting', 'called')
        """, (service_category,))

        ahead = cursor.fetchone()
        ahead_count = ahead['ahead_count'] if ahead else 0
        estimated_wait = ahead_count * service['estimated_service_time']
        queue_position = ahead_count + 1

        cursor.execute("""
            INSERT INTO queue_tokens (
                token_number, service_category, customer_name, customer_phone, 
                status, queue_position, estimated_wait_minutes, source, requested_at
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NOW())
        """, (
            token_number, service_category, customer_name,
            customer_phone, 'waiting', queue_position, estimated_wait, source
        ))

        conn.commit()

        return jsonify({
            'success': True,
            'token_number': token_number,
            'service_name': service['category_name'],
            'queue_position': queue_position,
            'ahead_count': ahead_count,
            'estimated_wait': estimated_wait,
            'message': 'Token generated successfully'
        })

    except Exception as e:
        conn.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        cursor.close()
        conn.close()

# ============================================
# GET QUEUE POSITION
# ============================================

@app.route('/api/queue/position/<token_number>', methods=['GET'])
def get_queue_position(token_number):
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
            SELECT q.*, t.teller_number as assigned_teller
            FROM queue_tokens q
            LEFT JOIN tellers t ON q.assigned_teller_id = t.id
            WHERE q.token_number = %s
        """, (token_number,))

        token = cursor.fetchone()

        if not token:
            return jsonify({'success': False, 'message': 'Token not found'}), 404

        cursor.execute("""
            SELECT COUNT(*) as ahead_count
            FROM queue_tokens
            WHERE service_category = %s
            AND status IN ('waiting', 'called')
            AND requested_at < %s
        """, (token['service_category'], token['requested_at']))

        ahead = cursor.fetchone()
        ahead_count = ahead['ahead_count'] if ahead else 0

        cursor.close()
        conn.close()

        return jsonify({
            'success': True,
            'token_number': token['token_number'],
            'status': token['status'],
            'queue_position': ahead_count + 1,
            'ahead_count': ahead_count
        })

    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

# ============================================
# GET CURRENT QUEUE STATUS
# ============================================

@app.route('/api/queue/current', methods=['GET'])
def get_current_queue():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
            SELECT 
                sc.category_code,
                sc.category_name,
                COUNT(CASE WHEN q.status = 'waiting' THEN 1 END) as waiting_count,
                COUNT(CASE WHEN q.status = 'called' THEN 1 END) as called_count,
                COUNT(CASE WHEN q.status = 'serving' THEN 1 END) as serving_count
            FROM service_categories sc
            LEFT JOIN queue_tokens q ON q.service_category = sc.category_code
            WHERE sc.is_active = 1
            GROUP BY sc.category_code, sc.category_name
            ORDER BY sc.display_order
        """)

        queue_data = cursor.fetchall()
        cursor.close()
        conn.close()

        return jsonify({
            'success': True,
            'queue': queue_data,
            'timestamp': datetime.now().isoformat()
        })

    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

# ============================================
# GET WAITING LIST FOR SERVICE
# ============================================

@app.route('/api/queue/waiting-list/<service_category>', methods=['GET'])
def get_waiting_list(service_category):
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
            SELECT 
                token_number,
                customer_name,
                customer_phone,
                requested_at,
                TIMESTAMPDIFF(MINUTE, requested_at, NOW()) as waiting_minutes
            FROM queue_tokens
            WHERE service_category = %s
            AND status = 'waiting'
            ORDER BY requested_at ASC
        """, (service_category,))

        waiting_tokens = cursor.fetchall()
        cursor.close()
        conn.close()

        return jsonify({
            'success': True,
            'waiting_tokens': waiting_tokens,
            'count': len(waiting_tokens)
        })

    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

# ============================================
# GET ALL TELLERS
# ============================================

@app.route('/api/tellers', methods=['GET'])
def get_tellers():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
            SELECT 
                id, teller_number, teller_name, status,
                current_token, serving_category,
                TIMESTAMPDIFF(MINUTE, last_activity, NOW()) as idle_minutes
            FROM tellers
            ORDER BY teller_number
        """)

        tellers = cursor.fetchall()
        cursor.close()
        conn.close()

        return jsonify({
            'success': True,
            'tellers': tellers
        })

    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

# ============================================
# TELLER LOGIN
# ============================================

@app.route('/api/tellers/login', methods=['POST'])
def teller_login():
    data = request.get_json()

    teller_number = data.get('teller_number')
    pin_code = data.get('pin_code')

    if not teller_number or not pin_code:
        return jsonify({'success': False, 'message': 'Teller number and PIN required'}), 400

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute("""
            SELECT id, teller_number, teller_name, serving_category, status
            FROM tellers
            WHERE teller_number = %s AND pin_code = %s
        """, (teller_number, pin_code))

        teller = cursor.fetchone()

        if teller:
            return jsonify({
                'success': True,
                'teller': teller,
                'message': 'Login successful'
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Invalid teller number or PIN'
            }), 401

    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        cursor.close()
        conn.close()

# ============================================
# TELLER: CALL SPECIFIC CUSTOMER
# ============================================

@app.route('/api/tellers/call-specific', methods=['POST'])
def call_specific_customer():
    data = request.get_json()

    teller_id = data.get('teller_id')
    teller_number = data.get('teller_number')
    token_number = data.get('token_number')

    if not all([teller_id, teller_number, token_number]):
        return jsonify({'success': False, 'message': 'Missing required fields'}), 400

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute("""
            SELECT id, token_number, customer_name
            FROM queue_tokens
            WHERE token_number = %s AND status = 'waiting'
        """, (token_number,))

        token = cursor.fetchone()

        if not token:
            return jsonify({'success': False, 'message': 'Token not found or already called'}), 404

        cursor.execute("""
            UPDATE queue_tokens 
            SET status = 'called', 
                called_at = NOW(),
                assigned_teller_id = %s,
                assigned_teller_number = %s
            WHERE id = %s
        """, (teller_id, teller_number, token['id']))

        cursor.execute("""
            UPDATE tellers 
            SET status = 'called',
                current_token = %s,
                last_activity = NOW()
            WHERE id = %s
        """, (token_number, teller_id))

        conn.commit()

        return jsonify({
            'success': True,
            'token_number': token_number,
            'teller_number': teller_number,
            'message': f"Customer {token_number} has been called"
        })

    except Exception as e:
        conn.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        cursor.close()
        conn.close()

# ============================================
# TELLER: SERVE CUSTOMER
# ============================================

@app.route('/api/tellers/serve', methods=['POST'])
def serve_customer():
    data = request.get_json()

    teller_id = data.get('teller_id')
    token_number = data.get('token_number')

    if not all([teller_id, token_number]):
        return jsonify({'success': False, 'message': 'Missing required fields'}), 400

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute("""
            UPDATE queue_tokens 
            SET status = 'serving', 
                serving_started_at = NOW()
            WHERE token_number = %s
        """, (token_number,))

        cursor.execute("""
            UPDATE tellers 
            SET status = 'busy',
                last_activity = NOW()
            WHERE id = %s
        """, (teller_id,))

        conn.commit()

        return jsonify({
            'success': True,
            'token_number': token_number,
            'message': f"Customer {token_number} is now being served"
        })

    except Exception as e:
        conn.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        cursor.close()
        conn.close()

# ============================================
# TELLER: COMPLETE SERVICE
# ============================================

@app.route('/api/tellers/complete', methods=['POST'])
def complete_service():
    data = request.get_json()

    teller_id = data.get('teller_id')
    token_number = data.get('token_number')

    if not all([teller_id, token_number]):
        return jsonify({'success': False, 'message': 'Missing required fields'}), 400

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute("""
            UPDATE queue_tokens 
            SET status = 'completed', 
                completed_at = NOW()
            WHERE token_number = %s
        """, (token_number,))

        cursor.execute("""
            UPDATE tellers 
            SET status = 'available',
                current_token = NULL,
                last_activity = NOW()
            WHERE id = %s
        """, (teller_id,))

        conn.commit()

        return jsonify({
            'success': True,
            'token_number': token_number,
            'message': f"Service completed for {token_number}"
        })

    except Exception as e:
        conn.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        cursor.close()
        conn.close()

# ============================================
# TELLER: SKIP CUSTOMER
# ============================================

@app.route('/api/tellers/skip', methods=['POST'])
def skip_customer():
    data = request.get_json()

    teller_id = data.get('teller_id')
    token_number = data.get('token_number')

    if not all([teller_id, token_number]):
        return jsonify({'success': False, 'message': 'Missing required fields'}), 400

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute("""
            UPDATE queue_tokens 
            SET status = 'skipped', 
                skipped_at = NOW()
            WHERE token_number = %s
        """, (token_number,))

        cursor.execute("""
            UPDATE tellers 
            SET status = 'available',
                current_token = NULL,
                last_activity = NOW()
            WHERE id = %s
        """, (teller_id,))

        conn.commit()

        return jsonify({
            'success': True,
            'token_number': token_number,
            'message': f"Customer {token_number} has been skipped"
        })

    except Exception as e:
        conn.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        cursor.close()
        conn.close()

# ============================================
# TELLER: RECALL CUSTOMER
# ============================================

@app.route('/api/tellers/recall', methods=['POST'])
def recall_customer():
    data = request.get_json()

    teller_id = data.get('teller_id')
    token_number = data.get('token_number')

    if not all([teller_id, token_number]):
        return jsonify({'success': False, 'message': 'Missing required fields'}), 400

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute("""
            SELECT q.status, q.token_number, t.teller_number
            FROM queue_tokens q
            LEFT JOIN tellers t ON q.assigned_teller_id = t.id
            WHERE q.token_number = %s
        """, (token_number,))

        token = cursor.fetchone()

        if not token:
            return jsonify({'success': False, 'message': 'Token not found'}), 404

        cursor.execute("""
            INSERT INTO queue_logs (token_number, teller_id, action, action_details, created_at)
            VALUES (%s, %s, 'recall', 'Recall announcement requested', NOW())
        """, (token_number, teller_id))

        conn.commit()

        return jsonify({
            'success': True,
            'token_number': token_number,
            'teller_number': token.get('teller_number'),
            'status': token['status'],
            'message': f"Recall announcement for {token_number}"
        })

    except Exception as e:
        conn.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        cursor.close()
        conn.close()

# ============================================
# GET RECENT RECALLS
# ============================================

@app.route('/api/queue/recent-recalls', methods=['GET'])
def get_recent_recalls():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
            SELECT token_number, teller_id, created_at
            FROM queue_logs
            WHERE action = 'recall'
            AND created_at > DATE_SUB(NOW(), INTERVAL 10 SECOND)
            ORDER BY created_at DESC
            LIMIT 5
        """)

        recalls = cursor.fetchall()
        cursor.close()
        conn.close()

        return jsonify({
            'success': True,
            'recalls': recalls
        })

    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

# ============================================
# TELLER MANAGEMENT
# ============================================

@app.route('/api/tellers', methods=['POST'])
def add_teller():
    data = request.get_json()

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute("""
            INSERT INTO tellers (teller_number, teller_name, email, phone, serving_category, pin_code, status)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (data['teller_number'], data['teller_name'], data.get('email'),
              data.get('phone'), data['serving_category'], data.get('pin_code', '1234'), 'available'))
        conn.commit()

        return jsonify({'success': True, 'message': 'Teller added successfully'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/api/tellers/<int:teller_id>', methods=['PUT'])
def update_teller(teller_id):
    data = request.get_json()

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute("""
            UPDATE tellers 
            SET teller_number = %s, teller_name = %s, email = %s, phone = %s, serving_category = %s
            WHERE id = %s
        """, (data['teller_number'], data['teller_name'], data.get('email'),
              data.get('phone'), data['serving_category'], teller_id))
        conn.commit()

        return jsonify({'success': True, 'message': 'Teller updated successfully'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/api/tellers/<int:teller_id>', methods=['DELETE'])
def delete_teller(teller_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute("DELETE FROM tellers WHERE id = %s", (teller_id,))
        conn.commit()

        return jsonify({'success': True, 'message': 'Teller deleted successfully'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/api/tellers/<int:teller_id>/reset-pin', methods=['POST'])
def reset_teller_pin(teller_id):
    data = request.get_json()

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute("UPDATE tellers SET pin_code = %s WHERE id = %s",
                       (data['pin_code'], teller_id))
        conn.commit()

        return jsonify({'success': True, 'message': 'PIN reset successfully'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        cursor.close()
        conn.close()

# ============================================
# RUN THE APPLICATION
# ============================================

if __name__ == '__main__':
    PORT = int(os.environ.get('PORT', 8080))

    print("=" * 50)
    print("🚀 Queue Management System API (Flask)")
    print("=" * 50)
    print(f"📍 Running on port: {PORT}")
    print(f"🗄️  DB Host: {DB_CONFIG.get('host')}")
    print(f"🗄️  DB Name: {DB_CONFIG.get('database')}")
    print(f"🗄️  DB User: {DB_CONFIG.get('user')}")
    print("=" * 50)

    app.run(host='0.0.0.0', port=PORT, debug=False)
