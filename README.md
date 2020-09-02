# Quantify

mkdir virt_env
virtualenv virt_env/virt1 --no-site-packages
source virt_env/virt1/bin/activate
pip install -r requirements.txt (might need sudo)
mongod (make sure that mongo is runing in the background, might need sudo. Leave mongo running, in a new terminal, run 'mongo' to access console)
python application.py


mongorestore --dbpath /gifgif_dump
http://docs.mongodb.org/manual/reference/program/mongorestore/