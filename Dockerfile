FROM jupyter/minimal-notebook

CMD ["start.sh","jupyter","lab","--LabApp.token=''","--ip=0.0.0.0"]

USER $NB_UID

RUN pip install tornado nodejs widgetsnbextension bptk_py==1.1.0
RUN jupyter nbextension enable --py widgetsnbextension
RUN jupyter labextension install @jupyter-widgets/jupyterlab-manager