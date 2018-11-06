from kubernetes import client, config
from pprint import pprint
from kubernetes.client.rest import ApiException
import time
from httplib2 import Http
from json import dumps
import os

nodeToPodsDict = {}
clusterName = ""
queryTime = 60
hangoutThreadURL = ""

def loadK8SConfig():
    if 'KUBERNETES_PORT' in os.environ:
        config.load_incluster_config()
    else:
        config.load_kube_config()

loadK8SConfig()
api_instance = client.CoreV1Api()

def readENVVariables():
    clusterName = os.environ['CLUSTER_NAME']
    queryTime = float(os.environ['QUERY_TIME'])
    hangoutThreadURL = os.environ['HANGOUT_URL']
    return clusterName,queryTime,hangoutThreadURL

def getWorkerNodesStatus():
    node_list = []
    try:
        print("Getting Nodes' Status") 
        # Get nodes from k8s api
        api_response = api_instance.list_node(include_uninitialized=True, pretty='true')
        node_list = api_response.items
        #Find nodes where Ready status is false
        unreadyNodes = getUnreadyNodes(node_list)
        #mapPodsToNode()
        #Send alerts for nodes not ready
        if len(unreadyNodes) != 0:
            sendNodeNotReadyAlert(createAlertMessage(unreadyNodes))
    except ApiException as e:
        print("Exception when calling CoreV1Api->list_node: %s\n" % e)

def getUnreadyNodes(node_list):
    unreadyNodes = []
    for node in node_list:
        nodeToPodsDict[node.metadata.name] = []
        node_ready = True
        node_status = node.status.conditions
        for current_status in node_status:
            if current_status.type == 'Ready' and current_status.status == "False":
                node_ready = False
                unreadyNodes.append(node)
        
        print(node.metadata.name + " ready: " + str(node_ready))
    return unreadyNodes

def mapPodsToNode():
    try: 
        api_response = api_instance.list_pod_for_all_namespaces()
        pods_list = api_response.items
        for pod in pods_list:
            nodeToPodsDict[pod.spec.node_name].append(pod.metadata.name)
    except ApiException as e:
        print("Exception when calling CoreV1Api->list_pod_for_all_namespaces: %s\n" % e)

def createAlertMessage(unreadyNodes):
    if len(unreadyNodes) == 0:
        return ""
    alert_string = "<users/all> NODES NOT READY in "+clusterName+"\n"
    node_string = "Unready Nodes\n"

    for node in unreadyNodes:
        node_string += node.metadata.name + "\n"
    alert_string += node_string
    return alert_string

def sendNodeNotReadyAlert(alertMesage):
    webhook_uri = hangoutThreadURL
    bot_message = {
        'text' : alertMesage}

    message_headers = { 'Content-Type': 'application/json; charset=UTF-8'}

    http_obj = Http()

    response = http_obj.request(
        uri=webhook_uri,
        method='POST',
        headers=message_headers,
        body=dumps(bot_message),
    )

clusterName,queryTime,hangoutThreadURL = readENVVariables()

print("Starting Kubernetes Monitor")
while True:
    getWorkerNodesStatus()
    time.sleep(queryTime)