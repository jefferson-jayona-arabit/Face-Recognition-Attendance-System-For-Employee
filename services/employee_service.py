from db.connection import get_connection


def get_all_departments():
    """Fetch all departments for the dropdown."""
    conn = get_connection()
    if not conn:
        return []
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT id, name FROM departments ORDER BY name")
        return cursor.fetchall()
    except Exception as e:
        print(f"[employee_service] get_all_departments error: {e}")
        return []
    finally:
        conn.close()


def add_employee(employee_no, first_name, last_name, department_id, position):
    """Insert a new employee. Returns the new employee's ID or None on failure."""
    conn = get_connection()
    if not conn:
        return None
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO employees (employee_no, first_name, last_name, department_id, position)
            VALUES (%s, %s, %s, %s, %s)
        """, (employee_no, first_name, last_name, department_id, position))
        conn.commit()
        return cursor.lastrowid
    except Exception as e:
        print(f"[employee_service] add_employee error: {e}")
        conn.rollback()
        return None
    finally:
        conn.close()


def get_all_employees():
    """Fetch all employees with their department name."""
    conn = get_connection()
    if not conn:
        return []
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT e.id, e.employee_no, e.first_name, e.last_name,
                   d.name AS department, e.position, e.status, e.created_at
            FROM employees e
            LEFT JOIN departments d ON e.department_id = d.id
            ORDER BY e.created_at DESC
        """)
        return cursor.fetchall()
    except Exception as e:
        print(f"[employee_service] get_all_employees error: {e}")
        return []
    finally:
        conn.close()


def get_employee_by_id(employee_id):
    """Fetch a single employee by ID."""
    conn = get_connection()
    if not conn:
        return None
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT e.*, d.name AS department_name
            FROM employees e
            LEFT JOIN departments d ON e.department_id = d.id
            WHERE e.id = %s
        """, (employee_id,))
        return cursor.fetchone()
    except Exception as e:
        print(f"[employee_service] get_employee_by_id error: {e}")
        return None
    finally:
        conn.close()


def update_employee(employee_id, employee_no, first_name, last_name, department_id, position, status):
    """Update an existing employee record."""
    conn = get_connection()
    if not conn:
        return False
    try:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE employees
            SET employee_no = %s, first_name = %s, last_name = %s,
                department_id = %s, position = %s, status = %s
            WHERE id = %s
        """, (employee_no, first_name, last_name, department_id, position, status, employee_id))
        conn.commit()
        return True
    except Exception as e:
        print(f"[employee_service] update_employee error: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()


def delete_employee(employee_id):
    """Delete an employee and their face encodings (cascade)."""
    conn = get_connection()
    if not conn:
        return False
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM employees WHERE id = %s", (employee_id,))
        conn.commit()
        return True
    except Exception as e:
        print(f"[employee_service] delete_employee error: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()


def employee_no_exists(employee_no, exclude_id=None):
    """Check if an employee number is already taken."""
    conn = get_connection()
    if not conn:
        return False
    try:
        cursor = conn.cursor()
        if exclude_id:
            cursor.execute(
                "SELECT id FROM employees WHERE employee_no = %s AND id != %s",
                (employee_no, exclude_id)
            )
        else:
            cursor.execute(
                "SELECT id FROM employees WHERE employee_no = %s",
                (employee_no,)
            )
        return cursor.fetchone() is not None
    except Exception as e:
        print(f"[employee_service] employee_no_exists error: {e}")
        return False
    finally:
        conn.close()


def has_face_encoding(employee_id):
    """Check if an employee already has a face encoding saved."""
    conn = get_connection()
    if not conn:
        return False
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id FROM face_encodings WHERE employee_id = %s",
            (employee_id,)
        )
        return cursor.fetchone() is not None
    except Exception as e:
        print(f"[employee_service] has_face_encoding error: {e}")
        return False
    finally:
        conn.close()