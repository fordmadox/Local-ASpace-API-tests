#Python3
import json, csv, requests, authenticate, runtime, pathlib

#this is all hacky for now, but just getting things to function for the time being.  will go back to the regular export process later this week.

def get_resource_ids(repo_id=None):
    timestamp = 1325394000 #2012/01/01
    endpoint = '/resource-update-feed'
    params={"timestamp": timestamp, "repo_id": repo_id}
    response = requests.get(baseURL + endpoint, headers=headers, params=params).json()
    adds = response['adds']
    return adds

def export_ead():
    directory = input("Enter the directory where you'd like to save the EAD exports: ")
    export_options = "?include_daos=true&include_unpublished=true&ead3=true"
    repo_id = input("Enter the repo ID: ")
    adds = get_resource_ids(repo_id)

    pathlib.Path(directory).mkdir(exist_ok=True)

    for x in adds:
        resource_id = str(x['id'])
        print(resource_id)
        try:
            ead = requests.get(baseURL + '/repositories/'+repo_id+'/resource_descriptions/'+resource_id+'.xml'+export_options, headers=headers).text
            f = open(directory + '/' + resource_id +'.xml', 'wb')
            f.write(ead.encode('utf-8'))
            f.close
            print('Exported EAD file for' + resource_id)
        except Exception as ex:
            print('Skipping invalid row for %s. Exception: %s\n', resource_id, ex)
            continue

def main():
    export_ead()

if __name__ == '__main__':
    baseURL, headers = authenticate.login()
    main()
