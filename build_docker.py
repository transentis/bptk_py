import sys, os
import docker
import time
from conf import release

def build_container(ver=release,tag="transentis/bptk-py"):

    build_tag = "{}:{}".format(tag,ver)
    latest_tag = "{}:latest".format(tag)
    print("-------------------------")
    print("Building Container and Pushing to Dockerhub")
    print("-------------------------")
    print("Building for Tag: " + str(build_tag))

    client = docker.APIClient()

    ## Build Container

    from io import BytesIO
    i = 0
    dockerfile = open("Dockerfile", "r").read()
    fileobj=BytesIO(dockerfile.encode('utf-8'))
    for line in client.build(path=".", rm=True, tag=build_tag, decode=True):
        try:
            print(line["stream"])
        except KeyError:
            try:
                print(line["status"])
            except:
                print(line)

    ## Push Container
    for line in client.push(build_tag, stream=True, decode=True):
        i += 1
        try:
            print(line["status"])
        except KeyError:
            print(line)

    ## Tag for latest
    client.tag(build_tag,latest_tag)

    for line in client.push(latest_tag, stream=True, decode=True):
        i += 1
        try:
            print(line["status"])
        except KeyError:
            print(line)

build_container(tag="transentis/bptk-py")

sys.exit(os.EX_OK)
