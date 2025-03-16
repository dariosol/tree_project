## 🌳 **Tree Management System**

A web-based system for managing and tracking urban trees. This app allows users to:
- **Add Trees** with details such as location (via GPS or address), species, and condition.
- **View Trees** in a searchable table and on a map (using Leaflet).
- **Edit Trees** to update the tree's condition and comments.
- **Delete Trees** by their custom ID.
- **Search** using a city name and a partial address.

---

## 📂 **Project Structure**
```
tree_project/
├── flaskenv/              # Virtual environment (optional)
├── app.py                 # Flask backend (API)
├── frontend/              # Frontend (HTML, JS, CSS)
│   ├── index.html         # Main webpage
│   └── app.js             # Frontend logic (fetch API calls, map)
└── requirements.txt       # Python package dependencies
```

---

## 🧰 **Prerequisites**
Ensure you have the following installed:
- Python (≥ 3.10)
- PostgreSQL (with PostGIS extension)
- Virtual environment tools (`venv`)

---

## 🚀 **Setup and Run Instructions**

### 1️⃣ **Clone the Repository**
```bash
git clone <your-repo-url>
cd tree_project
```

---

### 2️⃣ **Set Up the Virtual Environment**
Create and activate a virtual environment (recommended):

```bash
python3 -m venv flaskenv
source flaskenv/bin/activate
```

---

### 3️⃣ **Install Dependencies**
```bash
pip install -r requirements.txt
```

If `requirements.txt` is missing, install the needed packages manually:
```bash
pip install flask flask-sqlalchemy flask-cors psycopg2-binary geoalchemy2 geopy flask-migrate
```

---

### 4️⃣ **Set Up PostgreSQL and PostGIS**
1. Access PostgreSQL as the `postgres` user:
```bash
sudo -u postgres psql
```

2. Create a new database and enable PostGIS:
```sql
CREATE DATABASE trees_db;
\c trees_db
CREATE EXTENSION postgis;
SELECT postgis_version();  -- Ensure PostGIS is installed
```

---

### 5️⃣ **Migrate the Database**
Ensure the database schema reflects the latest changes:

1. Initialize the migration system (only once):
```bash
flask db init
```

2. Create and apply migrations:
```bash
flask db migrate -m "Initial migration with extended tree fields"
flask db upgrade
```

If the table exists but needs new columns, run:
```bash
flask db upgrade
```

---

### 6️⃣ **Run the Flask Backend**
```bash
flask run
```
By default, the API will be available at:
```
http://127.0.0.1:5000
```

If `flask` is not recognized, try:
```bash
python app.py
```

---

### 7️⃣ **Start the Frontend**
Navigate to the `frontend` folder:
```bash
cd frontend
python3 -m http.server 8080
```

Access the web app at:
```
http://127.0.0.1:8080
```

---

## 📊 **API Endpoints**
| **Method** | **Endpoint**                 | **Description**                  |
|------------|------------------------------|----------------------------------|
| `GET`      | `/trees`                     | Fetch all trees (with filters)   |
| `POST`     | `/add_tree`                  | Add a new tree                   |
| `PATCH`    | `/tree/<tree_id>`            | Update tree (condition/comments) |
| `DELETE`   | `/tree/<tree_id>`            | Delete a tree by ID              |
| `GET`      | `/tree/custom/<custom_id>`   | Find a tree by custom ID         |
| `GET`      | `/cities`                    | Get a list of unique cities      |

---

## 📌 **Usage Instructions**
1. **Add a Tree**: Provide the required fields (latitude/longitude or address, species, condition).
2. **View Trees**: Search by city or address keyword and display on the map.
3. **Edit Trees**: Modify condition/comments directly from the UI.
4. **Delete Trees**: Remove any tree using the "Delete" button.

---

## 🐛 **Troubleshooting**
1. **Missing `ST_AsEWKB` Error**:
   Ensure **PostGIS** is installed and enabled in your database:
   ```sql
   CREATE EXTENSION postgis;
   ```
   Check `geom` is of the correct type:
   ```sql
   SELECT column_name, data_type 
   FROM information_schema.columns 
   WHERE table_name = 'tree';
   ```
   If necessary, re-create the `geom` column:
   ```sql
   ALTER TABLE tree ALTER COLUMN geom TYPE geometry(Point, 4326) USING ST_GeomFromText(geom, 4326);
   ```

2. **Database Not Updating**:
   Ensure you’re running migrations:
   ```bash
   flask db migrate -m "Add new fields"
   flask db upgrade
   ```

3. **Frontend Not Loading**:
   Ensure you started the server in the `frontend` folder:
   ```bash
   python3 -m http.server 8080
   ```

---

## 📜 **Future Improvements**
- Add user authentication for secured access.
- Implement export/import tree data (CSV/Excel).
- Enhance the UI for better usability (e.g., use modals for editing).
- Implement automated testing with `pytest`.

---

## 📬 **Contributing**
Feel free to open issues and submit pull requests. Any contributions are welcome! 🎉

---

## 📖 **License**
This project is licensed under the **MIT License**.

---

Would you like to improve anything else? Let me know! 🚀