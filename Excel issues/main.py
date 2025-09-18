# full_pipeline_merge.py
import subprocess
import sys
import json
import re
import csv
import os

print("\nRecuerda actualizar el fichero -Backlog - Kanban - Pila de producto-" \
    " descargandolo desde el tablero del proyecto\n")

# =========================
# 1. Instalar requests si no está
# =========================
try:
    import requests
except ImportError:
    print("requests no está instalado. Instalando...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "requests"])
    import requests

# =========================
# 2. Descargar issues desde GitHub
# =========================
url = "https://api.github.com/repos/UNIZAR-30248-2025-LEEMAS/Docs/issues?per_page=100&page=1"

response = requests.get(url)
if response.status_code == 200:
    issues = response.json()
    with open("issues.json", "w", encoding="utf-8") as f:
        json.dump(issues, f, ensure_ascii=False, indent=2)
    print(f"Se han guardado {len(issues)} issues en 'issues.json'")
else:
    print(f"Error al acceder a la API: {response.status_code}")
    print(response.text)
    sys.exit(1)

# =========================
# 3. Simplificar issues
# =========================
simplified_issues = []

for issue in issues:
    # Extraer etiquetas como un string
    labels = ', '.join(label['name'] for label in issue.get('labels', []))

    # Limpiar ** del título y del body
    title_clean = (issue.get('title') or '').replace('**', '')
    body_raw = (issue.get('body') or '').replace('**', '')

    # Reemplazar múltiples saltos de línea por uno solo
    body_clean = re.sub(r'\n\s*\n+', '\n', body_raw).strip('\n')

    simplified_issues.append({
        'title': title_clean,
        'body': body_clean,
        'labels': labels
    })

with open("issues_simplified.json", 'w', encoding='utf-8') as f:
    json.dump(simplified_issues, f, ensure_ascii=False, indent=2)


# =========================
# 4. Guardar issues en CSV
# =========================
issues_csv_file = "issues_simplified.csv"
with open(issues_csv_file, 'w', encoding='utf-8', newline='') as f:
    writer = csv.writer(f, quoting=csv.QUOTE_ALL)
    writer.writerow(['Titulo', 'Descripcion', 'Etiquetas'])

    for issue in simplified_issues:
        writer.writerow([issue.get('title', ''),
                         issue.get('body', ''),
                         issue.get('labels', '')])


# =========================
# 5. Convertir TSV backlog a CSV
# =========================
backlog_tsv_file = "Backlog - Kanban - Pila de producto.tsv"
backlog_csv_file = "Backlog - Kanban - Pila de producto.csv"

with open(backlog_tsv_file, "r", encoding="utf-8") as tsv_file:
    tsv_reader = csv.reader(tsv_file, delimiter="\t")
    with open(backlog_csv_file, "w", newline="", encoding="utf-8") as csv_file:
        csv_writer = csv.writer(csv_file, quoting=csv.QUOTE_ALL)
        for row in tsv_reader:
            csv_writer.writerow(row)


# =========================
# 6. Mergear backlog y issues
# =========================
output_file = "pila_de_producto.csv"

# Leer backlog en un diccionario por título
backlog_data = {}
with open(backlog_csv_file, newline="", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    for row in reader:
        backlog_data[row["Title"]] = row

# Leer issues y hacer merge
with open(issues_csv_file, newline="", encoding="utf-8") as f_in, \
     open(output_file, "w", newline="", encoding="utf-8") as f_out:

    issues_reader = csv.DictReader(f_in)
    fieldnames = ["Titulo", "Descripcion", "Estado", "Etiqueta", "Tamaño", "Asignados", "URL"]
    writer = csv.DictWriter(f_out, fieldnames=fieldnames, quoting=csv.QUOTE_ALL)
    writer.writeheader()

    for row in issues_reader:
        title = row["Titulo"]
        backlog_row = backlog_data.get(title, {})  # Si no existe, devuelve {}
        merged_row = {
            "Titulo": title,
            "Descripcion": row.get("Descripcion", ""),
            "Estado": backlog_row.get("Status", ""),
            "Etiqueta": row.get("Etiquetas", ""),
            "Tamaño": backlog_row.get("Size", ""),
            "Asignados": backlog_row.get("Assignees", ""),
            "URL": backlog_row.get("URL", "")
        }
        writer.writerow(merged_row)

print(f"Archivo generado: {output_file}\n")

# =========================
# 7. Borrado de ficheros auxiliares
# =========================

print(f"Eliminando ficheros auxiliares...")

# Lista de ficheros a borrar
files_to_delete = [
    "issues.json",
    "issues_simplified.json",
    "issues_simplified.csv",
    "Backlog - Kanban - Pila de producto.csv"
]

for file_path in files_to_delete:
    try:
        os.remove(file_path)
        print(f"\tFichero eliminado: {file_path}")
    except FileNotFoundError:
        print(f"Fichero no encontrado, no se pudo eliminar: {file_path}")
    except Exception as e:
        print(f"Error al eliminar {file_path}: {e}")
