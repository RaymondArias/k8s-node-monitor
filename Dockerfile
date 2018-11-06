FROM python:2.7
RUN pip install kubernetes httplib2
RUN mkdir /app
COPY src/ /app
WORKDIR /app/
CMD ["python", "-u", "cluster-monitor.py"]