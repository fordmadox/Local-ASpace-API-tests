#!/usr/bin/env python3
import requests
import getpass
import json
import csv
import cgi
import datetime
from itertools import islice
from pathlib import Path

"""to do:
    1) add a lot more error handling
    2) skip rows if invalid data? (or, okay to fail in the middle?).  add better logs, if it's okay to continue processing the rest of the input file.
    3) find a better way to specify input/output files.
    4) iterate over a directory of files, or okay to go one by one?  if one by one, i should probably move the "infile" to a new directory after the end of processing, right?
    5) find the correct agent record based on the username in the user record.
    6) import the login function, instead of adding it to each file.
"""
#we should look these values up, but for now I've just hardcoded them in the file (people/1 = 'admin')
agent_authorizor = '/agents/people/1'
# Local values (update if needed)
repos = {'repo1': '2','repo2': '3','etc': '4'}
# Filenames, hardcoded for now
archival_objects_csv = 'infile-test.csv'
archival_objects_updated = 'outfile-test.csv'

def login (api_url, username, password):
    '''This function logs into the ArchivesSpace REST API and returns the HTTP header needed for CRUD actions'''
    auth = requests.post(api_url+'/users/'+username+'/login?password='+password).json()
    session = auth["session"]
    headers = {'X-ArchivesSpace-Session':session}
    return headers

def create_child_component ():
    ''''This function creates a new archival component, based on the data in the born-digtial accessioning worksheet'''
    if container != '':
        parent_component = requests.get(api_url+'/repositories/'+repo_num+'/archival_objects/'+ao_id,headers=headers).json()
        #this container business match works for Yale, since we don't use instance types to differntiate betweeen container_indcator_1 values.
        for instances in parent_component['instances']:
            if instances['container']['indicator_1'] == container:
                top_container_url =  instances['sub_container']['top_container']['ref']
        child_component = {"publish": True, "title": title, "level": "item",
                 "component_id": unitid, "jsonmodel_type": "archival_object","linked_events": [],
                 "extents": [{"number": '1',
                              "portion": "whole",
                              "extent_type": extent_type,
                              "jsonmodel_type": "extent"}],
                 "instances": [{"container": {"indicator_1": container,
                                              "type_1": 'box'},
                                "instance_type": 'mixed_materials',
                                "jsonmodel_type": 'instance',
                                "sub_container": {"jsonmodel_type": 'sub_container',
                                                  "top_container": {"ref": top_container_url}
                                                  }
                                }
                               ],
                 "resource": {"ref": '/repositories/'+repo_num+'+/resources/'+parent_id},
                 "parent": {"ref": '/repositories/'+repo_num+'/archival_objects/'+ao_id}} 
    else:
        child_component = {"publish": True, "title": title, "level": "item",
                 "component_id": unitid, "jsonmodel_type": "archival_object","linked_events": [],
                 "extents": [{ "number": '1', "portion": "whole", "extent_type": extent_type, "jsonmodel_type": "extent"}],
                 "resource": {"ref": '/repositories/'+repo_num+'+/resources/'+parent_id},
                 "parent": {"ref": '/repositories/'+repo_num+'/archival_objects/'+ao_id}} 
    child_component_data = json.dumps(child_component)      
    # Post the child archival object
    child_post = requests.post(api_url+'/repositories/'+repo_num+'/archival_objects',headers=headers,data=child_component_data).json()
    try:
        child_post['uri']
    except KeyError:
        print(child_post)
        print('Ooops! Something went wrong. Check the error message in the JSON response.')
        sys.exit(1)
    return child_post


