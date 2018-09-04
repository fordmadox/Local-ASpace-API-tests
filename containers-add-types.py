import authenticate, runtime, requests, json, csv, datetime, sys, logging


def open_csv():
    '''This function opens a csv file in DictReader mode'''
    input_csv = input('Please enter path to CSV: ')
    file = open(input_csv, 'r', encoding='utf-8')
    return csv.DictReader(file)

def update_top_containers(container_locations=None):
    csv = open_csv()
    default_date = str(datetime.date.today())
    for row in csv:
        try:
            record_uri = row.get("uri")


            record_json = requests.get(baseURL + record_uri, headers=headers).json()
            logging.info(record_uri + ' Original JSON: ' + json.dumps(record_json))

            #add type of "box" to empty container type
            record_json['type'] = 'Box'

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
    update_top_containers()
    logging.info('Finished updates in %s', baseURL)

if __name__ == '__main__':
    logging.basicConfig(filename='container-updates.log', level=logging.INFO, format='%(asctime)s %(message)s')
    logging.getLogger("requests").setLevel(logging.WARNING)
    baseURL, headers = authenticate.login()
    main()
