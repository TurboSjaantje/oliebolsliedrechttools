from flask import Flask, render_template, request, redirect, flash, url_for, send_file, jsonify
import json
import os
import subprocess
import threading
import pandas as pd
import time
import re
import openpyxl
from openpyxl.workbook import Workbook

app = Flask(__name__)
app.secret_key = 'supersecretkey'

# File paths for storing settings
BELBESTAND_FILE = 'belbestand_settings.json'
SHOPIFY_FILE = 'shopify_settings.json'

# Directory for uploaded files
UPLOAD_FOLDER = './uploads'
OUTPUT_FOLDER = './output'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# Variables to track uploaded files
uploaded_files = {'file1': None, 'file2': None}

# Merge task status
merge_status = {'running': False, 'output_file': None}


def run_merge_script(file1, file2, output_file):
    """Simulate running an external Python script."""
    try:
        merge_status['running'] = True  # Mark the task as running
        # Simulate a long-running task
        print("Starting merge process...")
        time.sleep(5)  # Replace this with the actual script logic
        # Write a result file (simulate merged content)
        with open(output_file, 'w') as f:
            f.write(f"Merged content of:\n{file1}\n{file2}\n")
        merge_status['output_file'] = output_file  # Update the output file path
        print("Merge process completed!")
    except Exception as e:
        print(f"Error during merge: {e}")
    finally:
        merge_status['running'] = False  # Ensure task is marked as not running


# Function to save settings to a JSON file
def save_settings_to_file(filename, data):
    with open(filename, 'w') as file:
        json.dump(data, file, indent=4)


# Function to load settings from a JSON file
def load_settings_from_file(filename):
    try:
        with open(filename, 'r') as file:
            return json.load(file)
    except FileNotFoundError:
        return {}


@app.route('/')
def index():
    files_uploaded = all(uploaded_files.values())  # True if both files are uploaded
    return render_template('tools.html', files_uploaded=files_uploaded, uploaded_files=uploaded_files)


@app.route('/upload', methods=['POST'])
def upload_files():
    global uploaded_files
    # Handle file1 upload (Bestand Belavond)
    if 'file1' in request.files and request.files['file1'].filename:
        file1 = request.files['file1']
        file1_path = os.path.join(UPLOAD_FOLDER, file1.filename)
        file1.save(file1_path)
        uploaded_files['file1'] = file1.filename

    # Handle file2 upload (Bestand Shopify)
    if 'file2' in request.files and request.files['file2'].filename:
        file2 = request.files['file2']
        file2_path = os.path.join(UPLOAD_FOLDER, file2.filename)
        file2.save(file2_path)
        uploaded_files['file2'] = file2.filename

    flash("Files uploaded successfully.", "success")
    return redirect(url_for('index'))


@app.route('/remove/<file_key>', methods=['POST'])
def remove_file(file_key):
    global uploaded_files
    if file_key in uploaded_files and uploaded_files[file_key]:
        file_path = os.path.join(UPLOAD_FOLDER, uploaded_files[file_key])
        if os.path.exists(file_path):
            os.remove(file_path)
        uploaded_files[file_key] = None
        flash(f"{file_key.capitalize()} removed successfully.", "success")
    else:
        flash("No file to remove.", "error")
    return redirect(url_for('index'))


@app.route('/settings', methods=['GET'])
def settings():
    # Load settings for both belbestand and shopify
    belbestand_settings = load_settings_from_file(BELBESTAND_FILE)
    shopify_settings = load_settings_from_file(SHOPIFY_FILE)
    return render_template('settings.html', belbestand=belbestand_settings, shopify=shopify_settings)


@app.route('/settings/belbestand', methods=['POST'])
def belbestand():
    # Process belbestand form data
    belbestand_settings = request.form.to_dict()
    save_settings_to_file(BELBESTAND_FILE, belbestand_settings)
    flash("Belbestand settings saved successfully!", "success")
    return redirect(url_for('settings'))


@app.route('/settings/shopifybestand', methods=['POST'])
def shopifybestand():
    # Process shopify form data
    shopify_settings = request.form.to_dict()
    save_settings_to_file(SHOPIFY_FILE, shopify_settings)
    flash("Shopify settings saved successfully!", "success")
    return redirect(url_for('settings'))


@app.route('/merge-files', methods=['POST'])
def merge_files():
    if not all(uploaded_files.values()):
        flash("Both files must be uploaded to merge.", "error")
        return redirect(url_for('index'))

    # Start the merge task
    merge_status['running'] = True
    merge_status['output_file'] = None
    file1 = os.path.join(UPLOAD_FOLDER, uploaded_files['file1'])
    file2 = os.path.join(UPLOAD_FOLDER, uploaded_files['file2'])
    output_file = os.path.join(OUTPUT_FOLDER, 'merged_result.txt')

    # Run the merge script in a separate thread
    thread = threading.Thread(target=run_merge_script, args=(file1, file2, output_file))
    thread.start()

    return jsonify({'status': 'started'})


@app.route('/download-merged', methods=['GET', 'HEAD'])
def download_merged():
    if not merge_status['output_file']:
        return ('', 404)  # Return a 404 if the file is not ready
    if request.method == 'HEAD':
        return ('', 200)  # Indicate the file is ready
    return send_file(merge_status['output_file'], as_attachment=True)