def create_event (event_type, outcome, date, note):
    '''This function creates an event in ASpace, based on the four possible parameters provided in the born-digital accessioning worksheet'''
    # Get the event type
    event_type = event_type.lower()
    # Get the event outcome
    outcome = outcome.lower()
    # Get the event date
    if date != '':
        date = datetime.datetime.strptime(date, '%m/%d/%Y').strftime('%Y-%m-%d')
    # Create a new event, linking to the archival object
    event = {"event_type": event_type, "jsonmodel_type": "event",
             "outcome": outcome,
             "outcome_note": note,
             "linked_agents": [{ "role": "authorizer", "ref": agent_authorizor }],
             "linked_records": [{ "role": "source", "ref": '/repositories/'+repo_num+'/archival_objects/'+new_component_uri }],
             "date": { "begin": date, "date_type": "single", "label": "event", "jsonmodel_type": "date" }}
    event_data = json.dumps(event)      
    # Post that event
    event_post = requests.post(api_url+'/repositories/'+repo_num+'/events',headers=headers,data=event_data).json()
    try:
        event_post['id']
    except KeyError:
        print(event_post)
        print('Ooops! Something went wrong. Check the error message in the JSON response.')
        sys.exit(1)
    return event_post

if __name__ == '__main__':
    api_url = input('Please enter the URL for the ArchivesSpace API: ')
    username = getpass.getuser()
    check_username = input('Is your username ' + username + '?: ')
    if check_username.lower() not in ('y', 'yes', 'yep', 'you know it'):
        username = input('Please enter ArchivesSpace username:  ')
    password = getpass.getpass(prompt=username + ', please enter your ArchivesSpace Password: ', stream=None)
    print('Logging in', api_url)
    headers = login(api_url, username, password)
    if headers != '':
        print('Success!')
    else:
        print('Ooops! Something went wrong.')
        sys.exit(1)
		
    with open(archival_objects_csv,'r') as f:
        #start at the third row, ignoring the two header rows in the file.
        for row in islice(csv.reader(f), 2, None):

            #should be a better way to skip empty/invalid rows, but i've added this for now
            if row[0] in repos:
                # save the original row length, since we'll be appending columsn to the row later on 
                original_row_length = len(row)
                # Get repo id from the repos dictionary
                repo_num = repos.get(row[0])
                # Get archival object parent ID from csv file, and remove most of the url, aside from the ID
                ao_id = str(row[1]).rpartition("_")[2]
                # Get the parent object id
                parent_id = str(row[1]).partition('#')[0].rpartition('/')[2]
                # Get the title
                title = cgi.escape(row[2])
                # Get the unitid
                unitid = row[3]
                # Get the extent type
                extent_type = row[4]       
                # Get the container number
                container = row[5]
                # row[6] is the collection title, and we don't need that.
                
                # Form the child object JSON... now messier, since it may or may not have top container data (but at least we won't have to create or delete those)
                new_component = create_child_component()
                print ('Archival Object status:', new_component['id'], new_component['status'])
                new_component_uri = new_component['uri']
                # Add the uri to the outfile
                row.append(new_component_uri)

                # Create events, if those are specificed in the file, and then add a row to the out file
                # should update this so that column numbers aren't needed
                if original_row_length > 9 and row[7] != '':
                    new_event = create_event(row[7], row[8], row[9], cgi.escape(row[10]))
                    print ('Event status:', new_event['id'], new_event['status'])	
                    row.append(new_event['uri'])
                if original_row_length > 13 and row[13] != '':
                    new_event = create_event(row[11], row[12], row[13], cgi.escape(row[14]))
                    print ('Event status:', new_event['id'], new_event['status'])	
                    row.append(new_event['uri'])
                if original_row_length > 17 and row[15] != '':
                    new_event = create_event(row[15], row[16], row[17], cgi.escape(row[18]))
                    print ('Event status:', new_event['id'], new_event['status'])	
                    row.append(new_event['uri'])
                if original_row_length > 21 and row[19] != '':
                    new_event = create_event(row[19], row[20], row[21], cgi.escape(row[22]))
                    print ('Event status:', new_event['id'], new_event['status'])	
                    row.append(new_event['uri'])

                with open(archival_objects_updated,'a', newline='') as csvout:
                    writer = csv.writer(csvout)
                    writer.writerow(row)
                        
        print('Input file completely processed. Please check the ' + archival_objects_updated + ' file.')
