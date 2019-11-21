FROM ubuntu:18.04
MAINTAINER transentis 
RUN apt-get update && apt-get install -y apt-transport-https
RUN apt-get update && apt-get install python3-pip python3 nodejs npm -y
RUN mkdir /bptk-py
WORKDIR /bptk-py 
RUN pip3 install scipy numpy matplotlib statsmodels boto3 BPTK-Py sklearn pyzmq>=17 tornado jupyterlab elasticsearch keras tensorflow nodejs
RUN jupyter labextension install @jupyter-widgets/jupyterlab-manager
RUN jupyter nbextension enable --py widgetsnbextension
CMD /usr/local/bin/jupyter lab --NotebookApp.token='' --allow-root --ip=0.0.0.0
