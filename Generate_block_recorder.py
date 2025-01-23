import csv
import xml.etree.ElementTree as ET
import uuid
import argparse
import os

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

        # Create XML root
        root = ET.Element("Root")

        # Iterate over rows and create XML blocks
        for row in reader:
            trackname = row["Trackname"]
            filename = row["Filename"]
            tc_start = row["TC start"]
            tc_end = row["TC end"]

            # Ignore rows where essential fields are missing
            if trackname and filename and tc_start and tc_end:
                block = create_xml(trackname, filename, tc_start, tc_end)
                root.append(block)

        # Write XML to file with pretty formatting
        tree = ET.ElementTree(root)
        indent_xml(root)
        tree.write(output_file, encoding="utf-8", xml_declaration=True)


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
        "-o", "--output",
        default="output.xml",
        help="Path to the output XML file (default: output.xml)."
    )
    args = parser.parse_args()

    # Check if the input file exists
    if not os.path.isfile(args.csv_file):
        print(f"Error: The file '{args.csv_file}' does not exist.")
        exit(1)

    # Generate XML
    generate_xml_from_csv(csv_file=args.csv_file, output_file=args.output)
    print(f"XML file generated: {args.output}")
