FROM python:3-onbuild
MAINTAINER Aleksey Pauls 'aleksey.pauls@mail.ru'
EXPOSE 5000
CMD ["python", "./countries_lib_server.py"]
