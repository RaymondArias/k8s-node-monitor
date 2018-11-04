from kubernetes import client, config
from pprint import pprint
from kubernetes.client.rest import ApiException
import time

nodeToPodsDict = {}

clusterName = "minikube"

def loadK8SConfig():
    config.load_kube_config()

loadK8SConfig()
api_instance = client.CoreV1Api()

def getWorkerNodesStatus():
    node_list = []
    try: 
        # Get nodes from k8s api
        api_response = api_instance.list_node(include_uninitialized=True, pretty='true')
        node_list = api_response.items
        #Find nodes where Ready status is false
        unreadyNodes = getUnreadyNodes(node_list)
        mapPodsToNode()
        #Send alerts for nodes not ready
        createAlertMessage(unreadyNodes)
    except ApiException as e:
        print("Exception when calling CoreV1Api->list_node: %s\n" % e)

def getUnreadyNodes(node_list):
    unreadyNodes = []
    for node in node_list:
        nodeToPodsDict[node.metadata.name] = []
        node_ready = True
        node_status = node.status.conditions
        for current_status in node_status:
            if current_status.type == 'Ready' and current_status.status != "True":
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
        return
    alert_string = "NODES NOT READY in "+clusterName+"\n"
    node_string = ""

    for node in unreadyNodes:
        tmp_str = "Node: "+node.metadata.name +"\nPods on Node\n"
        podsOnNode = nodeToPodsDict[node.metadata.name]
        for pod in podsOnNode:
            tmp_str += "    - " + pod + "\n"
        node_string += tmp_str
    alert_string += node_string
    print(alert_string)

print("Starting Kubernetes Monitor")
while True:
    getWorkerNodesStatus()
    time.sleep(10)