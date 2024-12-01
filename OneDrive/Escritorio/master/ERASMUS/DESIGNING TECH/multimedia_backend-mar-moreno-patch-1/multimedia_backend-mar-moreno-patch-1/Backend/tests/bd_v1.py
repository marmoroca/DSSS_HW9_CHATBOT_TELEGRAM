import os
import sqlite3
import argparse
from datetime import datetime
import random
import numpy as np
import cv2



BASE_DIR = "."
DB_PATH = os.path.join(BASE_DIR, "images.db")
IMAGE_DIR = os.path.join(BASE_DIR, "images")
EXAMPLE_IMAGE_DIR = os.path.join(BASE_DIR, "example_images")

def create_dirs() -> None:
    """
    make sure the directories exist
    """

    if not os.path.exists(BASE_DIR):
        os.makedirs(BASE_DIR)

    if not os.path.exists(IMAGE_DIR):
        os.makedirs(IMAGE_DIR)

    if not os.path.exists(EXAMPLE_IMAGE_DIR):
        os.makedirs(EXAMPLE_IMAGE_DIR)

    print("Made sure the directories exist!")


def get_db() -> sqlite3.Connection:
    db = sqlite3.connect(DB_PATH)
    db.row_factory = sqlite3.Row
    return db

def clean_images() -> None:
    """
    Delete all images from the file system
    Should only be used together with reset_db
    So that the database and the file system are in sync
    Otherwise the database will have references to images that do not exist
    """

    for f in os.listdir(IMAGE_DIR):
        os.remove(os.path.join(IMAGE_DIR, f))

    print("Deleted all images from the file system")

def reset_db() -> None:
    """
    reset/init the database
    """

    # Check if the database file exists before attempting to delete
    if os.path.exists(DB_PATH):
        # Delete the database file
        os.remove(DB_PATH)
        print(f"The database '{DB_PATH}' has been deleted.")
    else:
        print(f"The database '{DB_PATH}' does not exist.")

    create_table()
    print("Created the database and the table 'image'")

