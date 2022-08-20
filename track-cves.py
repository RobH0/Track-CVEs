# track-cves.py

# To implement:
# 1. Open reports in the default browser.
# 2. Ask user if they want to open the created reports in their default browser.
# 3. Ask user if they want the filtered CVEs to be output to the command line.
# 2. Refactor code.


import argparse
import datetime
import io
import json
import sys
import urllib.request
import zipfile
import os
import webbrowser

from datetime import datetime, timedelta


def read_vendor_file(vendor_filename):
    vendor_list = []

    try:
        if vendor_filename == None:
            vendor_filename = 'vendors.txt'
        with open(vendor_filename, 'r') as vendors:
            vendor_list = vendors.read().splitlines()
    except:
        print("The Vendor file you specified does not exist.")
        sys.exit()

    return vendor_list


def get_cve_data():

    print("Downloading the most recent CVE data.")

    cve_recent_url = "https://nvd.nist.gov/feeds/json/cve/1.1/nvdcve-1.1-recent.json.zip"
    cve_recent_feed_file = ''

    # Attempts to download the most recent CVE feed in json format.
    try:
        with urllib.request.urlopen(cve_recent_url) as cves:
            cve_recent_feed_file = cves.read()
        print("Successfully downloaded recent CVE feed from NVD.\n")
    except Exception as e:
        print(e)
        print("Error attempting to download the NVD recent CVE feed.")
        sys.exit(0)

    # Unzips the cve feed file
    cve_zip_file = zipfile.ZipFile(io.BytesIO(cve_recent_feed_file), mode='r')
    unzipped_cve_data = cve_zip_file.open("nvdcve-1.1-recent.json")

    cve_json_data = json.load(unzipped_cve_data)

    return cve_json_data


def sort_cve_data(cve_json_data, days):

    cve_dictionary = {}

    if days == None:
        days = 7
    else:
        days = int(days)

    oldest_date = datetime.today() - timedelta(days=days)

    for cve in cve_json_data['CVE_Items']:
        cve_modified_date = datetime.strptime(
            cve['lastModifiedDate'].split('T')[0], '%Y-%m-%d')

        if oldest_date <= cve_modified_date:

            cve_id = cve['cve']['CVE_data_meta']['ID']
            cve_pub_date = cve['publishedDate'].split('T')[0]
            cve_last_mod = cve['lastModifiedDate'].split('T')[0]

            cve_dictionary[cve_id] = {}
            cve_dictionary[cve_id]['published'] = cve_pub_date
            cve_dictionary[cve_id]['last_modified'] = cve_last_mod
            for cve_desc_item in cve['cve']['description']['description_data']:
                if cve_desc_item['lang'] == 'en':
                    cve_desc = cve_desc_item['value']
                    cve_dictionary[cve_id]['description'] = cve_desc

            for key in cve['impact']:
                if key == 'baseMetricV3':
                    cve_dictionary[cve_id]['exploitabilityScore'] = cve['impact']['baseMetricV3']['exploitabilityScore']
                    cve_dictionary[cve_id]['impactScore'] = cve['impact']['baseMetricV3']['impactScore']
                    cve_dictionary[cve_id]['baseScore'] = cve['impact']['baseMetricV3']['cvssV3']['baseScore']
                    cve_dictionary[cve_id]['baseSeverity'] = cve['impact']['baseMetricV3']['cvssV3']['baseSeverity']
                    cve_dictionary[cve_id]['attackVector'] = cve['impact']['baseMetricV3']['cvssV3']['attackVector']
                    cve_dictionary[cve_id]['attackComplexity'] = cve['impact']['baseMetricV3']['cvssV3']['attackComplexity']
                    cve_dictionary[cve_id]['privilegesRequired'] = cve['impact']['baseMetricV3']['cvssV3']['privilegesRequired']
                    cve_dictionary[cve_id]['userInteraction'] = cve['impact']['baseMetricV3']['cvssV3']['userInteraction']

    return cve_dictionary


def filter_cve_by_vendor(cve_dictionary, vendor_list):
    filtered_cves = {}
    for vendor in vendor_list:
        for cve in cve_dictionary:
            if vendor.lower() in cve_dictionary[cve]['description'].lower():

                filtered_cves[cve] = {}
                for key in cve_dictionary[cve]:
                    filtered_cves[cve][key] = cve_dictionary[cve][key]

    return filtered_cves


def output_cves(filtered_cves):
    print("\nFILTERED CVEs:")

    print("\nHigh Severity: ")
    for cve in filtered_cves:
        if filtered_cves[cve].get('baseSeverity') != None and filtered_cves[cve]['baseSeverity'] == 'HIGH':
            print("\n" + cve)
            for key in filtered_cves[cve]:
                print(key + ": " + str(filtered_cves[cve][key]))

    print("\nMedium Severity: ")
    for cve in filtered_cves:
        if filtered_cves[cve].get('baseSeverity') != None and filtered_cves[cve]['baseSeverity'] == 'MEDIUM':
            print("\n" + cve)
            for key in filtered_cves[cve]:
                print(key + ": " + str(filtered_cves[cve][key]))

    print("\nLow Severity: ")
    for cve in filtered_cves:
        if filtered_cves[cve].get('baseSeverity') != None and filtered_cves[cve]['baseSeverity'] == 'LOW':
            print("\n" + cve)
            for key in filtered_cves[cve]:
                print(key + ": " + str(filtered_cves[cve][key]))

    print("Unspecified Severity: ")
    for cve in filtered_cves:
        if filtered_cves[cve].get('baseSeverity') == None:
            print("\n" + cve)
            for key in filtered_cves[cve]:
                print(key + ": " + str(filtered_cves[cve][key]))


