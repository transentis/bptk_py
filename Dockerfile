FROM jupyter/base-notebook

USER root
RUN apt-get update
RUN apt-get install npm git -y

CMD ["start.sh","jupyter","lab","--LabApp.token=''","--ip=0.0.0.0"]

USER $NB_UID

RUN pip install scipy numpy matplotlib statsmodels boto3 BPTK-Py sklearn pyzmq>=17 tornado jupyterlab elasticsearch keras tensorflow nodejs
RUN jupyter nbextension enable --py widgetsnbextension
RUN jupyter labextension install @jupyter-widgets/jupyterlab-manager