##chat adri 
def create_table() -> None:
    """
    Crea la base de datos con las tablas role, worker, data y sus relaciones.
    """
    con = get_db()
    cur = con.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS role (
        role_id INTEGER PRIMARY KEY,  -- Identificador único del rol
        role_name VARCHAR(50) NOT NULL -- Nombre del rol
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS worker (
        worker_id INTEGER PRIMARY KEY, -- Identificador único del trabajador
        name VARCHAR(50),              -- Nombre del trabajador
        surname VARCHAR(50),           -- Apellido del trabajador
        email VARCHAR(100)             -- Correo electrónico
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS has_role (
        worker_id INTEGER NOT NULL,    -- Trabajador
        role_id INTEGER NOT NULL,      -- Rol
        PRIMARY KEY (worker_id, role_id),
        FOREIGN KEY (worker_id) REFERENCES worker(worker_id),
        FOREIGN KEY (role_id) REFERENCES role(role_id)
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS data (
        data_id INTEGER PRIMARY KEY, -- Identificador único de los datos
        data_type TEXT NOT NULL,     -- Tipo de datos (por ejemplo, JSON, XML)
        url TEXT NOT NULL,           -- URL donde se encuentran los datos
        data_info TEXT               -- Información adicional
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS request (
        request_id INTEGER PRIMARY KEY,    -- Identificador único de la petición
        worker_id INTEGER NOT NULL,        -- Trabajador asociado
        timestamp DATETIME DEFAULT(STRFTIME('%Y-%m-%d %H:%M:%f', 'NOW')), -- Fecha de la petición
        FOREIGN KEY (worker_id) REFERENCES worker(worker_id)
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS request_data (
        request_id INTEGER NOT NULL,  -- Relación a una petición
        data_id INTEGER NOT NULL,     -- Relación a los datos
        PRIMARY KEY (request_id, data_id),
        FOREIGN KEY (request_id) REFERENCES request(request_id),
        FOREIGN KEY (data_id) REFERENCES data(data_id)
    )
    """)
    
    con.commit()
    con.close()
    print("Base de datos creada con las tablas role, worker y data")


def save_img(img: np.ndarray) -> int | None:
    """
    Save the image metadata to the database and the image to the file system
    """

    con = get_db()
    cur = con.cursor()

    timestamp = datetime.now().strftime('%Y-%m-%d_%H:%M:%S.%f')[:-3]

    # Create new entry for the image to get the id
    cur.execute("INSERT INTO image (timestamp) VALUES (?)", (timestamp,))

    id = cur.lastrowid

    filename = f"{id}_{timestamp}.png"
    filepath = f"{IMAGE_DIR}/{filename}"

    # save the image to the file system
    cv2.imwrite(filepath, img)

    # Update the path of the image
    cur.execute("UPDATE image SET path = ? WHERE id = ?", (filepath, id))

    con.commit()
    con.close()

    return id


def add_sample_data(limit: int = 0) -> None:
    """
    insert some example images with dummy predictions into the database
    """


    image_files = [f for f in os.listdir(EXAMPLE_IMAGE_DIR) if os.path.isfile(os.path.join(EXAMPLE_IMAGE_DIR, f))]
    if len(image_files) == 0:
        print("No example images found")
        return

    if limit > 0:
        image_files = random.sample(image_files, limit)

    confs = [0.3, 0.7]
    while len(image_files) > len(confs):
        confs.append(random.choice(confs))

    ids = []

    for image_file in image_files:
        image_path = os.path.join(EXAMPLE_IMAGE_DIR, image_file)

        img = cv2.imread(image_path)
        id = save_img(img)
        ids.append(id)

    con = get_db()
    cur = con.cursor()

    for id, conf in zip(ids, confs):
        if conf < 0.5:
            cur.execute("UPDATE image SET status = 'predicted', class = (?), xmin = 0.1, ymin = 0.1, xmax = 0.9, ymax = 0.9 WHERE id = (?)", (conf, id))
        else:
            cur.execute("UPDATE image SET status = 'predicted', class = (?) WHERE id = (?)", (conf, id))

    print("Added some example images to the table")

    con.commit()
    con.close()

def save_db_schema_to_file(output_file: str = "db_schema.txt") -> None:
    """
    Guarda el esquema de la base de datos en un archivo de texto.
    """
    con = get_db()
    cur = con.cursor()
    
    # Obtener el esquema de todas las tablas
    cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cur.fetchall()
    
    with open(output_file, "w") as f:
        for table in tables:
            table_name = table["name"]
            f.write(f"TABLE: {table_name}\n")
            
            # Obtener la información de las columnas de cada tabla
            cur.execute(f"PRAGMA table_info({table_name});")
            columns = cur.fetchall()
            for column in columns:
                f.write(f"  {column['cid']}: {column['name']} ({column['type']})\n")
            
            f.write("\n")  # Separador entre tablas
    
    con.close()
    print(f"Esquema de la base de datos guardado en '{output_file}'")




if __name__ == "__main__":

    argparser = argparse.ArgumentParser()
    argparser.add_argument("--reset", action="store_true")
    argparser.add_argument("--clean", action="store_true")
    argparser.add_argument("-a", "--add_sample_data", action="store_true")
    argparser.add_argument("--schema", action="store_true")
    args = argparser.parse_args()

    create_dirs()


    if args.schema:
        save_db_schema_to_file()

    if args.reset:
        answer = input("Are you sure you want to reset/delete the database (and all the image files)? [y/n]")
        if answer.lower() in ["y","yes"]:
            clean_images()
            reset_db()
        else:
            exit()

    elif args.clean:
        answer = input("Are you sure you want to delete all images from the image directory? [y/n]")
        if answer.lower() in ["y","yes"]:
            clean_images()
        else:
            exit()
    elif args.add_sample_data:
        add_sample_data()


     


