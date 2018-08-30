#Python3
import json, csv, sys, requests, authenticate, runtime, logging

def open_csv():
    '''This function opens a csv file in DictReader mode'''
    input_csv = input('Please enter path to CSV: ')
    file = open(input_csv, 'r', encoding='utf-8')
    return csv.DictReader(file)

def update_accessions():
    csvfile = open_csv()
    for row in csvfile:
        try:
            record_uri = row.get("uri")
            record_json = requests.get(baseURL + record_uri, headers=headers).json()

            logging.info(record_uri + ' Original JSON: ' + json.dumps(record_json))


            if "collection_management" not in record_json:
                record_json["collection_management"] = {'processing_status': 'completed'}

            elif record_json["collection_management"]:
                new_status = "completed"
                record_json["collection_management"]["processing_status"] = new_status


            record_data = json.dumps(record_json)
            record_update = requests.post(baseURL + record_uri, headers=headers, data=record_data).json()
            print(record_update)
            logging.info('%s successfully updated', record_uri)
            logging.info(record_uri + ' Updated JSON: ' + record_data)
            logging.info('\n')

        except Exception as ex:
            print('Skipping invalid row')
            logging.warning('Skipping invalid row for %s. Exception: %s\n', record_uri, ex)
            continue

def main():
    logging.info('Started updates in %s', baseURL)
    update_accessions()
    logging.info('Finished updates in %s', baseURL)
    input("Press enter to exit... ")

if __name__ == '__main__':
    logging.basicConfig(filename='processing-status-updates.log', level=logging.INFO, format='%(asctime)s %(message)s')
    logging.getLogger("requests").setLevel(logging.WARNING)
    # This is where we connect to ArchivesSpace.  See authenticate.py
    baseURL, headers = authenticate.login()
    main()
