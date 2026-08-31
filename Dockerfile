FROM python:3.11

# Create the user that will run the app
RUN adduser --disabled-password --gecos '' ml-api-user


WORKDIR /opt/ml_api

ENV FLASK_APP=run.py

ADD ./packages/ml_api /opt/ml_api/

# The model package is downloaded from its GitHub Release before the build
# (see the Makefile) and installed from the local wheel, so the image records
# exactly which trained model it ships.
COPY model_pkg/*.whl /tmp/

RUN pip install --upgrade pip
RUN pip install /tmp/*.whl
RUN pip install -r /opt/ml_api/requirements.txt

RUN chmod +x /opt/ml_api/run.sh
RUN chown -R ml-api-user:ml-api-user ./

USER ml-api-user

EXPOSE 5000

CMD ["bash", "./run.sh"]