import xml.etree.ElementTree as ET
import csv
import os

reports_folder = "/path/to/reports/"

csv_fields = ["package_name", "instruction_coverage_percent", "method_coverage_percent", "class_coverage_percent", "total_instr", "total_method", "total_class"]
csv_rows = []

coverage_dict = {
    "covered" : 0,
    "missed" : 0,
    "covered_total" : 0,
    "missed_total" : 0,
}

def increment_cov_dict(cov_dict):
    cov_dict["covered_total"] += cov_dict["covered"]
    cov_dict["missed_total"] += cov_dict["missed"]
    cov_dict["covered"] = 0
    cov_dict["missed"] = 0

def get_coverage(package_name, dir_name):
    instr = coverage_dict.copy()
    method = coverage_dict.copy()

    tree = ET.parse(f"{reports_folder}{dir_name}/{package_name}")
    root = tree.getroot()

    class_missed = 0
    class_miss = 0
    class_total = 0

    for package in root.findall("package"):
        for cl4ss in package.findall("class"):
            class_total += 1
            for counter in cl4ss.findall("counter"):
                if counter.get("type") == "INSTRUCTION":
                    instr["covered"] += int(counter.get("covered"))
                    instr["missed"] += int(counter.get("missed"))
                if counter.get("type") == "METHOD":
                    method["covered"] += int(counter.get("covered"))
                    method["missed"] += int(counter.get("missed"))
                    class_miss += int(counter.get("covered"))

            if class_miss == 0:
                class_missed += 1
            class_miss = 0

        increment_cov_dict(instr)
        increment_cov_dict(method)

    total_instr = instr["covered_total"] + instr["missed_total"]
    total_method = method["covered_total"] + method["missed_total"]

    csv_rows.append([package_name,
                     round((instr["covered_total"] / total_instr) * 100, 3),
                     round((method["covered_total"] / total_method) * 100, 3),
                     round(((class_total - class_missed) / class_total) * 100, 3),
                     total_instr,
                     total_method,
                     class_total])

if __name__ == "__main__":
    for dirname in os.listdir(reports_folder):
        if os.path.isdir(reports_folder + dirname):
            for filename in os.listdir(reports_folder + dirname):
                get_coverage(filename, dirname)

            with open(dirname, 'w') as f:
                write = csv.writer(f)

                write.writerow(csv_fields)
                write.writerows(csv_rows)

            csv_rows = []
