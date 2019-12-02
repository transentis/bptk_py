FROM jupyter/base-notebook

USER root
RUN apt-get update
RUN apt-get install npm git -y

CMD ["start.sh","jupyter","lab","--LabApp.token=''","--ip=0.0.0.0"]

USER $NB_UID

RUN pip install tornado jupyterlab nodejs widgetsnbextension bptk_py
RUN jupyter nbextension enable --py widgetsnbextension
RUN jupyter labextension install @jupyter-widgets/jupyterlab-manager