@app.route('/normalize-shopify/<year_key>', methods=['POST'])
def normalize_shopify_tool(year_key):
    if not uploaded_files['file2']:
        flash("No Shopify file uploaded to normalize.", "error")
        return jsonify({'status': 'error', 'message': 'No Shopify file uploaded.'})

    # Paths for input and output
    input_file = os.path.join(UPLOAD_FOLDER, uploaded_files['file2'])
    output_file = os.path.join(OUTPUT_FOLDER, 'normalized_shopify.xlsx')

    # Start normalization task in a separate thread
    merge_status['running'] = True
    merge_status['output_file'] = None
    thread = threading.Thread(target=normalize_shopify, args=(input_file, output_file, year_key))
    thread.start()

    return jsonify({'status': 'started'})


@app.route('/check-normalized', methods=['GET', 'HEAD'])
def check_normalized():
    if not merge_status['output_file']:
        return ('', 404)  # File not ready
    if request.method == 'HEAD':
        return ('', 200)  # File ready for download
    return send_file(merge_status['output_file'], as_attachment=True)


def normalize_shopify(input_file, output_file, year):
    try:
        json_file = "./shopify_settings.json"
        with open(json_file, "r") as file:
            column_mapping = json.load(file)

        reversed_mapping = {v: k for k, v in column_mapping.items()}
        df = pd.read_csv(input_file)

        # Filter rows and rename columns
        order_rows = df[df['Name'].str.contains(r'^#\d+', na=False, flags=re.IGNORECASE)]
        columns_to_keep = list(column_mapping.values())
        filtered_rows = order_rows[columns_to_keep].rename(columns=reversed_mapping)

        # Initialize new columns
        filtered_rows.loc[:, 'Oliebollen'] = 0
        filtered_rows.loc[:, 'Appelbeignets'] = 0

        # Create Excel workbook and worksheet
        wb = Workbook()
        ws = wb.active
        ws.title = "Orders"

        # Append header row with rearranged columns
        header = ["Ordernummer", "Totaalprijs", "Betaald", "Oliebollen", "Appelbeignets",
                  "Naam", "Ophalen/Bezorgen", "Datum", "Tijd", "Factuuradres", "Leveradres",
                  "Factuurpostcode", "Leverpostcode", "Factuurplaats", "Leverplaats",
                  "Telefoonnummer", "Bezorgkosten", "Gift"]
        ws.append(header)

        # Dictionary to track row locations for each Ordernummer
        row_map = {}

        for index, row in filtered_rows.iterrows():
            current_ordernummer = row['Ordernummer']

            # Initialize variables for the current row
            aantal_oliebollen = 0
            aantal_appelbeignets = 0
            gift = 0
            betaald = "Ja" if row['Betaald'] == "paid" else "Nee"

            # Parse the Bezorging field
            ophalen_bezorgen, datum, tijd = "N/A", "N/A", "N/A"
            if pd.notnull(row['Bezorging']):
                try:
                    bezorging_parts = row['Bezorging'].split("|")
                    ophalen_bezorgen = bezorging_parts[0].split(":")[1].strip() if len(bezorging_parts) > 0 else "N/A"
                    datum = bezorging_parts[1].split(":")[1].strip() if len(bezorging_parts) > 1 else "N/A"
                    tijd = bezorging_parts[2].split("Time:")[1].strip() if len(bezorging_parts) > 2 else "N/A"
                except Exception as e:
                    print(f"Error parsing Bezorging field: {e}")

            # Your original logic to determine amounts
            if "Combi" in row['Productkolom']:
                split_row = row['Productkolom'].split(" ")
                aantal_oliebollen = int(split_row[1]) * int(row['Kwantiteitkolom'])
                aantal_appelbeignets = int(split_row[4]) * int(row['Kwantiteitkolom'])
            elif "Oliebollen" in row['Productkolom']:
                match = re.findall(r'\d+', row['Productkolom'])
                if match:
                    aantal_oliebollen = int(match[0]) * int(row['Kwantiteitkolom'])
            elif "Appelbeignets" in row['Productkolom']:
                match = re.findall(r'\d+', row['Productkolom'])
                if match:
                    aantal_appelbeignets = int(match[0]) * int(row['Kwantiteitkolom'])
            elif "Tip" in row['Productkolom']:
                gift = int(row['Gift']) if pd.notnull(row['Gift']) else 0

            if current_ordernummer not in row_map:
                # New order: create a new row in the workbook
                current_row = [
                    row['Ordernummer'], row['Totaalprijs'], betaald, aantal_oliebollen, aantal_appelbeignets,
                    row['Naam'], ophalen_bezorgen, datum, tijd, row['Factuuradres'], row['Leveradres'],
                    row['Factuurpostcode'], row['Leverpostcode'], row['Factuurplaats'], row['Leverplaats'],
                    row['Telefoonnummer'], row['Bezorgkosten'], gift
                ]
                ws.append(current_row)
                row_map[current_ordernummer] = ws.max_row  # Track the row index for this order
            else:
                # Existing order: update the existing row
                target_row = row_map[current_ordernummer]

                # Retrieve current values
                current_oliebollen = int(ws.cell(row=target_row, column=4).value or 0)  # Oliebollen
                current_appelbeignets = int(ws.cell(row=target_row, column=5).value or 0)  # Appelbeignets
                current_gift = int(ws.cell(row=target_row, column=18).value or 0)  # Gift

                # Update values for the current order
                ws.cell(row=target_row, column=4).value = current_oliebollen + aantal_oliebollen
                ws.cell(row=target_row, column=5).value = current_appelbeignets + aantal_appelbeignets
                ws.cell(row=target_row, column=18).value = current_gift + gift

        # Save the workbook
        wb.save(output_file)
        merge_status['output_file'] = output_file
        print("Shopify file normalized successfully!")
    except Exception as e:
        print(f"Error normalizing Shopify file: {e}")
    finally:
        merge_status['running'] = False




if __name__ == '__main__':
    app.run(debug=True)
