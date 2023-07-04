FROM library/python:3.11

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY filedrop /filedrop

VOLUME /filestore
ENV FD_FS_PATH /filestore
VOLUME /filedrop.db
ENV FD_DB_PATH /filedrop.db

EXPOSE 5000
WORKDIR /
CMD [ "gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "--access-logfile", "-", "filedrop.srv:create_app(gunicorn=True)" ]
