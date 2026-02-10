"""
Copyright (C) Arash Shiri 2024 - 2026
This work is licensed under Creative Commons Attribution-ShareAlike 4.0 International
https://creativecommons.org/licenses/by-sa/4.0/

You are free to:
- Share: copy and redistribute the material in any medium or format
- Adapt: remix, transform, and build upon the material

Under the following terms:
- Attribution: You must give appropriate credit
- ShareAlike: If you remix, transform, or build upon the material, you must distribute 
             your contributions under the same license as the original

Usage Instructions:
-------------------

Step 1: Prepare your CSV file
- Use the optional template: https://docs.google.com/spreadsheets/d/1dOEYUPY9M-j34zDl2i7qIqhwWhv-QaYcAaqZ8ShalG4/edit?usp=sharing
- Fill in your data following the template format
- Go to File > Download > CSV to save your filled template
- Make sure all required columns are present: Trackname, Filename, TC start, TC end
- Time codes should be in format HH:MM:SS:FF (hours:minutes:seconds:frames)

Step 2: Run the script
Option A) Basic usage:
    python script.py your_filled_template.csv

Option B) Specify custom output location:
    python script.py your_filled_template.csv -x custom_output.xml

Notes:
- If output XML exists, blocks will be updated
- If output XML doesn't exist, new file will be created
- Invalid XML files will trigger creation of new file named 'output-<datetime>.xml'



Dependencies:
-------------
Ensure the CSV file has the following columns: Trackname, Filename, TC start, TC end.
"""

import csv
import xml.etree.ElementTree as ET
import uuid
import argparse
import os
import unicodedata
import re
from datetime import datetime

def sanitize_input(text):
    """
    Sanitizes the input text by:
    1. Normalizing unicode characters (e.g., Å -> A, Ü -> U)
    2. Removing any characters that are not alphanumeric, underscore, or hyphen.
    """
    if not text:
        return ""
    
    # Normalize unicode characters to decompose combined characters
    normalized = unicodedata.normalize('NFKD', text)
    
    # Encode to ASCII bytes, ignoring non-ASCII characters, then decode back to string
    ascii_text = normalized.encode('ASCII', 'ignore').decode('ASCII')
    
    # Replace any character that is not a-z, A-Z, 0-9, _, or - with nothing
    sanitized = re.sub(r'[^a-zA-Z0-9_-]', '', ascii_text)
    
    return sanitized

def create_xml(trackname, filename, tc_start, tc_end):
    def timecode_to_absolute(tc):
        parts = list(map(int, tc.split(":")))  # Split TC into hours, minutes, seconds, frames
        hours, minutes, seconds = parts[:3]  # Ignore frames for now
        return hours * 3600 + minutes * 60 + seconds

    tc_start_parts = tc_start.split(":")  # Split TC start into hour, minute, second, frame
    tc_end_parts = tc_end.split(":")      # Split TC end into hour, minute, second, frame

    block = ET.Element("Block")
    
    # Generate GUID for ID
    block_id = ET.SubElement(block, "id")
    block_id.text = f"{uuid.uuid4()}"

    # tcRange
    tc_range = ET.SubElement(block, "tcRange")
    
    # Start time components
    ET.SubElement(tc_range, "startHour").text = tc_start_parts[0]
    ET.SubElement(tc_range, "startMinute").text = tc_start_parts[1]
    ET.SubElement(tc_range, "startSecond").text = tc_start_parts[2]
    ET.SubElement(tc_range, "startAbsolute").text = str(timecode_to_absolute(tc_start))

    # End time components
    ET.SubElement(tc_range, "endHour").text = tc_end_parts[0]
    ET.SubElement(tc_range, "endMinute").text = tc_end_parts[1]
    ET.SubElement(tc_range, "endSecond").text = tc_end_parts[2]
    ET.SubElement(tc_range, "endAbsolute").text = str(timecode_to_absolute(tc_end))

    # Additional elements
    ET.SubElement(block, "initialized").text = "true"
    ET.SubElement(block, "title").text = trackname
    ET.SubElement(block, "filename").text = filename
    ET.SubElement(block, "startTC").text = tc_start
    ET.SubElement(block, "endTC").text = tc_end

    return block


def generate_xml_from_csv(csv_file, output_file):
    # Open the CSV file
    with open(csv_file, mode="r", encoding="utf-8") as file:
        reader = csv.DictReader(file)

        # Initialize root and blocks
        root = None
        blocks = None

        # Check if the output XML file exists
        if os.path.exists(output_file):
            tree = ET.parse(output_file)
            root = tree.getroot()

            # Ensure root is named "ProjectData"
            if root.tag != "ProjectData":
                print(f"Warning: The root tag of '{output_file}' is invalid. A new XML file will be created.")
                output_file = f"output-{datetime.now().strftime('%Y%m%d-%H%M%S')}.xml"
                root = ET.Element("ProjectData")
            blocks = root.find("blocks")
            if blocks is None:
                blocks = ET.SubElement(root, "blocks")
            else:
                # Remove existing <Block> elements
                for block in blocks.findall("Block"):
                    blocks.remove(block)
        else:
            # Create new root and <blocks> tag
            root = ET.Element("ProjectData")
            blocks = ET.SubElement(root, "blocks")

        # Iterate over rows and create XML blocks
        for row in reader:
            # Sanitize inputs
            trackname = sanitize_input(row["Trackname"])
            filename = sanitize_input(row["Filename"])
            tc_start = row["TC start"]
            tc_end = row["TC end"]

            # Ignore rows where essential fields are missing
            if trackname and filename and tc_start and tc_end:
                block = create_xml(trackname, filename, tc_start, tc_end)
                blocks.append(block)

        # Write XML to file with pretty formatting
        tree = ET.ElementTree(root)
        indent_xml(root)
        tree.write(output_file, encoding="utf-8", xml_declaration=True)
        print(f"XML file generated or updated: {output_file}")


def indent_xml(elem, level=0):
    i = "\n" + level * "\t"
    if len(elem):
        if not elem.text or not elem.text.strip():
            elem.text = i + "\t"
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
        for child in elem:
            indent_xml(child, level + 1)
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
    else:
        if level and (not elem.tail or not elem.tail.strip()):
            elem.tail = i


if __name__ == "__main__":
    # Argument parsing for input/output files
    parser = argparse.ArgumentParser(description="Generate XML from a CSV file.")
    parser.add_argument("csv_file", help="Path to the input CSV file.")
    parser.add_argument(
        "-x", "--xml",
        default="output.xml",
        help="Path to the input/output XML file (default: output.xml)."
    )
    args = parser.parse_args()

    # Check if the input file exists
    if not os.path.isfile(args.csv_file):
        print(f"Error: The file '{args.csv_file}' does not exist.")
        exit(1)

    # Generate XML
    try:
        generate_xml_from_csv(csv_file=args.csv_file, output_file=args.xml)
    except ValueError as e:
        print(f"Error: {e}")