def report_generation(filtered_cves, severity, days):
    report_details = ''
    sev_count = 0
    string_severity = str(severity)
    report_name = string_severity.lower() + '_sev_report_'+ str(datetime.today().date()) +'.html'
    report_file_path = ''


    if days == None:
        days = 7

    for cve in filtered_cves:
        if filtered_cves[cve].get('baseSeverity') != None and filtered_cves[cve]['baseSeverity'] == severity:
            sev_count += 1
            report_details += '<br><br><b><a href="https://nvd.nist.gov/vuln/detail/' + \
                cve + '">' + cve + '</a></b>:<br> '
            report_details += '<b>Last modified: </b>' + filtered_cves[cve]['last_modified'] + '<br>'
            report_details += str(filtered_cves[cve]['description'])




    report = '<h2>' + str(sev_count) + ' ' + string_severity + \
        ' severity CVEs relating to your vendor list over the past ' + \
        str(days) + ' days:</h2>\n'

    report += report_details

    try:
        with open(report_name, 'w') as htmlfile:
            htmlfile.write(report)

        report_file_path = os.path.dirname(
            os.path.realpath(report_name)) + '\\' + report_name


        print(string_severity + " severity CVE report saved to " +  report_file_path)
    except:
        print("Error when writing to report file")

    return report_file_path


def generate_web_reports(filtered_cves, days):
    high_sev_file_path = report_generation(filtered_cves, 'HIGH', days)
    med_sev_file_path = report_generation(filtered_cves, 'MEDIUM', days)
    low_sev_file_path = report_generation(filtered_cves, 'LOW', days)
    na_sev_file_path = report_generation(filtered_cves, None, days)

    report_file_path_list = [high_sev_file_path, med_sev_file_path, low_sev_file_path, na_sev_file_path]

    return report_file_path_list

def open_reports_in_browser(reports_list):
    correct_input = False
    print('\n')


    while correct_input == False:
        user_response = input("Do you want the above reports to be open in your default browser (y/n)? ")

        if user_response.lower() == 'y':
            print("Opening reports in your default browser")
            correct_input = True
            for path in reports_list:
                webbrowser.open('file://' + path)
        elif user_response.lower() == 'n':
            print("Exiting")
            correct_input = True
        else:
            print("Invalid input!")



if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='TrackCVE')
    parser.add_argument(
        '-f', '--file', help='Text file from which Vendor names are read.')
    parser.add_argument(
        '-d', '--days', help='Used to only display CVEs that were released x number of days in the past.')
    args = parser.parse_args()

    if args.days != None:
        if int(args.days) > 7:
            print("Please pass a ''--days' argument value of less than 8.\nOnly 7 days of the most recent CVE data is downloaded")
            sys.exit()

    cve_json_data = get_cve_data()
    vendor_list = read_vendor_file(args.file)
    cve_dictionary = sort_cve_data(cve_json_data, args.days)
    filtered_cves = filter_cve_by_vendor(cve_dictionary, vendor_list)
    # output_cves(filtered_cves)
    report_file_path_list = generate_web_reports(filtered_cves, args.days)
    open_reports_in_browser(report_file_path_list)
    sys.exit()

"""
example json cve format

{'cve': {'data_type': 'CVE', 'data_format': 'MITRE', 'data_version': '4.0', 'CVE_data_meta': {'ID': 'CVE-2022-35672', 'ASSIGNER': 'psirt@adobe.com'}, 'problemtype': {'problemtype_data': [{'description': [{'lang': 'en', 'value': 'CWE-125'}]}]}, 'references': {'reference_data': [{'url': 'https://helpx.adobe.com/security/products/acrobat/apsb22-16.html', 'name': 'https://helpx.adobe.com/security/products/acrobat/apsb22-16.html', 'refsource': 'MISC', 'tags': []}]}, 'description': {'description_data': [{'lang': 'en', 'value': 'Adobe Acrobat Reader version 22.001.20085 (and earlier), 20.005.30314 (and earlier) and 17.012.30205 (and earlier) are affected by an out-of-bounds read vulnerability when parsing a crafted file, which could result in a read past the end of an allocated memory structure. An attacker could leverage this vulnerability to execute code in the context of the current user. Exploitation of this issue requires user interaction in that a victim must open a malicious file.'}]}}, 'configurations': {
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                           'CVE_data_version': '4.0', 'nodes': []}, 'impact': {'baseMetricV3': {'cvssV3': {'version': '3.1', 'vectorString': 'CVSS:3.1/AV:L/AC:L/PR:N/UI:R/S:U/C:H/I:H/A:H', 'attackVector': 'LOCAL', 'attackComplexity': 'LOW', 'privilegesRequired': 'NONE', 'userInteraction': 'REQUIRED', 'scope': 'UNCHANGED', 'confidentialityImpact': 'HIGH', 'integrityImpact': 'HIGH', 'availabilityImpact': 'HIGH', 'baseScore': 7.8, 'baseSeverity': 'HIGH'}, 'exploitabilityScore': 1.8, 'impactScore': 5.9}}, 'publishedDate': '2022-07-27T17:15Z', 'lastModifiedDate': '2022-07-27T17:15Z'}
"""
