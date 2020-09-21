FROM jupyter/minimal-notebook

CMD ["start.sh","jupyter","lab","--LabApp.token=''","--ip=0.0.0.0"]

USER $NB_UID
RUN mkdir /home/jovyan/bptk
COPY ./BPTK_Py /home/jovyan/bptk/BPTK_Py
COPY ./requirements.txt /home/jovyan/bptk/
COPY ./requirements-dev.txt /home/jovyan/bptk/
COPY ./setup.py /home/jovyan/bptk/
COPY ./conf.py /home/jovyan/bptk/
COPY ./README.md /home/jovyan/bptk/
RUN pip install tornado nodejs widgetsnbextension && pip install -r /home/jovyan/bptk/requirements-dev.txt && pip install /home/jovyan/bptk
RUN jupyter nbextension enable --py widgetsnbextension && jupyter labextension install @jupyter-widgets/jupyterlab-manager
USER root

RUN rm -rf /home/jovyan/bptk/
USER $NB_UID