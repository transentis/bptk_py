import sys, os
import docker
import time
from conf import release

def build_container(ver=release,tag="transentis/bptk_py"):


    build_tag = "{}:{}".format(tag,ver)
    latest_tag = "{}:latest".format(tag)
    print("-------------------------")
    print("Building Container and Pushing to Dockerhub")
    print("-------------------------")
    print("Building for Tag: " + str(build_tag))
    print("Sleeping for 10 seconds. If this version is wrong, please press CTRL+C and fix the release in conf.py")
    for i in range(10, 0, -1):
        sys.stdout.write(str(i) + ' ')
        sys.stdout.flush()
        time.sleep(1)

    client = docker.APIClient()

    ## Build Container

    from io import BytesIO
    i = 0
    dockerfile = open("Dockerfile", "r").read()
    for line in client.build(fileobj=BytesIO(dockerfile.encode('utf-8')), rm=True, tag=build_tag, decode=True):
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